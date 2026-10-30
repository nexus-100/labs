"""Сценарий проверки: нормальная работа, ошибки и обмен данными."""

from datetime import datetime

from bike_rental.app import create_demo_service
from bike_rental.exceptions import BikeRentalError
from bike_rental.service import RentalService
from bike_rental.storage import JsonStorage, XmlStorage


def dt(text: str) -> datetime:
    return datetime.strptime(text, "%Y-%m-%d %H:%M")


def attempt(title: str, action) -> None:
    """Выполняет действие и печатает результат или текст ошибки."""
    try:
        result = action()
        print(f"[OK]     {title}: {result}")
    except BikeRentalError as error:
        print(f"[ОШИБКА] {title}: {type(error).__name__}: {error}")


def main() -> None:
    service = create_demo_service()

    print("--- Нормальная работа ---")
    attempt("аренда городского", lambda: service.create_rental(
        1, 1, dt("2026-11-02 10:00"), dt("2026-11-02 13:00")))
    attempt("аренда «встык»", lambda: service.create_rental(
        1, 3, dt("2026-11-02 13:00"), dt("2026-11-02 15:00")))
    attempt("аренда электро", lambda: service.create_rental(
        3, 3, dt("2026-11-03 09:00"), dt("2026-11-03 12:00")))
    attempt("подтверждение залога", lambda: service.approve_rental(3))
    attempt("перенос аренды", lambda: service.reschedule_rental(
        1, dt("2026-11-04 10:00"), dt("2026-11-04 12:00")))
    attempt("перевод на другую станцию", lambda: service.move_bike(2, 1))
    attempt("свободные велосипеды", lambda: [
        b.model for b in service.find_free_bikes(
            dt("2026-11-03 10:00"), dt("2026-11-03 11:00"), 1, [1])])

    print("\n--- Обработка ошибок ---")
    attempt("занят (своё исключение)", lambda: service.create_rental(
        1, 3, dt("2026-11-04 11:00"), dt("2026-11-04 12:30")))
    attempt("клиент слишком молод", lambda: service.create_rental(
        3, 2, dt("2026-11-05 10:00"), dt("2026-11-05 11:00")))
    attempt("конец раньше начала", lambda: service.create_rental(
        1, 1, dt("2026-11-06 12:00"), dt("2026-11-06 11:00")))
    attempt("слишком долго", lambda: service.create_rental(
        3, 1, dt("2026-11-06 09:00"), dt("2026-11-06 20:00")))
    attempt("нет такого велосипеда", lambda: service.create_rental(
        99, 1, dt("2026-11-06 09:00"), dt("2026-11-06 10:00")))
    attempt("повторное подтверждение", lambda: service.approve_rental(3))
    attempt("удаление арендованного", lambda: service.delete_bike(1))
    attempt("удаление станции с велосипедами",
            lambda: service.delete_station(1))
    attempt("некорректный email", lambda: service.add_customer(
        "Тестов Т.Т.", "без-собаки", "1990-01-01"))
    attempt("неверная дата рождения", lambda: service.add_customer(
        "Тестов Т.Т.", "t@example.com", "01.01.1990"))

    print("\n--- JSON и XML ---")
    for storage in (JsonStorage("data/data.json"),
                    XmlStorage("data/data.xml")):
        storage.save(service)
        copy = RentalService()
        storage.load(copy)
        same = copy.export_data() == service.export_data()
        print(f"{type(storage).__name__}: записано, прочитано, "
              f"данные совпадают = {same}")

    print("\n--- Повреждённые файлы ---")
    for name, text in (("bad.json", "{ не json"),
                       ("bad.xml", "<bike_rental><bikes>"),
                       ("wrong.json", '{"bikes": [{"id": "x"}]}')):
        path = f"data/{name}"
        with open(path, "w", encoding="utf-8") as file:
            file.write(text)
        storage = JsonStorage(path) if name.endswith("json") \
            else XmlStorage(path)
        attempt(f"загрузка {name}", lambda: storage.load(RentalService()))
    attempt("файла нет", lambda: JsonStorage("data/none.json").load(
        RentalService()))


if __name__ == "__main__":
    main()
