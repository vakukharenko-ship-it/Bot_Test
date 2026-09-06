from telegram import ReplyKeyboardMarkup, KeyboardButton

def main_admin_keyboard():
    buttons = [
        [KeyboardButton("📊 Отчёт по продажам")],
        [KeyboardButton("📦 Отчёт по товарам")],
        [KeyboardButton("⚙️ Администрирование")],
        [KeyboardButton("📖 Справка")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def main_user_keyboard():
    buttons = [
        [KeyboardButton("📊 Отчёт по продажам")],
        [KeyboardButton("📦 Отчёт по товарам")],
        [KeyboardButton("📖 Справка")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def sales_reports_keyboard():
    buttons = [
        [KeyboardButton("📅 Продажи за сегодня")],
        [KeyboardButton("📆 Выбрать дату")],
        [KeyboardButton("📊 Выбрать период")],
        [KeyboardButton("📈 Динамика продаж")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def products_reports_keyboard():
    buttons = [
        [KeyboardButton("📅 Топ товаров за сегодня")],
        [KeyboardButton("📆 Выбрать дату (товары)")],
        [KeyboardButton("📊 Выбрать период (товары)")],
        [KeyboardButton("📈 Динамика по товару")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

def admin_keyboard():
    buttons = [
        [KeyboardButton("➕ Добавить менеджера"), KeyboardButton("➖ Удалить менеджера")],
        [KeyboardButton("📋 Список менеджеров")],
        [KeyboardButton("🔙 Назад")]
    ]
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)
