"""Тесты регулярного выражения для координат."""
import unittest

from coordinates import (
    Coordinate,
    InvalidCoordinateError,
    find_coordinates,
    is_valid_coordinate,
    parse_coordinate,
)


class TestIsValidCoordinate(unittest.TestCase):
    """Проверка целой строки."""

    def test_valid_signed(self):
        cases = [
            "55.7558, 37.6176",
            "55.7558,37.6176",
            "55.7558 ; 37.6176",
            "+55.7558, +37.6176",
            "-55.7558, -37.6176",
            "0.0, 0.0",
            "-0.5, 0.5",
            "89.99999999, 179.99999999",
            "90.0, 180.0",
            "-90.0, -180.0",
            "90.000, 180.000",
            "5.5, 5.5",
            "45.1, 100.1",
            "  55.7558, 37.6176  ",
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertTrue(is_valid_coordinate(text))

    def test_valid_hemisphere(self):
        cases = [
            "55.7558° N, 37.6176° E",
            "55.7558°N 37.6176°E",
            "33.8688° S, 151.2093° E",
            "40.7128° N; 74.0060° W",
            "55.7558° С, 37.6176° В",
            "33.8688° Ю, 70.6693° З",
            "90.0° N, 180.0° W",
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertTrue(is_valid_coordinate(text))

    def test_latitude_out_of_range(self):
        cases = ["90.1, 10.5", "91.5, 37.6", "99.9, 10.5", "-90.5, 10.5",
                 "100.0, 10.5", "90.1° N, 10.5° E"]
        for text in cases:
            with self.subTest(text=text):
                self.assertFalse(is_valid_coordinate(text))

    def test_longitude_out_of_range(self):
        cases = ["10.5, 180.1", "10.5, 181.2", "10.5, 200.0", "10.5, -180.5",
                 "10.5, 360.0", "10.5° N, 180.5° E"]
        for text in cases:
            with self.subTest(text=text):
                self.assertFalse(is_valid_coordinate(text))

    def test_bad_number_format(self):
        cases = [
            "55, 37",                  # нет дробной части
            "55.7558, 37",
            "55., 37.5",
            ".7558, 37.5",
            "05.7558, 37.6176",        # ведущий ноль
            "55.7558, 037.6176",
            "55.755812345, 37.6176",   # больше 8 знаков
            "55,7558, 37,6176",        # запятая вместо точки
            "1055.7558, 37.6176",
            "55.7558, 37.6176.1",
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertFalse(is_valid_coordinate(text))

    def test_bad_structure(self):
        cases = [
            "",
            "   ",
            "55.7558",
            "55.7558, ",
            ", 37.6176",
            "55.7558 37.6176",          # нет разделителя в формате 1
            "55.7558, 37.6176, 10.5",
            "abc, def",
            "55.7558, 37.6176 abc",
            "x55.7558, 37.6176",
            "--55.7558, 37.6176",
            "55.7558° N 37.6176",       # нет второго полушария
            "55.7558 N, 37.6176 E",     # нет знака градуса
            "55.7558° E, 37.6176° N",   # перепутаны полушария
            "55.7558° X, 37.6176° E",
            "55.7558° n, 37.6176° e",   # строчные буквы не допускаются
        ]
        for text in cases:
            with self.subTest(text=text):
                self.assertFalse(is_valid_coordinate(text))

    def test_not_string(self):
        for value in (None, 55.7, 123, ["1.0, 2.0"]):
            with self.subTest(value=value):
                self.assertFalse(is_valid_coordinate(value))


class TestParseCoordinate(unittest.TestCase):
    """Разбор строки в объект."""

    def test_signed(self):
        item = parse_coordinate("-33.8688, 151.2093")
        self.assertEqual(item.latitude, -33.8688)
        self.assertEqual(item.longitude, 151.2093)

    def test_hemisphere_signs(self):
        item = parse_coordinate("33.8688° S, 70.6693° W")
        self.assertEqual((item.latitude, item.longitude),
                         (-33.8688, -70.6693))
        item = parse_coordinate("33.8688° Ю, 70.6693° З")
        self.assertEqual((item.latitude, item.longitude),
                         (-33.8688, -70.6693))

    def test_hemisphere_positive(self):
        item = parse_coordinate("55.7558° N, 37.6176° E")
        self.assertEqual((item.latitude, item.longitude), (55.7558, 37.6176))

    def test_raw_and_str(self):
        item = parse_coordinate("  55.7558, 37.6176 ")
        self.assertEqual(item.raw, "55.7558, 37.6176")
        self.assertEqual(str(item), "55.755800, 37.617600")

    def test_equality_and_hash(self):
        first = Coordinate(1.5, 2.5, "a")
        self.assertEqual(first, Coordinate(1.5, 2.5, "a"))
        self.assertEqual(len({first, Coordinate(1.5, 2.5, "a")}), 1)

    def test_invalid_raises(self):
        with self.assertRaises(InvalidCoordinateError):
            parse_coordinate("91.0, 10.0")

    def test_invalid_is_value_error(self):
        with self.assertRaises(ValueError):
            parse_coordinate("abc")

    def test_not_string_raises(self):
        with self.assertRaises(InvalidCoordinateError):
            parse_coordinate(None)


class TestFindCoordinates(unittest.TestCase):
    """Поиск в произвольном тексте."""

    def test_empty_text(self):
        self.assertEqual(find_coordinates(""), [])

    def test_no_coordinates(self):
        self.assertEqual(find_coordinates("Просто текст, 12 велосипедов"), [])

    def test_single_in_sentence(self):
        found = find_coordinates("Станция на 55.7558, 37.6176 открыта.")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].raw, "55.7558, 37.6176")

    def test_end_of_sentence_dot(self):
        found = find_coordinates("Координаты: 55.7558, 37.6176.")
        self.assertEqual([x.raw for x in found], ["55.7558, 37.6176"])

    def test_in_brackets_and_quotes(self):
        text = '(55.7558, 37.6176) и "40.7128, -74.0060"'
        found = find_coordinates(text)
        self.assertEqual(len(found), 2)
        self.assertEqual(found[1].longitude, -74.006)

    def test_mixed_formats_order(self):
        text = ("A: 55.7558, 37.6176; B: 33.8688° S, 151.2093° E; "
                "C: -10.5, -20.5")
        found = find_coordinates(text)
        lats = [x.latitude for x in found]
        self.assertEqual(lats, [55.7558, -33.8688, -10.5])

    def test_duplicates_are_kept(self):
        found = find_coordinates("1.5, 2.5 и снова 1.5, 2.5")
        self.assertEqual(len(found), 2)

    def test_multiline(self):
        text = "первая 10.5, 20.5\nвторая 30.5, 40.5\n"
        self.assertEqual(len(find_coordinates(text)), 2)

    def test_out_of_range_skipped(self):
        text = "91.5, 37.6 и 55.7, 181.2"
        self.assertEqual(find_coordinates(text), [])

    def test_too_long_fraction_skipped(self):
        self.assertEqual(find_coordinates("55.123456789, 37.5"), [])

    def test_glued_to_other_numbers_skipped(self):
        self.assertEqual(find_coordinates("1055.7558, 37.6176"), [])
        self.assertEqual(find_coordinates("id55.7558, 37.6176"), [])
        self.assertEqual(find_coordinates("10-55.7558, 37.6176"), [])

    def test_ip_like_and_versions_skipped(self):
        self.assertEqual(find_coordinates("версия 1.2.3, 192.168.0.1"), [])

    def test_semicolon_separator(self):
        found = find_coordinates("55.7101; 37.5537")
        self.assertEqual(len(found), 1)


if __name__ == "__main__":
    unittest.main()
