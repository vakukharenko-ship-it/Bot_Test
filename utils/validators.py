import datetime
import calendar
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import MOSCOW_TZ

def get_moscow_today():
    """Возвращает текущую дату по московскому времени."""
    return datetime.datetime.now(MOSCOW_TZ).date()

def get_current_time_msk():
    """Возвращает текущее время по московскому времени."""
    return datetime.datetime.now(MOSCOW_TZ)

def validate_date(date_str):
    """
    Проверяет корректность даты в формате YYYY-MM-DD.
    Возвращает (True, date) или (False, сообщение_об_ошибке).
    """
    try:
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        today = get_moscow_today()
        if date > today:
            return False, "❌ Дата не может быть в будущем"
        two_years_ago = today - datetime.timedelta(days=730)
        if date < two_years_ago:
            return False, "❌ Дата слишком старая (более 2 лет назад)"
        return True, date
    except ValueError:
        return False, "❌ Неверный формат даты. Используйте YYYY-MM-DD"

def validate_period(date_from, date_to):
    """
    Проверяет корректность периода: даты должны быть валидными, from <= to, не более года.
    Возвращает (True, (from_date, to_date)) или (False, сообщение_об_ошибке).
    """
    valid_from, from_date = validate_date(date_from)
    if not valid_from:
        return False, from_date
    valid_to, to_date = validate_date(date_to)
    if not valid_to:
        return False, to_date
    if from_date > to_date:
        return False, "❌ Начальная дата не может быть позже конечной"
    delta = (to_date - from_date).days
    if delta > 365:
        return False, "❌ Период не может быть больше года"
    return True, (from_date, to_date)

def create_calendar(year, month, callback_prefix):
    """
    Создаёт InlineKeyboardMarkup для календаря.
    callback_prefix используется для идентификации callback-данных.
    Возвращает InlineKeyboardMarkup.
    """
    month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                   "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
    keyboard = []
    # Заголовок с месяцем и годом
    header = f"{month_names[month-1]} {year}"
    keyboard.append([InlineKeyboardButton(header, callback_data="ignore")])
    # Дни недели
    week_days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    row = [InlineKeyboardButton(day, callback_data="ignore") for day in week_days]
    keyboard.append(row)

    first_day, num_days = calendar.monthrange(year, month)
    row = []
    # Пустые ячейки до первого дня
    for _ in range(first_day):
        row.append(InlineKeyboardButton(" ", callback_data="ignore"))
    for day in range(1, num_days + 1):
        row.append(InlineKeyboardButton(str(day), callback_data=f"{callback_prefix}{year}-{month:02d}-{day:02d}"))
        if len(row) == 7:
            keyboard.append(row)
            row = []
    if row:
        while len(row) < 7:
            row.append(InlineKeyboardButton(" ", callback_data="ignore"))
        keyboard.append(row)

    # Навигация
    nav_row = [
        InlineKeyboardButton("◀️", callback_data=f"{callback_prefix}prev_month_{year}_{month}"),
        InlineKeyboardButton(" ", callback_data="ignore"),
        InlineKeyboardButton("▶️", callback_data=f"{callback_prefix}next_month_{year}_{month}")
    ]
    keyboard.append(nav_row)
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=f"{callback_prefix}cancel")])
    return InlineKeyboardMarkup(keyboard)
