"""Тесты консольного меню: ввод и вывод заменены списками."""
import os
import unittest
from unittest.mock import patch

import app
from sources import SourceError

DATA = os.path.join(os.path.dirname(__file__), "..", "data")


def run_app(*answers):
    """Запускает меню с заранее заданными ответами, возвращает вывод."""
    inputs = iter(answers)
    output = []

    def fake_input(prompt=""):
        try:
            return next(inputs)
        except StopIteration:
            raise EOFError from None

    app.run(input_fn=fake_input, print_fn=output.append)
    return "\n".join(output)


class TestMenu(unittest.TestCase):
    def test_exit(self):
        self.assertIn("До свидания", run_app("0"))

    def test_unknown_item(self):
        self.assertIn("Нет такого пункта", run_app("abc", "0"))

    def test_check_valid(self):
        out = run_app("1", "55.7558, 37.6176", "0")
        self.assertIn("Корректно: 55.755800, 37.617600", out)

    def test_check_invalid(self):
        out = run_app("1", "91.0, 10.0", "0")
        self.assertIn("Некорректная координата", out)

    def test_find_in_text(self):
        out = run_app("2", "тут 10.5, 20.5 и 30.5° N, 40.5° W", "0")
        self.assertIn("Найдено координат: 2", out)
        self.assertIn("-40.500000", out)

    def test_find_in_text_nothing(self):
        self.assertIn("не найдены", run_app("2", "ничего", "0"))

    def test_find_in_file(self):
        out = run_app("3", os.path.join(DATA, "stations.txt"), "0")
        self.assertIn("Найдено координат: 5", out)

    def test_missing_file_does_not_stop_program(self):
        out = run_app("3", "нет_такого.txt", "0")
        self.assertIn("Ошибка: Файл нет_такого.txt не найден", out)
        self.assertIn("До свидания", out)

    @patch("app.fetch_url_text")
    def test_find_by_url(self, fetch):
        fetch.return_value = "Арбат: 55.7522, 37.5927"
        out = run_app("4", "https://example.com", "0")
        self.assertIn("Найдено координат: 1", out)
        fetch.assert_called_once_with("https://example.com")

    @patch("app.fetch_url_text", side_effect=SourceError("нет сети"))
    def test_url_error_is_reported(self, _fetch):
        out = run_app("4", "https://example.com", "0")
        self.assertIn("Ошибка: нет сети", out)

    @patch("app.fetch_url_text", side_effect=RuntimeError("сбой"))
    def test_unexpected_error_is_caught(self, _fetch):
        out = run_app("4", "https://example.com", "0")
        self.assertIn("Непредвиденная ошибка: сбой", out)
        self.assertIn("До свидания", out)

    def test_eof_ends_program(self):
        self.assertIn("Ввод прерван", run_app())

    def test_keyboard_interrupt_ends_program(self):
        def raise_interrupt(prompt=""):
            raise KeyboardInterrupt
        output = []
        app.run(input_fn=raise_interrupt, print_fn=output.append)
        self.assertIn("Ввод прерван", "\n".join(output))


if __name__ == "__main__":
    unittest.main()
