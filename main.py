"""Главный модуль — точка входа для демонстрации всей функциональности проекта."""
from src.config import get_path
from src.logger import get_logger
from src.utils import read_operations
from src.views import get_main_page

logger = get_logger()


def main() -> None:
    """Запускает демонстрацию всех реализованных функциональностей."""
    logger.info("Запуск демонстрации приложения")

    df = read_operations(get_path("data/operations.xlsx"))

    # --- Веб-страницы ---
    print("\n=== Страница «Главная» ===")
    # current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = get_main_page("2021-12-31 16:44:00", df)
    print(result)


if __name__ == "__main__":
    main()
