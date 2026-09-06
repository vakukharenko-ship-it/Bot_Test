import datetime
import re
import asyncio
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove
from telegram.ext import ContextTypes, ConversationHandler

from config import VERSION
from utils.logger import write_log
from utils.validators import (
    validate_date, validate_period, create_calendar,
    get_moscow_today, get_current_time_msk
)
from utils.managers import has_access, is_admin, is_manager, get_manager_info
from services.aggregator import aggregate_products
from services.formatter import (
    format_top_products, format_products_summary,
    format_product_combined, get_product_data_for_date,
    get_product_data_for_period
)
from api.seller import fetch_postings
from bot.handlers.charts import generate_product_chart_by_metric
from bot.keyboards import (
    products_reports_keyboard, main_admin_keyboard, main_user_keyboard
)
from bot.states import (
    WAITING_PRODUCT_DATE, WAITING_PRODUCT_PERIOD_TYPE,
    WAITING_PRODUCT_PERIOD_START, WAITING_PRODUCT_PERIOD_END,
    WAITING_PRODUCT_YEAR, WAITING_PRODUCT_MONTH,
    WAITING_PRODUCT_QUARTER, WAITING_PRODUCT_YEAR_SELECT,
    WAITING_PRODUCT_SELECT, WAITING_PRODUCT_METRIC,
    WAITING_PRODUCT_PERIOD_CHOICE, WAITING_PRODUCT_SINGLE_YEAR,
    WAITING_PRODUCT_RANGE_START, WAITING_PRODUCT_RANGE_END
)

# ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------
async def get_top_products_for_select(days=30):
    """Возвращает топ-20 товаров за последние N дней для выбора."""
    now = get_current_time_msk()
    end_date = now.date().isoformat()
    start_date = (now.date() - datetime.timedelta(days=days)).isoformat()
    postings = await fetch_postings(start_date, end_date)
    products = aggregate_products(
        postings,
        date_from=start_date,
        date_to=end_date,
        time_limit=now.time(),
        apply_limit_on_day=end_date
    )
    sorted_items = sorted(products.items(), key=lambda x: x[1]["ordered_sum"], reverse=True)[:20]
    return [(sku, stats) for sku, stats in sorted_items]

# ---------- ОБРАБОТЧИКИ ПОДМЕНЮ ТОВАРОВ ----------
async def handle_products_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

    if text == "📅 Топ товаров за сегодня":
        progress_msg = await update.message.reply_text("⏳ Загружаю данные...")
        report = await format_product_combined()
        await progress_msg.delete()
        await update.message.reply_text(report)
        return

    if text == "📆 Выбрать дату (товары)":
        now = get_moscow_today()
        keyboard = create_calendar(now.year, now.month, "pdate_")
        await update.message.reply_text("Выберите дату (товары):", reply_markup=keyboard)
        return WAITING_PRODUCT_DATE

    if text == "📊 Выбрать период (товары)":
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗓️ По месяцам", callback_data="pmonth")],
            [InlineKeyboardButton("📅 По кварталам", callback_data="pquarter")],
            [InlineKeyboardButton("📆 По годам", callback_data="pyear")],
            [InlineKeyboardButton("📊 Произвольный период", callback_data="pcustom")],
            [InlineKeyboardButton("🔙 Назад", callback_data="pcancel")]
        ])
        await update.message.reply_text("Выберите тип периода для товаров:", reply_markup=keyboard)
        return WAITING_PRODUCT_PERIOD_TYPE

    if text == "📈 Динамика по товару":
        progress_msg = await update.message.reply_text("⏳ Загружаю список товаров за последние 30 дней...")
        top_products = await get_top_products_for_select(days=30)
        await progress_msg.delete()
        if not top_products:
            await update.message.reply_text("❌ Нет данных о товарах за последние 30 дней.")
            return ConversationHandler.END
        context.user_data['product_list'] = top_products
        keyboard = []
        for idx, (sku, stats) in enumerate(top_products, 1):
            name = stats['name']
            short_name = name[:12] + "..." if len(name) > 12 else name
            offer_id = stats.get('offer_id', '')
            if offer_id:
                button_text = f"{offer_id} {sku} {short_name}"
            else:
                button_text = f"{sku} {short_name}"
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"prod_{sku}")])
        keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data="prod_cancel")])
        await update.message.reply_text(
            "Выберите товар, нажав на соответствующую кнопку:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return WAITING_PRODUCT_SELECT

    await update.message.reply_text("Неизвестная команда.")

# ---------- КОМАНДА /top ----------
async def top_products_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not has_access(chat_id):
        await update.message.reply_text("❌ Нет доступа! Обратитесь к администратору.")
        return

    now = get_current_time_msk()
    today_date = now.date()
    month_start = today_date.replace(day=1).isoformat()
    today_str = today_date.isoformat()
    postings = await fetch_postings(month_start, today_str)
    products = aggregate_products(
        postings,
        date_from=month_start,
        date_to=today_str,
        time_limit=now.time(),
        apply_limit_on_day=today_str
    )

    if not products:
        await update.message.reply_text("❌ Нет данных о товарах за текущий месяц.")
        return

    sorted_items = sorted(products.items(), key=lambda x: x[1]["ordered_sum"], reverse=True)[:10]
    lines = ["🏆 <b>ТОП-10 ТОВАРОВ ЗА ТЕКУЩИЙ МЕСЯЦ</b>\n"]
    for i, (sku, stats) in enumerate(sorted_items, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        name = stats.get("name", "Без названия")[:40]
        offer_id = stats.get("offer_id", "")
        revenue = stats["ordered_sum"]
        units = stats["ordered_units"]
        line = f"{medal} <b>{name}</b>"
        if offer_id:
            line += f" (Арт: {offer_id})"
        line += f"\n   Выручка: {revenue:,.0f} ₽, шт: {units}\n"
        lines.append(line)
    await update.message.reply_text("\n".join(lines), parse_mode='HTML')

# ---------- КОМАНДА /version ----------
async def version_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not has_access(chat_id):
        await update.message.reply_text("❌ Нет доступа.")
        return
    await update.message.reply_text(f"🤖 Версия бота: {VERSION}")

# ---------- ОБРАБОТЧИКИ ДИНАМИКИ ПО ТОВАРУ ----------
async def product_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "prod_cancel":
        await query.edit_message_text("Выбор товара отменён.")
        await query.message.reply_text("Выберите действие:", reply_markup=products_reports_keyboard())
        return ConversationHandler.END

    if data.startswith("prod_"):
        sku = data[5:]
        context.user_data['product_sku'] = sku
        product_list = context.user_data.get('product_list', [])
        product_name = "Товар"
        for p_sku, stats in product_list:
            if p_sku == sku:
                product_name = stats['name'][:40]
                break
        context.user_data['product_name'] = product_name

        keyboard = [
            [InlineKeyboardButton("Заказано (₽)", callback_data="metric_ordered_sum")],
            [InlineKeyboardButton("Заказано (шт.)", callback_data="metric_ordered_units")],
            [InlineKeyboardButton("Доставлено (₽)", callback_data="metric_delivered_sum")],
            [InlineKeyboardButton("Доставлено (шт.)", callback_data="metric_delivered_units")],
            [InlineKeyboardButton("Отменено (₽)", callback_data="metric_canceled_sum")],
            [InlineKeyboardButton("Отменено (шт.)", callback_data="metric_canceled_units")],
            [InlineKeyboardButton("Средний чек (₽)", callback_data="metric_avg_check")],
            [InlineKeyboardButton("🔙 Назад", callback_data="metric_cancel")]
        ]
        await query.edit_message_text(
            f"Выбран товар: {product_name} (SKU: {sku})\nТеперь выберите метрику для графика:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return WAITING_PRODUCT_METRIC

async def product_metric_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "metric_cancel":
        await query.edit_message_text("Выбор метрики отменён.")
        await query.message.reply_text("Выберите действие:", reply_markup=products_reports_keyboard())
        return ConversationHandler.END

    if data.startswith("metric_"):
        metric = data[7:]
        context.user_data['product_metric'] = metric

        current_year = get_moscow_today().year
        keyboard = [
            [InlineKeyboardButton("📅 Текущий год", callback_data="period_current")],
            [InlineKeyboardButton("📆 Выбрать год", callback_data="period_select_year")],
            [InlineKeyboardButton("📊 Диапазон лет", callback_data="period_range")],
            [InlineKeyboardButton("🔙 Назад", callback_data="period_cancel")]
        ]
        await query.edit_message_text(
            "Выберите период для построения графика:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return WAITING_PRODUCT_PERIOD_CHOICE

async def product_period_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "period_cancel":
        await query.edit_message_text("Построение графика отменено.")
        await query.message.reply_text("Выберите действие:", reply_markup=products_reports_keyboard())
        return ConversationHandler.END

    if data == "period_current":
        current_year = get_moscow_today().year
        sku = context.user_data.get('product_sku')
        metric = context.user_data.get('product_metric')
        if not sku or not metric:
            await query.edit_message_text("❌ Ошибка: потеряны данные. Начните заново.")
            return ConversationHandler.END
        await query.edit_message_text("⏳ Строю график...")
        chart_buf = await generate_product_chart_by_metric(sku, metric, [current_year])
        if chart_buf:
            context.user_data['product_year'] = current_year
            caption = f"Динамика по товару (SKU: {sku}) за {current_year} год"
            keyboard = [
                [InlineKeyboardButton("Другая метрика", callback_data=f"change_metric_{sku}")],
                [InlineKeyboardButton("Другой год", callback_data=f"change_year_{sku}")],
                [InlineKeyboardButton("🔙 Назад", callback_data="product_chart_back")]
            ]
            await query.message.reply_photo(photo=chart_buf, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
            await query.delete_message()
        else:
            await query.edit_message_text("❌ Нет данных для построения графика.")
        return ConversationHandler.END

    elif data == "period_select_year":
        current_year = get_moscow_today().year
        years = list(range(current_year - 9, current_year + 1))
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"year_{y}")] for y in years]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="period_cancel")])
        await query.edit_message_text("Выберите год:", reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_PRODUCT_SINGLE_YEAR

    elif data == "period_range":
        await query.edit_message_text("Введите начальный год (например, 2020):")
        return WAITING_PRODUCT_RANGE_START

# ---------- ДИАЛОГИ ДИНАМИКИ ПО ТОВАРУ (диапазон) ----------
async def product_range_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Пожалуйста, введите число (год).")
        return WAITING_PRODUCT_RANGE_START
    year = int(text)
    if year < 2000 or year > get_moscow_today().year + 1:
        await update.message.reply_text("❌ Некорректный год. Введите год от 2000 до текущего.")
        return WAITING_PRODUCT_RANGE_START
    context.user_data['product_range_start'] = year
    await update.message.reply_text("Введите конечный год (включительно):")
    return WAITING_PRODUCT_RANGE_END

async def product_range_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit():
        await update.message.reply_text("❌ Пожалуйста, введите число (год).")
        return WAITING_PRODUCT_RANGE_END
    year_end = int(text)
    year_start = context.user_data.get('product_range_start')
    if year_start is None:
        await update.message.reply_text("❌ Ошибка: начальный год не найден. Начните заново.")
        return ConversationHandler.END
    if year_end < year_start:
        await update.message.reply_text("❌ Конечный год должен быть не меньше начального.")
        return WAITING_PRODUCT_RANGE_END
    years = list(range(year_start, year_end + 1))
    if len(years) > 10:
        await update.message.reply_text("⚠️ Слишком много лет (максимум 10). Пожалуйста, выберите меньший диапазон.")
        return ConversationHandler.END

    sku = context.user_data.get('product_sku')
    metric = context.user_data.get('product_metric')
    if not sku or not metric:
        await update.message.reply_text("❌ Ошибка: потеряны данные. Начните заново.")
        return ConversationHandler.END
    progress_msg = await update.message.reply_text("⏳ Строю график...")
    chart_buf = await generate_product_chart_by_metric(sku, metric, years)
    await progress_msg.delete()
    if chart_buf:
        caption = f"Динамика по товару (SKU: {sku}) за {year_start}-{year_end} гг."
        keyboard = [
            [InlineKeyboardButton("Другая метрика", callback_data=f"change_metric_{sku}")],
            [InlineKeyboardButton("Другой год", callback_data=f"change_year_{sku}")],
            [InlineKeyboardButton("🔙 Назад", callback_data="product_chart_back")]
        ]
        await update.message.reply_photo(photo=chart_buf, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await update.message.reply_text("❌ Нет данных для построения графика.")
    await update.message.reply_text("Выберите действие:", reply_markup=products_reports_keyboard())
    context.user_data.pop('product_sku', None)
    context.user_data.pop('product_metric', None)
    context.user_data.pop('product_name', None)
    context.user_data.pop('product_range_start', None)
    return ConversationHandler.END

# ---------- ИНТЕРАКТИВНЫЕ ГРАФИКИ (переключение метрик/годов) ----------
async def product_chart_interactive_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "product_chart_back":
        await query.message.delete()
        await query.message.reply_text("Выберите действие:", reply_markup=products_reports_keyboard())
        return ConversationHandler.END

    if data.startswith("change_metric_"):
        sku = data.split("_")[-1]
        await query.message.delete()
        keyboard = [
            [InlineKeyboardButton("Заказано (₽)", callback_data="metric_ordered_sum")],
            [InlineKeyboardButton("Заказано (шт.)", callback_data="metric_ordered_units")],
            [InlineKeyboardButton("Доставлено (₽)", callback_data="metric_delivered_sum")],
            [InlineKeyboardButton("Доставлено (шт.)", callback_data="metric_delivered_units")],
            [InlineKeyboardButton("Отменено (₽)", callback_data="metric_canceled_sum")],
            [InlineKeyboardButton("Отменено (шт.)", callback_data="metric_canceled_units")],
            [InlineKeyboardButton("Средний чек (₽)", callback_data="metric_avg_check")],
            [InlineKeyboardButton("🔙 Назад", callback_data="product_chart_back")]
        ]
        await query.message.reply_text(f"Выберите метрику для товара SKU:{sku}:", reply_markup=InlineKeyboardMarkup(keyboard))
        return WAITING_PRODUCT_METRIC

    if data.startswith("change_year_"):
        sku = data.split("_")[-1]
        await query.message.delete()
        current_year = get_moscow_today().year
        years = list(range(current_year - 9, current_year + 1))
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"year_{y}")] for y in years]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="product_chart_back")])
        await query.message.reply_text(f"Выберите год для товара SKU:{sku}:", reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_PRODUCT_SINGLE_YEAR

    if data.startswith("year_"):
        year = int(data.split("_")[-1])
        sku = context.user_data.get('product_sku')
        metric = context.user_data.get('product_metric')
        if not sku or not metric:
            await query.message.reply_text("❌ Ошибка: потеряны данные.")
            return ConversationHandler.END
        await query.message.delete()
        progress_msg = await query.message.reply_text("⏳ Строю график...")
        chart_buf = await generate_product_chart_by_metric(sku, metric, [year])
        await progress_msg.delete()
        if chart_buf:
            context.user_data['product_year'] = year
            caption = f"Динамика по товару (SKU: {sku}) за {year} год"
            keyboard = [
                [InlineKeyboardButton("Другая метрика", callback_data=f"change_metric_{sku}")],
                [InlineKeyboardButton("Другой год", callback_data=f"change_year_{sku}")],
                [InlineKeyboardButton("🔙 Назад", callback_data="product_chart_back")]
            ]
            await query.message.reply_photo(photo=chart_buf, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await query.message.reply_text("❌ Нет данных для построения графика.")
        return ConversationHandler.END

# ---------- ОБРАБОТЧИКИ INLINE CALLBACK ДЛЯ ТОВАРОВ ----------
async def handle_product_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор даты для товаров (pdate_)."""
    query = update.callback_query
    data = query.data
    if data == "pdate_cancel":
        await query.edit_message_text("Выбор даты отменён.")
        await query.message.reply_text("Выберите действие:", reply_markup=products_reports_keyboard())
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
            return WAITING_PRODUCT_DATE
        if action == "prev_month":
            month -= 1
            if month == 0: month = 12; year -= 1
        else:
            month += 1
            if month == 13: month = 1; year += 1
        keyboard = create_calendar(year, month, "pdate_")
        await query.edit_message_reply_markup(reply_markup=keyboard)
        return WAITING_PRODUCT_DATE

    date_str = data[6:]  # убираем "pdate_"
    if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
        valid, result = validate_date(date_str)
        if not valid:
            await query.edit_message_text(result)
            return WAITING_PRODUCT_DATE
        progress_msg = await query.message.reply_text("⏳ Загружаю данные...")
        products = await get_product_data_for_date(date_str)
        await progress_msg.delete()
        msg = format_top_products(products, f"Товары за {date_str}", limit=20)
        summary = format_products_summary(products)
        await query.edit_message_text(msg + "\n\n" + summary)
        await query.message.reply_text("Выберите действие:", reply_markup=products_reports_keyboard())
        return ConversationHandler.END
    else:
        await query.edit_message_text("❌ Ошибка формата даты.")
        return WAITING_PRODUCT_DATE

async def handle_product_period_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор периода для товаров (pmonth, pquarter, pyear, pcustom)."""
    query = update.callback_query
    data = query.data
    if data == "pmonth":
        current_year = get_moscow_today().year
        years = list(range(current_year - 9, current_year + 1))
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"pyear_month_{y}")] for y in years]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="pcancel")])
        await query.edit_message_text("Выберите год:", reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_PRODUCT_YEAR
    if data == "pquarter":
        current_year = get_moscow_today().year
        years = list(range(current_year - 9, current_year + 1))
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"pyear_quarter_{y}")] for y in years]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="pcancel")])
        await query.edit_message_text("Выберите год:", reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_PRODUCT_YEAR
    if data == "pyear":
        current_year = get_moscow_today().year
        years = list(range(current_year - 9, current_year + 1))
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"pyear_only_{y}")] for y in years]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="pcancel")])
        await query.edit_message_text("Выберите год:", reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_PRODUCT_YEAR_SELECT
    if data == "pcustom":
        now = get_moscow_today()
        keyboard = create_calendar(now.year, now.month, "pstart_")
        await query.edit_message_text("Выберите начальную дату:", reply_markup=keyboard)
        return WAITING_PRODUCT_PERIOD_START
    if data == "pcancel":
        await query.edit_message_text("Выбор периода отменён.")
        await query.message.reply_text("Выберите действие:", reply_markup=products_reports_keyboard())
        return ConversationHandler.END

    if data.startswith("pyear_month_"):
        year = int(data.split("_")[-1])
        context.user_data['p_year'] = year
        months = ["Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
                  "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"]
        buttons = [[InlineKeyboardButton(name, callback_data=f"pmonth_{i}_{year}")] for i, name in enumerate(months, 1)]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="pcancel")])
        await query.edit_message_text(f"Выберите месяц {year}:", reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_PRODUCT_MONTH
    if data.startswith("pyear_quarter_"):
        year = int(data.split("_")[-1])
        context.user_data['p_year'] = year
        quarters = ["1 квартал (янв-мар)", "2 квартал (апр-июн)", "3 квартал (июл-сен)", "4 квартал (окт-дек)"]
        buttons = [[InlineKeyboardButton(name, callback_data=f"pquarter_{i}_{year}")] for i, name in enumerate(quarters, 1)]
        buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="pcancel")])
        await query.edit_message_text(f"Выберите квартал {year}:", reply_markup=InlineKeyboardMarkup(buttons))
        return WAITING_PRODUCT_QUARTER

    if data.startswith("pyear_only_"):
        year = int(data.split("_")[-1])
        first_day = datetime.date(year, 1, 1)
        last_day = datetime.date(year, 12, 31)
        progress_msg = await query.message.reply_text("⏳ Загружаю данные...")
        products = await get_product_data_for_period(first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d"))
        await progress_msg.delete()
        msg = format_top_products(products, f"Товары за {year} год", limit=20)
        summary = format_products_summary(products)
        await query.edit_message_text(msg + "\n\n" + summary)
        await query.message.reply_text("Выберите действие:", reply_markup=products_reports_keyboard())
        return ConversationHandler.END

    if data.startswith("pmonth_"):
        parts = data.split("_")
        month_num, year = int(parts[1]), int(parts[2])
        first_day = datetime.date(year, month_num, 1)
        if month_num == 12:
            last_day = datetime.date(year, 12, 31)
        else:
            last_day = datetime.date(year, month_num+1, 1) - datetime.timedelta(days=1)
        date_from, date_to = first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")
        progress_msg = await query.message.reply_text("⏳ Загружаю данные...")
        products = await get_product_data_for_period(date_from, date_to)
        await progress_msg.delete()
        msg = format_top_products(products, f"Товары за {first_day.strftime('%B %Y')}", limit=20)
        summary = format_products_summary(products)
        await query.edit_message_text(msg + "\n\n" + summary)
        await query.message.reply_text("Выберите действие:", reply_markup=products_reports_keyboard())
        return ConversationHandler.END

    if data.startswith("pquarter_"):
        parts = data.split("_")
        q, year = int(parts[1]), int(parts[2])
        start_month = (q-1)*3 + 1
        end_month = q*3
        first_day = datetime.date(year, start_month, 1)
        if end_month == 12:
            last_day = datetime.date(year, 12, 31)
        else:
            last_day = datetime.date(year, end_month+1, 1) - datetime.timedelta(days=1)
        date_from, date_to = first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")
        progress_msg = await query.message.reply_text("⏳ Загружаю данные...")
        products = await get_product_data_for_period(date_from, date_to)
        await progress_msg.delete()
        msg = format_top_products(products, f"Товары за {q} квартал {year}", limit=20)
        summary = format_products_summary(products)
        await query.edit_message_text(msg + "\n\n" + summary)
        await query.message.reply_text("Выберите действие:", reply_markup=products_reports_keyboard())
        return ConversationHandler.END

    if data.startswith("pstart_"):
        if data == "pstart_cancel":
            await query.edit_message_text("Выбор периода отменён.")
            await query.message.reply_text("Выберите действие:", reply_markup=products_reports_keyboard())
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
                return WAITING_PRODUCT_PERIOD_START
            if action == "prev_month":
                month -= 1
                if month == 0: month = 12; year -= 1
            else:
                month += 1
                if month == 13: month = 1; year += 1
            keyboard = create_calendar(year, month, "pstart_")
            await query.edit_message_reply_markup(reply_markup=keyboard)
            return WAITING_PRODUCT_PERIOD_START
        date_str = data[7:]  # убираем "pstart_"
        if re.match(r"\d{4}-\d{2}-\d{2}", date_str):
            valid, result = validate_date(date_str)
            if not valid:
                await query.edit_message_text(result)
                return WAITING_PRODUCT_PERIOD_START
            context.user_data['p_start_date'] = date_str
            now = get_moscow_today()
            keyboard = create_calendar(now.year, now.month, "pend_")
            await query.edit_message_text(f"Начало: {date_str}\nТеперь выберите конечную дату:", reply_markup=keyboard)
            return WAITING_PRODUCT_PERIOD_END
        else:
            await query.edit_message_text("❌ Ошибка формата даты.")
            return WAITING_PRODUCT_PERIOD_START

    if data.startswith("pend_"):
        if data == "pend_cancel":
            await query.edit_message_text("Выбор периода отменён.")
            await query.message.reply_text("Выберите действие:", reply_markup=products_reports_keyboard())
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
                return WAITING_PRODUCT_PERIOD_END
            if action == "prev_month":
                month -= 1
                if month == 0: month = 12; year -= 1
            else:
                month += 1
                if month == 13: month = 1; year += 1
            keyboard = create_calendar(year, month, "pend_")
            await query.edit_message_reply_markup(reply_markup=keyboard)
            return WAITING_PRODUCT_PERIOD_END
        end_date_str = data[5:]  # убираем "pend_"
        if re.match(r"\d{4}-\d{2}-\d{2}", end_date_str):
            valid, result = validate_date(end_date_str)
            if not valid:
                await query.edit_message_text(result)
                return WAITING_PRODUCT_PERIOD_END
            start_date = context.user_data.get('p_start_date')
            if not start_date:
                await query.edit_message_text("❌ Ошибка: начальная дата не найдена. Попробуйте снова.")
                return ConversationHandler.END
            valid_period, msg = validate_period(start_date, end_date_str)
            if not valid_period:
                await query.edit_message_text(msg)
                now = get_moscow_today()
                keyboard = create_calendar(now.year, now.month, "pstart_")
                await query.message.reply_text("Выберите начальную дату заново:", reply_markup=keyboard)
                return WAITING_PRODUCT_PERIOD_START
            progress_msg = await query.message.reply_text("⏳ Загружаю данные...")
            products = await get_product_data_for_period(start_date, end_date_str)
            await progress_msg.delete()
            msg = format_top_products(products, f"Товары за период {start_date} – {end_date_str}", limit=20)
            summary = format_products_summary(products)
            await query.edit_message_text(msg + "\n\n" + summary)
            await query.message.reply_text("Выберите действие:", reply_markup=products_reports_keyboard())
            context.user_data.pop('p_start_date', None)
            return ConversationHandler.END
        else:
            await query.edit_message_text("❌ Ошибка формата даты.")
            return WAITING_PRODUCT_PERIOD_END

    # Если ничего не подошло – игнорируем
    await query.edit_message_text("❌ Неизвестная команда.")
    return ConversationHandler.END
