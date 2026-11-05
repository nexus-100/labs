"""Тесты получения текста из файла и по URL (сеть заменена заглушками)."""
import os
import tempfile
import unittest
from unittest.mock import MagicMock, patch

import requests

from sources import SourceError, fetch_url_text, html_to_text, read_text_file


class TestReadTextFile(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.dir.cleanup)

    def _write(self, name, data, mode="w", **kwargs):
        path = os.path.join(self.dir.name, name)
        with open(path, mode, **kwargs) as file:
            file.write(data)
        return path

    def test_reads_utf8(self):
        path = self._write(
            "a.txt", "Центральная: 55.7, 37.6\n", encoding="utf-8")
        self.assertEqual(read_text_file(path), "Центральная: 55.7, 37.6\n")

    def test_missing_file(self):
        with self.assertRaises(SourceError) as ctx:
            read_text_file(os.path.join(self.dir.name, "none.txt"))
        self.assertIn("не найден", str(ctx.exception))

    def test_wrong_encoding(self):
        path = self._write("b.bin", b"\xff\xfe\xfa", mode="wb")
        with self.assertRaises(SourceError) as ctx:
            read_text_file(path)
        self.assertIn("кодировке", str(ctx.exception))

    def test_directory_instead_of_file(self):
        with self.assertRaises(SourceError):
            read_text_file(self.dir.name)

    def test_other_encoding(self):
        path = self._write("c.txt", "Привет", encoding="cp1251")
        self.assertEqual(read_text_file(path, encoding="cp1251"), "Привет")


class TestHtmlToText(unittest.TestCase):
    def test_removes_tags(self):
        self.assertEqual(html_to_text("<b>1.5</b>, 2.5").replace(" ", ""),
                         "1.5,2.5")

    def test_removes_script_and_style(self):
        page = ("<style>a{width:1.5px}</style><script>x='1.5, 2.5'</script>"
                "<p>text</p>")
        text = html_to_text(page)
        self.assertNotIn("1.5", text)
        self.assertIn("text", text)

    def test_script_case_insensitive_multiline(self):
        page = "<SCRIPT>\nvar a = '10.5, 20.5';\n</SCRIPT>ok"
        self.assertNotIn("10.5", html_to_text(page))

    def test_unescapes_entities(self):
        self.assertIn("°", html_to_text("55.7&deg; N"))


class TestFetchUrlText(unittest.TestCase):
    URL = "https://example.com/stations"

    def _response(self, text="", error=None):
        response = MagicMock()
        response.text = text
        if error is not None:
            response.raise_for_status.side_effect = error
        return response

    @patch("sources.requests.get")
    def test_success(self, get):
        get.return_value = self._response("<p>55.7, 37.6</p>")
        text = fetch_url_text(self.URL, timeout=3)
        self.assertIn("55.7, 37.6", text)
        self.assertNotIn("<p>", text)
        get.assert_called_once_with(self.URL, timeout=3)

    @patch("sources.requests.get")
    def test_http_error(self, get):
        get.return_value = self._response(
            error=requests.exceptions.HTTPError("404 Not Found"))
        with self.assertRaises(SourceError) as ctx:
            fetch_url_text(self.URL)
        self.assertIn("404", str(ctx.exception))

    @patch("sources.requests.get")
    def test_connection_error(self, get):
        get.side_effect = requests.exceptions.ConnectionError("нет сети")
        with self.assertRaises(SourceError):
            fetch_url_text(self.URL)

    @patch("sources.requests.get")
    def test_timeout(self, get):
        get.side_effect = requests.exceptions.Timeout("долго")
        with self.assertRaises(SourceError):
            fetch_url_text(self.URL)

    @patch("sources.requests.get")
    def test_bad_url_does_not_call_network(self, get):
        for url in ("", "example.com", "ftp://example.com", "http://", "abc"):
            with self.subTest(url=url):
                with self.assertRaises(SourceError):
                    fetch_url_text(url)
        get.assert_not_called()


if __name__ == "__main__":
    unittest.main()
