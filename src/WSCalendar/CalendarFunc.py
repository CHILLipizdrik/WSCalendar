from .UserClass import User

import json
import calendar
from datetime import datetime, date
from pathlib import Path
from itertools import cycle

# Создание месяца
def create_month(year: int, month: int, schedule: list,
                 start_day: int = 1, offset: int = 0) -> dict:
    """Создаёт структуру месяца.
    schedule — шаблон графика, например [1, 1, 0, 0].
    start_day — с какого дня месяца начинается цикл (дни до него = 0).
    offset — с какой позиции schedule начинать (для продолжения между месяцами).
    """

    if not schedule:
        raise ValueError("schedule не может быть пустым")

    days_in_month = calendar.monthrange(year, month)[1]
    start_day = max(1, min(start_day, days_in_month))

    days = {str(d): 0 for d in range(1, start_day)}

    shifts = cycle(schedule)
    # Прокручиваем цикл до начала позции
    for _ in range(offset):
        next(shifts)

    for day in range(start_day, days_in_month + 1):
        days[str(day)] = next(shifts)

    return {
        "year": year,
        "month": month,
        "days": days
    }

# Добавление месяца в общий календарь
def add_month_to_data(file_path: Path, year: int, month: int,
                      user: User, overwrite: bool = False) -> dict:
    data = load_calendar(file_path)
    key = f"{year:04d}-{month:02d}"
    anchor = user.anchor
    schedule = user.schedule
    start_day = int(anchor.split("-")[2])

    if key in data and not overwrite:
        print(f"Месяц {key} уже есть в календаре.")
        return data

    # В первый месяц задаем график
    if not file_path.exists() or file_path.stat().st_size == 0:
        offset = 0
    else:
        offset = (date(year, month, 1) - date.fromisoformat(anchor)).days % len(schedule)
        start_day = 1

    data[key] = create_month(year, month, schedule, start_day, offset)

    save_calendar(file_path, data)
    print(f"Месяц {key} добавлен в {file_path}")
    return data

# Читает JSON-файл календаря. Если файла нет, он пуст или битый — возвращает {}.
# Если все норм возвращает имеющийся словарь
def load_calendar(file_path: Path) -> dict:
    if not file_path.exists() or file_path.stat().st_size == 0:
        print("Файл отсутствуюет, был создан новый")
        return {}
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print("Файл поврежден и был очищен")
        return {}

# Сохраняет словарь календаря в JSON-файл
def save_calendar(file_path: Path, data: dict) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)