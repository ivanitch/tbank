"""Вспомогательные функции: фильтрация транзакций, получение данных через API."""
import os
from datetime import datetime
from typing import Any, Optional

import yfinance as yf
import pandas as pd
import requests
from dotenv import load_dotenv

from src.config import load_config
from src.logger import get_logger

load_dotenv()

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Работа с транзакциями
# ---------------------------------------------------------------------------


def read_operations(path: str) -> pd.DataFrame:
    """Читает операции из Excel-файла.

    :param path: Путь к Excel-файлу.
    :return: DataFrame с данными транзакций.
    """
    logger.info("Чтение операций из %s", path)
    df = pd.read_excel(path)
    logger.info("Загружено строк: %d", len(df))
    return df


def filter_by_date_range(df: pd.DataFrame, start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Фильтрует DataFrame по диапазону дат включительно.

    :param df: DataFrame со столбцом 'Дата операции' в формате ДД.ММ.ГГГГ ЧЧ:ММ:СС.
    :param start_date: Начало диапазона.
    :param end_date: Конец диапазона.
    :return: Отфильтрованный DataFrame.
    """
    logger.info("Фильтрация транзакций с %s по %s", start_date, end_date)
    df = df.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    mask = (df["Дата операции"] >= start_date) & (df["Дата операции"] <= end_date)
    result = df[mask]
    logger.info("Найдено транзакций в диапазоне: %d", len(result))
    return result


def get_greeting(dt: datetime) -> str:
    """Возвращает приветствие в зависимости от времени суток.

    :param dt: Объект datetime для определения времени суток.
    :return: Строка приветствия: 'Доброе утро', 'Добрый день', 'Добрый вечер' или 'Доброй ночи'.
    """
    hour = dt.hour
    if 5 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_cards_info(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Рассчитывает расходы и кешбэк по каждой карте.

    :param df: Отфильтрованный DataFrame с данными транзакций.
    :return: Список словарей с ключами: last_digits, total_spent, cashback.
    """
    logger.info("Расчёт данных по картам")
    expenses = df[df["Сумма операции"] < 0].copy()
    result = []
    for card, group in expenses.groupby("Номер карты"):
        total_spent = round(group["Сумма операции"].abs().sum())
        cashback = round(total_spent / 100, 2)
        result.append(
            {
                "last_digits": str(card).replace("*", ""),
                "total_spent": total_spent,
                "cashback": cashback,
            }
        )
    logger.info("Найдено карт: %d", len(result))
    return result


def get_top_transactions(df: pd.DataFrame, top_n: int = 5) -> list[dict[str, Any]]:
    """Возвращает топ N транзакций по абсолютной сумме платежа.

    :param df: Отфильтрованный DataFrame с данными транзакций.
    :param top_n: Количество топ-транзакций для возврата. По умолчанию 5.
    :return: Список словарей с ключами: date, amount, category, description.
    """
    logger.info("Получение топ-%d транзакций", top_n)
    expenses = df[df["Сумма операции"] < 0].copy()
    if expenses.empty:
        return []
    expenses["abs_amount"] = expenses["Сумма операции"].abs().astype(float)
    top = expenses.nlargest(top_n, "abs_amount")
    result = []
    for _, row in top.iterrows():
        date_val = row["Дата операции"]
        date_str = date_val.strftime("%d.%m.%Y") if isinstance(date_val, pd.Timestamp) else str(date_val)[:10]
        result.append(
            {
                "date": date_str,
                "amount": round(float(row["Сумма операции"]), 2),
                "category": str(row["Категория"]),
                "description": str(row["Описание"]),
            }
        )
    logger.info("Топ-транзакций подготовлено: %d", len(result))
    return result


# ---------------------------------------------------------------------------
# Универсальный HTTP-клиент с гибкой авторизацией
# ---------------------------------------------------------------------------


def _resolve_auth(auth_cfg: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    """Формирует headers и params для запроса на основе настроек авторизации.

    Поддерживаемые типы (auth.type в config.json):
      - ``query_param`` — токен передаётся как query-параметр (?param_name=token)
      - ``header``      — токен передаётся в HTTP-заголовке (param_name: token)
      - ``bearer``      — токен передаётся как Bearer в заголовке Authorization

    Имя параметра задаётся в ``auth.param_name``.
    Переменная окружения с токеном задаётся в ``auth.env_key``.

    :param auth_cfg: Словарь секции auth из config.json.
    :return: Кортеж (headers, params) для передачи в requests.get.
    """
    headers: dict[str, str] = {}
    params: dict[str, str] = {}

    if not auth_cfg.get("enabled"):
        return headers, params

    env_key = auth_cfg.get("env_key", "")
    token = os.getenv(env_key, "")
    if not token:
        logger.warning("Авторизация включена, но токен '%s' не найден в .env", env_key)
        return headers, params

    auth_type = auth_cfg.get("type", "query_param")
    param_name = auth_cfg.get("param_name", "apikey")

    if auth_type == "query_param":
        params[param_name] = token
        logger.info("Auth: query_param '%s' загружен из %s", param_name, env_key)
    elif auth_type == "header":
        headers[param_name] = token
        logger.info("Auth: header '%s' загружен из %s", param_name, env_key)
    elif auth_type == "bearer":
        headers["Authorization"] = f"Bearer {token}"
        logger.info("Auth: Bearer токен загружен из %s", env_key)
    else:
        logger.warning("Неизвестный тип авторизации: %s", auth_type)

    return headers, params


def _fetch(url: str, auth_cfg: Optional[dict[str, Any]] = None) -> Optional[dict[str, Any]]:
    """Выполняет GET-запрос и возвращает JSON-ответ.

    :param url: URL для запроса.
    :param auth_cfg: Секция auth из config.json.
    :return: Распарсенный JSON или None при ошибке.
    """
    headers, params = _resolve_auth(auth_cfg or {})
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error("Ошибка HTTP-запроса к %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Курсы валют — парсеры
# ---------------------------------------------------------------------------


def _parse_cbr(data: dict[str, Any], currencies: list[str]) -> list[dict[str, Any]]:
    """Разбирает ответ ЦБ РФ (cbr-xml-daily.ru).

    :param data: JSON-ответ от ЦБ РФ.
    :param currencies: Список запрошенных кодов валют.
    :return: Список словарей с ключами currency, rate.
    """
    result = []
    valutes = data.get("Valute", {})
    for currency in currencies:
        if currency in valutes:
            rate = round(float(valutes[currency]["Value"]), 2)
            result.append({"currency": currency, "rate": rate})
            logger.info("ЦБ РФ — %s/RUB: %s", currency, rate)
        else:
            logger.warning("Валюта %s не найдена в ответе ЦБ РФ", currency)
    return result


def _parse_exchangerate(data: dict[str, Any], currencies: list[str]) -> list[dict[str, Any]]:
    """Разбирает ответ exchangerate-api.com.

    :param data: JSON-ответ от ExchangeRate-API.
    :param currencies: Список запрошенных кодов валют.
    :return: Список словарей с ключами currency, rate.
    """
    result = []
    rates = data.get("conversion_rates", {})
    for currency in currencies:
        if currency in rates and rates[currency] != 0:
            rate = round(1 / rates[currency], 2)
            result.append({"currency": currency, "rate": rate})
            logger.info("ExchangeRate-API — %s/RUB: %s", currency, rate)
        else:
            logger.warning("Валюта %s не найдена в ответе ExchangeRate-API", currency)
    return result


def _select_currency_parser(data: dict[str, Any]) -> Optional[Any]:
    """Определяет парсер по структуре ответа провайдера.

    :param data: JSON-ответ от провайдера.
    :return: Функция-парсер или None, если формат не распознан.
    """
    if "Valute" in data:
        return _parse_cbr
    if "conversion_rates" in data:
        return _parse_exchangerate
    return None


def get_currency_rates(currencies: list[str]) -> list[dict[str, Any]]:
    """Получает курсы валют к рублю согласно настройкам из config.json.

    URL, тип авторизации и провайдер задаются в разделе api.currency.
    Сам токен хранится в .env (имя переменной — в auth.env_key).
    Смена источника — только правка конфига, код не меняется.

    :param currencies: Список кодов валют, например ['USD', 'EUR', 'UAH'].
    :return: Список словарей с ключами: currency, rate.
    """
    logger.info("Запрос курсов валют: %s", currencies)
    cfg = load_config().get("api", {}).get("currency", {})
    url = cfg.get("url", "https://www.cbr-xml-daily.ru/daily_json.js")
    auth_cfg = cfg.get("auth", {"enabled": False})

    data = _fetch(url, auth_cfg)
    if data is None:
        return []

    parser = _select_currency_parser(data)
    if parser is None:
        logger.error("Неизвестный формат ответа от %s", url)
        return []

    return parser(data, currencies)


# ---------------------------------------------------------------------------
# Цены акций — yfinance (официальная Python-библиотека для Yahoo Finance)
# ---------------------------------------------------------------------------


def get_stock_prices(stocks: list[str]) -> list[dict[str, Any]]:
    """Получает цены акций из S&P 500 через библиотеку yfinance.

    Использует yfinance вместо прямых HTTP-запросов — библиотека сама управляет
    сессией, куками и задержками, что исключает ошибку 429 Too Many Requests.
    Список тикеров задаётся в config.json (поле stocks).

    :param stocks: Список тикеров акций, например ['AAPL', 'AMZN'].
    :return: Список словарей с ключами: stock, price.
    """
    logger.info("Запрос цен акций через yfinance: %s", stocks)
    result = []
    for symbol in stocks:
        try:
            ticker = yf.Ticker(symbol)
            price = ticker.fast_info.last_price
            if price is not None:
                result.append({"stock": symbol, "price": round(float(price), 2)})
                logger.info("Цена акции %s: %s", symbol, price)
            else:
                logger.warning("Цена для %s не найдена", symbol)
        except Exception as e:
            logger.error("Ошибка получения цены акции %s: %s", symbol, e)
    return result
