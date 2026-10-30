"""Классы предметной области «Прокат велосипедов»."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime
from enum import Enum
from typing import Any, ClassVar

from .exceptions import (
    AgeRestrictionError,
    InvalidStatusError,
    ValidationError,
)

DATETIME_FORMAT = "%Y-%m-%dT%H:%M"
DATE_FORMAT = "%Y-%m-%d"


# ---------------------------------------------------------------- helpers
def require_text(value: Any, field: str) -> str:
    """Проверяет, что значение - непустая строка, и возвращает её."""
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"Поле «{field}» не может быть пустым")
    return value.strip()


def require_positive(value: Any, field: str) -> int:
    """Проверяет, что значение - целое положительное число."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"Поле «{field}» должно быть числом") from None
    if number <= 0:
        raise ValidationError(f"Поле «{field}» должно быть больше нуля")
    return number


def require_price(value: Any, field: str) -> float:
    """Проверяет, что значение - положительное число (цена)."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"Поле «{field}» должно быть числом") from None
    if number <= 0:
        raise ValidationError(f"Поле «{field}» должно быть больше нуля")
    return round(number, 2)


def parse_datetime(value: str) -> datetime:
    """Разбирает строку формата ГГГГ-ММ-ДДTЧЧ:ММ."""
    try:
        return datetime.strptime(value.strip(), DATETIME_FORMAT)
    except (AttributeError, ValueError):
        raise ValidationError(
            f"Дата «{value}» не соответствует формату ГГГГ-ММ-ДДTЧЧ:ММ"
        ) from None


def parse_date(value: str) -> date:
    """Разбирает строку формата ГГГГ-ММ-ДД."""
    try:
        return datetime.strptime(value.strip(), DATE_FORMAT).date()
    except (AttributeError, ValueError):
        raise ValidationError(
            f"Дата «{value}» не соответствует формату ГГГГ-ММ-ДД"
        ) from None


# ------------------------------------------------------------ base entity
class Entity(ABC):
    """Базовый класс всех хранимых объектов: имеет целочисленный id."""

    def __init__(self, entity_id: int) -> None:
        self._id: int = require_positive(entity_id, "id")

    @property
    def id(self) -> int:
        return self._id

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Преобразует объект в словарь для записи в JSON/XML."""

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict[str, Any]) -> Entity:
        """Создаёт объект из словаря, прочитанного из JSON/XML."""

    def __eq__(self, other: object) -> bool:
        if type(self) is not type(other):
            return False
        return self.id == other.id  # type: ignore[attr-defined]

    def __hash__(self) -> int:
        return hash((type(self).__name__, self._id))


# ---------------------------------------------------------------- simple
class Accessory(Entity):
    """Аксессуар к велосипеду (шлем, замок, детское кресло)."""

    def __init__(self, entity_id: int, name: str) -> None:
        super().__init__(entity_id)
        self.name = name

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = require_text(value, "название аксессуара")

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Accessory:
        return cls(int(data["id"]), data["name"])

    def __str__(self) -> str:
        return self.name


class Station(Entity):
    """Станция проката, где хранятся велосипеды."""

    def __init__(self, entity_id: int, name: str, address: str) -> None:
        super().__init__(entity_id)
        self.name = name
        self.address = address

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = require_text(value, "название станции")

    @property
    def address(self) -> str:
        return self._address

    @address.setter
    def address(self, value: str) -> None:
        self._address = require_text(value, "адрес")

    def to_dict(self) -> dict[str, Any]:
        return {"id": self.id, "name": self.name, "address": self.address}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Station:
        return cls(int(data["id"]), data["name"], data["address"])

    def __str__(self) -> str:
        return f"{self.name} ({self.address})"


class Customer(Entity):
    """Клиент проката."""

    def __init__(self, entity_id: int, full_name: str, email: str,
                 birth_date: date) -> None:
        super().__init__(entity_id)
        self.full_name = full_name
        self.email = email
        self.birth_date = birth_date

    @property
    def full_name(self) -> str:
        return self._full_name

    @full_name.setter
    def full_name(self, value: str) -> None:
        self._full_name = require_text(value, "ФИО")

    @property
    def email(self) -> str:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        value = require_text(value, "email")
        if "@" not in value or value.startswith("@") or value.endswith("@"):
            raise ValidationError(f"Некорректный email: {value}")
        self._email = value

    @property
    def birth_date(self) -> date:
        return self._birth_date

    @birth_date.setter
    def birth_date(self, value: date) -> None:
        if not isinstance(value, date) or value > date.today():
            raise ValidationError("Дата рождения указана неверно")
        self._birth_date = value

    def age_on(self, day: date) -> int:
        """Возраст клиента (полных лет) на указанную дату."""
        years = day.year - self._birth_date.year
        if (day.month, day.day) < (self._birth_date.month,
                                   self._birth_date.day):
            years -= 1
        return years

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "full_name": self.full_name,
            "email": self.email,
            "birth_date": self.birth_date.strftime(DATE_FORMAT),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Customer:
        return cls(int(data["id"]), data["full_name"], data["email"],
                   parse_date(data["birth_date"]))

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"


# ------------------------------------------------------- time and rental
class TimeSlot:
    """Временной интервал [start, end). Неизменяемый объект-значение."""

    def __init__(self, start: datetime, end: datetime) -> None:
        if end <= start:
            raise ValidationError("Время окончания должно быть позже начала")
        self._start = start
        self._end = end

    @property
    def start(self) -> datetime:
        return self._start

    @property
    def end(self) -> datetime:
        return self._end

    @property
    def duration_hours(self) -> float:
        return (self._end - self._start).total_seconds() / 3600

    def overlaps(self, other: TimeSlot) -> bool:
        """Интервалы пересекаются, если каждый начинается до конца другого.

        Аренды «встык» (одна заканчивается в 10:00, другая начинается
        в 10:00) конфликтом не считаются.
        """
        return self._start < other.end and other.start < self._end

    def __str__(self) -> str:
        return f"{self._start:%d.%m.%Y %H:%M}-{self._end:%d.%m %H:%M}"

    def __eq__(self, other: object) -> bool:
        return (isinstance(other, TimeSlot) and self._start == other.start
                and self._end == other.end)

    def __hash__(self) -> int:
        return hash((self._start, self._end))


class RentalStatus(Enum):
    """Статус аренды."""

    PENDING = "pending"        # ожидает подтверждения залога
    CONFIRMED = "confirmed"    # подтверждена
    CANCELLED = "cancelled"    # отменена

    @property
    def title(self) -> str:
        return {
            RentalStatus.PENDING: "ожидает залога",
            RentalStatus.CONFIRMED: "подтверждена",
            RentalStatus.CANCELLED: "отменена",
        }[self]


# ------------------------------------------------------------------ bikes
class Bike(Entity):
    """Велосипед (базовый класс для иерархии велосипедов)."""

    KIND: ClassVar[str] = "bike"
    MAX_HOURS: ClassVar[float] = 24.0
    MIN_AGE: ClassVar[int] = 12
    REQUIRES_APPROVAL: ClassVar[bool] = False

    def __init__(self, entity_id: int, model: str, station_id: int,
                 price_per_hour: float,
                 accessory_ids: list[int] | None = None) -> None:
        super().__init__(entity_id)
        self.model = model
        self.station_id = require_positive(station_id, "станция")
        self.price_per_hour = price_per_hour
        self.accessory_ids: list[int] = list(accessory_ids or [])

    @property
    def model(self) -> str:
        return self._model

    @model.setter
    def model(self, value: str) -> None:
        self._model = require_text(value, "модель велосипеда")

    @property
    def price_per_hour(self) -> float:
        return self._price_per_hour

    @price_per_hour.setter
    def price_per_hour(self, value: float) -> None:
        self._price_per_hour = require_price(value, "цена за час")

    def initial_status(self) -> RentalStatus:
        """Статус новой аренды: полиморфный метод."""
        if self.REQUIRES_APPROVAL:
            return RentalStatus.PENDING
        return RentalStatus.CONFIRMED

    def calculate_cost(self, slot: TimeSlot) -> float:
        """Стоимость аренды на интервал."""
        return round(self._price_per_hour * slot.duration_hours, 2)

    def check_rental(self, slot: TimeSlot, customer: Customer) -> None:
        """Проверяет, можно ли выдать велосипед клиенту на интервал."""
        age = customer.age_on(slot.start.date())
        if age < self.MIN_AGE:
            raise AgeRestrictionError(
                f"Велосипед «{self.model}» выдаётся с {self.MIN_AGE} лет, "
                f"а клиенту {age}"
            )
        if slot.duration_hours > self.MAX_HOURS:
            raise ValidationError(
                f"Аренда «{self.model}» не может быть длиннее "
                f"{self.MAX_HOURS:g} ч."
            )

    def _base_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.KIND,
            "model": self.model,
            "station_id": self.station_id,
            "price_per_hour": self.price_per_hour,
            "accessory_ids": list(self.accessory_ids),
        }

    def to_dict(self) -> dict[str, Any]:
        return self._base_dict()

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Bike:
        return cls(
            int(data["id"]), data["model"], int(data["station_id"]),
            float(data["price_per_hour"]),
            [int(x) for x in data.get("accessory_ids", [])],
        )

    def __str__(self) -> str:
        return f"{self.model} ({self.price_per_hour:g} руб./ч)"


class CityBike(Bike):
    """Городской велосипед: до 24 часов, с 12 лет, без залога."""

    KIND = "city"
    MAX_HOURS = 24.0
    MIN_AGE = 12
    REQUIRES_APPROVAL = False


class ElectricBike(Bike):
    """Электровелосипед: до 8 часов, с 16 лет, нужен залог."""

    KIND = "electric"
    MAX_HOURS = 8.0
    MIN_AGE = 16
    REQUIRES_APPROVAL = True

    def __init__(self, entity_id: int, model: str, station_id: int,
                 price_per_hour: float,
                 accessory_ids: list[int] | None = None,
                 battery_wh: int = 400) -> None:
        super().__init__(entity_id, model, station_id, price_per_hour,
                         accessory_ids)
        self.battery_wh = require_positive(battery_wh, "ёмкость батареи")

    def to_dict(self) -> dict[str, Any]:
        data = self._base_dict()
        data["battery_wh"] = self.battery_wh
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ElectricBike:
        return cls(
            int(data["id"]), data["model"], int(data["station_id"]),
            float(data["price_per_hour"]),
            [int(x) for x in data.get("accessory_ids", [])],
            int(data.get("battery_wh", 400)),
        )


BIKE_KINDS: dict[str, type[Bike]] = {
    CityBike.KIND: CityBike,
    ElectricBike.KIND: ElectricBike,
}


def bike_from_dict(data: dict[str, Any]) -> Bike:
    """Фабрика: по полю kind выбирает нужный класс велосипеда."""
    kind = data.get("kind", CityBike.KIND)
    try:
        bike_class = BIKE_KINDS[kind]
    except KeyError:
        raise ValidationError(f"Неизвестный тип велосипеда: {kind}") from None
    return bike_class.from_dict(data)


# ----------------------------------------------------------------- rental
class Rental(Entity):
    """Аренда велосипеда клиентом на временной интервал."""

    def __init__(self, entity_id: int, bike_id: int, customer_id: int,
                 slot: TimeSlot, cost: float,
                 status: RentalStatus = RentalStatus.CONFIRMED) -> None:
        super().__init__(entity_id)
        self.bike_id = require_positive(bike_id, "велосипед")
        self.customer_id = require_positive(customer_id, "клиент")
        self.slot = slot
        self.cost = cost
        self._status = status

    @property
    def status(self) -> RentalStatus:
        return self._status

    @property
    def is_active(self) -> bool:
        return self._status is not RentalStatus.CANCELLED

    def confirm(self) -> None:
        if self._status is not RentalStatus.PENDING:
            raise InvalidStatusError(
                f"Подтвердить можно только аренду в ожидании залога, "
                f"а сейчас: {self._status.title}"
            )
        self._status = RentalStatus.CONFIRMED

    def cancel(self) -> None:
        if self._status is RentalStatus.CANCELLED:
            raise InvalidStatusError("Аренда уже отменена")
        self._status = RentalStatus.CANCELLED

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "bike_id": self.bike_id,
            "customer_id": self.customer_id,
            "start": self.slot.start.strftime(DATETIME_FORMAT),
            "end": self.slot.end.strftime(DATETIME_FORMAT),
            "cost": self.cost,
            "status": self._status.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Rental:
        try:
            status = RentalStatus(data.get("status", "confirmed"))
        except ValueError:
            raise ValidationError(
                f"Неизвестный статус: {data.get('status')}") from None
        slot = TimeSlot(parse_datetime(data["start"]),
                        parse_datetime(data["end"]))
        return cls(int(data["id"]), int(data["bike_id"]),
                   int(data["customer_id"]), slot,
                   float(data["cost"]), status)

    def __str__(self) -> str:
        return (f"№{self.id}, {self.slot}, {self.cost:g} руб., "
                f"{self._status.title}")


class Notification:
    """Уведомление клиенту о событии аренды."""

    def __init__(self, recipient_email: str, text: str) -> None:
        self.recipient_email = recipient_email
        self.text = text
        self.created_at = datetime.now()

    def __str__(self) -> str:
        return (f"[{self.created_at:%H:%M:%S}] -> "
                f"{self.recipient_email}: {self.text}")
