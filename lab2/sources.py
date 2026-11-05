"""Получение текста из файла и с веб-страницы."""
import html
import re
from urllib.parse import urlparse

import requests


class SourceError(Exception):
    """Не удалось получить текст из источника (файл или URL)."""


_SCRIPT_STYLE = re.compile(
    r"<(script|style)\b.*?</\1\s*>", re.IGNORECASE | re.DOTALL
)
_TAG = re.compile(r"<[^>]+>")


def read_text_file(path: str, encoding: str = "utf-8") -> str:
    """Читает текстовый файл целиком."""
    try:
        with open(path, "r", encoding=encoding) as file:
            return file.read()
    except FileNotFoundError:
        raise SourceError(f"Файл {path} не найден") from None
    except UnicodeDecodeError:
        raise SourceError(
            f"Файл {path} нельзя прочитать в кодировке {encoding}"
        ) from None
    except OSError as error:
        raise SourceError(f"Ошибка чтения файла {path}: {error}") from None


def html_to_text(page: str) -> str:
    """Убирает из HTML скрипты, стили и теги, раскрывает сущности."""
    page = _SCRIPT_STYLE.sub(" ", page)
    page = _TAG.sub(" ", page)
    return html.unescape(page)


def fetch_url_text(url: str, timeout: float = 10) -> str:
    """Скачивает страницу по URL и возвращает её текст без HTML-разметки."""
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise SourceError(f"Некорректный URL: {url}")
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        raise SourceError(f"Сервер вернул ошибку: {error}") from None
    except requests.exceptions.RequestException as error:
        raise SourceError(f"Не удалось загрузить страницу: {error}") from None
    return html_to_text(response.text)
