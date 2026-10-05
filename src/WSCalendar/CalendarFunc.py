from .UserClass import User

import json
import calendar
from datetime import date
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

def create_empty_month(year: int, month: int) -> dict:
    """Создаёт структуру месяца, где все дни = 0 (до начала работы)."""
    days_in_month = calendar.monthrange(year, month)[1]
    return {
        "year": year,
        "month": month,
        "days": {str(d): 0 for d in range(1, days_in_month + 1)},
    }

# Добавление месяца в общий календарь
def add_month_to_data(file_path: Path, year: int, month: int,
                      user: User, overwrite: bool = False) -> dict:
    data = load_calendar(file_path)
    key = f"{year:04d}-{month:02d}"

    if key in data and not overwrite:
        print(f"Месяц {key} уже есть в календаре.")
        return data

    if not user.schedule:
        raise ValueError("У пользователя пустой schedule — невозможно построить календарь")

    anchor_date = date.fromisoformat(user.anchor)
    schedule = user.schedule

    # Сравниваем месяц с anchor по (год, месяц)
    requested = (year, month)
    anchor_month = (anchor_date.year, anchor_date.month)

    if requested < anchor_month:
        # Месяц ДО начала работы — весь месяц нули
        data[key] = create_empty_month(year, month)
        print(f"Месяц {key} до начала работы — заполнен нулями.")

    elif requested == anchor_month:
        # Месяц старта — заполняем с дня anchor, цикл начинается с schedule[0]
        data[key] = create_month(
            year, month, schedule,
            start_day=anchor_date.day,
            offset=0,
        )
        print(f"Месяц {key} — месяц начала работы.")

    else:
        # Любой последующий месяц — полный, позиция от anchor
        offset = (date(year, month, 1) - anchor_date).days % len(schedule)
        data[key] = create_month(
            year, month, schedule,
            start_day=1,
            offset=offset,
        )
        print(f"Месяц {key} добавлен (offset={offset}).")

    save_calendar(file_path, data)
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