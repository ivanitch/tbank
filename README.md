# TBank Finance Analysis

Приложение для анализа личных финансов на основе выгрузки из TBank.

## Описание

Проект реализует несколько функциональных блоков:

**Веб-страницы** (`src/views.py`)
- `get_main_page` — главная страница: приветствие, данные по картам, топ-5 транзакций, курсы валют, стоимость акций из S&P 500.
- `get_events_page` — страница событий: сводка расходов и поступлений по категориям за выбранный период, курсы валют, стоимость акций.

**Вспомогательные утилиты** (`src/utils.py`)
- Фильтрация транзакций по дате и периоду (`W` / `M` / `Y` / `ALL`).
- Расчёт расходов по категориям: топ-7 + «Остальное», «Переводы и наличные» отдельно.
- Расчёт поступлений по категориям.
- Получение курсов валют — по умолчанию через открытый [API ЦБ РФ](https://www.cbr-xml-daily.ru) (без ключа). Смена источника — только правка `config.json`.
- Получение цен акций через библиотеку [yfinance](https://github.com/ranaroussi/yfinance) (бесплатно, без ключа).
- Гибкая авторизация для любого HTTP-провайдера: `query_param`, `header`, `bearer`.

**Конфигурация** (`src/config.py`)
- `get_path` — построение путей относительно корня проекта.
- `load_config` — загрузка `config.json`.

**Логирование** (`src/logger.py`)
- Вывод в консоль и в файл `logs/<name>.log`.
- Уровень логирования задаётся в `config.json` → `params.log_level`.

## Структура проекта

```
.
├── src/
│   ├── __init__.py
│   ├── config.py       # пути и загрузка конфига (без внутренних зависимостей)
│   ├── logger.py       # настройка логирования
│   ├── utils.py        # бизнес-логика и работа с API
│   ├── views.py        # генерация JSON-ответов
│   └── main.py         # точка входа
├── data/
│   └── operations.xlsx
├── tests/
│   ├── __init__.py
│   ├── test_utils.py
│   └── test_views.py
├── logs/               # создаётся автоматически при запуске
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
# Через Poetry
poetry install

# Или через pip
pip install pandas openpyxl requests python-dotenv yfinance
```

## Конфигурация

### .env

Скопируйте шаблон и заполните ключи (нужны только если используете платные провайдеры):

```bash
cp .env_template .env
```

| Переменная | Описание |
|---|---|
| `CURRENCY_API_KEY` | Опционально. Ключ альтернативного провайдера курсов валют. По умолчанию используется ЦБ РФ без ключа |

### config.json

Все настройки приложения — валюты, акции, API-провайдеры:

```json
{
  "params": {
    "log_level": "INFO"
  },
  "currencies": ["USD", "EUR", "UAH"],
  "stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"],
  "api": {
    "currency": {
      "url": "https://www.cbr-xml-daily.ru/daily_json.js",
      "auth": {
        "enabled": false,
        "type": "query_param",
        "param_name": "apikey",
        "env_key": "CURRENCY_API_KEY"
      }
    }
  }
}
```

### Смена провайдера курсов валют

Достаточно изменить `config.json` — код не меняется:

```json
"currency": {
  "url": "https://v6.exchangerate-api.com/v6",
  "auth": {
    "enabled": true,
    "type": "query_param",
    "param_name": "apikey",
    "env_key": "CURRENCY_API_KEY"
  }
}
```

Поддерживаемые типы авторизации (`auth.type`):

| Тип | Как передаётся токен |
|---|---|
| `query_param` | `?apikey=TOKEN` |
| `header` | `X-Api-Key: TOKEN` |
| `bearer` | `Authorization: Bearer TOKEN` |

## Запуск

```bash
python -m src.main
```

## Тестирование

```bash
# Запустить все тесты
pytest

# С отчётом о покрытии
pytest --cov=src --cov-report=term-missing
```

## Примеры JSON-ответов

### Главная страница

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
    {"currency": "USD", "rate": 90.5},
    {"currency": "EUR", "rate": 98.3},
    {"currency": "UAH", "rate": 2.3}
  ],
  "stock_prices": [
    {"stock": "AAPL", "price": 150.12},
    {"stock": "AMZN", "price": 3173.18}
  ]
}
```

### Страница событий

Принимает DataFrame, дату и необязательный параметр периода:

| Значение | Диапазон |
|---|---|
| `W` | Неделя, на которую приходится дата (с понедельника) |
| `M` | Месяц, на который приходится дата (по умолчанию) |
| `Y` | Год, на который приходится дата |
| `ALL` | Все данные до указанной даты |

```json
{
  "expenses": {
    "total_amount": 32101,
    "main": [
      {"category": "Супермаркеты", "amount": 17319},
      {"category": "Фастфуд", "amount": 3324},
      {"category": "Остальное", "amount": 2954}
    ],
    "transfers_and_cash": [
      {"category": "Переводы", "amount": 1198},
      {"category": "Наличные", "amount": 500}
    ]
  },
  "income": {
    "total_amount": 74440,
    "main": [
      {"category": "Пополнения", "amount": 74440}
    ]
  },
  "currency_rates": [
    {"currency": "USD", "rate": 90.5},
    {"currency": "EUR", "rate": 98.3},
    {"currency": "UAH", "rate": 2.3}
  ],
  "stock_prices": [
    {"stock": "AAPL", "price": 150.12},
    {"stock": "AMZN", "price": 3173.18}
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
