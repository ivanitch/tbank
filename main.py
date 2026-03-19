"""Главный модуль — точка входа для демонстрации всей функциональности проекта."""
from src.config import get_path
from src.logger import get_logger
from src.utils import read_operations
from src.views import get_events_page, get_main_page

logger = get_logger(__name__)


def main() -> None:
    """Запускает демонстрацию всех реализованных функциональностей."""
    logger.info("Запуск демонстрации приложения")

    df = read_operations(get_path("data/operations.xlsx"))

    print("\n=== Страница «Главная» ===")
    # current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(get_main_page("2021-12-31 16:44:00", df))

    print("\n=== Страница «События» (месяц) ===")
    print(get_events_page(df, "2021-12-31 16:44:00", period="M"))


if __name__ == "__main__":
    main()
