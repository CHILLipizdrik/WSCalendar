import json
import re
from pathlib import Path


class User:
    # Регулярка для формата "ЧЧ:ММ - ЧЧ:ММ" (часы могут быть 1 или 2 цифры)
    TIME_PATTERN = re.compile(r"^(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})$")

    def __init__(self, name: str, anchor: str, schedule: list | None = None,
                 day_hours: str = "-", night_hours: str = "-"):
        if schedule is None:
            schedule = []
        if not schedule:
            raise ValueError("График не может быть пустым")
        self.name = name
        self.anchor = anchor
        self.schedule = schedule
        self.day_hours = day_hours
        self.night_hours = night_hours

    def __repr__(self):
        return (f"User({self.name!r}, {self.anchor}, {self.schedule}, "
                f"day={self.day_hours!r}, night={self.night_hours!r})")

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "anchor": self.anchor,
            "schedule": self.schedule,
            "day_hours": self.day_hours,
            "night_hours": self.night_hours,
        }

    # ---------- JSON ----------

    def save_to_json(self, file_path: Path) -> None:
        """Сохраняет пользователя в JSON по указанному пути."""
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=4)

    @classmethod
    def load_from_json(cls, file_path: Path) -> User | None:
        """Загружает пользователя из JSON. Возвращает None, если файла нет."""
        file_path = Path(file_path)
        if not file_path.exists() or file_path.stat().st_size == 0:
            return None
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            return None
        return cls(
            name=data["name"],
            anchor=data["anchor"],
            schedule=data["schedule"],
            day_hours=data["day_hours"],
            night_hours=data["night_hours"],
        )

    # ---------- utilities ----------

    @classmethod
    def exists(cls, file_path: Path) -> bool:
        """Проверяет, есть ли сохранённый пользователь."""
        file_path = Path(file_path)
        return file_path.exists() and file_path.stat().st_size > 0

    @classmethod
    def delete_user_file(cls, file_path: Path) -> bool:
        """Удаляет файл с данными пользователя."""
        file_path = Path(file_path)
        if file_path.exists():
            file_path.unlink()
            return True
        return False

    @staticmethod
    def parse_schedule(raw: str) -> list:
        """Разбирает строку '1,1,0,0' или '1100' в список [1,1,0,0]."""
        raw = raw.strip().replace(" ", "")
        if not raw:
            raise ValueError("Введите график")

        parts = raw.split(",") if "," in raw else list(raw)

        try:
            schedule = [int(p) for p in parts if p != ""]
        except ValueError:
            raise ValueError("График должен состоять только из цифр 0, 1, 2")

        if any(v not in (0, 1, 2) for v in schedule):
            raise ValueError("Каждое значение графика — 0, 1 или 2")

        if not schedule:
            raise ValueError("График не может быть пустым")

        return schedule

    @classmethod
    def validate_hours(cls, value: str) -> str:
        """Проверяет формат 'ЧЧ:ММ - ЧЧ:ММ'. Возвращает нормализованную строку.
        '-' или пустая строка означает отсутствие смены."""
        value = (value or "").strip()
        if value in ("", "-"):
            return "-"

        match = cls.TIME_PATTERN.match(value)
        if not match:
            raise ValueError("Формат часов: ЧЧ:ММ - ЧЧ:ММ или '-'")

        h1, m1, h2, m2 = map(int, match.groups())
        if not (0 <= h1 <= 23 and 0 <= m1 <= 59
                and 0 <= h2 <= 23 and 0 <= m2 <= 59):
            raise ValueError("Некорректное время (часы 00–23, минуты 00–59)")

        return f"{h1:02d}:{m1:02d} - {h2:02d}:{m2:02d}"