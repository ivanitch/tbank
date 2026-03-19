"""Тесты для модуля src.reports."""
import json

import pandas as pd
import pytest

from src.reports import spending_by_weekday


# ---------------------------------------------------------------------------
# Фикстуры
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """
    Фикстура: транзакции за октябрь–декабрь 2021.
    """
    data = {
        "Дата операции": [
            "01.10.2021 10:00:00",  # пятница
            "04.10.2021 12:00:00",  # понедельник
            "06.10.2021 14:00:00",  # среда
            "01.11.2021 09:00:00",  # понедельник
            "03.11.2021 11:00:00",  # среда
            "13.12.2021 18:00:00",  # понедельник
            "15.12.2021 20:00:00",  # среда
            "31.12.2021 16:00:00",  # пятница (доход — не учитывается)
        ],
        "Номер карты": ["*7197"] * 8,
        "Статус": ["OK"] * 8,
        "Сумма операции": [
            -500.0,
            -1000.0,
            -300.0,
            -800.0,
            -400.0,
            -600.0,
            -200.0,
            5000.0,
        ],
        "Валюта операции": ["RUB"] * 8,
        "Категория": [
            "Фастфуд",
            "Супермаркеты",
            "Транспорт",
            "Супермаркеты",
            "Фастфуд",
            "Супермаркеты",
            "Транспорт",
            "Пополнения",
        ],
        "Описание": [
            "KFC", "Лента", "Метро",
            "Перекрёсток", "McDonald's",
            "Лента", "Метро", "Зарплата",
        ],
    }
    return pd.DataFrame(data)


@pytest.fixture
def empty_df() -> pd.DataFrame:
    """
    Фикстура: пустой DataFrame с нужными столбцами.
    """
    return pd.DataFrame(
        columns=[
            "Дата операции",
            "Номер карты",
            "Статус",
            "Сумма операции",
            "Валюта операции",
            "Категория",
            "Описание",
        ]
    )


# ---------------------------------------------------------------------------
# spending_by_weekday
# ---------------------------------------------------------------------------


def test_spending_by_weekday_returns_valid_json(
        sample_df: pd.DataFrame,
) -> None:
    """
    Должна вернуть валидную JSON-строку.
    """
    result = spending_by_weekday(sample_df, date="2021-12-31")
    assert isinstance(json.loads(result), list)


def test_spending_by_weekday_returns_seven_days(
        sample_df: pd.DataFrame,
) -> None:
    """
    В ответе должно быть ровно 7 дней недели.
    """
    result = json.loads(spending_by_weekday(sample_df, date="2021-12-31"))
    assert len(result) == 7


def test_spending_by_weekday_day_names(
        sample_df: pd.DataFrame,
) -> None:
    """
    Дни недели должны идти от понедельника до воскресенья.
    """
    expected = [
        "Понедельник", "Вторник", "Среда", "Четверг",
        "Пятница", "Суббота", "Воскресенье",
    ]
    result = json.loads(spending_by_weekday(sample_df, date="2021-12-31"))
    assert [item["day"] for item in result] == expected


def test_spending_by_weekday_has_required_keys(
        sample_df: pd.DataFrame,
) -> None:
    """
    Каждый элемент должен содержать ключи day и amount.
    """
    result = json.loads(spending_by_weekday(sample_df, date="2021-12-31"))
    for item in result:
        assert "day" in item
        assert "amount" in item


def test_spending_by_weekday_amounts_non_negative(
        sample_df: pd.DataFrame,
) -> None:
    """
    Суммы должны быть неотрицательными.
    """
    result = json.loads(spending_by_weekday(sample_df, date="2021-12-31"))
    for item in result:
        assert item["amount"] >= 0


def test_spending_by_weekday_excludes_income(
        sample_df: pd.DataFrame,
) -> None:
    """
    Поступления не должны влиять на средние траты.
    """
    result = json.loads(spending_by_weekday(sample_df, date="2021-12-31"))
    friday = next(item for item in result if item["day"] == "Пятница")
    # Пятница: только расход 500, поступление 5000 не учитывается
    assert friday["amount"] == 500.0


def test_spending_by_weekday_monday_average(
        sample_df: pd.DataFrame,
) -> None:
    """
    Среднее по понедельникам должно быть верным.
    """
    result = json.loads(spending_by_weekday(sample_df, date="2021-12-31"))
    monday = next(item for item in result if item["day"] == "Понедельник")
    # Понедельники: 1000, 800, 600 → среднее 800
    assert monday["amount"] == 800.0


def test_spending_by_weekday_empty_days_are_zero(
        sample_df: pd.DataFrame,
) -> None:
    """
    Дни без трат должны иметь amount = 0.
    """
    result = json.loads(spending_by_weekday(sample_df, date="2021-12-31"))
    sunday = next(item for item in result if item["day"] == "Воскресенье")
    assert sunday["amount"] == 0.0


def test_spending_by_weekday_empty_df(
        empty_df: pd.DataFrame,
) -> None:
    """
    На пустом DataFrame должна вернуть 7 дней с нулевыми суммами.
    """
    result = json.loads(spending_by_weekday(empty_df, date="2021-12-31"))
    assert len(result) == 7
    assert all(item["amount"] == 0.0 for item in result)


def test_spending_by_weekday_default_date(
        sample_df: pd.DataFrame,
) -> None:
    """
    Без параметра date не должна падать с ошибкой.
    """
    result = spending_by_weekday(sample_df)
    assert isinstance(json.loads(result), list)


@pytest.mark.parametrize("date", ["2021-10-31", "2021-11-30", "2021-12-31"])
def test_spending_by_weekday_different_dates(
        sample_df: pd.DataFrame,
        date: str,
) -> None:
    """
    Должна корректно работать для разных дат отсчёта.
    """
    result = json.loads(spending_by_weekday(sample_df, date=date))
    assert len(result) == 7
