"""Модуль сервисов — аналитические функции над транзакциями."""

import json
from typing import Any

from src.logger import get_logger

logger = get_logger(__name__)


def simple_search(
    query: str,
    transactions: list[dict[str, Any]],
) -> str:
    """Выполняет поиск транзакций по строке запроса.

    Поиск регистронезависимый, выполняется по полям «Описание» и «Категория».

    :param query: Строка поискового запроса.
    :param transactions: Список транзакций в формате списка словарей.
    :return: JSON-строка со списком подходящих транзакций.
    """
    logger.info("Простой поиск по запросу: '%s'", query)

    query_lower = query.lower()
    result = []
    for tx in transactions:
        in_description = query_lower in str(tx.get("Описание", "")).lower()
        in_category = query_lower in str(tx.get("Категория", "")).lower()
        if in_description or in_category:
            result.append(tx)

    logger.info("Найдено транзакций: %d", len(result))

    return json.dumps(result, ensure_ascii=False, indent=2)
