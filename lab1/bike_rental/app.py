"""Консольный интерфейс приложения «Прокат велосипедов»."""

from __future__ import annotations

from datetime import datetime
from typing import Callable

from .exceptions import BikeRentalError
from .models import BIKE_KINDS, parse_datetime
from .service import RentalService
from .storage import JsonStorage, Storage, XmlStorage

MENU = """
===== Прокат велосипедов =====
 1. Показать велосипеды и клиентов
 2. Показать аренды
 3. Оформить аренду
 4. Перенести аренду
 5. Подтвердить залог (электровелосипед)
 6. Отменить аренду
 7. Найти свободные велосипеды
 8. Добавить велосипед
 9. Добавить клиента
10. Перевести велосипед на другую станцию
11. Удалить велосипед
12. Сохранить данные (JSON/XML)
13. Загрузить данные (JSON/XML)
 0. Выход
"""

DEFAULT_FILES = {"json": "data/data.json", "xml": "data/data.xml"}


def create_demo_service() -> RentalService:
    """Создаёт сервис с небольшим набором тестовых данных."""
    service = RentalService()
    park = service.add_station("Парк Горького", "Крымский Вал, 9")
    river = service.add_station("Набережная", "Пресненская наб., 12")
    helmet = service.add_accessory("Шлем")
    lock = service.add_accessory("Замок")
    seat = service.add_accessory("Детское кресло")

    service.add_bike("city", "Stels Navigator", park.id, 150,
                     [helmet.id, lock.id])
    service.add_bike("city", "Forward Racer", river.id, 120, [lock.id])
    service.add_bike("electric", "Xiaomi Mi E-Bike", park.id, 400,
                     [helmet.id, lock.id], battery_wh=480)
    service.add_bike("electric", "Kugoo Cargo", river.id, 450,
                     [helmet.id, seat.id], battery_wh=600)

    service.add_customer("Иванова Мария Петровна", "ivanova@example.com",
                         "2000-03-14")
    service.add_customer("Петров Артём Сергеевич", "petrov@example.com",
                         "2012-08-02")
    service.add_customer("Сидоров Олег Иванович", "sidorov@example.com",
                         "1985-11-30")
    return service


class ConsoleApp:
    """Меню в консоли. Любая ошибка ввода или данных не завершает работу."""

    def __init__(self, service: RentalService,
                 input_func: Callable[[str], str] = input,
                 output_func: Callable[[str], None] = print) -> None:
        self.service = service
        self._input = input_func
        self._print = output_func
        self._actions: dict[str, Callable[[], None]] = {
            "1": self.show_directories,
            "2": self.show_rentals,
            "3": self.create_rental,
            "4": self.reschedule_rental,
            "5": self.approve_rental,
            "6": self.cancel_rental,
            "7": self.find_free_bikes,
            "8": self.add_bike,
            "9": self.add_customer,
            "10": self.move_bike,
            "11": self.delete_bike,
            "12": self.save_data,
            "13": self.load_data,
        }

    # -------------------------------------------------------- ввод данных
    def _ask(self, prompt: str) -> str:
        return self._input(prompt + ": ").strip()

    def _ask_int(self, prompt: str) -> int:
        text = self._ask(prompt)
        try:
            return int(text)
        except ValueError:
            raise ValueError(f"«{text}» - не целое число") from None

    def _ask_float(self, prompt: str) -> float:
        text = self._ask(prompt)
        try:
            return float(text.replace(",", "."))
        except ValueError:
            raise ValueError(f"«{text}» - не число") from None

    def _ask_datetime(self, prompt: str) -> datetime:
        return parse_datetime(self._ask(f"{prompt} (ГГГГ-ММ-ДДTЧЧ:ММ)"))

    def _ask_int_list(self, prompt: str) -> list[int]:
        text = self._ask(prompt + " (id через запятую, можно пусто)")
        if not text:
            return []
        try:
            return [int(part) for part in text.split(",")]
        except ValueError:
            raise ValueError("Ожидался список чисел через запятую") from None

    def _make_storage(self) -> Storage:
        kind = self._ask("Формат (json/xml)").lower()
        default = DEFAULT_FILES.get(kind)
        if default is None:
            raise ValueError("Допустимые форматы: json, xml")
        path = self._ask(f"Файл [{default}]") or default
        return JsonStorage(path) if kind == "json" else XmlStorage(path)

    # ------------------------------------------------------------ команды
    def show_directories(self) -> None:
        for bike in self.service.bikes:
            station = self.service.stations.get(bike.station_id)
            accessories = ", ".join(
                self.service.accessories.get(i).name
                for i in bike.accessory_ids) or "нет"
            self._print(f"[{bike.id}] {bike}; {station.name}; "
                        f"аксессуары: {accessories}")
        for customer in self.service.customers:
            self._print(f"[{customer.id}] {customer}; "
                        f"род. {customer.birth_date:%d.%m.%Y}")

    def show_rentals(self) -> None:
        if not len(self.service.rentals):
            self._print("Аренд нет")
        for rental in self.service.rentals:
            bike = self.service.bikes.get(rental.bike_id)
            customer = self.service.customers.get(rental.customer_id)
            self._print(f"{rental} | {bike.model} | {customer.full_name}")

    def create_rental(self) -> None:
        rental = self.service.create_rental(
            self._ask_int("id велосипеда"),
            self._ask_int("id клиента"),
            self._ask_datetime("Начало"),
            self._ask_datetime("Окончание"),
        )
        self._print(f"Оформлено: {rental}")

    def reschedule_rental(self) -> None:
        rental = self.service.reschedule_rental(
            self._ask_int("id аренды"),
            self._ask_datetime("Новое начало"),
            self._ask_datetime("Новое окончание"),
        )
        self._print(f"Перенесено: {rental}")

    def approve_rental(self) -> None:
        self._print(f"Подтверждено: "
                    f"{self.service.approve_rental(self._ask_int('id'))}")

    def cancel_rental(self) -> None:
        self._print(f"Отменено: "
                    f"{self.service.cancel_rental(self._ask_int('id'))}")

    def find_free_bikes(self) -> None:
        start = self._ask_datetime("Начало")
        end = self._ask_datetime("Окончание")
        station = self._ask("id станции (можно пусто)")
        bikes = self.service.find_free_bikes(
            start, end, int(station) if station else None,
            self._ask_int_list("Нужные аксессуары"),
        )
        if not bikes:
            self._print("Подходящих свободных велосипедов нет")
        for bike in bikes:
            self._print(f"[{bike.id}] {bike}")

    def add_bike(self) -> None:
        kind = self._ask(f"Тип ({'/'.join(BIKE_KINDS)})")
        extra = {}
        if kind == "electric":
            extra["battery_wh"] = self._ask_int("Ёмкость батареи, Вт*ч")
        bike = self.service.add_bike(
            kind,
            self._ask("Модель"),
            self._ask_int("id станции"),
            self._ask_float("Цена за час"),
            self._ask_int_list("Аксессуары"),
            **extra,
        )
        self._print(f"Добавлено: [{bike.id}] {bike}")

    def add_customer(self) -> None:
        customer = self.service.add_customer(
            self._ask("ФИО"), self._ask("Email"),
            self._ask("Дата рождения (ГГГГ-ММ-ДД)"))
        self._print(f"Добавлено: [{customer.id}] {customer}")

    def move_bike(self) -> None:
        bike = self.service.move_bike(self._ask_int("id велосипеда"),
                                      self._ask_int("id новой станции"))
        self._print(f"Перемещено: {bike.model} -> станция {bike.station_id}")

    def delete_bike(self) -> None:
        bike = self.service.delete_bike(self._ask_int("id велосипеда"))
        self._print(f"Удалено: {bike.model}")

    def save_data(self) -> None:
        storage = self._make_storage()
        storage.save(self.service)
        self._print(f"Данные сохранены в {storage.path}")

    def load_data(self) -> None:
        storage = self._make_storage()
        storage.load(self.service)
        self._print(f"Данные загружены из {storage.path}")

    # ------------------------------------------------------- главный цикл
    def run(self) -> None:
        while True:
            self._print(MENU)
            try:
                choice = self._ask("Выберите пункт")
                if choice == "0":
                    self._print("До свидания!")
                    return
                action = self._actions.get(choice)
                if action is None:
                    self._print("Нет такого пункта меню")
                    continue
                action()
            except BikeRentalError as error:
                self._print(f"Ошибка: {error}")
            except ValueError as error:
                self._print(f"Некорректный ввод: {error}")
            except (EOFError, KeyboardInterrupt):
                self._print("\nВвод прерван, работа завершена")
                return
            except Exception as error:  # последний рубеж: не падать
                self._print(f"Непредвиденная ошибка: "
                            f"{type(error).__name__}: {error}")
