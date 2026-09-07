import datetime
import re
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler
from config import VERSION, ADMIN_CHAT_ID
from utils.logger import write_log
from utils.validators import (
    validate_date, validate_period, create_calendar,
    get_moscow_today, get_current_time_msk
)
from utils.managers import (
    load_managers, is_admin, is_manager, has_access,
    get_manager_info, add_manager, remove_manager
)
from services.formatter import (
    format_combined_metrics_with_deltas,
    format_single_metrics,
    format_period_comparison_metrics
)
from api.seller import fetch_postings, fetch_finance_transactions
from api.performance import fetch_advertising_expense
from services.aggregator import aggregate_postings, aggregate_finance_expenses
from bot.keyboards import (
    main_admin_keyboard, main_user_keyboard,
    sales_reports_keyboard, admin_keyboard, products_reports_keyboard
)
from bot.states import (
    WAITING_DATE_SINGLE, WAITING_PERIOD_TYPE,
    WAITING_PERIOD_START, WAITING_PERIOD_END,
    WAITING_PERIOD_YEAR, WAITING_PERIOD_MONTH,
    WAITING_PERIOD_QUARTER, WAITING_YEAR_SELECT,
    WAITING_DYNAMICS_SELECT, WAITING_DYNAMICS_RANGE_START,
    WAITING_DYNAMICS_RANGE_END,
    # Состояния для товаров не импортируем, они не нужны здесь
)

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
def get_greeting(name):
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))
    now = datetime.datetime.now(moscow_tz)
    hour = now.hour
    if 5 <= hour < 12:
        part = "Доброе утро"
    elif 12 <= hour < 18:
        part = "Добрый день"
    elif 18 <= hour < 24:
        part = "Добрый вечер"
    else:
        part = "Доброй ночи"
    if name:
        return f"{part}, {name}!"
    else:
        return f"{part}, уважаемый пользователь!"

# ---------- ОБРАБОТЧИКИ КОМАНД ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    if is_admin(chat_id):
        name = user.first_name if user.first_name else ""
        greeting = get_greeting(name)
        await update.message.reply_text(
            f"{greeting}\n\n🤖 Версия бота: {VERSION}",
            reply_markup=main_admin_keyboard()
        )
    elif is_manager(chat_id):
        manager = get_manager_info(chat_id)
        name = manager.get("first_name") if manager and manager.get("first_name") else user.first_name or ""
        greeting = get_greeting(name)
        await update.message.reply_text(
            f"{greeting}\n\n🤖 Версия бота: {VERSION}",
            reply_markup=main_user_keyboard()
        )
    else:
        await update.message.reply_text("❌ Нет доступа! Обратитесь к администратору.", reply_markup=ReplyKeyboardRemove())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if is_admin(chat_id):
        help_text = (
            "📖 *Справка для администратора*\n\n"
            "🔹 *Основные функции*\n"
            "• 📊 Отчёт по продажам – актуальная сводка по продажам за сегодня и текущий месяц.\n"
            "• 📦 Отчёт по товарам – топ товаров по выручке за сегодня и текущий месяц.\n"
            "• 📆 Выбрать дату – просмотр данных за конкретный день (продажи или товары).\n"
            "• 📊 Выбрать период – гибкий выбор отчётного периода (месяц, квартал, год, произвольный).\n"
            "• 📈 Динамика продаж – график доставленных заказов по месяцам за выбранный год (или несколько лет).\n"
            "• 📈 Динамика по товару – график продаж конкретного товара по месяцам.\n"
            "• ⚙️ Администрирование – управление доступом менеджеров.\n\n"
            "🔹 *Управление менеджерами*\n"
            "• ➕ Добавить менеджера – введите Telegram ID или @username пользователя, затем номер телефона (или '-' для пропуска).\n"
            "• ➖ Удалить менеджера – введите Telegram ID пользователя.\n"
            "• 📋 Список менеджеров – просмотр всех добавленных пользователей (ID, username, имя, телефон).\n\n"
            "🔹 *Автоматические отчёты*\n"
            "• В 10:00 МСК – отчёт с блоками «Вчера», «Сегодня» и «Текущий месяц».\n"
            "• В 22:00 МСК – отчёт с блоками «Сегодня» и «Текущий месяц».\n\n"
            "🔹 *Метрики*\n"
            "• 🛒 Заказано – сумма и количество всех заказов.\n"
            "• 📦 Доставлено – сумма и количество доставленных заказов.\n"
            "• ❌ Отменено – сумма и количество отменённых заказов.\n"
            "• 📢 Реклама – расходы на рекламу, ДРР (общий) и ДРР (по доставленным).\n"
            "• 💰 Расходы (финансовые) – детальная разбивка: комиссии, логистика, эквайринг, кросс-докинг, хранение, возвраты и др.\n\n"
            "🔹 *Сравнение динамики*\n"
            "• Для «Сегодня» – сравнение с аналогичным временем вчера.\n"
            "• Для «Текущий месяц» – сравнение с аналогичным периодом предыдущего месяца (с учётом времени).\n\n"
            "🔹 *Часовой пояс*\n"
            "• Все расчёты ведутся по московскому времени (МСК, UTC+3).\n\n"
            f"🤖 Версия бота: {VERSION}"
        )
    else:
        help_text = (
            "📖 *Справка для менеджера*\n\n"
            "🔹 *Основные функции*\n"
            "• 📊 Отчёт по продажам – актуальная сводка по продажам за сегодня и текущий месяц.\n"
            "• 📦 Отчёт по товарам – топ товаров по выручке за сегодня и текущий месяц.\n"
            "• 📆 Выбрать дату – просмотр данных за конкретный день (продажи или товары).\n"
            "• 📊 Выбрать период – гибкий выбор отчётного периода (месяц, квартал, год, произвольный).\n"
            "• 📈 Динамика продаж – график доставленных заказов по месяцам за выбранный год (или несколько лет).\n"
            "• 📈 Динамика по товару – график продаж конкретного товара по месяцам.\n\n"
            "🔹 *Автоматические отчёты*\n"
            "• В 10:00 МСК – отчёт с блоками «Вчера», «Сегодня» и «Текущий месяц».\n"
            "• В 22:00 МСК – отчёт с блоками «Сегодня» и «Текущий месяц».\n\n"
            "🔹 *Метрики*\n"
            "• 🛒 Заказано – сумма и количество всех заказов.\n"
            "• 📦 Доставлено – сумма и количество доставленных заказов.\n"
            "• ❌ Отменено – сумма и количество отменённых заказов.\n"
            "• 📢 Реклама – расходы на рекламу, ДРР (общий) и ДРР (по доставленным).\n"
            "• 💰 Расходы (финансовые) – детальная разбивка: комиссии, логистика, эквайринг, кросс-докинг, хранение, возвраты и др.\n\n"
            "🔹 *Сравнение динамики*\n"
            "• Для «Сегодня» – сравнение с аналогичным временем вчера.\n"
            "• Для «Текущий месяц» – сравнение с аналогичным периодом предыдущего месяца (с учётом времени).\n\n"
            "🔹 *Часовой пояс*\n"
            "• Все расчёты ведутся по московскому времени (МСК, UTC+3).\n\n"
            f"🤖 Версия бота: {VERSION}"
        )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id

    if text == "📊 Отчёт по продажам":
        if not has_access(chat_id):
            await update.message.reply_text("❌ Нет доступа! Обратитесь к администратору.")
            return
        await update.message.reply_text("Выберите тип отчёта по продажам:", reply_markup=sales_reports_keyboard())
        return

    if text == "📦 Отчёт по товарам":
        if not has_access(chat_id):
            await update.message.reply_text("❌ Нет доступа! Обратитесь к администратору.")
            return
        # Товарный раздел обрабатывается в products.py, но здесь мы просто пересылаем
        # Для этого нужен импорт из products, но мы не можем его сделать из-за циклической зависимости.
        # Поэтому оставим как есть: пользователь сам перейдёт в раздел товаров через клавиатуру.
        # Но handle_main_menu вызывается только для главного меню.
        await update.message.reply_text("Выберите тип отчёта по товарам:", reply_markup=products_reports_keyboard())
        return

    if text == "⚙️ Администрирование":
        if not is_admin(chat_id):
            await update.message.reply_text("⛔ Только для администратора.")
            return
        await update.message.reply_text("Управление менеджерами:", reply_markup=admin_keyboard())
        return

    if text == "📖 Справка":
        await help_command(update, context)
        return

    await update.message.reply_text("Используйте кнопки меню.")

# ---------- ОБРАБОТЧИКИ ПОДМЕНЮ ПРОДАЖ ----------
async def handle_sales_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    chat_id = update.effective_chat.id

    if text == "🔙 Назад":
        if is_admin(chat_id):
            await update.message.reply_text(
                f"Главное меню\n\n🤖 Версия бота: {VERSION}",
                reply_markup=main_admin_keyboard()
            )
        else:
            await update.message.reply_text(
                f"Главное меню\n\n🤖 Версия бота: {VERSION}",
                reply_markup=main_user_keyboard()
            )
        return

    if not has_access(chat_id):
        await update.message.reply_text("❌ Нет доступа! Обратитесь к администратору.")
        return

    if text == "📅 Продажи за сегодня":
        progress_msg = await update.message.reply_text("⏳ Загружаю данные за сегодня...")
        report = await format_combined_metrics_with_deltas(include_yesterday=False, progress_callback=None)
        await progress_msg.delete()
        await update.message.reply_text(report, parse_mode="Markdown")
        return

    if text == "📆 Выбрать дату":
        now = get_moscow_today()
        keyboard = create_calendar(now.year, now.month, "date_")
        await update.message.reply_text("Выберите дату (продажи):", reply_markup=keyboard)
        return WAITING_DATE_SINGLE

    if text == "📊 Выбрать период":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗓️ По месяцам", callback_data="period_month")],
            [InlineKeyboardButton("📅 По кварталам", callback_data="period_quarter")],
            [InlineKeyboardButton("📆 По годам", callback_data="period_year")],
            [InlineKeyboardButton("📊 Произвольный период", callback_data="period_custom")],
            [InlineKeyboardButton("🔙 Назад", callback_data="period_cancel")]
        ])
        await update.message.reply_text("Выберите тип периода:", reply_markup=keyboard)
        return WAITING_PERIOD_TYPE

    if text == "📈 Динамика продаж":
        current_year = get_moscow_today().year
        years = list(range(current_year - 9, current_year + 1))
        buttons = [
            [InlineKeyboardButton("📅 Текущий год", callback_data="dynamics_current")],
            [InlineKeyboardButton("📆 Выбрать год", callback_data="dynamics_select")],
            [InlineKeyboardButton("📊 Диапазон лет", callback_data="dynamics_range")],
            [InlineKeyboardButton("🔙 Назад", callback_data="dynamics_cancel")]
        ]
        await update.message.reply_text(
            "Выберите вариант для построения графика:\n"
            "• Текущий год – сразу покажет динамику за текущий год.\n"
            "• Выбрать год – покажет список годов (последние 10).\n"
            "• Диапазон лет – введите начальный и конечный год.",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return WAITING_DYNAMICS_SELECT

    await update.message.reply_text("Неизвестная команда.")

# ---------- INLINE CALLBACK (только раздел продаж) ----------
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    chat_id = update.effective_chat.id

    if not has_access(chat_id):
        await query.edit_message_text("❌ Нет доступа! Обратитесь к администратору.")
        return ConversationHandler.END

    # -------------------- ВЫБОР ДАТЫ (продажи) --------------------
    if data.startswith("date_"):
        if data == "date_cancel":
            await query.edit_message_text("Выбор даты отменён.")
            await query.message.reply_text("Выберите действие:", reply_markup=sales_reports_keyboard())
            return ConversationHandler.END

        if "prev_month" in data or "next_month" in data:
            match = re.search(r'prev_month_(\d+)_(\d+)|next_month_(\d+)_(\d+)', data)
            if match:
                if match.group(1) and match.group(2):
                    year = int(match.group(1)); month = int(match.group(2)); action = "prev_month"
                else:
                    year = int(match.group(3)); month = int(match.group(4)); action = "next_month"
            else:
                await query.edit_message_text("❌ Ошибка формата навигации.")
                return WAITING_DATE_SINGLE

            if action == "prev_month":
                month -= 1
                if month == 0: month = 12; year -= 1
            else:
                month += 1
                if month == 13: month = 1; year += 1
            keyboard = create_calendar(year, month, "date_")
            await query.edit_message_reply_markup(reply_markup=keyboard)
            return WAITING_DATE_SINGLE

        date_str = data[5:]  # убираем "date_"
        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            valid, result = validate_date(date_str)
            if not valid:
                await query.edit_message_text(result)
                return WAITING_DATE_SINGLE
            progress_msg = await query.message.reply_text("⏳ Загружаю данные...")
            metrics = await get_metrics_for_date(date_str)  # функция должна быть определена в этом же модуле или импортирована
            await progress_msg.delete()
            msg = format_single_metrics(metrics, f"Продажи за {date_str}")
            await query.edit_message_text(msg, parse_mode="Markdown")
            await query.message.reply_text("Выберите действие:", reply_markup=sales_reports_keyboard())
            return ConversationHandler.END
        else:
            await query.edit_message_text("❌ Ошибка формата даты.")
            return WAITING_DATE_SINGLE

    # -------------------- ВЫБОР ПЕРИОДА (продажи) --------------------
    if data == "period_month":
        current_year = get_moscow_today().year
        years = list(range(current_year - 9, current_year + 1))
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"period_year_month_{y}")] for y in years]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="period_cancel")])
        await query.edit_message_text("Выберите год:", reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_PERIOD_YEAR

    if data == "period_quarter":
        current_year = get_moscow_today().year
        years = list(range(current_year - 9, current_year + 1))
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"period_year_quarter_{y}")] for y in years]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="period_cancel")])
        await query.edit_message_text("Выберите год:", reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_PERIOD_YEAR

    if data == "period_year":
        current_year = get_moscow_today().year
        years = list(range(current_year - 9, current_year + 1))
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"period_year_only_{y}")] for y in years]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="period_cancel")])
        await query.edit_message_text("Выберите год:", reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_YEAR_SELECT

    if data == "period_custom":
        now = get_moscow_today()
        keyboard = create_calendar(now.year, now.month, "start_")
        await query.edit_message_text("Выберите начальную дату:", reply_markup=keyboard)
        return WAITING_PERIOD_START

    if data == "period_cancel":
        await query.edit_message_text("Выбор периода отменён.")
        await query.message.reply_text("Выберите действие:", reply_markup=sales_reports_keyboard())
        return ConversationHandler.END

    # Обработка выбора года для месяцев
    if data.startswith("period_year_month_"):
        year = int(data.split("_")[-1])
        context.user_data['period_year'] = year
        months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        buttons = [[InlineKeyboardButton(name, callback_data=f"period_month_{i}_{year}")] for i, name in enumerate(months, 1)]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="period_cancel")])
        await query.edit_message_text(f"Выберите месяц {year}:", reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_PERIOD_MONTH

    # Обработка выбора года для кварталов
    if data.startswith("period_year_quarter_"):
        year = int(data.split("_")[-1])
        context.user_data['period_year'] = year
        quarters = ["1 квартал (янв-мар)", "2 квартал (апр-июн)", "3 квартал (июл-сен)", "4 квартал (окт-дек)"]
        buttons = [[InlineKeyboardButton(name, callback_data=f"period_quarter_{i}_{year}")] for i, name in enumerate(quarters, 1)]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="period_cancel")])
        await query.edit_message_text(f"Выберите квартал {year}:", reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_PERIOD_QUARTER

    # Отчёт за год
    if data.startswith("period_year_only_"):
        year = int(data.split("_")[-1])
        first_day = datetime.date(year, 1, 1)
        last_day = datetime.date(year, 12, 31)
        progress_msg = await query.message.reply_text("⏳ Загружаю данные...")
        metrics_current = await get_metrics_for_period(first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d"))
        prev_year = year - 1
        prev_first_day = datetime.date(prev_year, 1, 1)
        prev_last_day = datetime.date(prev_year, 12, 31)
        metrics_prev = await get_metrics_for_period(prev_first_day.strftime("%Y-%m-%d"), prev_last_day.strftime("%Y-%m-%d"))
        await progress_msg.delete()
        period_name = str(year)
        report = format_period_comparison_metrics(metrics_current, metrics_prev, period_name)
        await query.edit_message_text(report, parse_mode="Markdown")
        await query.message.reply_text("Выберите действие:", reply_markup=sales_reports_keyboard())
        return ConversationHandler.END

    # Отчёт за месяц
    if data.startswith("period_month_"):
        parts = data.split("_")
        month_num, year = int(parts[2]), int(parts[3])
        first_day = datetime.date(year, month_num, 1)
        if month_num == 12:
            last_day = datetime.date(year, 12, 31)
        else:
            last_day = datetime.date(year, month_num+1, 1) - datetime.timedelta(days=1)
        date_from, date_to = first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")
        progress_msg = await query.message.reply_text("⏳ Загружаю данные...")
        metrics_current = await get_metrics_for_period(date_from, date_to)
        if month_num == 1:
            prev_month_num = 12
            prev_year = year - 1
        else:
            prev_month_num = month_num - 1
            prev_year = year
        prev_first_day = datetime.date(prev_year, prev_month_num, 1)
        if prev_month_num == 12:
            prev_last_day = datetime.date(prev_year, 12, 31)
        else:
            prev_last_day = datetime.date(prev_year, prev_month_num+1, 1) - datetime.timedelta(days=1)
        metrics_prev = await get_metrics_for_period(prev_first_day.strftime("%Y-%m-%d"), prev_last_day.strftime("%Y-%m-%d"))
        await progress_msg.delete()
        month_names = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                       "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        period_name = f"{month_names[month_num-1]} {year}"
        report = format_period_comparison_metrics(metrics_current, metrics_prev, period_name)
        await query.edit_message_text(report, parse_mode="Markdown")
        await query.message.reply_text("Выберите действие:", reply_markup=sales_reports_keyboard())
        return ConversationHandler.END

    # Отчёт за квартал
    if data.startswith("period_quarter_"):
        parts = data.split("_")
        q, year = int(parts[2]), int(parts[3])
        start_month = (q-1)*3 + 1
        end_month = q*3
        first_day = datetime.date(year, start_month, 1)
        if end_month == 12:
            last_day = datetime.date(year, 12, 31)
        else:
            last_day = datetime.date(year, end_month+1, 1) - datetime.timedelta(days=1)
        date_from, date_to = first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")
        progress_msg = await query.message.reply_text("⏳ Загружаю данные...")
        metrics_current = await get_metrics_for_period(date_from, date_to)
        if q == 1:
            prev_q = 4
            prev_year = year - 1
            prev_start_month = (prev_q-1)*3 + 1
            prev_end_month = prev_q*3
        else:
            prev_q = q - 1
            prev_year = year
            prev_start_month = (prev_q-1)*3 + 1
            prev_end_month = prev_q*3
        prev_first_day = datetime.date(prev_year, prev_start_month, 1)
        if prev_end_month == 12:
            prev_last_day = datetime.date(prev_year, 12, 31)
        else:
            prev_last_day = datetime.date(prev_year, prev_end_month+1, 1) - datetime.timedelta(days=1)
        metrics_prev = await get_metrics_for_period(prev_first_day.strftime("%Y-%m-%d"), prev_last_day.strftime("%Y-%m-%d"))
        await progress_msg.delete()
        period_name = f"{q} квартал {year}"
        report = format_period_comparison_metrics(metrics_current, metrics_prev, period_name)
        await query.edit_message_text(report, parse_mode="Markdown")
        await query.message.reply_text("Выберите действие:", reply_markup=sales_reports_keyboard())
        return ConversationHandler.END

    # Произвольный период: начало
    if data.startswith("start_"):
        if data == "start_cancel":
            await query.edit_message_text("Выбор периода отменён.")
            await query.message.reply_text("Выберите действие:", reply_markup=sales_reports_keyboard())
            return ConversationHandler.END

        if "prev_month" in data or "next_month" in data:
            match = re.search(r'prev_month_(\d+)_(\d+)|next_month_(\d+)_(\d+)', data)
            if match:
                if match.group(1) and match.group(2):
                    year = int(match.group(1)); month = int(match.group(2)); action = "prev_month"
                else:
                    year = int(match.group(3)); month = int(match.group(4)); action = "next_month"
            else:
                await query.edit_message_text("❌ Ошибка формата навигации.")
                return WAITING_PERIOD_START

            if action == "prev_month":
                month -= 1
                if month == 0: month = 12; year -= 1
            else:
                month += 1
                if month == 13: month = 1; year += 1
            keyboard = create_calendar(year, month, "start_")
            await query.edit_message_reply_markup(reply_markup=keyboard)
            return WAITING_PERIOD_START

        date_str = data[6:]  # убираем "start_"
        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            valid, result = validate_date(date_str)
            if not valid:
                await query.edit_message_text(result)
                return WAITING_PERIOD_START
            context.user_data['period_start_date'] = date_str
            now = get_moscow_today()
            keyboard = create_calendar(now.year, now.month, "end_")
            await query.edit_message_text(f"Начало: {date_str}\nТеперь выберите конечную дату:", reply_markup=keyboard)
            return WAITING_PERIOD_END
        else:
            await query.edit_message_text("❌ Ошибка формата даты.")
            return WAITING_PERIOD_START

    # Произвольный период: конец
    if data.startswith("end_"):
        if data == "end_cancel":
            await query.edit_message_text("Выбор периода отменён.")
            await query.message.reply_text("Выберите действие:", reply_markup=sales_reports_keyboard())
            return ConversationHandler.END

        if "prev_month" in data or "next_month" in data:
            match = re.search(r'prev_month_(\d+)_(\d+)|next_month_(\d+)_(\d+)', data)
            if match:
                if match.group(1) and match.group(2):
                    year = int(match.group(1)); month = int(match.group(2)); action = "prev_month"
                else:
                    year = int(match.group(3)); month = int(match.group(4)); action = "next_month"
            else:
                await query.edit_message_text("❌ Ошибка формата навигации.")
                return WAITING_PERIOD_END

            if action == "prev_month":
                month -= 1
                if month == 0: month = 12; year -= 1
            else:
                month += 1
                if month == 13: month = 1; year += 1
            keyboard = create_calendar(year, month, "end_")
            await query.edit_message_reply_markup(reply_markup=keyboard)
            return WAITING_PERIOD_END

        end_date_str = data[4:]  # убираем "end_"
        if re.match(r"\d{4}-\d{2}-\d{2}", end_date_str):
            valid, result = validate_date(end_date_str)
            if not valid:
                await query.edit_message_text(result)
                return WAITING_PERIOD_END
            start_date = context.user_data.get('period_start_date')
            if not start_date:
                await query.edit_message_text("❌ Ошибка: начальная дата не найдена. Попробуйте снова.")
                return ConversationHandler.END
            valid_period, msg = validate_period(start_date, end_date_str)
            if not valid_period:
                await query.edit_message_text(msg)
                now = get_moscow_today()
                keyboard = create_calendar(now.year, now.month, "start_")
                await query.message.reply_text("Выберите начальную дату заново:", reply_markup=keyboard)
                return WAITING_PERIOD_START
            progress_msg = await query.message.reply_text("⏳ Загружаю данные...")
            metrics = await get_metrics_for_period(start_date, end_date_str)
            await progress_msg.delete()
            msg = format_single_metrics(metrics, f"Продажи за период {start_date} – {end_date_str}")
            await query.edit_message_text(msg, parse_mode="Markdown")
            await query.message.reply_text("Выберите действие:", reply_markup=sales_reports_keyboard())
            context.user_data.pop('period_start_date', None)
            return ConversationHandler.END
        else:
            await query.edit_message_text("❌ Ошибка формата даты.")
            return WAITING_PERIOD_END

    # -------------------- ДИНАМИКА ПРОДАЖ (график) --------------------
    if data == "dynamics_current":
        await query.edit_message_text("⏳ Загружаю данные...")
        current_year = get_moscow_today().year
        # Импортируем функцию генерации графика из charts
        from bot.handlers.charts import generate_sales_chart
        chart_buf = await generate_sales_chart([current_year])
        if chart_buf:
            await query.message.reply_photo(photo=chart_buf, caption=f"Динамика доставленных заказов за {current_year} год")
        else:
            await query.message.reply_text("❌ Не удалось построить график.")
        await query.edit_message_text("Выберите действие:", reply_markup=sales_reports_keyboard())
        return ConversationHandler.END

    if data == "dynamics_select":
        current_year = get_moscow_today().year
        years = list(range(current_year - 9, current_year + 1))
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"dynamics_year_{y}")] for y in years]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="dynamics_cancel")])
        await query.edit_message_text("Выберите год для отображения графика:", reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_DYNAMICS_SELECT

    if data == "dynamics_range":
        await query.edit_message_text("Введите начальный год (например, 2020):")
        return WAITING_DYNAMICS_RANGE_START

    if data == "dynamics_cancel":
        await query.edit_message_text("Построение графика отменено.")
        await query.message.reply_text("Выберите действие:", reply_markup=sales_reports_keyboard())
        return ConversationHandler.END

    if data.startswith("dynamics_year_"):
        year = int(data.split("_")[-1])
        await query.edit_message_text("⏳ Загружаю данные...")
        from bot.handlers.charts import generate_sales_chart
        chart_buf = await generate_sales_chart([year])
        if chart_buf:
            await query.message.reply_photo(photo=chart_buf, caption=f"Динамика доставленных заказов за {year} год")
        else:
            await query.message.reply_text("❌ Не удалось построить график.")
        await query.edit_message_text("Выберите действие:", reply_markup=sales_reports_keyboard())
        return ConversationHandler.END

    # Если ничего не подошло – игнорируем (это могут быть callback'и для товаров)
    await query.edit_message_text("❌ Неизвестная команда.")
    return ConversationHandler.END

# ---------- ДИАЛОГ ДИНАМИКИ ПРОДАЖ (диапазон) ----------
async def dynamics_range_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Пожалуйста, введите число (год).")
        return WAITING_DYNAMICS_RANGE_START
    year = int(text)
    if year < 2000 or year > get_moscow_today().year + 1:
        await update.message.reply_text("❌ Некорректный год. Введите год от 2000 до текущего.")
        return WAITING_DYNAMICS_RANGE_START
    context.user_data['dynamics_range_start'] = year
    await update.message.reply_text("Введите конечный год (включительно):")
    return WAITING_DYNAMICS_RANGE_END

async def dynamics_range_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Пожалуйста, введите число (год).")
        return WAITING_DYNAMICS_RANGE_END
    year_end = int(text)
    year_start = context.user_data.get('dynamics_range_start')
    if year_start is None:
        await update.message.reply_text("❌ Ошибка: начальный год не найден. Начните заново.")
        return ConversationHandler.END
    if year_end < year_start:
        await update.message.reply_text("❌ Конечный год должен быть не меньше начального.")
        return WAITING_DYNAMICS_RANGE_END
    years = list(range(year_start, year_end + 1))
    if len(years) > 10:
        await update.message.reply_text("⚠️ Слишком много лет (максимум 10). Пожалуйста, выберите меньший диапазон.")
        return ConversationHandler.END
    progress_msg = await update.message.reply_text("⏳ Загружаю данные...")
    from bot.handlers.charts import generate_sales_chart
    chart_buf = await generate_sales_chart(years)
    await progress_msg.delete()
    if chart_buf:
        caption = f"Динамика доставленных заказов за {year_start}-{year_end} гг."
        await update.message.reply_photo(photo=chart_buf, caption=caption)
    else:
        await update.message.reply_text("❌ Не удалось построить график.")
    await update.message.reply_text("Выберите действие:", reply_markup=sales_reports_keyboard())
    context.user_data.pop('dynamics_range_start', None)
    return ConversationHandler.END

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ ПОЛУЧЕНИЯ МЕТРИК (используются выше) ----------
# Эти функции перенесены из старого bot.py (раздел "АСИНХРОННЫЕ ФУНКЦИИ ДЛЯ ПОЛУЧЕНИЯ МЕТРИК")
# Они нужны для обработчиков продаж

async def get_metrics_for_date(date_str, progress_callback=None):
    today = get_moscow_today()
    start = (today - datetime.timedelta(days=183)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    postings_task = fetch_postings(start, end, progress_callback)
    ad_task = fetch_advertising_expense(date_str, date_str, progress_callback)
    fin_task = fetch_finance_transactions(date_str, date_str, progress_callback)
    postings, ad_expense, transactions = await asyncio.gather(postings_task, ad_task, fin_task)
    if progress_callback:
        await progress_callback("Агрегируем данные...", 80)
    agg = aggregate_postings(postings, date_from=date_str, date_to=date_str)
    metrics = agg.get(date_str, {})
    metrics["ad_expense"] = ad_expense if ad_expense is not None else 0.0
    revenue = metrics.get("ordered_sum", 0)
    if revenue > 0 and ad_expense is not None:
        metrics["drr"] = (ad_expense / revenue) * 100
    else:
        metrics["drr"] = None
    delivered_revenue = metrics.get("delivered_sum", 0)
    if delivered_revenue > 0 and ad_expense is not None:
        metrics["effective_drr"] = (ad_expense / delivered_revenue) * 100
    else:
        metrics["effective_drr"] = None

    expenses = aggregate_finance_expenses(transactions)
    metrics["expenses"] = expenses
    if progress_callback:
        await progress_callback("Готово", 100)
    return metrics

async def get_metrics_for_period(date_from, date_to, progress_callback=None):
    # Используем параллельную загрузку из aggregator
    from services.aggregator import fetch_metrics_for_period_parallel
    return await fetch_metrics_for_period_parallel(date_from, date_to, progress_callback)
