from src.config import get_path
from src.logger import get_logger
from src.utils import read_operations
from src.services import simple_search
from src.views import get_events_page, get_main_page

logger = get_logger()


def main() -> None:
    logger.info("🚀 Запуск демонстрации приложения")

    df = read_operations(get_path("data/operations.xlsx"))
    # current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    print("\n=== Страница «Главная» ===")
    print(get_main_page("2021-12-31 16:44:00", df))

    print("\n=== Страница «События» (месяц) ===")
    print(get_events_page(df, "2021-12-31 16:44:00", period="M"))

    print("\n=== Сервис «Простой поиск» ===")
    print(simple_search("Лента", df.to_dict(orient="records")))

    logger.info("⏹️ Демонстрация приложения завершена")


if __name__ == "__main__":
    main()
