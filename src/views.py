"""Модуль представлений — генерация JSON-ответов для веб-страниц."""

import json
from datetime import datetime
from typing import Optional

import pandas as pd

from src.config import load_config
from src.logger import get_logger
from src.utils import (
    filter_by_date_range,
    get_cards_info,
    get_currency_rates,
    get_date_range,
    get_expenses_data,
    get_greeting,
    get_income_data,
    get_stock_prices,
    get_top_transactions,
)

logger = get_logger(__name__)


def get_main_page(date_time_str: str, df: pd.DataFrame, config_path: Optional[str] = None) -> str:
    """Генерирует JSON-ответ для страницы «Главная».

    Принимает строку с датой и временем, возвращает JSON с приветствием,
    данными по картам, топ-5 транзакций, курсами валют и ценами акций из S&P 500.
    Диапазон данных: с начала месяца входящей даты по входящую дату.
    Конфигурация (валюты, акции, API) читается из config.json.

    :arg date_time_str: Строка с датой и временем в формате 'YYYY-MM-DD HH:MM:SS'.
    :arg df: DataFrame с данными транзакций.
    :arg config_path: Путь к config.json. По умолчанию — config.json в корне проекта.
    :return: JSON-строка с данными главной страницы.
    """
    logger.info("Формирование страницы «Главная» для даты: %s", date_time_str)

    dt = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
    start_date = dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    filtered_df = filter_by_date_range(df, start_date, dt)

    config = load_config(config_path)

    response = {
        "greeting": get_greeting(dt),
        "cards": get_cards_info(filtered_df),
        "top_transactions": get_top_transactions(filtered_df),
        "currency_rates": get_currency_rates(config.get("currencies", [])),
        "stock_prices": get_stock_prices(config.get("stocks", [])),
    }

    logger.info("Страница «Главная» сформирована успешно")

    return json.dumps(response, ensure_ascii=False, indent=2)


def get_events_page(df: pd.DataFrame, date_time_str: str, period: str = "M") -> str:
    """Генерирует JSON-ответ для страницы «События».

    Возвращает сводку по расходам и поступлениям за указанный период,
    а также актуальные курсы валют и цены акций.

    Возможные значения параметра period:
      - ``W``   — неделя, на которую приходится дата (с понедельника)
      - ``M``   — месяц, на который приходится дата (по умолчанию)
      - ``Y``   — год, на который приходится дата
      - ``ALL`` — все данные до указанной даты

    :arg df: DataFrame с данными транзакций.
    :arg date_time_str: Строка с датой в формате 'YYYY-MM-DD HH:MM:SS'.
    :arg period: Код периода. По умолчанию 'M'.
    :return: JSON-строка с данными страницы «События».
    """
    logger.info("Формирование страницы «События» для даты=%s, период=%s", date_time_str, period)

    dt = datetime.strptime(date_time_str, "%Y-%m-%d %H:%M:%S")
    start_date, end_date = get_date_range(dt, period)
    filtered_df = filter_by_date_range(df, start_date, end_date)

    config = load_config()

    response = {
        "expenses": get_expenses_data(filtered_df),
        "income": get_income_data(filtered_df),
        "currency_rates": get_currency_rates(config.get("currencies", [])),
        "stock_prices": get_stock_prices(config.get("stocks", [])),
    }

    logger.info("Страница «События» сформирована успешно")

    return json.dumps(response, ensure_ascii=False, indent=2)
