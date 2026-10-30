# Прокат велосипедов (ЛР № 1)

ООП в Python, собственные исключения, хранение данных в JSON и XML.

## Запуск
    python main.py      # консольное меню
    python demo.py      # сценарий проверки (нормальная работа + ошибки)

Требуется Python 3.10+, внешних библиотек нет.

## Структура
- `bike_rental/models.py` - классы предметной области
- `bike_rental/exceptions.py` - собственные исключения
- `bike_rental/service.py` - Repository (CRUD) и RentalService
- `bike_rental/storage.py` - JsonStorage и XmlStorage
- `bike_rental/app.py` - консольный интерфейс
- `data/` - примеры файлов data.json и data.xml
- `docs/` - диаграммы классов (Graphviz + PNG)
