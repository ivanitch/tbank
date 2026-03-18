# Bank Widget Masks

Учебный проект для курса по Python. Реализует функции маскирования банковских данных,
обработки и поиска операций, интерактивный CLI и генераторы для виджета личного кабинета
пользователя банка.

---

## Цель проекта

IT-отдел крупного банка разрабатывает новый виджет для личного кабинета клиента.
Виджет отображает последние банковские операции клиента, обеспечивая:

1. **Маскирование конфиденциальных данных** — номера карт и счетов
2. **Фильтрацию операций** — по статусу выполнения и валюте
3. **Сортировку операций** — по дате для удобного отображения
4. **Форматирование дат** — в понятный для пользователя формат (ДД.ММ.ГГГГ)
5. **Эффективную обработку больших объёмов данных** — через генераторы
6. **Декорирование функций** — логирование через декораторы
7. **Чтение данных из JSON-файлов** — загрузка списка транзакций из файла
8. **Чтение данных из CSV и Excel** — загрузка транзакций через pandas
9. **Конвертацию валют** — получение актуального курса через внешний API
10. **Логирование событий** — запись в файл с временной меткой, модулем и уровнем
11. **Поиск транзакций по описанию** — фильтрация с помощью регулярных выражений
12. **Подсчёт операций по категориям** — статистика через `Counter`
13. **Интерактивный CLI** — пользовательский интерфейс с пошаговым меню

Проект демонстрирует практическое применение Python для решения реальных задач
финтех-индустрии с соблюдением стандартов безопасности данных (PCI DSS).

---

## Структура проекта

```
bank-widget-masks/
├── data/                         # Данные проекта
│   ├── operations.json           # Файл с банковскими операциями (JSON)
│   ├── transactions.csv          # Файл с банковскими операциями (CSV)
│   └── transactions_excel.xlsx   # Файл с банковскими операциями (Excel)
│
│── htmlcov/                      # Отчет о покрытии тестами (не хранится в Git)
│
├── logs/                         # Лог-файлы (создаются автоматически, не хранится в Git)
│
├── src/                          # Исходный код проекта
│   ├── __init__.py               # Инициализация пакета
│   ├── masks.py                  # Маскирование номеров карт и счетов
│   ├── widget.py                 # Форматирование карт, счетов и дат
│   ├── processing.py             # Фильтрация и сортировка операций
│   ├── generators.py             # Генераторы для работы с данными
│   ├── decorators.py             # Декоратор логирования
│   ├── utils.py                  # Чтение JSON-файлов
│   ├── file_reader.py            # Чтение транзакций из CSV и Excel
│   ├── external_api.py           # Конвертация валют через внешний API
│   ├── logger.py                 # Фабрика логеров
│   └── search.py                 # Поиск по описанию и подсчёт категорий
│
├── tests/                        # Тесты проекта
│   ├── __init__.py               # Инициализация пакета
│    ├── conftest.py               # Фикстуры для тестов
│   ├── test_masks.py             # Маскирование карт и счетов
│   ├── test_widget.py            # Форматирование карт, счетов, дат
│   ├── test_processing.py        # Фильтрация и сортировка
│   ├── test_generators.py        # Генераторы
│   ├── test_decorators.py        # Декоратор `@log`
│   ├── test_utils.py             # Чтение JSON-файлов
│   ├── test_file_reader.py       # Чтение CSV и Excel (Mock и patch)
│   ├── test_external_api.py      # Конвертация валют (Mock и patch)
│   └── test_search.py            # Поиск по описанию, подсчёт категорий
│
│── .coverage                     # Бинарный файл с данными о покрытии кода
├── .env                          # Переменные окружения (не хранится в Git)
├── .env.template                 # Шаблон переменных окружения
├── .flake8                       # Конфигурация линтера
├── .gitignore                    # Игнорируемые файлы Git
├── lint.sh                       # Запуск литреров одной командой
├── main.py                       # Интерактивный CLI
├── poetry.lock                   # Точные версии всех зависимостей, которые фиксируются Poetry
├── pyproject.toml                # Конфигурация Poetry и зависимостей
├── README.md                     # Документация проекта
├── test.py                       # Тестовый/Dev-файл
└── test.sh                       # Запуск тестов
```

---

## Требования

- **Python**: 3.11 или выше
- **Poetry**: для управления зависимостями
- **pandas** и **openpyxl**: для чтения CSV и Excel-файлов

---

## Установка и настройка

### 1. Клонирование репозитория

```bash
git clone git@github.com:ivanitch/bank-widget-masks.git
cd bank-widget-masks
```

### 2. Установка зависимостей

```bash
poetry shell
poetry install
```

Poetry создаст виртуальное окружение и установит все необходимые библиотеки
(pytest, flake8, black, isort, mypy, requests, python-dotenv, pandas, openpyxl).

### 3. Настройка переменных окружения

```bash
cp .env.template .env
```

Откройте `.env` и укажите API-ключ для конвертации валют:

```
EXCHANGE_RATES_API_KEY=your_api_key_here
```

Получить ключ можно бесплатно на [apilayer.com](https://apilayer.com/marketplace/exchangerates_data-api).

> Файл `.env` добавлен в `.gitignore` и не попадает в репозиторий.

---

## Запуск программы

```bash
python main.py
```

Программа запускает интерактивный CLI и последовательно задаёт вопросы:

```
Привет! Добро пожаловать в программу работы с банковскими транзакциями.
Выберите необходимый пункт меню:
1. Получить информацию о транзакциях из JSON-файла
2. Получить информацию о транзакциях из CSV-файла
3. Получить информацию о транзакциях из XLSX-файла

Пользователь: 1

Для обработки выбран JSON-файл.

Введите статус, по которому необходимо выполнить фильтрацию.
Доступные для фильтровки статусы: EXECUTED, CANCELED, PENDING

Пользователь: EXECUTED

Операции отфильтрованы по статусу "EXECUTED"

Отсортировать операции по дате? Да/Нет
Пользователь: Да

Отсортировать по возрастанию или по убыванию? (1 - по возрастанию / 2 - по убыванию)
Пользователь: 2

Выводить только рублевые транзакции? Да/Нет
Пользователь: Нет

Отфильтровать список транзакций по определенному слову в описании? Да/Нет
Пользователь: Да
Введите слово для поиска: Перевод

Распечатываю итоговый список транзакций...

Всего банковских операций в выборке: 3

21.06.2019 Перевод организации
Счет **1234 -> Счет **5678
Сумма: 25762.92 RUB

...
```

Если ни одна транзакция не подошла под условия фильтрации:

```
Не найдено ни одной транзакции, подходящей под ваши условия фильтрации
```

---

## Описание модулей

### `masks.py` — Маскирование данных

#### `get_mask_card_number(card_number: str) -> str`

Маскирует номер карты, оставляя видимыми первые 6 и последние 4 цифры.

```
"7000792289606361" → "7000 79** **** 6361"
```

#### `get_mask_account(account_number: str) -> str`

Маскирует номер счёта, оставляя видимыми только последние 4 цифры.

```
"73654108430135874305" → "**4305"
```

---

### `widget.py` — Виджет

#### `mask_account_card(card_or_account: str) -> str`

Универсальная функция: маскирует карту или счёт вместе с их названием.

```
"Visa Platinum 7000792289606361" → "Visa Platinum 7000 79** **** 6361"
"Счет 73654108430135874305"      → "Счет **4305"
```

#### `get_date(date_string: str) -> str`

Преобразует дату из ISO 8601 в формат ДД.ММ.ГГГГ.

```
"2024-03-11T02:26:18.671407" → "11.03.2024"
```

---

### `processing.py` — Обработка операций

#### `filter_by_state(data: list[dict], state: str = "EXECUTED") -> list[dict]`

Фильтрует список операций по статусу (`EXECUTED`, `CANCELED`, `PENDING`).

#### `sort_by_date(data: list[dict], reverse: bool = True) -> list[dict]`

Сортирует операции по полю `date`. По умолчанию — от новых к старым.

---

### `generators.py` — Генераторы

#### `filter_by_currency(transactions, currency: str)`

Генератор: фильтрует транзакции по коду валюты (`USD`, `RUB`, `EUR`).

#### `transaction_descriptions(transactions)`

Генератор: поочерёдно возвращает поле `description` каждой транзакции.

#### `card_number_generator(start: int, stop: int)`

Генератор: создаёт номера карт в формате `XXXX XXXX XXXX XXXX` в диапазоне `[start, stop]`.

---

### `decorators.py` — Декораторы

#### `@log(filename: str | None = None)`

Декоратор логирования. Записывает в консоль или в файл:

- при успехе — имя функции и результат
- при ошибке — имя функции, тип и текст исключения

---

### `utils.py` — Утилиты

#### `get_transactions_from_json(file_path: str) -> list[dict]`

Читает список транзакций из JSON-файла. При отсутствии файла или некорректных данных
возвращает пустой список.

---

### `file_reader.py` — Чтение CSV и Excel

#### `get_transactions_from_csv(file_path: str) -> list[dict]`

Читает транзакции из CSV-файла (разделитель — `;`). При ошибке возвращает пустой список.

Ожидаемые колонки: `id`, `state`, `date`, `amount`, `currency_name`, `currency_code`,
`from`, `to`, `description`.

#### `get_transactions_from_excel(file_path: str) -> list[dict]`

Читает транзакции из Excel-файла (`.xlsx`) через pandas. При ошибке возвращает пустой список.
Отсутствующие значения конвертируются в `None`.

---

### `external_api.py` — Конвертация валют

#### `convert_transaction_amount(transaction: dict) -> float`

Возвращает сумму транзакции в рублях:

- если валюта `RUB` — возвращает исходную сумму без запроса к API
- если `USD` или `EUR` — обращается к Exchange Rates Data API за актуальным курсом

Требует заполненного `EXCHANGE_RATES_API_KEY` в файле `.env`.

---

### `logger.py` — Логирование

#### `get_logger(name: str) -> logging.Logger`

Возвращает настроенный логер. Файл лога создаётся в `logs/<name>.log` и перезаписывается
при каждом запуске.

Формат записи: `дата-время - модуль - уровень - сообщение`

---

### `search.py` — Поиск и статистика

#### `process_bank_search(data: list[dict], search: str) -> list[dict]`

Возвращает транзакции, у которых поле `description` содержит строку `search`.
Регистр не учитывается; поиск выполняется через библиотеку `re`.

```python
result = process_bank_search(transactions, "Перевод")
# вернёт все транзакции, где в description есть слово "Перевод"
```

#### `process_bank_operations(data: list[dict], categories: list) -> dict`

Подсчитывает количество операций по каждой категории из `categories`
на основе поля `description`. Использует `Counter` из `collections`.

```python
result = process_bank_operations(transactions, ["Перевод организации", "Открытие вклада"])
# {"Перевод организации": 5, "Открытие вклада": 2}
```

---

## Тестирование

### Запуск тестов

```bash
# Все тесты
pytest tests

# Подробный вывод
pytest tests -v

# С отчётом о покрытии кода
pytest tests -v --cov=src --cov-report=html
```

### Запуск конкретного файла

```bash
pytest tests/test_masks.py -v
pytest tests/test_search.py -v
```

### Просмотр покрытия

```bash
coverage report          # таблица в консоли
coverage html            # HTML-отчёт в папке `htmlcov/` с интерактивным сайтом. Открыть: `path/to/project/htmlcov/index.html`
```

---

## Проверка качества кода

```bash
# Проверка стиля (PEP 8)
flake8 main.py src

# Автоформатирование
black main.py src

# Сортировка импортов
isort main.py src

# Проверка типов
mypy main.py src
```

Все проверки одной командой:

```bash
flake8 main.py src && \
black --check main.py src && \
isort --check-only main.py src && \
mypy main.py src && \
pytest tests -v
```

Или через скрипт:

```bash
./lint.sh
```

---

## Безопасность данных

Проект следует лучшим практикам защиты конфиденциальных данных:

- **PCI DSS Compliance** — маскирование карт соответствует стандарту
- **Минимизация данных** — показываем только необходимый минимум
- **Защита ключей** — API-ключи хранятся в `.env`, не попадают в репозиторий
- **Эффективность** — генераторы не загружают всё в память

---

## Полезные ссылки

- [Документация Python](https://docs.python.org/3/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [PEP 8 Style Guide](https://pep8.org/)
- [pytest Documentation](https://docs.pytest.org/)
- [Exchange Rates Data API](https://apilayer.com/marketplace/exchangerates_data-api)
- [python-dotenv Documentation](https://pypi.org/project/python-dotenv/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [PCI DSS Requirements](https://www.pcisecuritystandards.org/)
- [Python Testing with pytest (Brian Okken)](https://tisten.ir/blog/wp-content/uploads/2019/01/Python-Testing-with-pytest-Pragmatic-Bookshelf-2017-Brian-Okken.pdf)
- [Pytest-Cheatsheet](https://github.com/mananrg/Pytest-Cheatsheet)
- [Раздел про тестирование в Hitchhiker's Guide to Python](https://docs.python-guide.org/writing/tests/)

---

*Этот проект создан с ❤️ для изучения Python и best practices разработки*
