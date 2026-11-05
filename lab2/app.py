"""Консольное приложение: поиск и проверка координат станций проката."""
from coordinates import (
    InvalidCoordinateError,
    find_coordinates,
    is_valid_coordinate,
    parse_coordinate,
)
from sources import SourceError, fetch_url_text, read_text_file

MENU = (
    "\n1 - проверить введённую строку\n"
    "2 - найти координаты в введённом тексте\n"
    "3 - найти координаты в файле\n"
    "4 - найти координаты на веб-странице по URL\n"
    "0 - выход"
)


def show_found(text, print_fn=print):
    """Печатает все координаты, найденные в тексте."""
    found = find_coordinates(text)
    if not found:
        print_fn("Координаты не найдены")
        return
    print_fn(f"Найдено координат: {len(found)}")
    for number, item in enumerate(found, start=1):
        print_fn(f"{number}. {item.raw} -> {item}")


def check_string(input_fn=input, print_fn=print):
    """Пункт 1: проверка одной строки."""
    value = input_fn("Строка: ")
    if is_valid_coordinate(value):
        print_fn(f"Корректно: {parse_coordinate(value)}")
    else:
        print_fn("Некорректная координата")


def run(input_fn=input, print_fn=print):
    """Главный цикл меню. Ошибки не завершают программу."""
    actions = {
        "1": lambda: check_string(input_fn, print_fn),
        "2": lambda: show_found(input_fn("Текст: "), print_fn),
        "3": lambda: show_found(
            read_text_file(input_fn("Путь к файлу: ")), print_fn
        ),
        "4": lambda: show_found(
            fetch_url_text(input_fn("URL: ")), print_fn
        ),
    }
    while True:
        print_fn(MENU)
        try:
            choice = input_fn("Выберите пункт: ").strip()
            if choice == "0":
                print_fn("До свидания!")
                return
            action = actions.get(choice)
            if action is None:
                print_fn("Нет такого пункта меню")
                continue
            action()
        except (SourceError, InvalidCoordinateError) as error:
            print_fn(f"Ошибка: {error}")
        except (EOFError, KeyboardInterrupt):
            print_fn("\nВвод прерван, выход")
            return
        except Exception as error:  # непредвиденная ошибка не роняет меню
            print_fn(f"Непредвиденная ошибка: {error}")


if __name__ == "__main__":
    run()
