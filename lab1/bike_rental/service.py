"""Репозиторий (CRUD) и сервис проката велосипедов."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Callable, Generic, Iterable, Iterator, TypeVar

from .exceptions import (
    DependencyError,
    DuplicateEntityError,
    EntityNotFoundError,
    RentalConflictError,
)
from .models import (
    Accessory,
    Bike,
    Customer,
    Entity,
    Notification,
    Rental,
    Station,
    TimeSlot,
    bike_from_dict,
    parse_date,
)

T = TypeVar("T", bound=Entity)


class Repository(Generic[T]):
    """Хранилище объектов одного типа в памяти. Реализует CRUD."""

    def __init__(self, entity_name: str) -> None:
        self._entity_name = entity_name
        self._items: dict[int, T] = {}

    def next_id(self) -> int:
        """Возвращает свободный идентификатор."""
        return max(self._items, default=0) + 1

    # Create
    def add(self, item: T) -> T:
        if item.id in self._items:
            raise DuplicateEntityError(
                f"{self._entity_name} с id={item.id} уже существует")
        self._items[item.id] = item
        return item

    # Read
    def get(self, item_id: int) -> T:
        try:
            return self._items[item_id]
        except KeyError:
            raise EntityNotFoundError(self._entity_name, item_id) from None

    def all(self) -> list[T]:
        return sorted(self._items.values(), key=lambda item: item.id)

    def find(self, predicate: Callable[[T], bool]) -> list[T]:
        return [item for item in self.all() if predicate(item)]

    # Update
    def update(self, item: T) -> T:
        self.get(item.id)  # бросит EntityNotFoundError, если нет такого id
        self._items[item.id] = item
        return item

    # Delete
    def delete(self, item_id: int) -> T:
        item = self.get(item_id)
        del self._items[item_id]
        return item

    def clear(self) -> None:
        self._items.clear()

    def __len__(self) -> int:
        return len(self._items)

    def __contains__(self, item_id: int) -> bool:
        return item_id in self._items

    def __iter__(self) -> Iterator[T]:
        return iter(self.all())


class RentalService:
    """Бизнес-логика: управление справочниками и арендами."""

    def __init__(self) -> None:
        self.stations: Repository[Station] = Repository("Станция")
        self.accessories: Repository[Accessory] = Repository("Аксессуар")
        self.bikes: Repository[Bike] = Repository("Велосипед")
        self.customers: Repository[Customer] = Repository("Клиент")
        self.rentals: Repository[Rental] = Repository("Аренда")
        self.notifications: list[Notification] = []

    # ------------------------------------------------------ справочники
    def add_station(self, name: str, address: str) -> Station:
        return self.stations.add(
            Station(self.stations.next_id(), name, address))

    def add_accessory(self, name: str) -> Accessory:
        return self.accessories.add(
            Accessory(self.accessories.next_id(), name))

    def add_customer(self, full_name: str, email: str,
                     birth_date: str) -> Customer:
        return self.customers.add(Customer(
            self.customers.next_id(), full_name, email,
            parse_date(birth_date)))

    def add_bike(self, kind: str, model: str, station_id: int,
                 price_per_hour: float, accessory_ids: Iterable[int] = (),
                 **extra: Any) -> Bike:
        """Создаёт велосипед нужного типа ('city' или 'electric')."""
        data = {
            "id": self.bikes.next_id(), "kind": kind, "model": model,
            "station_id": station_id, "price_per_hour": price_per_hour,
            "accessory_ids": list(accessory_ids), **extra,
        }
        self.stations.get(station_id)
        for accessory_id in data["accessory_ids"]:
            self.accessories.get(accessory_id)
        return self.bikes.add(bike_from_dict(data))

    def move_bike(self, bike_id: int, station_id: int) -> Bike:
        """Переводит велосипед на другую станцию (Update)."""
        bike = self.bikes.get(bike_id)
        self.stations.get(station_id)
        bike.station_id = station_id
        return self.bikes.update(bike)

    # ---------------------------------------------------------- аренда
    def _find_conflict(self, bike_id: int, slot: TimeSlot,
                       ignore_id: int | None = None) -> Rental | None:
        for rental in self.rentals:
            if (rental.bike_id == bike_id and rental.is_active
                    and rental.id != ignore_id
                    and rental.slot.overlaps(slot)):
                return rental
        return None

    def create_rental(self, bike_id: int, customer_id: int,
                      start: datetime, end: datetime) -> Rental:
        bike = self.bikes.get(bike_id)
        customer = self.customers.get(customer_id)
        slot = TimeSlot(start, end)

        bike.check_rental(slot, customer)
        conflict = self._find_conflict(bike_id, slot)
        if conflict is not None:
            raise RentalConflictError(bike.model, conflict.id)

        rental = Rental(self.rentals.next_id(), bike_id, customer_id, slot,
                        bike.calculate_cost(slot), bike.initial_status())
        self.rentals.add(rental)
        self._notify(customer, f"Оформлена аренда {rental}")
        return rental

    def reschedule_rental(self, rental_id: int, start: datetime,
                          end: datetime) -> Rental:
        """Переносит аренду на другое время (Update)."""
        rental = self.rentals.get(rental_id)
        bike = self.bikes.get(rental.bike_id)
        customer = self.customers.get(rental.customer_id)
        slot = TimeSlot(start, end)
        bike.check_rental(slot, customer)
        conflict = self._find_conflict(bike.id, slot, ignore_id=rental.id)
        if conflict is not None:
            raise RentalConflictError(bike.model, conflict.id)
        rental.slot = slot
        rental.cost = bike.calculate_cost(slot)
        self.rentals.update(rental)
        self._notify(customer, f"Аренда перенесена: {rental}")
        return rental

    def approve_rental(self, rental_id: int) -> Rental:
        rental = self.rentals.get(rental_id)
        rental.confirm()
        self._notify(self.customers.get(rental.customer_id),
                     f"Залог принят, аренда подтверждена: {rental}")
        return rental

    def cancel_rental(self, rental_id: int) -> Rental:
        rental = self.rentals.get(rental_id)
        rental.cancel()
        self._notify(self.customers.get(rental.customer_id),
                     f"Аренда отменена: {rental}")
        return rental

    def find_free_bikes(self, start: datetime, end: datetime,
                        station_id: int | None = None,
                        accessory_ids: Iterable[int] = ()) -> list[Bike]:
        """Ищет свободные на интервале велосипеды с нужными аксессуарами."""
        slot = TimeSlot(start, end)
        needed = set(accessory_ids)
        return self.bikes.find(
            lambda bike: (station_id is None or bike.station_id == station_id)
            and needed <= set(bike.accessory_ids)
            and self._find_conflict(bike.id, slot) is None
        )

    def rentals_of_bike(self, bike_id: int) -> list[Rental]:
        self.bikes.get(bike_id)
        return self.rentals.find(lambda r: r.bike_id == bike_id)

    def rentals_of_customer(self, customer_id: int) -> list[Rental]:
        self.customers.get(customer_id)
        return self.rentals.find(lambda r: r.customer_id == customer_id)

    # ------------------------------------------------- удаление с ссылками
    def delete_bike(self, bike_id: int) -> Bike:
        if any(r.is_active for r in self.rentals_of_bike(bike_id)):
            raise DependencyError(
                "Нельзя удалить велосипед с активными арендами")
        return self.bikes.delete(bike_id)

    def delete_customer(self, customer_id: int) -> Customer:
        if any(r.is_active for r in self.rentals_of_customer(customer_id)):
            raise DependencyError(
                "Нельзя удалить клиента с активными арендами")
        return self.customers.delete(customer_id)

    def delete_station(self, station_id: int) -> Station:
        if self.bikes.find(lambda b: b.station_id == station_id):
            raise DependencyError("На станции остались велосипеды")
        return self.stations.delete(station_id)

    def _notify(self, customer: Customer, text: str) -> None:
        self.notifications.append(Notification(customer.email, text))

    # ------------------------------------------------ обмен с хранилищем
    def export_data(self) -> dict[str, list[dict[str, Any]]]:
        """Собирает все данные в словарь для записи в файл."""
        return {
            "stations": [x.to_dict() for x in self.stations],
            "accessories": [x.to_dict() for x in self.accessories],
            "bikes": [x.to_dict() for x in self.bikes],
            "customers": [x.to_dict() for x in self.customers],
            "rentals": [x.to_dict() for x in self.rentals],
        }

    def import_data(self, data: dict[str, list[dict[str, Any]]]) -> None:
        """Заменяет содержимое сервиса данными, прочитанными из файла."""
        loaders: list[tuple[str, Repository[Any],
                            Callable[[dict[str, Any]], Entity]]] = [
            ("stations", self.stations, Station.from_dict),
            ("accessories", self.accessories, Accessory.from_dict),
            ("bikes", self.bikes, bike_from_dict),
            ("customers", self.customers, Customer.from_dict),
            ("rentals", self.rentals, Rental.from_dict),
        ]
        # сначала разбираем всё во временные списки: если в файле ошибка,
        # текущие данные программы не будут испорчены
        parsed = [(repo, [builder(row) for row in data.get(key, [])])
                  for key, repo, builder in loaders]
        for repo, items in parsed:
            repo.clear()
            for item in items:
                repo.add(item)
