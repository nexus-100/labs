"""Сохранение и загрузка данных в форматах JSON и XML."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .exceptions import BikeRentalError, StorageError
from .service import RentalService

Data = dict[str, list[dict[str, Any]]]

# название коллекции -> название элемента одной записи в XML
XML_RECORD_NAMES: dict[str, str] = {
    "stations": "station",
    "accessories": "accessory",
    "bikes": "bike",
    "customers": "customer",
    "rentals": "rental",
}
XML_ROOT = "bike_rental"


class Storage(ABC):
    """Абстрактное файловое хранилище данных сервиса бронирования."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, service: RentalService) -> None:
        """Записывает данные сервиса в файл."""
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._write(service.export_data())
        except OSError as error:
            raise StorageError(
                f"Не удалось записать файл {self.path}: {error}") from error

    def load(self, service: RentalService) -> None:
        """Читает файл и заменяет данные сервиса."""
        try:
            data = self._read()
            service.import_data(data)
        except StorageError:
            raise  # уже содержит понятное сообщение
        except FileNotFoundError:
            raise StorageError(f"Файл {self.path} не найден") from None
        except OSError as error:
            raise StorageError(
                f"Не удалось прочитать файл {self.path}: {error}"
            ) from error
        except BikeRentalError as error:
            raise StorageError(
                f"В файле {self.path.name} некорректные данные: {error}"
            ) from error
        except (KeyError, TypeError, ValueError, AttributeError) as error:
            raise StorageError(
                f"Файл {self.path.name} имеет неверную структуру "
                f"({type(error).__name__}: {error})"
            ) from error

    @abstractmethod
    def _write(self, data: Data) -> None:
        """Записывает словарь данных в файл конкретного формата."""

    @abstractmethod
    def _read(self) -> Data:
        """Читает файл конкретного формата и возвращает словарь."""


class JsonStorage(Storage):
    """Хранилище в формате JSON."""

    def _write(self, data: Data) -> None:
        with open(self.path, "w", encoding="utf-8") as file:
            json.dump(data, file, ensure_ascii=False, indent=2)

    def _read(self) -> Data:
        try:
            with open(self.path, encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError as error:
            raise StorageError(
                f"Файл {self.path.name} - не корректный JSON: {error}"
            ) from error
        if not isinstance(data, dict):
            raise StorageError("Корень JSON-файла должен быть объектом")
        return data


class XmlStorage(Storage):
    """Хранилище в формате XML.

    Каждая запись - элемент, поля записи - вложенные элементы. Списки
    (например, accessory_ids) помечены атрибутом list="true", а их
    значения лежат во вложенных элементах <item>.
    """

    def _write(self, data: Data) -> None:
        root = ET.Element(XML_ROOT)
        for collection, record_name in XML_RECORD_NAMES.items():
            collection_element = ET.SubElement(root, collection)
            for record in data.get(collection, []):
                record_element = ET.SubElement(collection_element,
                                               record_name)
                for field, value in record.items():
                    self._write_field(record_element, field, value)
        tree = ET.ElementTree(root)
        ET.indent(tree, space="  ")
        tree.write(self.path, encoding="utf-8", xml_declaration=True)

    @staticmethod
    def _write_field(parent: ET.Element, field: str, value: Any) -> None:
        element = ET.SubElement(parent, field)
        if isinstance(value, list):
            element.set("list", "true")
            for item in value:
                ET.SubElement(element, "item").text = str(item)
        elif isinstance(value, bool):
            element.text = "true" if value else "false"
        else:
            element.text = str(value)

    def _read(self) -> Data:
        try:
            root = ET.parse(self.path).getroot()
        except ET.ParseError as error:
            raise StorageError(
                f"Файл {self.path.name} - не корректный XML: {error}"
            ) from error
        if root.tag != XML_ROOT:
            raise StorageError(
                f"Корневой элемент должен называться <{XML_ROOT}>")
        data: Data = {}
        for collection, record_name in XML_RECORD_NAMES.items():
            collection_element = root.find(collection)
            records = []
            if collection_element is not None:
                for record_element in collection_element.findall(
                        record_name):
                    records.append(self._read_record(record_element))
            data[collection] = records
        return data

    @staticmethod
    def _read_record(record_element: ET.Element) -> dict[str, Any]:
        record: dict[str, Any] = {}
        for field in record_element:
            if field.get("list") == "true":
                record[field.tag] = [item.text or ""
                                     for item in field.findall("item")]
            else:
                record[field.tag] = field.text or ""
        return record
