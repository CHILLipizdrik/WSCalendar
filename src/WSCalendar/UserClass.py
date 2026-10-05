import json
from pathlib import Path


class User:
    def __init__(self, name: str, anchor: str, schedule: list | None = None):
        if schedule is None:
            schedule = []
        if not schedule:
            raise ValueError("График не может быть пустым")
        self.name = name
        self.anchor = anchor
        self.schedule = schedule

    def __repr__(self):
        return f"User({self.name!r}, {self.anchor}, {self.schedule})"

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

    # ---------- JSON ----------

    def to_dict(self) -> dict:
        """Возвращает данные пользователя в виде словаря."""
        return {
            "name": self.name,
            "anchor": self.anchor,
            "schedule": self.schedule,
        }

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
        )

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