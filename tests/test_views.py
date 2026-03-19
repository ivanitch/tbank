import json
from unittest.mock import patch

import pandas as pd
import pytest

from src.views import get_main_page

# ---------------------------------------------------------------------------
# Фикстуры
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Фикстура: DataFrame с транзакциями за декабрь 2021."""
    data = {
        "Дата операции": [
            "01.12.2021 10:00:00",
            "15.12.2021 14:30:00",
            "20.12.2021 09:15:00",
            "25.12.2021 11:00:00",
            "28.12.2021 18:00:00",
            "31.12.2021 20:00:00",
        ],
        "Номер карты": ["*7197", "*7197", "*5678", "*7197", "*5678", "*7197"],
        "Статус": ["OK"] * 6,
        "Сумма операции": [-500.0, -1000.0, -200.0, -300.0, -150.0, 5000.0],
        "Валюта операции": ["RUB"] * 6,
        "Кэшбэк": [5.0, 10.0, 2.0, 3.0, 1.5, 0.0],
        "Категория": ["Супермаркеты", "Переводы", "Фастфуд", "Развлечения", "Кафе", "Пополнения"],
        "Описание": ["Лента", "Перевод", "KFC", "Кино", "Starbucks", "Зарплата"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def config_file(tmp_path) -> str:
    """Фикстура: временный файл config.json."""
    config = {
        "currencies": ["USD", "EUR", "UAH"],
        "stocks": ["AAPL", "AMZN"],
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------------------
# get_main_page — структура ответа
# ---------------------------------------------------------------------------


def test_get_main_page_returns_valid_json(sample_df: pd.DataFrame, config_file: str) -> None:
    """Должна вернуть валидную JSON-строку."""
    with patch("src.views.get_currency_rates", return_value=[]):
        with patch("src.views.get_stock_prices", return_value=[]):
            result = get_main_page("2021-12-31 20:00:00", sample_df, config_file)
    assert isinstance(json.loads(result), dict)


def test_get_main_page_has_required_keys(sample_df: pd.DataFrame, config_file: str) -> None:
    """JSON-ответ должен содержать все обязательные ключи верхнего уровня."""
    with patch("src.views.get_currency_rates", return_value=[]):
        with patch("src.views.get_stock_prices", return_value=[]):
            data = json.loads(get_main_page("2021-12-31 20:00:00", sample_df, config_file))
    for key in ("greeting", "cards", "top_transactions", "currency_rates", "stock_prices"):
        assert key in data


@pytest.mark.parametrize(
    "date_time_str, expected_greeting",
    [
        ("2021-12-31 06:00:00", "Доброе утро"),
        ("2021-12-31 13:00:00", "Добрый день"),
        ("2021-12-31 19:00:00", "Добрый вечер"),
        ("2021-12-31 01:00:00", "Доброй ночи"),
    ],
)
def test_get_main_page_greeting(
    date_time_str: str, expected_greeting: str, sample_df: pd.DataFrame, config_file: str
) -> None:
    """Приветствие должно соответствовать времени суток из входящей даты."""
    with patch("src.views.get_currency_rates", return_value=[]):
        with patch("src.views.get_stock_prices", return_value=[]):
            data = json.loads(get_main_page(date_time_str, sample_df, config_file))
    assert data["greeting"] == expected_greeting


def test_get_main_page_cards_structure(sample_df: pd.DataFrame, config_file: str) -> None:
    """Каждая карта в ответе должна содержать ключи last_digits, total_spent, cashback."""
    with patch("src.views.get_currency_rates", return_value=[]):
        with patch("src.views.get_stock_prices", return_value=[]):
            data = json.loads(get_main_page("2021-12-31 20:00:00", sample_df, config_file))
    for card in data["cards"]:
        assert "last_digits" in card
        assert "total_spent" in card
        assert "cashback" in card


def test_get_main_page_top_transactions_max_5(sample_df: pd.DataFrame, config_file: str) -> None:
    """Список топ-транзакций должен содержать не более 5 элементов."""
    with patch("src.views.get_currency_rates", return_value=[]):
        with patch("src.views.get_stock_prices", return_value=[]):
            data = json.loads(get_main_page("2021-12-31 20:00:00", sample_df, config_file))
    assert len(data["top_transactions"]) <= 5


def test_get_main_page_filters_by_month(sample_df: pd.DataFrame, config_file: str) -> None:
    """Данные должны фильтроваться с начала месяца по указанную дату."""
    with patch("src.views.get_currency_rates", return_value=[]):
        with patch("src.views.get_stock_prices", return_value=[]):
            data = json.loads(get_main_page("2021-12-15 14:30:00", sample_df, config_file))
    assert len(data["cards"]) >= 1


def test_get_main_page_currency_rates_three_currencies(sample_df: pd.DataFrame, config_file: str) -> None:
    """Ответ должен содержать курсы трёх валют: USD, EUR, UAH."""
    rates = [
        {"currency": "USD", "rate": 90.5},
        {"currency": "EUR", "rate": 98.3},
        {"currency": "UAH", "rate": 2.3},
    ]
    with patch("src.views.get_currency_rates", return_value=rates):
        with patch("src.views.get_stock_prices", return_value=[]):
            data = json.loads(get_main_page("2021-12-31 20:00:00", sample_df, config_file))
    assert data["currency_rates"] == rates
    assert len(data["currency_rates"]) == 3
    assert {r["currency"] for r in data["currency_rates"]} == {"USD", "EUR", "UAH"}


def test_get_main_page_stock_prices_passed(sample_df: pd.DataFrame, config_file: str) -> None:
    """Цены акций из API должны быть включены в ответ."""
    stocks = [{"stock": "AAPL", "price": 150.12}, {"stock": "AMZN", "price": 3173.18}]
    with patch("src.views.get_currency_rates", return_value=[]):
        with patch("src.views.get_stock_prices", return_value=stocks):
            data = json.loads(get_main_page("2021-12-31 20:00:00", sample_df, config_file))
    assert data["stock_prices"] == stocks


def test_get_main_page_no_data_for_period(config_file: str) -> None:
    """Должна вернуть пустые карты и транзакции при отсутствии данных в диапазоне."""
    empty_df = pd.DataFrame(
        columns=[
            "Дата операции",
            "Номер карты",
            "Статус",
            "Сумма операции",
            "Валюта операции",
            "Кэшбэк",
            "Категория",
            "Описание",
        ]
    )
    with patch("src.views.get_currency_rates", return_value=[]):
        with patch("src.views.get_stock_prices", return_value=[]):
            data = json.loads(get_main_page("2021-12-31 20:00:00", empty_df, config_file))
    assert data["cards"] == []
    assert data["top_transactions"] == []
