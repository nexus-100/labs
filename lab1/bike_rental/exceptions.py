"""Собственные исключения предметной области «Прокат велосипедов».

Все исключения наследуются от BikeRentalError, поэтому пользовательский
интерфейс может перехватить их одним блоком ``except BikeRentalError``.
"""


class BikeRentalError(Exception):
    """Базовое исключение приложения."""


class ValidationError(BikeRentalError):
    """Некорректное значение поля (пустое имя, отрицательная цена)."""


class EntityNotFoundError(BikeRentalError):
    """Объект с указанным идентификатором не найден в хранилище."""

    def __init__(self, entity_name: str, entity_id: int) -> None:
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} с id={entity_id} не найден(а)")


class DuplicateEntityError(BikeRentalError):
    """Объект с таким идентификатором уже существует."""


class DependencyError(BikeRentalError):
    """Объект нельзя удалить: на него ссылаются другие объекты."""


class RentalConflictError(BikeRentalError):
    """Собственное исключение: велосипед уже арендован на это время."""

    def __init__(self, bike_model: str, conflict_rental_id: int) -> None:
        self.bike_model = bike_model
        self.conflict_rental_id = conflict_rental_id
        super().__init__(
            f"Велосипед «{bike_model}» уже арендован "
            f"(аренда №{conflict_rental_id})"
        )


class AgeRestrictionError(BikeRentalError):
    """Клиент младше минимального возраста для этого велосипеда."""


class InvalidStatusError(BikeRentalError):
    """Недопустимый переход между статусами аренды."""


class StorageError(BikeRentalError):
    """Ошибка чтения или записи файла данных (JSON или XML)."""
