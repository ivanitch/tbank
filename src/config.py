import json
import os
from typing import Any, Optional


def get_path(dir_or_file: Optional[str] = None) -> str:
    """Возвращает абсолютный путь относительно рабочей директории проекта.

    :arg dir_or_file: Относительный путь к файлу или директории.
        Если не передан — возвращает корень проекта.
    :return: Абсолютный путь в виде строки.
    """
    root_path = os.getcwd()
    if dir_or_file is None:
        return root_path
    return os.path.join(root_path, dir_or_file)


def load_config(path: Optional[str] = None) -> dict[str, Any]:
    """Загружает конфигурацию приложения из config.json.

    :arg path: Путь к файлу конфигурации. По умолчанию — config.json в корне проекта.
    :return: Словарь с конфигурацией приложения.
    """
    config_path = path or get_path("config.json")
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"params": {"log_level": "INFO"}, "currencies": [], "stocks": [], "api": {}}
