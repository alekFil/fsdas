from pathlib import Path
from typing import Any

import joblib


def load_resources(resources_type: str, file_type: str) -> Any:
    """
    Загрузка ресурсов из файла.

    Parameters
    ----------
    resources_type : str
        Тип ресурса (например, "vectorizer", "reference_vec").
    file_type : str
        Тип файла (например, "joblib").

    Returns
    -------
    Any
        Загруженные ресурсы.

    Raises
    ------
    ValueError
        Если указан неподдерживаемый тип файла.
    """
    # Формируем путь к файлу с ресурсами
    model_path = (
        Path("app/services/school_matcher/resources") / f"{resources_type}.{file_type}"
    )

    # Проверка типа файла и загрузка ресурсов
    if file_type == "joblib":
        with open(model_path, "rb") as file:
            resources = joblib.load(file)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")

    return resources
