"""Точка входа: запуск консольного приложения."""

from bike_rental.app import ConsoleApp, create_demo_service


def main() -> None:
    ConsoleApp(create_demo_service()).run()


if __name__ == "__main__":
    main()
