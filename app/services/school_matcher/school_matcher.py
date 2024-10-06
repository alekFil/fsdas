import os
import shutil

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import (
    cosine_similarity,
    euclidean_distances,
    manhattan_distances,
)
from sqlalchemy.orm import sessionmaker

from app.core.logger import setup_logger
from app.services.school_matcher.utils.load_functions import load_resources
from app.services.school_matcher.utils.preprocess_functions import (
    abbr_preprocess_text,
    lemmatize_text,
    process_region,
    remove_short_words,
    remove_substrings,
    replace_numbers_with_text,
    simple_preprocess_text,
)

# Инициализируем логгер для school_matcher
logger = setup_logger("school_matcher", "app/logs/school_matcher/logs.log")


def calculate_similarity(
    x: np.ndarray, y: np.ndarray, method: str = "cosine"
) -> np.ndarray:
    """
    Вычисляет схожесть между двумя векторами с использованием указанного метода.

    Parameters
    ----------
    x : np.ndarray
        Первый вектор.
    y : np.ndarray
        Второй вектор.
    method : str, optional
        Метод вычисления схожести. Может быть "cosine", "euclidean"
        или "manhattan" (default is "cosine").

    Returns
    -------
    np.ndarray
        Массив схожестей.
    """
    if method == "cosine":
        return cosine_similarity(x, y)
    elif method == "euclidean":
        return -euclidean_distances(x, y)  # Инвертируем, чтобы максимизировать схожесть
    elif method == "manhattan":
        return -manhattan_distances(x, y)  # Инвертируем, чтобы максимизировать схожесть
    else:
        raise ValueError(f"Unknown similarity method: {method}")


def find_matches(
    x_vec: np.ndarray,
    x_region: np.ndarray,
    reference_id: np.ndarray,
    reference_vec: np.ndarray,
    reference_region: np.ndarray,
    top_k: int = 5,
    threshold: float = 0.9,
    filter_by_region: bool = True,
    empty_region: str = "all",
    similarity_method: str = "cosine",
):
    """
    Находит совпадения для заданных векторов с использованием
    различных методов схожести и фильтрации по регионам.

    Parameters
    ----------
    x_vec : np.ndarray
        Векторизованные названия школ.
    x_region : np.ndarray
        Регионы для векторов названий школ.
    reference_id : np.ndarray
        Идентификаторы референсных школ.
    reference_vec : np.ndarray
        Векторизованные референсные названия школ.
    reference_region : np.ndarray
        Регионы для референсных школ.
    top_k : int, optional
        Количество топ-совпадений, которые нужно вернуть (default is 5).
    threshold : float, optional
        Порог схожести для отбора совпадений (default is 0.9).
    filter_by_region : bool, optional
        Флаг для включения фильтрации по регионам (default is True).
    empty_region : str, optional
        Способ обработки, если в текущем регионе нет школ для сравнения (default is "all").
    similarity_method : str, optional
        Метод вычисления схожести (default is "cosine").

    Returns
    -------
    Tuple[List[List[Tuple[Union[int, None], float]]], List[np.ndarray]]
        Список совпадений и список для ручной обработки.
    """
    y_pred = []
    manual_review = []

    for i, x in enumerate(x_vec):
        # Фильтруем reference_vec и reference_id по текущему региону,
        # если включена фильтрация по регионам
        if filter_by_region:
            # Фильтруем reference_vec и reference_id по текущему региону
            current_region = x_region[i]
            region_mask = reference_region == current_region
            filtered_reference_vec = reference_vec[region_mask]
            filtered_reference_id = reference_id[region_mask]

            # Способ обработки, если в текущем регионе нет школ для сравнения
            if empty_region == "all":
                # Если в текущем регионе нет школ для сравнения, используем все школы
                if filtered_reference_vec.shape[0] == 0:
                    filtered_reference_vec = reference_vec
                    filtered_reference_id = reference_id
            else:
                if filtered_reference_vec.shape[0] == 0:
                    # Если в текущем регионе нет школ для сравнения,
                    # то помечаем на ручную обработку
                    manual_review.append(x)
                    top_matches = [(None, 0.0)] * top_k
                    y_pred.append(top_matches)
                    continue
        else:
            filtered_reference_vec = reference_vec
            filtered_reference_id = reference_id

        # Вычисляем выбранное расстояние
        similarities = calculate_similarity(
            x, filtered_reference_vec, method=similarity_method
        ).flatten()
        top_indices = similarities.argsort()[-top_k:][::-1]
        max_similarity = max(similarities)

        # Учитываем пороговое значение для различных методов
        if similarity_method == "cosine":
            if max_similarity < threshold:
                manual_review.append(x)
                top_matches = [(None, 0.0)] * top_k
            else:
                top_matches = [
                    (filtered_reference_id[i], similarities[i]) for i in top_indices
                ]
                if len(top_matches) < top_k:
                    top_matches += [(None, 0.0)] * (top_k - len(top_matches))
        else:  # Для других методов расстояний (евклидово и манхэттенское)
            if max_similarity > -threshold:  # Обратим внимание на инверсию
                manual_review.append(x)
                top_matches = [(None, 0.0)] * top_k
            else:
                top_matches = [
                    (filtered_reference_id[i], -similarities[i]) for i in top_indices
                ]
                if len(top_matches) < top_k:
                    top_matches += [(None, 0.0)] * (top_k - len(top_matches))

        y_pred.append(top_matches)

    return y_pred, manual_review


class SchoolMatcher:
    def __init__(self, engine):
        self.engine = engine
        self.Session = sessionmaker(bind=engine)
        self.resources_dir = "app/services/school_matcher/resources"
        self.original_dir = "app/services/school_matcher/original_resources"
        self.ensure_resources_exist()
        self.load_resources()

    def ensure_resources_exist(self):
        """
        Проверяет, существует ли ресурсная директория и содержатся ли там необходимые файлы.
        Если файлы отсутствуют, копирует их из директории original_resources.
        """
        logger.info("Copy resources")
        if not os.path.exists(self.resources_dir):
            os.makedirs(self.resources_dir)

        files_to_copy = os.listdir(self.original_dir)

        for file in files_to_copy:
            original_file = os.path.join(self.original_dir, file)
            destination_file = os.path.join(self.resources_dir, file)
            if not os.path.exists(destination_file):
                logger.debug(
                    f"Copy {file} from {self.original_dir} " f"to {self.resources_dir}"
                )
                shutil.copy(original_file, destination_file)
            else:
                logger.debug(
                    "File {file} is existed in {self.resources_dir}, coping is passed"
                )

    def load_resources(self):
        logger.info("Load resources")
        self.vectorizer = load_resources("vectorizer", "joblib")
        self.reference_vec = load_resources("reference_vec", "joblib")
        self.reference_id = load_resources("reference_id", "joblib")
        self.reference_region = load_resources("reference_region", "joblib")
        self.reference_name = load_resources("reference_name", "joblib")
        self.abbreviations_dict = load_resources("abbreviations_dict", "joblib")
        self.region_dict = load_resources("region_dict", "joblib")
        self.blacklist_opf = load_resources("blacklist_opf", "joblib")
        self.stop_words_list = load_resources("stop_words_list", "joblib")
        logger.info("Resources is loaded/updated")

    def find_school_match(self, school_name):
        """
        Предсказывает соответствия для заданного названия школы.

        Parameters
        ----------
        school_name : str
            Название школы.

        Returns
        -------
        List[int]
            Список id наиболее вероятных совпадений.
        """

        def preprocess_name(x: str) -> str:
            """
            Предобрабатывает название школы.

            Parameters
            ----------
            x : str
                Название школы.

            Returns
            -------
            str
                Предобработанное название школы.
            """
            x = simple_preprocess_text(x)
            x = replace_numbers_with_text(x)
            x = abbr_preprocess_text(
                x,
                self.abbreviations_dict,
                False,
                False,
                False,
                False,
            )
            x = process_region(x, self.region_dict)
            x = remove_substrings(x, self.blacklist_opf)
            x = lemmatize_text(x, self.stop_words_list)
            x = remove_short_words(x)
            return x

        def preprocess_region(x: str) -> str:
            """
            Предобрабатывает регион школы.

            Parameters
            ----------
            x : str
                Название школы.

            Returns
            -------
            str
                Регион школы.
            """
            x = simple_preprocess_text(x)
            x = replace_numbers_with_text(x)
            x = abbr_preprocess_text(
                x, self.abbreviations_dict, False, False, False, False
            )
            return process_region(x, self.region_dict, return_region=True)

        vectorized_preprocess = np.vectorize(preprocess_name)
        vectorized_region = np.vectorize(preprocess_region)

        x = vectorized_preprocess(np.array([school_name]))
        region = vectorized_region(np.array([school_name]))

        # Векторизация текста
        x_vec = self.vectorizer.transform(x)

        y_pred, manual_review = find_matches(
            x_vec,
            region,
            self.reference_id,
            self.reference_vec,
            self.reference_region,
            top_k=5,
            threshold=0.00000001,
            filter_by_region=True,
            empty_region="all",  # is ignored if filter_by_region=False
            similarity_method="cosine",
        )

        converted_results = [
            {
                "id": int(id_) if id_ is not None else -1,
                "score": float(score),
            }
            for id_, score in y_pred[0]
        ]

        return converted_results

    def create_resources(self):
        session = self.Session()

        try:
            # Выполняем запросы к базе данных
            query_schools = "SELECT id, name, region FROM schools"
            query_similar_schools = """
                SELECT ss.school_id, ss.name, s.name AS reference_name, s.region 
                FROM similar_schools AS ss 
                LEFT JOIN schools AS s ON ss.school_id = s.id
            """

            # Используем session.connection() для выполнения SQL запросов с Pandas
            data_reference = pd.read_sql(query_schools, session.connection())
            data_train = pd.read_sql(query_similar_schools, session.connection())

            # Логика создания ресурсов на основе данных
            if self.process_resource(data_reference, data_train[["school_id", "name"]]):
                print("Ресурсы созданы")

            # Если всё прошло успешно, коммитим транзакцию
            session.commit()

        except Exception as e:
            # В случае ошибки откатываем транзакцию
            print(f"Произошла ошибка при создании ресурсов: {e}")
            session.rollback()
            raise

        finally:
            # Закрываем сессию в любом случае
            session.close()

    def process_resource(self, data_reference, data_train):
        # preprocess data_reference
        data_reference.region = data_reference.region.apply(
            simple_preprocess_text
        ).str.lower()
        for reference_region in data_reference.region.sort_values().unique():
            if reference_region not in self.region_dict:
                for region in self.region_dict:
                    if reference_region in self.region_dict[region]:
                        data_reference.region = data_reference.region.str.replace(
                            f"{reference_region}", f"{region}"
                        )

        for reference_region in data_reference.region.sort_values().unique():
            if reference_region not in self.region_dict:
                print(f"Unknown region: {reference_region}")

        data_reference.region = data_reference.region.str.replace(
            "республика саха",
            "республика саха якутия",
        )
        data_reference.region = data_reference.region.str.replace(
            "республика чувашия",
            "чувашская республика",
        )
        data_reference.region = data_reference.region.str.replace(
            "хмао югра",
            "ханты мансийский автономный округ",
        )
        data_reference.region = data_reference.region.str.replace(
            "ямало ненецкий ао",
            "ямало ненецкий автономный округ",
        )
        data_reference.region = data_reference.region.str.replace(
            "бранская область",
            "брянская область",
        )
        data_reference.region = data_reference.region.str.replace(
            "воронежская обл",
            "воронежская область",
        )

        data_reference = data_reference[~data_reference.duplicated(subset="id")]
        data_reference = data_reference[~(data_reference.id == 99999)]

        data_reference["processed_name"] = data_reference.name.apply(
            simple_preprocess_text
        )
        data_reference.processed_name = data_reference.processed_name.apply(
            replace_numbers_with_text
        )
        data_reference.processed_name = data_reference.processed_name.apply(
            abbr_preprocess_text,
            args=(self.abbreviations_dict, False, False, False, False),
        )
        data_reference.processed_name = data_reference.processed_name.apply(
            process_region, args=(list(self.region_dict.keys()),)
        )
        data_reference.processed_name = data_reference.processed_name.apply(
            remove_substrings, args=(self.blacklist_opf,)
        )
        data_reference.processed_name = data_reference.processed_name.apply(
            simple_preprocess_text
        )
        data_reference.processed_name = data_reference.processed_name.apply(
            lemmatize_text, args=(self.stop_words_list,)
        )
        data_reference.processed_name = data_reference.processed_name.apply(
            remove_short_words
        )

        reference_id = data_reference["id"].to_numpy(dtype="int").flatten()
        reference_name = (
            data_reference["processed_name"].to_numpy(dtype="str").flatten()
        )
        reference_region = data_reference["region"].to_numpy(dtype="str").flatten()

        # preprocess data_train

        data_train = data_train.dropna()
        data_train["processed_name"] = data_train.name.apply(simple_preprocess_text)
        data_train.processed_name = data_train.processed_name.apply(
            replace_numbers_with_text
        )

        data_train.processed_name = data_train.processed_name.apply(
            abbr_preprocess_text,
            args=(self.abbreviations_dict, False, False, False, False),
        )
        data_train["region"] = data_train.processed_name.apply(
            process_region, args=(list(self.region_dict.keys()), True)
        )
        data_train.processed_name = data_train.processed_name.apply(
            process_region, args=(list(self.region_dict.keys()),)
        )
        data_train.processed_name = data_train.processed_name.apply(
            remove_substrings, args=(self.blacklist_opf,)
        )
        data_train.processed_name = data_train.processed_name.apply(
            simple_preprocess_text
        )
        data_train.processed_name = data_train.processed_name.apply(
            lemmatize_text, args=(self.stop_words_list,)
        )
        data_train.processed_name = data_train.processed_name.apply(remove_short_words)

        x_train = data_train["processed_name"].to_numpy(dtype="str").flatten()

        # Векторизация текстов
        vectorizer = TfidfVectorizer().fit(np.append(x_train, reference_name))

        reference_vec = vectorizer.transform(reference_name)

        joblib.dump(
            reference_id, "app/services/school_matcher/resources/reference_id.joblib"
        )
        joblib.dump(
            reference_name,
            "app/services/school_matcher/resources/reference_name.joblib",
        )
        joblib.dump(
            reference_region,
            "app/services/school_matcher/resources/reference_region.joblib",
        )
        joblib.dump(
            reference_vec, "app/services/school_matcher/resources/reference_vec.joblib"
        )
        joblib.dump(
            vectorizer, "app/services/school_matcher/resources/vectorizer.joblib"
        )

        return True
