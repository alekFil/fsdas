import itertools
import re
from typing import Dict, List, Union

import nltk
import pymorphy3
from nltk.tokenize import word_tokenize
from num2words import num2words

from app.core.logger import setup_logger

# Загружаем необходимые ресурсы
nltk.download("punkt", quiet=True)
nltk.download("punkt_tab", quiet=True)

# Инициализация морфологического анализатора для русского языка
morph = pymorphy3.MorphAnalyzer()

# Инициализируем логгер для school_matcher
logger = setup_logger("school_matcher", "app/logs/school_matcher/logs.log")


def simple_preprocess_text(text: str) -> str:
    """
    Простая предобработка текста: удаление служебных символов, пунктуации, отдельных букв, лишних пробелов и замена букв "ё".

    Parameters
    ----------
    text : str
        Исходный текст.

    Returns
    -------
    str
        Предобработанный текст.
    """
    # Удаляем служебные символы (перенос строки, табуляция и т.д.)
    text = re.sub(r"[\n\t\r]", " ", text)

    # Удаление пунктуации
    text = re.sub(r"[^\w\s]", " ", text)

    # Удаление отдельных букв
    text = re.sub(r"\b[А-ЯЁа-яё]\b", " ", text)

    # Замена букв ё
    text = re.sub(r"[Ёё]", "е", text)

    # Регулярное выражение для поиска различных обозначений номера, включая случаи, когда за ними сразу идут цифры
    pattern = re.compile(r"\b(?:No|no|N|NO|№)(\d*)\b")

    # Замена найденных обозначений на "номер"
    text = pattern.sub(lambda match: f" {match.group(1)}", text)

    # Удаление лишних пробелов
    text = re.sub(r"\s+", " ", text)

    # Удаление пробелов в начале и в конце
    text = text.strip()

    return text


def replace_numbers_with_text(text: str) -> str:
    """
    Замена чисел в тексте на их текстовое представление.

    Parameters
    ----------
    text : str
        Исходный текст.

    Returns
    -------
    str
        Текст с замененными числами.
    """

    # Функция для замены чисел на их текстовое представление
    def num_to_text(match):
        num = match.group(0)
        return num2words(int(num), lang="ru")

    # Регулярное выражение для поиска чисел
    pattern = re.compile(r"\d+")

    # Замена чисел на текст
    return pattern.sub(num_to_text, text)


def abbr_preprocess_text(
    name: str,
    abbreviation_dict: Dict[str, Union[str, List[str]]],
    output_list: bool = False,
    unknown_answer: bool = False,
    remove_unknown_abbr: bool = False,
    remove_all_abbr: bool = False,
) -> Union[str, List[str]]:
    """
    Предобработка текста с учетом сокращений и аббревиатур.

    Parameters
    ----------
    name : str
        Исходный текст.
    abbreviation_dict : Dict[str, Union[str, List[str]]]
        Словарь сокращений и аббревиатур.
    output_list : bool, optional
        Флаг для вывода списка всех возможных комбинаций (default is False).
    unknown_answer : bool, optional
        Флаг для возврата списка неизвестных аббревиатур (default is False).
    remove_unknown_abbr : bool, optional
        Флаг для удаления неизвестных аббревиатур (default is False).
    remove_all_abbr : bool, optional
        Флаг для удаления всех аббревиатур (default is False).

    Returns
    -------
    Union[str, List[str]]
        Обработанный текст или список всех возможных комбинаций.
    """
    two_letter_prepositions = [
        " в ",
        " во ",
        " до ",
        " из ",
        " на ",
        " по ",
        " о ",
        " об ",
        " обо ",
        " у ",
    ]

    symbols = [" no", " NO", " No", "номер"]

    # Удаляем служебные символы (перенос строки, табуляция и т.д.)
    name = re.sub(r"[\n\t\r]", " ", name)

    # Создаем регулярное выражение для предлогов
    prepositions_pattern = (
        r"\b(?:" + "".join(two_letter_prepositions) + "".join(symbols) + r")\b"
    )

    # Заменяем все предлоги на пробел (предварительное решение
    # вместо трудоемкого удаления стоп-слов)
    name = re.sub(prepositions_pattern, " ", name)

    # Удаление пунктуации
    name = re.sub(r"[^\w\s]", " ", name)

    # Удаление отдельных букв
    name = re.sub(r"\b[А-ЯЁа-яё]\b", " ", name)

    # Удаление букв ё
    name = re.sub(r"[Ёё]", "е", name)

    unknown_abbr = []
    # Находим аббревиатуры большими буквами и приводим их к нижнему регистру
    # Надо уточнить поиск неизвестных.
    # А если в конце аббревиатуры прописная буква?
    uppercase_abbreviations = re.findall(r"\b[А-ЯЁа-яё]+[а-яё]*[А-ЯЁ]+\b", name)
    for abbr in uppercase_abbreviations:
        abbr = abbr.lower()
        if abbr not in abbreviation_dict:
            unknown_abbr.append(abbr.upper())
            logger.info(unknown_abbr)
            if remove_unknown_abbr:
                name = re.sub(r"\b" + re.escape(abbr.upper()) + r"\b", " ", name)

    # Удаление лишних пробелов
    name = re.sub(r"\s+", " ", name)

    # Удаление пробелов в начале и в конце
    name = name.strip()

    possible_replacements = []
    parts = name.lower().split()

    for part in parts:
        if part in abbreviation_dict:
            if not remove_all_abbr:
                replacements = abbreviation_dict[part]
                if isinstance(replacements, str):
                    replacements = [replacements]
                elif not output_list:
                    replacements = [""]
                possible_replacements.append(replacements)
            else:
                pass
        else:
            possible_replacements.append([part])

    # Генерируем все возможные комбинации
    all_combinations = list(itertools.product(*possible_replacements))

    # Формируем итоговые наименования
    final_phrases = [" ".join(combination).strip() for combination in all_combinations]

    if not output_list:
        final_phrases = final_phrases[0]

    if unknown_answer:
        return list(set(unknown_abbr))

    return final_phrases


def process_region(
    text: str, region_list: List[str], return_region: bool = False
) -> Union[str, Union[str, None]]:
    """
    Функция находит в тексте регион из списка регионов, удаляет его и возвращает
    либо новый текст без региона, либо регион в зависимости от флага return_region.

    Parameters
    ----------
    text : str
        Исходный текст.
    region_list : List[str]
        Список регионов для поиска.
    return_region : bool, optional
        Если True, возвращает найденный регион, иначе возвращает
        текст без региона (default is False).

    Returns
    -------
    Union[str, Union[str, None]]
        Либо новый текст без региона, либо найденный регион.
    """
    for region in region_list:
        # Используем регулярное выражение для точного поиска региона
        pattern = re.compile(r"\b" + re.escape(region) + r"\b", re.IGNORECASE)
        match = pattern.search(text)
        if match:
            found_region = match.group(0)
            new_text = pattern.sub("", text).strip()
            return found_region if return_region else new_text
    return None if return_region else text


def remove_substrings(input_string: str, substrings: List[str]) -> str:
    """
    Удаляет все подстроки из списка из исходной строки.

    Parameters
    ----------
    input_string : str
        Исходная строка.
    substrings : List[str]
        Список подстрок для удаления.

    Returns
    -------
    str
        Строка без подстрок.
    """
    for substring in substrings:
        input_string = input_string.replace(substring, "").strip()
    return input_string


def process_cities(
    text: str, region_list: Dict[str, List[str]], return_city: bool = False
) -> Union[str, Union[str, None]]:
    """
    Функция находит в тексте город из списка регионов, удаляет его и возвращает
    либо новый текст без города, либо город в зависимости от флага return_city.

    Parameters
    ----------
    text : str
        Исходный текст.
    region_list : Dict[str, List[str]]
        Список городов по регионам для поиска.
    return_city : bool, optional
        Если True, возвращает найденный город, иначе возвращает
        текст без города (default is False).

    Returns
    -------
    Union[str, Union[str, None]]
        Либо новый текст без города, либо найденный город.
    """
    for cities_list in region_list.values():
        for city in cities_list:
            # Используем регулярное выражение для точного поиска региона
            pattern = re.compile(r"\b" + re.escape(city) + r"[а-я]*\b", re.IGNORECASE)
            match = pattern.search(text)
            if match:
                found_city = match.group(0)
                new_text = pattern.sub("", text).strip()
                return found_city if return_city else new_text
    return None if return_city else text


def lemmatize_text(text: str, stop_words_list: List[str]) -> str:
    """
    Лемматизация текста и удаление стоп-слов.

    Parameters
    ----------
    text : str
        Исходный текст.
    stop_words_list : List[str]
        Список стоп-слов для удаления.

    Returns
    -------
    str
        Лемматизированный текст без стоп-слов.
    """
    # Токенизация
    words = word_tokenize(text.lower(), language="russian")

    # Лемматизация
    lemmatized_words = [morph.parse(word)[0].normal_form for word in words]

    # Удаление стоп-слов
    filtered_words = [word for word in lemmatized_words if word not in stop_words_list]

    return " ".join(filtered_words)


def remove_short_words(text: str) -> str:
    """
    Удаляет слова короче двух символов из текста.

    Parameters
    ----------
    text : str
        Исходный текст.

    Returns
    -------
    str
        Текст без коротких слов.
    """
    words = text.split()  # разбиваем текст на слова
    filtered_words = [
        word for word in words if len(word) > 2
    ]  # фильтруем слова длиннее двух символов
    return " ".join(filtered_words)  # объединяем отфильтрованные слова в строку
