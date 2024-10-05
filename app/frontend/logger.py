import logging
import os


# Функция для настройки логирования
def setup_logger(name: str, log_file: str, level=logging.DEBUG):
    # Создаем директорию для логов, если она не существует
    log_dir = os.path.dirname(log_file)
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Создаем логгер с именем
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Создаем обработчик для записи логов в файл
    handler = logging.FileHandler(log_file)
    handler.setLevel(level)

    # Формат сообщений в логах
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Добавляем обработчик в логгер
    if not logger.handlers:
        logger.addHandler(handler)

    return logger
