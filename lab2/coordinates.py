"""Регулярное выражение для поиска и проверки географических координат.

Предметная область: координаты станций проката велосипедов (см. ЛР1).
Поддерживаются два формата записи координат (широта, затем долгота):

1. Десятичные градусы со знаком: 55.7558, 37.6176
2. Десятичные градусы с полушарием: 55.7558° N, 37.6176° E
   (допустимы латинские N/S/E/W и русские С/Ю/В/З).
"""
import re
from dataclasses import dataclass


class InvalidCoordinateError(ValueError):
    """Строка не является синтаксически корректной координатой."""


# Широта: от 0 до 90 включительно, обязательная дробная часть (1-8 цифр).
LAT_NUMBER = r"(?:90\.0{1,8}|[1-8]?\d\.\d{1,8})"
# Долгота: от 0 до 180 включительно, обязательная дробная часть (1-8 цифр).
LON_NUMBER = r"(?:180\.0{1,8}|1[0-7]\d\.\d{1,8}|[1-9]?\d\.\d{1,8})"

# Формат 1: знак перед числом, разделитель - запятая или точка с запятой.
_SIGNED = (
    rf"(?P<lat>[+-]?{LAT_NUMBER})\s*[,;]\s*(?P<lon>[+-]?{LON_NUMBER})"
)
# Формат 2: знак градуса и буква полушария после каждого числа.
# Между широтой и долготой обязательны разделитель или пробельный символ.
_HEMISPHERE = (
    rf"(?P<lat_h>{LAT_NUMBER})\s*°\s*(?P<ns>[NSСЮ])"
    rf"(?:\s*[,;]\s*|\s+)"
    rf"(?P<lon_h>{LON_NUMBER})\s*°\s*(?P<ew>[EWВЗ])"
)

# Слева не должно быть буквы, цифры, точки, плюса или минуса,
# справа - буквы/цифры или точки с цифрой (чтобы не резать длинные числа).
COORDINATE_PATTERN = re.compile(
    rf"(?<![\w.+-])(?:{_SIGNED}|{_HEMISPHERE})(?!\w)(?!\.\d)"
)

_NEGATIVE_HEMISPHERES = {"S", "Ю", "W", "З"}


@dataclass(frozen=True)
class Coordinate:
    """Пара «широта - долгота» в десятичных градусах."""

    latitude: float
    longitude: float
    raw: str = ""

    def __str__(self) -> str:
        return f"{self.latitude:.6f}, {self.longitude:.6f}"


def _from_match(match: re.Match) -> Coordinate:
    """Строит объект Coordinate по результату совпадения."""
    if match.group("lat") is not None:
        lat = float(match.group("lat"))
        lon = float(match.group("lon"))
    else:
        lat = float(match.group("lat_h"))
        lon = float(match.group("lon_h"))
        if match.group("ns") in _NEGATIVE_HEMISPHERES:
            lat = -lat
        if match.group("ew") in _NEGATIVE_HEMISPHERES:
            lon = -lon
    return Coordinate(lat, lon, match.group(0))


def is_valid_coordinate(text: str) -> bool:
    """Проверяет, что вся строка (без краевых пробелов) - координата."""
    if not isinstance(text, str):
        return False
    return COORDINATE_PATTERN.fullmatch(text.strip()) is not None


def parse_coordinate(text: str) -> Coordinate:
    """Разбирает строку в Coordinate или бросает InvalidCoordinateError."""
    if not isinstance(text, str):
        raise InvalidCoordinateError("Ожидалась строка")
    match = COORDINATE_PATTERN.fullmatch(text.strip())
    if match is None:
        raise InvalidCoordinateError(
            f"«{text}» не является корректной координатой"
        )
    return _from_match(match)


def find_coordinates(text: str) -> list[Coordinate]:
    """Возвращает все координаты, найденные в тексте, в порядке появления."""
    return [_from_match(m) for m in COORDINATE_PATTERN.finditer(text)]
