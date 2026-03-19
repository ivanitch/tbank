"""Модуль настройки логирования.

Импортирует только из src.config — нет циклических зависимостей.
"""
import logging
import os
import sys
from typing import Optional

from src.config import get_path, load_config


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Создаёт и возвращает настроенный логгер с выводом в файл и консоль.

    :param name: Имя логгера (используется как имя файла лога).
        Если не передан — используется корневой логгер.
    :return: Настроенный экземпляр logging.Logger.
    """
    log_dir = get_path("logs")
    os.makedirs(log_dir, exist_ok=True)

    logger = logging.getLogger(name)

    if not logger.handlers:
        log_level = load_config().get("params", {}).get("log_level", "INFO").upper()
        logger.setLevel(log_level)

        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

        # Запись в файл
        log_filename = f"{name}.log" if name else "app.log"
        file_handler = logging.FileHandler(
            os.path.join(log_dir, log_filename),
            mode="w",
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Вывод в консоль
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger
