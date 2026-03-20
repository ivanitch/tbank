import json
import os
from datetime import datetime
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from src.config import get_path, load_config
from src.utils import (
    _fetch,
    _parse_cbr,
    _parse_exchangerate,
    _resolve_auth,
    filter_by_date_range,
    get_cards_info,
    get_currency_rates,
    get_greeting,
    get_stock_prices,
    get_top_transactions,
    read_operations,
)

# ---------------------------------------------------------------------------
# Фикстуры
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Фикстура: небольшой DataFrame, имитирующий структуру operations.xlsx."""
    data = {
        "Дата операции": [
            "01.12.2021 10:00:00",
            "05.12.2021 14:30:00",
            "10.12.2021 09:15:00",
            "15.12.2021 20:00:00",
            "20.12.2021 11:00:00",
            "25.12.2021 08:00:00",
            "28.12.2021 18:00:00",
        ],
        "Номер карты": ["*7197", "*7197", "*5678", "*7197", "*5678", "*7197", "*5678"],
        "Статус": ["OK"] * 7,
        "Сумма операции": [-500.0, -1000.0, -200.0, 5000.0, -300.0, -800.0, -150.0],
        "Валюта операции": ["RUB"] * 7,
        "Кэшбэк": [5.0, 10.0, 2.0, 0.0, 3.0, 8.0, 1.5],
        "Категория": ["Супермаркеты", "Переводы", "Фастфуд", "Пополнения", "Развлечения", "Транспорт", "Кафе"],
        "Описание": ["Лента", "Перевод", "KFC", "Зарплата", "Кино", "Метро", "Starbucks"],
    }
    return pd.DataFrame(data)


@pytest.fixture
def config_file(tmp_path) -> str:
    """Фикстура: временный config.json с двумя провайдерами API."""
    config = {
        "params": {"log_level": "INFO"},
        "currencies": ["USD", "EUR", "UAH"],
        "stocks": ["AAPL", "AMZN", "TSLA"],
        "api": {
            "currency": {
                "url": "https://www.cbr-xml-daily.ru/daily_json.js",
                "auth": {
                    "enabled": False,
                    "type": "query_param",
                    "param_name": "apikey",
                    "env_key": "CURRENCY_API_KEY",
                },
            },
            "stocks": {
                "url": "https://query1.finance.yahoo.com/v8/finance/chart/{symbol}",
                "auth": {"enabled": False, "type": "query_param", "param_name": "apikey", "env_key": "STOCK_API_KEY"},
            },
        },
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return str(path)


# ---------------------------------------------------------------------------
# get_path
# ---------------------------------------------------------------------------


def test_get_path_no_args_returns_cwd() -> None:
    """Без аргументов должна вернуть текущую рабочую директорию."""
    assert get_path() == os.getcwd()


def test_get_path_with_directory() -> None:
    """С аргументом должна вернуть корректный путь относительно cwd."""
    assert get_path("data/operations.xlsx") == os.path.join(os.getcwd(), "data/operations.xlsx")


def test_get_path_returns_string() -> None:
    """Должна возвращать строку в обоих случаях."""
    assert isinstance(get_path(), str)
    assert isinstance(get_path("some/path"), str)


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------


def test_load_config_success(config_file: str) -> None:
    """Должна загрузить все секции из файла."""
    result = load_config(config_file)
    assert result["currencies"] == ["USD", "EUR", "UAH"]
    assert result["stocks"] == ["AAPL", "AMZN", "TSLA"]
    assert "api" in result


def test_load_config_currencies_count(config_file: str) -> None:
    """В конфиге должно быть ровно 3 валюты."""
    assert len(load_config(config_file)["currencies"]) == 3


def test_load_config_api_sections(config_file: str) -> None:
    """Конфиг должен содержать секции api.currency и api.stocks."""
    api = load_config(config_file)["api"]
    assert "currency" in api
    assert "stocks" in api


def test_load_config_api_auth_fields(config_file: str) -> None:
    """Секция auth должна содержать все обязательные поля."""
    auth = load_config(config_file)["api"]["stocks"]["auth"]
    assert "enabled" in auth
    assert "type" in auth
    assert "param_name" in auth
    assert "env_key" in auth


def test_load_config_file_not_found() -> None:
    """Должна вернуть безопасные значения по умолчанию при отсутствии файла."""
    result = load_config("nonexistent.json")
    assert result["currencies"] == []
    assert result["stocks"] == []
    assert result["api"] == {}


def test_load_config_invalid_json(tmp_path) -> None:
    """Должна вернуть значения по умолчанию при невалидном JSON."""
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    assert load_config(str(bad))["currencies"] == []


# ---------------------------------------------------------------------------
# _resolve_auth
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "auth_type, param_name, expected_key, in_params",
    [
        ("query_param", "apikey", "apikey", True),
        ("header", "X-Api-Key", "X-Api-Key", False),
    ],
)
def test_resolve_auth_types(auth_type: str, param_name: str, expected_key: str, in_params: bool, monkeypatch) -> None:
    """Должна корректно строить headers/params для каждого типа авторизации."""
    monkeypatch.setenv("TEST_API_KEY", "secret123")
    auth_cfg = {"enabled": True, "type": auth_type, "param_name": param_name, "env_key": "TEST_API_KEY"}
    headers, params = _resolve_auth(auth_cfg)
    if in_params:
        assert params.get(expected_key) == "secret123"
    else:
        assert headers.get(expected_key) == "secret123"


def test_resolve_auth_bearer(monkeypatch) -> None:
    """Тип bearer должен добавлять заголовок Authorization: Bearer <token>."""
    monkeypatch.setenv("MY_TOKEN", "tok_abc")
    auth_cfg = {"enabled": True, "type": "bearer", "param_name": "ignored", "env_key": "MY_TOKEN"}
    headers, params = _resolve_auth(auth_cfg)
    assert headers.get("Authorization") == "Bearer tok_abc"
    assert params == {}


def test_resolve_auth_disabled() -> None:
    """При disabled авторизации headers и params должны быть пустыми."""
    headers, params = _resolve_auth({"enabled": False, "env_key": "SOME_KEY"})
    assert headers == {}
    assert params == {}


def test_resolve_auth_missing_token(monkeypatch) -> None:
    """При отсутствии токена в .env должны вернуться пустые dicts."""
    monkeypatch.delenv("MISSING_KEY", raising=False)
    auth_cfg = {"enabled": True, "type": "query_param", "param_name": "key", "env_key": "MISSING_KEY"}
    headers, params = _resolve_auth(auth_cfg)
    assert headers == {}
    assert params == {}


# ---------------------------------------------------------------------------
# _fetch
# ---------------------------------------------------------------------------


def test_fetch_success() -> None:
    """Должна вернуть JSON при успешном запросе."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"key": "value"}
    mock_resp.raise_for_status = MagicMock()
    with patch("src.utils.requests.get", return_value=mock_resp):
        result = _fetch("https://example.com")
    assert result == {"key": "value"}


def test_fetch_network_error() -> None:
    """Должна вернуть None при сетевой ошибке."""
    import requests as req

    with patch("src.utils.requests.get", side_effect=req.RequestException("timeout")):
        assert _fetch("https://example.com") is None


def test_fetch_passes_auth_query_param(monkeypatch) -> None:
    """Должна передавать query-параметр авторизации в запрос."""
    monkeypatch.setenv("MY_KEY", "secret")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status = MagicMock()
    auth_cfg = {"enabled": True, "type": "query_param", "param_name": "token", "env_key": "MY_KEY"}
    with patch("src.utils.requests.get", return_value=mock_resp) as mock_get:
        _fetch("https://example.com", auth_cfg)
    _, kwargs = mock_get.call_args
    assert kwargs["params"].get("token") == "secret"


def test_fetch_passes_auth_header(monkeypatch) -> None:
    """Должна передавать заголовок авторизации в запрос."""
    monkeypatch.setenv("MY_KEY", "secret")
    mock_resp = MagicMock()
    mock_resp.json.return_value = {}
    mock_resp.raise_for_status = MagicMock()
    auth_cfg = {"enabled": True, "type": "header", "param_name": "X-Api-Key", "env_key": "MY_KEY"}
    with patch("src.utils.requests.get", return_value=mock_resp) as mock_get:
        _fetch("https://example.com", auth_cfg)
    _, kwargs = mock_get.call_args
    assert kwargs["headers"].get("X-Api-Key") == "secret"


# ---------------------------------------------------------------------------
# get_greeting
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "hour, expected",
    [
        (5, "Доброе утро"),
        (11, "Доброе утро"),
        (12, "Добрый день"),
        (17, "Добрый день"),
        (18, "Добрый вечер"),
        (22, "Добрый вечер"),
        (23, "Доброй ночи"),
        (0, "Доброй ночи"),
        (4, "Доброй ночи"),
    ],
)
def test_get_greeting(hour: int, expected: str) -> None:
    """Приветствие должно соответствовать времени суток."""
    assert get_greeting(datetime(2021, 12, 31, hour, 0, 0)) == expected


# ---------------------------------------------------------------------------
# filter_by_date_range
# ---------------------------------------------------------------------------


def test_filter_by_date_range_basic(sample_df: pd.DataFrame) -> None:
    """Должна вернуть строки строго в указанном диапазоне."""
    result = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 15, 23, 59, 59))
    assert len(result) == 4


def test_filter_by_date_range_empty(sample_df: pd.DataFrame) -> None:
    """Должна вернуть пустой DataFrame если нет строк в диапазоне."""
    assert filter_by_date_range(sample_df, datetime(2022, 1, 1), datetime(2022, 1, 31)).empty


def test_filter_by_date_range_inclusive(sample_df: pd.DataFrame) -> None:
    """Граничные даты должны включаться."""
    result = filter_by_date_range(sample_df, datetime(2021, 12, 1, 10, 0, 0), datetime(2021, 12, 1, 10, 0, 0))
    assert len(result) == 1


# ---------------------------------------------------------------------------
# get_cards_info
# ---------------------------------------------------------------------------


def test_get_cards_info_keys(sample_df: pd.DataFrame) -> None:
    """Каждый словарь карты должен содержать нужные ключи."""
    filtered = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 31))
    for card in get_cards_info(filtered):
        assert {"last_digits", "total_spent", "cashback"} <= card.keys()


def test_get_cards_info_cashback_formula(sample_df: pd.DataFrame) -> None:
    """Кешбэк должен равняться total_spent / 100."""
    filtered = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 31))

    for card in get_cards_info(filtered):
        assert card["cashback"] == round(card["total_spent"] / 100, 2)


def test_get_cards_info_only_expenses(sample_df: pd.DataFrame) -> None:
    """Поступления не должны учитываться в расходах."""
    filtered = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 31))

    for card in get_cards_info(filtered):
        assert card["total_spent"] > 0


# ---------------------------------------------------------------------------
# get_top_transactions
# ---------------------------------------------------------------------------


def test_get_top_transactions_count(sample_df: pd.DataFrame) -> None:
    """Должна вернуть не более top_n транзакций."""
    filtered = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 31))
    assert len(get_top_transactions(filtered, top_n=3)) <= 3


def test_get_top_transactions_sorted(sample_df: pd.DataFrame) -> None:
    """Транзакции должны быть отсортированы по убыванию абсолютной суммы."""
    filtered = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 31))
    amounts = [abs(t["amount"]) for t in get_top_transactions(filtered)]
    assert amounts == sorted(amounts, reverse=True)


def test_get_top_transactions_keys(sample_df: pd.DataFrame) -> None:
    """Каждая транзакция должна содержать нужные ключи."""
    filtered = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 31))
    for tx in get_top_transactions(filtered):
        assert {"date", "amount", "category", "description"} <= tx.keys()


def test_get_top_transactions_only_expenses(sample_df: pd.DataFrame) -> None:
    """Топ должен включать только расходы (отрицательные суммы)."""
    filtered = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 31))
    for tx in get_top_transactions(filtered):
        assert tx["amount"] < 0


def test_get_top_transactions_empty_df() -> None:
    """Должна вернуть пустой список при пустом DataFrame."""
    empty = pd.DataFrame(columns=["Дата операции", "Номер карты", "Сумма операции", "Категория", "Описание"])
    assert get_top_transactions(empty) == []


# ---------------------------------------------------------------------------
# _parse_cbr
# ---------------------------------------------------------------------------


def test_parse_cbr_known_currency() -> None:
    """Должна корректно разобрать курс известной валюты."""
    data = {"Valute": {"USD": {"Value": 90.5}, "EUR": {"Value": 98.3}, "UAH": {"Value": 2.3}}}
    result = _parse_cbr(data, ["USD", "EUR", "UAH"])
    assert len(result) == 3
    assert result[0] == {"currency": "USD", "rate": 90.5}


def test_parse_cbr_unknown_currency() -> None:
    """Должна пропустить валюту, которой нет в ответе."""
    data = {"Valute": {"USD": {"Value": 90.5}}}
    assert _parse_cbr(data, ["GBP"]) == []


# ---------------------------------------------------------------------------
# _parse_exchangerate
# ---------------------------------------------------------------------------


def test_parse_exchangerate_known_currency() -> None:
    """Должна корректно вычислить курс из ответа ExchangeRate-API."""
    data = {"conversion_rates": {"USD": 0.011}}
    result = _parse_exchangerate(data, ["USD"])
    assert result[0]["currency"] == "USD"
    assert result[0]["rate"] > 0


def test_parse_exchangerate_zero_rate() -> None:
    """Должна пропустить валюту с нулевым курсом."""
    assert _parse_exchangerate({"conversion_rates": {"USD": 0}}, ["USD"]) == []


# ---------------------------------------------------------------------------
# get_currency_rates
# ---------------------------------------------------------------------------


def test_get_currency_rates_cbr_success() -> None:
    """Должна вернуть три курса валют при успешном ответе ЦБ РФ."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"Valute": {"USD": {"Value": 90.5}, "EUR": {"Value": 98.3}, "UAH": {"Value": 2.3}}}
    mock_resp.raise_for_status = MagicMock()
    with patch("src.utils.requests.get", return_value=mock_resp):
        result = get_currency_rates(["USD", "EUR", "UAH"])
    assert len(result) == 3
    assert {r["currency"] for r in result} == {"USD", "EUR", "UAH"}


def test_get_currency_rates_unknown_format() -> None:
    """Должна вернуть пустой список при неизвестном формате ответа."""
    mock_resp = MagicMock()
    mock_resp.json.return_value = {"unexpected": {}}
    mock_resp.raise_for_status = MagicMock()
    with patch("src.utils.requests.get", return_value=mock_resp):
        assert get_currency_rates(["USD"]) == []


def test_get_currency_rates_network_error() -> None:
    """Должна вернуть пустой список при ошибке сети."""
    import requests as req

    with patch("src.utils.requests.get", side_effect=req.RequestException("timeout")):
        assert get_currency_rates(["USD", "EUR", "UAH"]) == []


# ---------------------------------------------------------------------------
# get_stock_prices (yfinance)
# ---------------------------------------------------------------------------


def test_get_stock_prices_success() -> None:
    """Должна вернуть цены для всех запрошенных акций через yfinance."""
    mock_ticker = MagicMock()
    mock_ticker.fast_info.last_price = 150.0
    with patch("src.utils.yf.Ticker", return_value=mock_ticker):
        result = get_stock_prices(["AAPL", "AMZN"])
    assert len(result) == 2
    assert result[0] == {"stock": "AAPL", "price": 150.0}
    assert result[1] == {"stock": "AMZN", "price": 150.0}


@pytest.mark.parametrize("symbol", ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"])
def test_get_stock_prices_each_symbol(symbol: str) -> None:
    """Должна корректно обрабатывать каждый тикер из конфига."""
    mock_ticker = MagicMock()
    mock_ticker.fast_info.last_price = 200.0
    with patch("src.utils.yf.Ticker", return_value=mock_ticker):
        result = get_stock_prices([symbol])
    assert result[0]["stock"] == symbol
    assert result[0]["price"] == 200.0


def test_get_stock_prices_none_price() -> None:
    """Должна пропустить акцию, если цена равна None."""
    mock_ticker = MagicMock()
    mock_ticker.fast_info.last_price = None
    with patch("src.utils.yf.Ticker", return_value=mock_ticker):
        result = get_stock_prices(["AAPL"])
    assert result == []


def test_get_stock_prices_exception() -> None:
    """Должна вернуть пустой список при исключении yfinance."""
    with patch("src.utils.yf.Ticker", side_effect=Exception("network error")):
        assert get_stock_prices(["AAPL"]) == []


# ---------------------------------------------------------------------------
# read_operations
# ---------------------------------------------------------------------------


def test_read_operations_returns_dataframe(tmp_path) -> None:
    """Должна вернуть DataFrame из Excel-файла."""
    df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
    path = tmp_path / "test.xlsx"
    df.to_excel(str(path), index=False)
    result = read_operations(str(path))
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# get_date_range
# ---------------------------------------------------------------------------


def test_get_date_range_month() -> None:
    """Период M должен начинаться с первого числа месяца."""
    from src.utils import get_date_range

    dt = datetime(2021, 12, 15, 14, 30, 0)
    start, end = get_date_range(dt, "M")
    assert start == datetime(2021, 12, 1, 0, 0, 0)
    assert end == dt


def test_get_date_range_week() -> None:
    """Период W должен начинаться с понедельника текущей недели."""
    from src.utils import get_date_range

    dt = datetime(2021, 12, 15, 14, 30, 0)  # среда
    start, end = get_date_range(dt, "W")
    assert start.weekday() == 0  # понедельник
    assert end == dt


def test_get_date_range_year() -> None:
    """Период Y должен начинаться с 1 января текущего года."""
    from src.utils import get_date_range

    dt = datetime(2021, 12, 15)
    start, end = get_date_range(dt, "Y")
    assert start == datetime(2021, 1, 1, 0, 0, 0)
    assert end == dt


def test_get_date_range_all() -> None:
    """Период ALL должен начинаться с 1970-01-01."""
    from src.utils import get_date_range

    dt = datetime(2021, 12, 15)
    start, _ = get_date_range(dt, "ALL")
    assert start == datetime(1970, 1, 1)


def test_get_date_range_case_insensitive() -> None:
    """Код периода должен быть нечувствителен к регистру."""
    from src.utils import get_date_range

    dt = datetime(2021, 12, 15)
    start_upper, _ = get_date_range(dt, "M")
    start_lower, _ = get_date_range(dt, "m")
    assert start_upper == start_lower


# ---------------------------------------------------------------------------
# get_expenses_data
# ---------------------------------------------------------------------------


def test_get_expenses_data_total(sample_df: pd.DataFrame) -> None:
    """Общая сумма расходов должна быть суммой всех отрицательных транзакций."""
    from src.utils import get_expenses_data

    filtered = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 31))
    result = get_expenses_data(filtered)
    expected = round(abs(sum(x for x in [-500, -1000, -200, 5000, -300, -800, -150] if x < 0)))
    assert result["total_amount"] == expected


def test_get_expenses_data_transfers_separated(sample_df: pd.DataFrame) -> None:
    """Переводы и наличные не должны попадать в основные категории."""
    from src.utils import get_expenses_data

    filtered = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 31))
    result = get_expenses_data(filtered)
    main_cats = {item["category"] for item in result["main"]}
    assert "Переводы" not in main_cats
    assert "Наличные" not in main_cats


def test_get_expenses_data_has_all_keys(sample_df: pd.DataFrame) -> None:
    """Результат должен содержать все обязательные ключи."""
    from src.utils import get_expenses_data

    filtered = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 31))
    result = get_expenses_data(filtered)
    assert "total_amount" in result
    assert "main" in result
    assert "transfers_and_cash" in result


def test_get_expenses_data_main_sorted(sample_df: pd.DataFrame) -> None:
    """Основные категории расходов должны быть отсортированы по убыванию суммы."""
    from src.utils import get_expenses_data

    filtered = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 31))
    result = get_expenses_data(filtered)
    amounts = [item["amount"] for item in result["main"] if item["category"] != "Остальное"]
    assert amounts == sorted(amounts, reverse=True)


# ---------------------------------------------------------------------------
# get_income_data
# ---------------------------------------------------------------------------


def test_get_income_data_total(sample_df: pd.DataFrame) -> None:
    """Общая сумма поступлений должна равняться сумме положительных транзакций."""
    from src.utils import get_income_data

    filtered = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 31))
    result = get_income_data(filtered)
    assert result["total_amount"] == 5000


def test_get_income_data_has_keys(sample_df: pd.DataFrame) -> None:
    """Результат должен содержать total_amount и main."""
    from src.utils import get_income_data

    filtered = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 31))
    result = get_income_data(filtered)
    assert "total_amount" in result
    assert "main" in result


def test_get_income_data_sorted(sample_df: pd.DataFrame) -> None:
    """Категории поступлений должны быть отсортированы по убыванию."""
    from src.utils import get_income_data

    filtered = filter_by_date_range(sample_df, datetime(2021, 12, 1), datetime(2021, 12, 31))
    result = get_income_data(filtered)
    amounts = [item["amount"] for item in result["main"]]
    assert amounts == sorted(amounts, reverse=True)
