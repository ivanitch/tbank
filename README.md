# TBank Finance Analysis

Приложение для анализа личных финансов на основе выгрузки из банковского приложения.

## Описание

Проект реализует несколько функциональных блоков:

**Веб-страницы** (`src/views.py`)
- `get_main_page` — генерирует JSON-ответ для главной страницы: приветствие, данные по картам, топ-5 транзакций, курсы валют, стоимость акций.

**Вспомогательные утилиты** (`src/utils.py`)
- Парсинг и фильтрация транзакций по дате.
- Получение курсов валют через [ExchangeRate-API](https://www.exchangerate-api.com/).
- Получение цен акций через [Alpha Vantage](https://www.alphavantage.co/).
- Загрузка пользовательских настроек из `user_settings.json`.

## Структура проекта

```
.
├── src/
│   ├── __init__.py
│   ├── utils.py
│   ├── main.py
│   └── views.py
├── data/
│   └── operations.xlsx
├── tests/
│   ├── __init__.py
│   ├── test_utils.py
│   └── test_views.py│
├── config.json
├── .env
├── .env_template
├── .flake8
├── .gitignore
├── pyproject.toml
├── poetry.lock
└── README.md
```

## Установка

```bash
# Установить зависимости через Poetry
poetry install

# Или через pip
pip install pandas openpyxl requests python-dotenv
```

## Конфигурация

Скопируйте `.env.example` в `.env` и заполните ключи:

```bash
cp .env.example .env
```

## Запуск

```bash
python main
```

---

## Тестирование

```bash
# Запустить все тесты
pytest

# С отчётом о покрытии
pytest --cov=src --cov-report=term-missing
```

## Пример JSON-ответа главной страницы

```json
{
  "greeting": "Добрый день",
  "cards": [
    {
      "last_digits": "7197",
      "total_spent": 17319,
      "cashback": 173.19
    }
  ],
  "top_transactions": [
    {
      "date": "21.12.2021",
      "amount": -1198.23,
      "category": "Переводы",
      "description": "Перевод Кредитная карта"
    }
  ],
  "currency_rates": [
    {"currency": "USD", "rate": 73.21},
    {"currency": "EUR", "rate": 87.08}
  ],
  "stock_prices": [
    {"stock": "AAPL", "price": 150.12}
  ]
}
```

## Кодстайл

```bash
flake8 src tests          # линтер
black src tests           # форматирование
isort src tests           # сортировка импортов
mypy src                  # проверка типов
```

Или запустить все линтеры одной командой:
```bash
./lint.sh
```
