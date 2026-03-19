"""Модуль отчётов — аналитические отчёты по транзакциям."""

import json
from datetime import datetime
from typing import Optional

import pandas as pd

from src.config import load_config
from src.logger import get_logger

logger = get_logger(__name__)

DEFAULT_WEEKDAY_NAMES = [
    "Понедельник",
    "Вторник",
    "Среда",
    "Четверг",
    "Пятница",
    "Суббота",
    "Воскресенье",
]


def spending_by_weekday(
    df: pd.DataFrame,
    date: Optional[str] = None,
) -> str:
    """
    Возвращает средние траты по дням недели за последние три месяца.

    Анализируется период из трёх месяцев до указанной даты включительно.
    Учитываются только расходные операции (отрицательные суммы).
    Названия дней недели берутся из config.json (поле weekday_names).
    По умолчанию используется текущая дата.

    :arg df: DataFrame с данными транзакций.
    :arg date: Дата отсчёта в формате 'YYYY-MM-DD'. По умолчанию — сегодня.
    :return: JSON-строка со средними тратами по дням недели.
    """
    end_date = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now().replace(hour=23, minute=59, second=59)
    start_date = end_date.replace(
        month=((end_date.month - 4) % 12) + 1,
        day=1,
        hour=0,
        minute=0,
        second=0,
    )
    if end_date.month <= 3:
        start_date = start_date.replace(year=end_date.year - 1)

    logger.info(
        "Отчёт по дням недели: период с %s по %s",
        start_date.date(),
        end_date.date(),
    )

    day_names = load_config().get("weekday_names", DEFAULT_WEEKDAY_NAMES)

    data = df.copy()
    data["Дата операции"] = pd.to_datetime(
        data["Дата операции"],
        format="%d.%m.%Y %H:%M:%S",
    )

    mask = (data["Дата операции"] >= start_date) & (data["Дата операции"] <= end_date) & (data["Сумма операции"] < 0)
    expenses = data[mask].copy()

    if expenses.empty:
        result = [{"day": day, "amount": 0.0} for day in day_names]
        logger.info("Нет данных за указанный период")
        return json.dumps(result, ensure_ascii=False, indent=2)

    expenses["weekday"] = expenses["Дата операции"].dt.weekday
    expenses["amount"] = expenses["Сумма операции"].abs()

    avg_by_day = expenses.groupby("weekday")["amount"].mean().reindex(range(7), fill_value=0.0)

    result = [{"day": day_names[i], "amount": round(float(avg_by_day[i]), 2)} for i in range(7)]

    logger.info("Отчёт по дням недели сформирован")
    return json.dumps(result, ensure_ascii=False, indent=2)
