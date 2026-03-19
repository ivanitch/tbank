import json

import pytest

from src.services import simple_search


# ---------------------------------------------------------------------------
# Фикстуры
# ---------------------------------------------------------------------------


@pytest.fixture
def transactions() -> list[dict]:
    """Фикстура: список транзакций для тестирования поиска."""
    return [
        {
            "Дата операции": "01.12.2021 10:00:00",
            "Сумма операции": -500.0,
            "Категория": "Супермаркеты",
            "Описание": "Лента",
        },
        {
            "Дата операции": "05.12.2021 14:00:00",
            "Сумма операции": -300.0,
            "Категория": "Фастфуд",
            "Описание": "KFC",
        },
        {
            "Дата операции": "10.12.2021 09:00:00",
            "Сумма операции": -850.0,
            "Категория": "Фастфуд",
            "Описание": "McDonald's",
        },
        {
            "Дата операции": "15.12.2021 18:00:00",
            "Сумма операции": -2000.0,
            "Категория": "Переводы",
            "Описание": "Иванов Иван И.",
        },
        {
            "Дата операции": "25.12.2021 16:00:00",
            "Сумма операции": 5000.0,
            "Категория": "Пополнения",
            "Описание": "Зарплата",
        },
    ]


# ---------------------------------------------------------------------------
# simple_search
# ---------------------------------------------------------------------------


def test_simple_search_returns_valid_json(transactions: list[dict]) -> None:
    """Должна вернуть валидную JSON-строку."""
    result = simple_search("лента", transactions)
    assert isinstance(json.loads(result), list)


def test_simple_search_by_description(transactions: list[dict]) -> None:
    """Должна находить транзакции по вхождению в поле Описание."""
    result = json.loads(simple_search("лента", transactions))
    assert len(result) == 1
    assert result[0]["Описание"] == "Лента"


def test_simple_search_by_category(transactions: list[dict]) -> None:
    """Должна находить транзакции по вхождению в поле Категория."""
    result = json.loads(simple_search("фастфуд", transactions))
    assert len(result) == 2


def test_simple_search_case_insensitive(transactions: list[dict]) -> None:
    """Поиск должен быть нечувствителен к регистру."""
    result_lower = json.loads(simple_search("kfc", transactions))
    result_upper = json.loads(simple_search("KFC", transactions))
    assert result_lower == result_upper


def test_simple_search_no_results(transactions: list[dict]) -> None:
    """При отсутствии совпадений должна вернуть пустой список."""
    result = json.loads(simple_search("несуществующий запрос xyz", transactions))
    assert result == []


def test_simple_search_empty_query(transactions: list[dict]) -> None:
    """Пустой запрос должен вернуть все транзакции."""
    result = json.loads(simple_search("", transactions))
    assert len(result) == len(transactions)


def test_simple_search_empty_transactions() -> None:
    """На пустом списке должна вернуть пустой список."""
    result = json.loads(simple_search("лента", []))
    assert result == []


@pytest.mark.parametrize("query, expected_count", [
    ("лента", 1),
    ("фастфуд", 2),
    ("переводы", 1),
    ("зарплата", 1),
    ("kfc", 1),
])
def test_simple_search_parametrized(
        query: str, expected_count: int, transactions: list[dict]
) -> None:
    """Параметризованная проверка количества результатов для разных запросов."""
    result = json.loads(simple_search(query, transactions))
    assert len(result) == expected_count
