from datetime import date
import calendar

import toga
from toga.style import Pack
from toga.style.pack import COLUMN, ROW, CENTER

from .UserClass import User
from . import CalendarFunc

# ---------- Русские названия ----------
RU_MONTHS_GEN = [
    "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря",
]
RU_MONTHS_NOM = [
    "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]
RU_WEEKDAYS_FULL = [
    "Понедельник", "Вторник", "Среда", "Четверг",
    "Пятница", "Суббота", "Воскресенье",
]
WEEKDAY_SHORT = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВСК"]

# Цвета ячеек: ключ — тип смены из JSON
SHIFT_BG = {
    0: "white",     # выходной
    1: "green",     # дневная смена
    2: "red",       # ночная смена
}
SHIFT_FG = {
    0: "black",
    1: "white",
    2: "white",
}
# Цвет рамки вокруг сегодняшнего дня
TODAY_BORDER = "#2196F3"

class RegistrationView(toga.Box):
    """Экран регистрации. Не окно, а содержимое главного окна."""

    def __init__(self, on_success):
        super().__init__(style=Pack(direction=COLUMN, margin=20))
        self.on_success = on_success

        # --- Поля ввода ---
        self.name_input = toga.TextInput(placeholder="Иван Иванов")
        self.date_input = toga.DateInput(value=date.today())
        self.schedule_input = toga.TextInput(placeholder="1,1,0,0")
        self.error_label = toga.Label("", style=Pack(color="red"))

        button = toga.Button(
            "Зарегистрировать и продолжить",
            on_press=self.handle_register,
            style=Pack(margin=10),
        )

        # --- Сборка интерфейса ---
        self.add(
            toga.Label("Имя:", style=Pack(margin_top=10)),
            self.name_input,
            toga.Label("Дата выхода на работу:", style=Pack(margin_top=10)),
            self.date_input,
            toga.Label(
                "График (0 — выходной, 1 — дневная, 2 — ночная):",
                style=Pack(margin_top=10),
            ),
            self.schedule_input,
            self.error_label,
            button,
        )

    def handle_register(self, widget):
        # 1. Имя
        name = self.name_input.value.strip()
        if not name:
            self.error_label.text = "Введите имя"
            return

        # 2. Дата
        start_date = self.date_input.value
        if start_date is None:
            self.error_label.text = "Выберите дату выхода на работу"
            return

        # 3. График
        try:
            schedule = User.parse_schedule(self.schedule_input.value)
        except ValueError as e:
            self.error_label.text = str(e)
            return

        # Всё ок
        self.error_label.text = ""
        self.on_success({
            "name": name,
            "start_date": start_date.isoformat(),
            "schedule": schedule,
        })

    """@staticmethod
    def parse_schedule(raw: str) -> list:
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

        return schedule"""


class ProfileView(toga.Box):
    """Страница профиля с inline-редактированием полей."""

    # (имя_атрибута, отображаемое название)
    FIELDS = [
        ("name", "Имя"),
        ("anchor", "Дата начала работы"),
        ("schedule", "График"),
    ]

    def __init__(self, user: User, on_save, on_back, on_reset=None):
        super().__init__(style=Pack(direction=COLUMN, margin=20))
        self.user = user
        self.on_save = on_save       # callback(field_name) — вызывается после успешного изменения
        self.on_back = on_back       # callback() — возврат к календарю
        self.on_reset = on_reset     # - сброс профиля

        self.add(
            toga.Label(
                "Профиль",
                style=Pack(font_size=20, margin_bottom=15, text_align=CENTER),
            )
        )

        # Контейнеры для строк — чтобы можно было перерисовывать по одной
        self.row_containers: dict[str, toga.Box] = {}
        for field, label in self.FIELDS:
            container = toga.Box(style=Pack(direction=ROW, margin=5))
            self.row_containers[field] = container
            self._render_view_row(field, label, container)
            self.add(container)

        # Общая метка ошибок
        self.error_label = toga.Label("", style=Pack(color="red", margin_top=10))
        self.add(self.error_label)

        # --- Кнопки внизу ---
        buttons_row = toga.Box(style=Pack(direction=ROW, margin_top=15))

        buttons_row.add(
            toga.Button(
                "Назад к календарю",
                on_press=lambda w: self.on_back(),
                style=Pack(flex=1, margin=5),
            )
        )

        if on_reset is not None:
            buttons_row.add(
                toga.Button(
                    "Сбросить профиль",
                    on_press=on_reset,
                    style=Pack(flex=1, margin=5),
                )
            )

        self.add(buttons_row)

    # ---------- Строка в режиме просмотра ----------
    def _render_view_row(self, field: str, label: str, container: toga.Box):
        container.clear()
        value = getattr(self.user, field)
        if field == "schedule":
            value = ",".join(str(x) for x in value)

        container.add(
            toga.Label(f"{label}: {value}", style=Pack(flex=1)),
            toga.Button(
                "Изменить",
                on_press=lambda w: self._render_edit_row(field, label, container),
                style=Pack(width=90),
            ),
        )

    # ---------- Строка в режиме редактирования ----------
    def _render_edit_row(self, field: str, label: str, container: toga.Box):
        container.clear()
        current = getattr(self.user, field)

        if field == "anchor":
            input_widget = toga.DateInput(
                value=date.fromisoformat(current),
                style=Pack(flex=1),
            )
            get_value = lambda: input_widget.value.isoformat()
        elif field == "schedule":
            input_widget = toga.TextInput(
                value=",".join(str(x) for x in current),
                style=Pack(flex=1),
            )
            get_value = lambda: input_widget.value.strip()
        else:
            input_widget = toga.TextInput(
                value=str(current),
                style=Pack(flex=1),
            )
            get_value = lambda: input_widget.value.strip()

        def save(w):
            try:
                self._apply_change(field, get_value())
            except ValueError as e:
                self.error_label.text = str(e)
                return
            self.error_label.text = ""
            self._render_view_row(field, label, container)

        def cancel(w):
            self.error_label.text = ""
            self._render_view_row(field, label, container)

        container.add(
            input_widget,
            toga.Button("✓", on_press=save, style=Pack(width=40)),
            toga.Button("✗", on_press=cancel, style=Pack(width=40)),
        )

    # ---------- Применение изменений ----------
    def _apply_change(self, field: str, value):
        if field == "name":
            if not value:
                raise ValueError("Имя не может быть пустым")
            self.user.name = value

        elif field == "anchor":
            try:
                date.fromisoformat(value)
            except ValueError:
                raise ValueError("Дата должна быть в формате ГГГГ-ММ-ДД")
            self.user.anchor = value

        elif field == "schedule":
            parsed = User.parse_schedule(value)
            self.user.schedule = parsed

        # Сообщаем приложению, что поле изменилось
        self.on_save(field)


class CalendarView(toga.Box):
    """Полноценный календарь с навигацией по месяцам и подсветкой сегодня."""

    def __init__(self, user: User, calendar_file, on_open_profile=None):
        super().__init__(style=Pack(direction=COLUMN, margin=10))
        self.user = user
        self.calendar_file = calendar_file
        self.on_open_profile = on_open_profile

        # Данные календаря
        self.data = CalendarFunc.load_calendar(calendar_file)
        self.today = date.today()

        # Текущее отображаемое состояние
        self.view_year = self.today.year
        self.view_month = self.today.month

        # --- 1. Шапка: сегодняшняя дата ---
        self.add(self._make_today_header())

        # --- 2. Навигация по месяцам ---
        self.month_label = toga.Label(
            "",
            style=Pack(flex=1, text_align=CENTER, font_size=16, font_weight="bold"),
        )
        self.add(self._make_nav_row())

        # --- 3. Дни недели ---
        self.add(self._make_weekday_header())

        # --- 4. Сетка месяца (контейнер, который перестраивается) ---
        self.grid_container = toga.Box(style=Pack(direction=COLUMN))
        self.add(self.grid_container)

        # --- 5. Кнопка перехода в профиль ---
        if on_open_profile is not None:
            self.add(
                toga.Button(
                    "Профиль",
                    on_press=lambda w: on_open_profile(),
                    style=Pack(margin_top=15),
                )
            )

        # Первичная отрисовка сетки
        self._refresh_grid()

    # ---------- Шапка ----------
    def _make_today_header(self) -> toga.Label:
        weekday = RU_WEEKDAYS_FULL[self.today.weekday()]
        month = RU_MONTHS_GEN[self.today.month - 1]
        text = f"{self.today.day} {month} {self.today.year}, {weekday}"
        return toga.Label(
            text,
            style=Pack(font_size=18, margin_bottom=10, text_align=CENTER),
        )

    # ---------- Навигация ----------
    def _make_nav_row(self) -> toga.Box:
        prev_btn = toga.Button(
            "◀",
            on_press=self._prev_month,
            style=Pack(width=50),
        )
        next_btn = toga.Button(
            "▶",
            on_press=self._next_month,
            style=Pack(width=50),
        )

        row = toga.Box(style=Pack(direction=ROW, margin_bottom=5))
        row.add(prev_btn, self.month_label, next_btn)
        return row

    def _prev_month(self, widget):
        if self.view_month == 1:
            self.view_month = 12
            self.view_year -= 1
        else:
            self.view_month -= 1
        self._refresh_grid()

    def _next_month(self, widget):
        if self.view_month == 12:
            self.view_month = 1
            self.view_year += 1
        else:
            self.view_month += 1
        self._refresh_grid()

    # ---------- Дни недели ----------
    def _make_weekday_header(self) -> toga.Box:
        row = toga.Box(style=Pack(direction=ROW, margin_bottom=2))
        for name in WEEKDAY_SHORT:
            row.add(
                toga.Label(
                    name,
                    style=Pack(
                        flex=1,
                        text_align=CENTER,
                        font_weight="bold",
                        margin=1,
                    ),
                )
            )
        return row

    # ---------- Обновление сетки ----------
    def _refresh_grid(self):
        key = f"{self.view_year:04d}-{self.view_month:02d}"

        # Если месяца нет в данных — генерируем его через add_month_to_data
        if key not in self.data:
            CalendarFunc.add_month_to_data(
                self.calendar_file,
                year=self.view_year,
                month=self.view_month,
                user=self.user,
            )
            self.data = CalendarFunc.load_calendar(self.calendar_file)

        # Обновляем подпись
        month_name = RU_MONTHS_NOM[self.view_month - 1]
        self.month_label.text = f"{month_name} {self.view_year}"

        # Пересобираем сетку
        self.grid_container.clear()
        self.grid_container.add(self._make_month_grid(self.view_year, self.view_month))

    # ---------- Сетка месяца ----------
    def _make_month_grid(self, year: int, month: int) -> toga.Box:
        key = f"{year:04d}-{month:02d}"
        month_data = self.data.get(key, {}).get("days", {})

        days_in_month = calendar.monthrange(year, month)[1]
        first_weekday = date(year, month, 1).weekday()  # 0 = ПНД

        grid = toga.Box(style=Pack(direction=COLUMN, background_color="#CCCCCC"))

        total_cells = first_weekday + days_in_month
        rows_needed = (total_cells + 6) // 7

        day = 1
        for row_idx in range(rows_needed):
            row = toga.Box(style=Pack(direction=ROW))
            for col_idx in range(7):
                cell_pos = row_idx * 7 + col_idx

                if cell_pos < first_weekday or day > days_in_month:
                    # Пустая ячейка
                    row.add(toga.Box(style=Pack(flex=1, height=40, margin=1)))
                else:
                    shift = month_data.get(str(day), 0)
                    is_today = (
                        year == self.today.year
                        and month == self.today.month
                        and day == self.today.day
                    )
                    row.add(self._make_day_cell(day, shift, is_today))
                    day += 1
            grid.add(row)

        return grid

    # ---------- Ячейка дня ----------
    def _make_day_cell(self, day_num: int, shift: int, is_today: bool) -> toga.Box:
        bg = SHIFT_BG.get(shift, "white")
        fg = SHIFT_FG.get(shift, "black")

        if is_today:
            # Внешний синий бокс + внутренний с margin=2 создают эффект рамки
            outer = toga.Box(
                style=Pack(flex=1, background_color=TODAY_BORDER, margin=1)
            )
            inner = toga.Box(
                style=Pack(
                    flex=1,
                    height=36,
                    background_color=bg,
                    direction=COLUMN,
                    alignment=CENTER,
                    margin=2,
                )
            )
            inner.add(toga.Label(str(day_num), style=Pack(color=fg, font_weight="bold")))
            outer.add(inner)
            return outer
        else:
            cell = toga.Box(
                style=Pack(
                    flex=1,
                    height=40,
                    background_color=bg,
                    direction=COLUMN,
                    alignment=CENTER,
                    margin=1,
                )
            )
            cell.add(toga.Label(str(day_num), style=Pack(color=fg, font_weight="bold")))
            return cell


class WSCalendarApp(toga.App):
    """Основное приложение."""

    def startup(self):
        # Пути к файлам данных
        self.users_file = self.paths.data / "users.json"
        self.calendar_file = self.paths.data / "calendar.json"

        # Создаём главное окно сразу — Toga требует его наличия
        self.main_window = toga.MainWindow(title="Work Shift Calendar")
        self.main_window.show()

        # Загружаем пользователя
        self.user = User.load_from_json(self.users_file)

        if self.user is None:
            self.show_registration()
        else:
            self.show_calendar()

    def show_registration(self):
        """Показывает экран регистрации как содержимое главного окна."""
        self.main_window.content = RegistrationView(
            on_success=self.on_registration_success
        )

    def on_registration_success(self, data: dict):
        """Создаёт пользователя и переключает на календарь."""
        self.user = User(
            name=data["name"],
            anchor=data["start_date"],
            schedule=data["schedule"],
        )
        self.user.save_to_json(self.users_file)

        # Генерируем первый месяц
        today = date.today()
        CalendarFunc.add_month_to_data(
            self.calendar_file,
            year=today.year,
            month=today.month,
            user=self.user,
        )

        self.show_calendar()

    def show_calendar(self):
        """Показывает экран календаря."""
        self.main_window.content = CalendarView(
            user=self.user,
            calendar_file=self.calendar_file,
            on_open_profile=self.show_profile,
        )

    def on_user_field_changed(self, field: str):
        """Сохраняет изменения профиля. При смене anchor или schedule — пересоздаёт календарь."""
        self.user.save_to_json(self.users_file)

        if field in ("anchor", "schedule"):
            # Полная перегенерация календаря: старые месяцы недействительны
            if self.calendar_file.exists():
                self.calendar_file.unlink()

            today = date.today()
            CalendarFunc.add_month_to_data(
                self.calendar_file,
                year=today.year,
                month=today.month,
                user=self.user,
            )

    def show_profile(self):
        """Открывает страницу профиля."""
        self.main_window.content = ProfileView(
            user=self.user,
            on_save=self.on_user_field_changed,
            on_back=self.show_calendar,
            on_reset=self.reset_profile,
        )

    async def reset_profile(self, widget):
        """Сбрасывает профиль после подтверждения."""
        confirmed = await self.main_window.dialog(
            toga.ConfirmDialog(
                title="Сбросить профиль?",
                message="Все данные пользователя и календарь будут удалены. Продолжить?",
            )
        )
        if not confirmed:
            return

        User.delete_user_file(self.users_file)
        if self.calendar_file.exists():
            self.calendar_file.unlink()

        self.user = None
        self.show_registration()


def main():
    return WSCalendarApp("WSCalendar", "org.ia.wscalendar")


