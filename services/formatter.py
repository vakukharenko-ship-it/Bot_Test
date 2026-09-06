import datetime
import asyncio
from config import MOSCOW_TZ
from utils.validators import get_current_time_msk, get_moscow_today
from api.seller import fetch_postings, fetch_finance_transactions
from api.performance import fetch_advertising_expense
from services.aggregator import aggregate_postings, aggregate_finance_expenses, aggregate_products
from utils.logger import write_log

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ФОРМАТИРОВАНИЯ ====================
def fmt_num(val):
    return f"{val:,.2f}".replace(",", " ") if val else "0.00"

def fmt_int(val):
    return str(val) if val else "0"

def fmt_pct(val):
    if val is None:
        return "∞"
    if val > 0:
        return f"+{val:.1f}%"
    elif val < 0:
        return f"{val:.1f}%"
    else:
        return f"{val:.1f}%"

def calc_delta(current, previous):
    if previous == 0:
        return None
    try:
        return ((current - previous) / abs(previous)) * 100
    except:
        return None

def indicator(value_current, value_prev, better_is_higher):
    """
    Возвращает 🟢 если улучшение, 🔴 если ухудшение, иначе пустую строку.
    """
    if value_prev is None or value_current is None:
        return ""
    if value_prev == 0:
        return "🟢" if value_current > 0 else ""
    delta = calc_delta(value_current, value_prev)
    if delta is None:
        return ""
    if better_is_higher:
        return "🟢" if delta > 0 else ("🔴" if delta < 0 else "")
    else:
        return "🟢" if delta < 0 else ("🔴" if delta > 0 else "")

# ==================== ФОРМАТИРОВАНИЕ РАСХОДОВ ====================
def format_expense_block(expenses_by_type, title):
    if not expenses_by_type:
        return f"🔹 *{title}*\nНет данных о расходах.\n"

    total = sum(expenses_by_type.values())
    lines = [f"🔹 *{title}*", f"  *Итого расходов:* {total:,.2f} ₽"]

    name_map = {
        "Комиссия Ozon": "Комиссия",
        "Оплата эквайринга": "Эквайринг",
        "Доставка покупателю": "Доставка покупателю",
        "Доставка и обработка возврата, отмены, невыкупа": "Доставка/возвраты",
        "Кросс-докинг": "Кросс-докинг",
        "Страхование товара от массовых повреждений": "Страхование",
        "Обеспечение материалами для упаковки товара": "Обеспечение упаковкой",
        "Упаковка товара партнёрами": "Упаковка",
        "Подписка Управление отзывами": "Подписка",
        "Оплата за клик": "Оплата за клик",
        "Получение возврата, отмены, невыкупа от покупателя": "Получение возвратов",
        "MarketplaceServiceItemDirectFlowLogistic": "Логистика прямая",
        "MarketplaceServiceItemRedistributionLastMileCourier": "Логистика последняя миля",
        "MarketplaceServiceItemReturnFlowLogistic": "Логистика возврат",
        "MarketplaceServiceItemDeliveryToHandoverPlaceOzon": "Доставка до ПВЗ",
        "MarketplaceRedistributionOfAcquiringOperation": "Эквайринг",
        "MarketplaceServiceItemRedistributionReturnsPVZ": "Обработка возвратов (ПВЗ)",
        "MarketplaceServiceItemPackageRedistribution": "Переупаковка",
        "MarketplaceServiceItemPackageMaterialsProvision": "Обеспечение упаковкой",
        "MarketplaceServiceItemProductReviewsManagementSubscription": "Подписка",
        "MarketplaceServiceItemRedistributionLastMilePVZ": "Логистика последняя миля (ПВЗ)",
        "MarketplaceServiceItemDirectFlowLogisticFBS": "Логистика прямая (FBS)",
        "MarketplaceServiceItemReturnFlowLogisticFBS": "Логистика возврат (FBS)",
        "ItemAgentServiceStarsMembership": "Звёздные товары",
        "MarketplaceServiceSellerReturnsCargoAssortment": "Обработка возвратов партнёрами",
        "MarketplaceServiceItemTemporaryStorageRedistribution": "Временное размещение",
        "MarketplaceServiceProductMovementFromWarehouse": "Вывоз до ПВЗ",
        "MarketplaceServiceItemDisposalDetailed": "Утилизация",
        "Звёздные товары": "Звёздные товары",
        "Временное размещение товара партнерами": "Временное размещение",
        "Обработка товара в составе грузоместа: Поштучная приёмка": "Поштучная приёмка",
        "Обработка товара в составе грузоместа на FBO": "Поштучная приёмка",
        "Подготовка товара к вывозу: Брак": "Подготовка к вывозу (брак)",
        "Вывоз товара со склада силами Ozon: Доставка до ПВЗ": "Вывоз до ПВЗ",
        "Вывоз товара со Склада силами Ozon: Доставка до ПВЗ": "Вывоз до ПВЗ",
        "Бронирование места и персонала для поставки с неполным составом в составе грузоместа": "Бронирование места",
        "Услуга по бронированию места и персонала для поставки с неполным составом в составе ГМ": "Бронирование места",
        "Обработка опознанных излишков в составе грузоместа": "Обработка излишков",
        "Услуга по обработке опознанных излишков в составе ГМ": "Обработка излишков",
        "Утилизация товара: Пролились/просыпались из-за упаковки": "Утилизация",
        "Потеря по вине Ozon на складе": "Потеря (склад)",
        "Потеря по вине Ozon в логистике": "Потеря (логистика)",
        "Вознаграждение за продажу": "Вознаграждение",
        "Возврат вознаграждения": "Возврат вознаграждения",
        "Программы партнёров": "Программы партнёров",
        "Баллы за скидки": "Баллы за скидки",
        "Выручка": "Выручка",
        "Возврат выручки": "Возврат выручки",
    }

    sorted_items = sorted(expenses_by_type.items(), key=lambda x: x[1], reverse=True)

    for category, amount in sorted_items:
        if category in name_map:
            short_name = name_map[category]
        else:
            found = False
            for key, value in name_map.items():
                if key in category or category in key:
                    short_name = value
                    found = True
                    break
            if not found:
                short_name = category[:40]
                write_log(f"⚠️ Не найдено соответствие для категории: {category}")
        lines.append(f"    {short_name}: {amount:,.2f} ₽")

    return "\n".join(lines)

def format_expense_comparison(expenses_current, expenses_prev, title):
    """Форматирует блок расходов с сравнением двух периодов."""
    if not expenses_current and not expenses_prev:
        return f"🔹 *{title}*\nНет данных о расходах.\n"
    
    total_current = sum(expenses_current.values()) if expenses_current else 0
    total_prev = sum(expenses_prev.values()) if expenses_prev else 0
    total_indicator = indicator(total_current, total_prev, False)
    lines = [f"🔹 *{title}*"]
    lines.append(f"  Итого расходов: {fmt_num(total_current)} ₽ / {fmt_num(total_prev)} ₽ {total_indicator}")
    
    all_categories = set(expenses_current.keys()) | set(expenses_prev.keys())
    sorted_categories = sorted(all_categories, key=lambda x: expenses_current.get(x, 0), reverse=True)
    
    name_map = {
        "Комиссия Ozon": "Комиссия",
        "Оплата эквайринга": "Эквайринг",
        "Доставка покупателю": "Доставка покупателю",
        "Доставка и обработка возврата, отмены, невыкупа": "Доставка/возвраты",
        "Кросс-докинг": "Кросс-докинг",
        "Страхование товара от массовых повреждений": "Страхование",
        "Обеспечение материалами для упаковки товара": "Обеспечение упаковкой",
        "Упаковка товара партнёрами": "Упаковка",
        "Подписка Управление отзывами": "Подписка",
        "Оплата за клик": "Оплата за клик",
        "Получение возврата, отмены, невыкупа от покупателя": "Получение возвратов",
        "MarketplaceServiceItemDirectFlowLogistic": "Логистика прямая",
        "MarketplaceServiceItemRedistributionLastMileCourier": "Логистика последняя миля",
        "MarketplaceServiceItemReturnFlowLogistic": "Логистика возврат",
        "MarketplaceServiceItemDeliveryToHandoverPlaceOzon": "Доставка до ПВЗ",
        "MarketplaceRedistributionOfAcquiringOperation": "Эквайринг",
        "MarketplaceServiceItemRedistributionReturnsPVZ": "Обработка возвратов (ПВЗ)",
        "MarketplaceServiceItemPackageRedistribution": "Переупаковка",
        "MarketplaceServiceItemPackageMaterialsProvision": "Обеспечение упаковкой",
        "MarketplaceServiceItemProductReviewsManagementSubscription": "Подписка",
        "MarketplaceServiceItemRedistributionLastMilePVZ": "Логистика последняя миля (ПВЗ)",
        "MarketplaceServiceItemDirectFlowLogisticFBS": "Логистика прямая (FBS)",
        "MarketplaceServiceItemReturnFlowLogisticFBS": "Логистика возврат (FBS)",
        "ItemAgentServiceStarsMembership": "Звёздные товары",
        "MarketplaceServiceSellerReturnsCargoAssortment": "Обработка возвратов партнёрами",
        "MarketplaceServiceItemTemporaryStorageRedistribution": "Временное размещение",
        "MarketplaceServiceProductMovementFromWarehouse": "Вывоз до ПВЗ",
        "MarketplaceServiceItemDisposalDetailed": "Утилизация",
        "Звёздные товары": "Звёздные товары",
        "Временное размещение товара партнерами": "Временное размещение",
        "Обработка товара в составе грузоместа: Поштучная приёмка": "Поштучная приёмка",
        "Обработка товара в составе грузоместа на FBO": "Поштучная приёмка",
        "Подготовка товара к вывозу: Брак": "Подготовка к вывозу (брак)",
        "Вывоз товара со склада силами Ozon: Доставка до ПВЗ": "Вывоз до ПВЗ",
        "Вывоз товара со Склада силами Ozon: Доставка до ПВЗ": "Вывоз до ПВЗ",
        "Бронирование места и персонала для поставки с неполным составом в составе грузоместа": "Бронирование места",
        "Услуга по бронированию места и персонала для поставки с неполным составом в составе ГМ": "Бронирование места",
        "Обработка опознанных излишков в составе грузоместа": "Обработка излишков",
        "Услуга по обработке опознанных излишков в составе ГМ": "Обработка излишков",
        "Утилизация товара: Пролились/просыпались из-за упаковки": "Утилизация",
        "Потеря по вине Ozon на складе": "Потеря (склад)",
        "Потеря по вине Ozon в логистике": "Потеря (логистика)",
        "Вознаграждение за продажу": "Вознаграждение",
        "Возврат вознаграждения": "Возврат вознаграждения",
        "Программы партнёров": "Программы партнёров",
        "Баллы за скидки": "Баллы за скидки",
        "Выручка": "Выручка",
        "Возврат выручки": "Возврат выручки",
    }
    
    for category in sorted_categories:
        amount_cur = expenses_current.get(category, 0)
        amount_prev = expenses_prev.get(category, 0)
        ind = indicator(amount_cur, amount_prev, False)
        short_name = name_map.get(category, category)
        lines.append(f"    {short_name}: {fmt_num(amount_cur)} ₽ / {fmt_num(amount_prev)} ₽ {ind}")
    
    return "\n".join(lines)

# ==================== ФОРМАТИРОВАНИЕ ОТЧЁТОВ СРАВНЕНИЯ ====================
def format_period_comparison_metrics(metrics_current, metrics_prev, period_name):
    """
    Формирует отчёт с сравнением текущего и предыдущего периодов (месяц/квартал/год).
    """
    cur_ordered_sum = metrics_current.get('ordered_sum', 0)
    cur_ordered_units = metrics_current.get('ordered_units', 0)
    cur_delivered_sum = metrics_current.get('delivered_sum', 0)
    cur_delivered_units = metrics_current.get('delivered_units', 0)
    cur_canceled_sum = metrics_current.get('canceled_sum', 0)
    cur_canceled_units = metrics_current.get('canceled_units', 0)
    cur_ad_expense = metrics_current.get('ad_expense', 0)
    cur_drr = metrics_current.get('drr')
    cur_eff_drr = metrics_current.get('effective_drr')
    cur_expenses = metrics_current.get('expenses', {})

    prev_ordered_sum = metrics_prev.get('ordered_sum', 0)
    prev_ordered_units = metrics_prev.get('ordered_units', 0)
    prev_delivered_sum = metrics_prev.get('delivered_sum', 0)
    prev_delivered_units = metrics_prev.get('delivered_units', 0)
    prev_canceled_sum = metrics_prev.get('canceled_sum', 0)
    prev_canceled_units = metrics_prev.get('canceled_units', 0)
    prev_ad_expense = metrics_prev.get('ad_expense', 0)
    prev_drr = metrics_prev.get('drr')
    prev_eff_drr = metrics_prev.get('effective_drr')
    prev_expenses = metrics_prev.get('expenses', {})

    cur_cancel_rate = (cur_canceled_units / cur_delivered_units * 100) if cur_delivered_units > 0 else None
    prev_cancel_rate = (prev_canceled_units / prev_delivered_units * 100) if prev_delivered_units > 0 else None

    ind_ordered_sum = indicator(cur_ordered_sum, prev_ordered_sum, True)
    ind_ordered_units = indicator(cur_ordered_units, prev_ordered_units, True)
    ind_delivered_sum = indicator(cur_delivered_sum, prev_delivered_sum, True)
    ind_delivered_units = indicator(cur_delivered_units, prev_delivered_units, True)
    ind_canceled_sum = indicator(cur_canceled_sum, prev_canceled_sum, False)
    ind_canceled_units = indicator(cur_canceled_units, prev_canceled_units, False)
    ind_cancel_rate = indicator(cur_cancel_rate, prev_cancel_rate, False)
    ind_ad_expense = indicator(cur_ad_expense, prev_ad_expense, False)
    ind_drr = indicator(cur_drr, prev_drr, False)
    ind_eff_drr = indicator(cur_eff_drr, prev_eff_drr, False)

    lines = []
    lines.append(f"📊 *Продажи за {period_name}*")
    lines.append("")

    lines.append(f"🛒 *Заказано*")
    lines.append(f"  На сумму: {fmt_num(cur_ordered_sum)} ₽ {ind_ordered_sum}")
    lines.append(f"  Штук: {fmt_int(cur_ordered_units)} {ind_ordered_units}")
    lines.append("vs предыдущий период:")
    lines.append(f"  На сумму: {fmt_num(prev_ordered_sum)} ₽")
    lines.append(f"  Штук: {fmt_int(prev_ordered_units)}")
    lines.append("")

    lines.append(f"📦 *Доставлено*")
    lines.append(f"  На сумму: {fmt_num(cur_delivered_sum)} ₽ {ind_delivered_sum}")
    lines.append(f"  Штук: {fmt_int(cur_delivered_units)} {ind_delivered_units}")
    lines.append("vs предыдущий период:")
    lines.append(f"  На сумму: {fmt_num(prev_delivered_sum)} ₽")
    lines.append(f"  Штук: {fmt_int(prev_delivered_units)}")
    lines.append("")

    lines.append(f"❌ *Отменено*")
    lines.append(f"  На сумму: {fmt_num(cur_canceled_sum)} ₽ {ind_canceled_sum}")
    lines.append(f"  Штук: {fmt_int(cur_canceled_units)} {ind_canceled_units}")
    cur_cancel_rate_text = f"{cur_cancel_rate:.2f}%" if cur_cancel_rate is not None else "∞"
    prev_cancel_rate_text = f"{prev_cancel_rate:.2f}%" if prev_cancel_rate is not None else "∞"
    lines.append(f"  Доля отмен: {cur_cancel_rate_text} {ind_cancel_rate}")
    lines.append("vs предыдущий период:")
    lines.append(f"  На сумму: {fmt_num(prev_canceled_sum)} ₽")
    lines.append(f"  Штук: {fmt_int(prev_canceled_units)}")
    lines.append(f"  Доля отмен: {prev_cancel_rate_text}")
    lines.append("")

    lines.append(f"📢 *Реклама*")
    lines.append(f"  Расходы: {fmt_num(cur_ad_expense)} ₽ {ind_ad_expense}")
    cur_drr_text = f"{cur_drr:.2f}%" if cur_drr is not None else "∞"
    cur_eff_drr_text = f"{cur_eff_drr:.2f}%" if cur_eff_drr is not None else "∞"
    prev_drr_text = f"{prev_drr:.2f}%" if prev_drr is not None else "∞"
    prev_eff_drr_text = f"{prev_eff_drr:.2f}%" if prev_eff_drr is not None else "∞"
    lines.append(f"  ДРР (общий): {cur_drr_text} {ind_drr}")
    lines.append(f"  ДРР (по доставленным): {cur_eff_drr_text} {ind_eff_drr}")
    lines.append("vs предыдущий период:")
    lines.append(f"  Расходы: {fmt_num(prev_ad_expense)} ₽")
    lines.append(f"  ДРР (общий): {prev_drr_text}")
    lines.append(f"  ДРР (по доставленным): {prev_eff_drr_text}")
    lines.append("")

    expense_block = format_expense_comparison(cur_expenses, prev_expenses, "Расходы за период")
    lines.append(expense_block)

    return "\n".join(lines)

# ==================== ФОРМАТИРОВАНИЕ ОТЧЁТА ПО ОДНОЙ ДАТЕ/ПЕРИОДУ ====================
def format_single_metrics(metrics, title):
    if not metrics:
        return f"📊 *{title}*\n\n❌ Нет данных за указанный период."
    has_data = False
    for key, val in metrics.items():
        if key in ["drr", "effective_drr", "ad_expense", "expenses"]:
            continue
        if isinstance(val, (int, float)) and val != 0:
            has_data = True
            break
    if not has_data:
        return f"📊 *{title}*\n\n❌ Нет данных за указанный период."

    ad_expense = metrics.get("ad_expense", 0)
    drr = metrics.get("drr")
    eff_drr = metrics.get("effective_drr")
    drr_text = f"{drr:.2f}%" if drr is not None else "∞"
    eff_drr_text = f"{eff_drr:.2f}%" if eff_drr is not None else "∞"

    canceled_units = metrics.get('canceled_units', 0)
    delivered_units = metrics.get('delivered_units', 0)
    cancel_rate = (canceled_units / delivered_units * 100) if delivered_units > 0 else None
    cancel_rate_text = f"{cancel_rate:.2f}%" if cancel_rate is not None else "∞"

    main_text = (
        f"📊 *{title}*\n\n"
        f"🛒 *Заказано*\n  На сумму: {metrics.get('ordered_sum', 0):,.2f} ₽\n"
        f"  Штук: {metrics.get('ordered_units', 0)}\n\n"
        f"📦 *Доставлено*\n  На сумму: {metrics.get('delivered_sum', 0):,.2f} ₽\n"
        f"  Штук: {metrics.get('delivered_units', 0)}\n\n"
        f"❌ *Отменено*\n  На сумму: {metrics.get('canceled_sum', 0):,.2f} ₽\n"
        f"  Штук: {metrics.get('canceled_units', 0)}\n"
        f"  Доля отмен: {cancel_rate_text}\n\n"
        f"📢 *Реклама*\n"
        f"  Расходы: {ad_expense:,.2f} ₽\n"
        f"  ДРР (общий): {drr_text}\n"
        f"  ДРР (по доставленным): {eff_drr_text}"
    )

    expenses = metrics.get("expenses", {})
    if expenses:
        expense_block = format_expense_block(expenses, "Расходы за период")
        main_text += "\n\n" + expense_block

    return main_text

# ==================== КОМБИНИРОВАННЫЙ ОТЧЁТ "ПРОДАЖИ ЗА СЕГОДНЯ" ====================
async def format_combined_metrics_with_deltas(include_yesterday=False, progress_callback=None):
    now = get_current_time_msk()
    today_date = now.date()
    current_time = now.time()
    today_str = today_date.isoformat()
    yesterday_date = today_date - datetime.timedelta(days=1)
    yesterday_str = yesterday_date.isoformat()

    current_month_start = today_date.replace(day=1)
    current_month_start_str = current_month_start.isoformat()
    current_month_end_str = today_str

    previous_month_start = (current_month_start - datetime.timedelta(days=1)).replace(day=1)
    previous_month_start_str = previous_month_start.isoformat()
    previous_month_end = current_month_start - datetime.timedelta(days=1)
    previous_month_end_str = previous_month_end.isoformat()

    days_passed = (today_date - current_month_start).days + 1
    prev_period_end = previous_month_start + datetime.timedelta(days=days_passed - 1)
    prev_period_end_str = prev_period_end.isoformat()

    if progress_callback:
        await progress_callback("Загрузка отгрузок за текущий месяц...", 10)
    postings_current_task = fetch_postings(current_month_start_str, current_month_end_str)
    postings_prev_task = fetch_postings(previous_month_start_str, previous_month_end_str)
    postings_current, postings_prev = await asyncio.gather(postings_current_task, postings_prev_task)
    if progress_callback:
        await progress_callback("Отгрузки загружены, агрегируем...", 30)

    agg_yesterday_full = aggregate_postings(
        postings_current,
        date_from=yesterday_str,
        date_to=yesterday_str
    )
    yesterday_full_metrics = agg_yesterday_full.get(yesterday_str, {}) if yesterday_str in agg_yesterday_full else {}

    agg_today = aggregate_postings(
        postings_current,
        date_from=today_str,
        date_to=today_str,
        time_limit=current_time,
        apply_limit_on_day=today_str
    )
    today_metrics = agg_today.get(today_str, {}) if today_str in agg_today else {}

    agg_yesterday = aggregate_postings(
        postings_current,
        date_from=yesterday_str,
        date_to=yesterday_str,
        time_limit=current_time,
        apply_limit_on_day=yesterday_str
    )
    yesterday_metrics = agg_yesterday.get(yesterday_str, {}) if yesterday_str in agg_yesterday else {}

    agg_current_month = aggregate_postings(
        postings_current,
        date_from=current_month_start_str,
        date_to=current_month_end_str,
        time_limit=current_time,
        apply_limit_on_day=today_str
    )
    month_metrics = {
        "ordered_units": 0,
        "ordered_sum": 0.0,
        "delivered_units": 0,
        "delivered_sum": 0.0,
        "canceled_units": 0,
        "canceled_sum": 0.0,
    }
    for vals in agg_current_month.values():
        for key in month_metrics:
            month_metrics[key] += vals.get(key, 0)

    agg_prev_month = aggregate_postings(
        postings_prev,
        date_from=previous_month_start_str,
        date_to=prev_period_end_str,
        time_limit=current_time,
        apply_limit_on_day=prev_period_end_str
    )
    prev_month_metrics = {
        "ordered_units": 0,
        "ordered_sum": 0.0,
        "delivered_units": 0,
        "delivered_sum": 0.0,
        "canceled_units": 0,
        "canceled_sum": 0.0,
    }
    for vals in agg_prev_month.values():
        for key in prev_month_metrics:
            prev_month_metrics[key] += vals.get(key, 0)

    if progress_callback:
        await progress_callback("Загрузка рекламы и финансов...", 50)

    ad_today_task = fetch_advertising_expense(today_str, today_str)
    ad_yesterday_task = fetch_advertising_expense(yesterday_str, yesterday_str)
    ad_month_task = fetch_advertising_expense(current_month_start_str, today_str)
    ad_prev_task = fetch_advertising_expense(previous_month_start_str, prev_period_end_str)
    fin_today_task = fetch_finance_transactions(today_str, today_str)
    fin_month_task = fetch_finance_transactions(current_month_start_str, today_str)

    ad_today, ad_yesterday, ad_month, ad_prev_period, fin_today, fin_month = await asyncio.gather(
        ad_today_task, ad_yesterday_task, ad_month_task, ad_prev_task,
        fin_today_task, fin_month_task
    )
    if progress_callback:
        await progress_callback("Данные загружены, формируем отчёт...", 80)

    expenses_today = aggregate_finance_expenses(fin_today)
    expenses_month = aggregate_finance_expenses(fin_month)

    if ad_today > 0:
        expenses_today["Оплата за клик"] = ad_today
        expenses_today.pop("Реклама", None)
    if ad_month > 0:
        expenses_month["Оплата за клик"] = ad_month
        expenses_month.pop("Реклама", None)

    d_ord_sum = calc_delta(today_metrics.get("ordered_sum", 0), yesterday_metrics.get("ordered_sum", 0))
    d_ord_units = calc_delta(today_metrics.get("ordered_units", 0), yesterday_metrics.get("ordered_units", 0))
    d_ad = calc_delta(ad_today, ad_yesterday)

    d_ord_sum_m = calc_delta(month_metrics.get("ordered_sum", 0), prev_month_metrics.get("ordered_sum", 0))
    d_ord_units_m = calc_delta(month_metrics.get("ordered_units", 0), prev_month_metrics.get("ordered_units", 0))
    d_del_sum_m = calc_delta(month_metrics.get("delivered_sum", 0), prev_month_metrics.get("delivered_sum", 0))
    d_del_units_m = calc_delta(month_metrics.get("delivered_units", 0), prev_month_metrics.get("delivered_units", 0))
    d_can_sum_m = calc_delta(month_metrics.get("canceled_sum", 0), prev_month_metrics.get("canceled_sum", 0))
    d_can_units_m = calc_delta(month_metrics.get("canceled_units", 0), prev_month_metrics.get("canceled_units", 0))
    d_ad_m = calc_delta(ad_month, ad_prev_period)

    cancel_rate_today = (today_metrics.get("canceled_units", 0) / today_metrics.get("delivered_units", 0) * 100) if today_metrics.get("delivered_units", 0) > 0 else None
    cancel_rate_month = (month_metrics["canceled_units"] / month_metrics["delivered_units"] * 100) if month_metrics["delivered_units"] > 0 else None
    cancel_rate_prev = (prev_month_metrics["canceled_units"] / prev_month_metrics["delivered_units"] * 100) if prev_month_metrics["delivered_units"] > 0 else None

    def format_today_block():
        ordered_sum = fmt_num(today_metrics.get("ordered_sum", 0))
        ordered_units = fmt_int(today_metrics.get("ordered_units", 0))
        canceled_sum = fmt_num(today_metrics.get("canceled_sum", 0))
        canceled_units = fmt_int(today_metrics.get("canceled_units", 0))

        delta_ord_sum = fmt_pct(d_ord_sum)
        delta_ord_units = fmt_pct(d_ord_units)
        delta_can_sum = fmt_pct(calc_delta(today_metrics.get("canceled_sum", 0), yesterday_metrics.get("canceled_sum", 0)))
        delta_can_units = fmt_pct(calc_delta(today_metrics.get("canceled_units", 0), yesterday_metrics.get("canceled_units", 0)))

        cancel_rate_text = f"{cancel_rate_today:.2f}%" if cancel_rate_today is not None else "∞"

        return (
            f"🔹 *Сегодня (на {now.strftime('%H:%M')} МСК)*\n"
            f"  🛒 Заказано: \n  {ordered_sum} ₽ / {ordered_units} шт.\n"
            f"    vs Вчера: \n  {delta_ord_sum} ₽ / {delta_ord_units} шт.\n\n"
            f"  ❌ Отменено: \n  {canceled_sum} ₽ / {canceled_units} шт.\n"
            f"    vs Вчера: \n  {delta_can_sum} ₽ / {delta_can_units} шт.\n"
            f"  Доля отмен: {cancel_rate_text}\n"
        )

    def format_month_block():
        ordered_sum = fmt_num(month_metrics.get("ordered_sum", 0))
        ordered_units = fmt_int(month_metrics.get("ordered_units", 0))
        delivered_sum = fmt_num(month_metrics.get("delivered_sum", 0))
        delivered_units = fmt_int(month_metrics.get("delivered_units", 0))
        canceled_sum = fmt_num(month_metrics.get("canceled_sum", 0))
        canceled_units = fmt_int(month_metrics.get("canceled_units", 0))
        ad_expense = fmt_num(ad_month)
        ad_prev = fmt_num(ad_prev_period)

        revenue = month_metrics.get("ordered_sum", 0)
        drr = (ad_month / revenue * 100) if revenue > 0 else None
        delivered_revenue = month_metrics.get("delivered_sum", 0)
        eff_drr = (ad_month / delivered_revenue * 100) if delivered_revenue > 0 else None

        prev_rev = prev_month_metrics.get("ordered_sum", 0)
        prev_del_rev = prev_month_metrics.get("delivered_sum", 0)
        prev_drr_val = (ad_prev_period / prev_rev * 100) if prev_rev > 0 else None
        prev_eff_drr_val = (ad_prev_period / prev_del_rev * 100) if prev_del_rev > 0 else None

        drr_str = f"{drr:.2f}%" if drr is not None else "∞"
        eff_drr_str = f"{eff_drr:.2f}%" if eff_drr is not None else "∞"
        prev_drr_str = f"{prev_drr_val:.2f}%" if prev_drr_val is not None else "∞"
        prev_eff_drr_str = f"{prev_eff_drr_val:.2f}%" if prev_eff_drr_val is not None else "∞"

        delta_ord_sum_m = fmt_pct(d_ord_sum_m)
        delta_ord_units_m = fmt_pct(d_ord_units_m)
        delta_del_sum_m = fmt_pct(d_del_sum_m)
        delta_del_units_m = fmt_pct(d_del_units_m)
        delta_can_sum_m = fmt_pct(d_can_sum_m)
        delta_can_units_m = fmt_pct(d_can_units_m)

        cancel_rate_month_text = f"{cancel_rate_month:.2f}%" if cancel_rate_month is not None else "∞"
        cancel_rate_prev_text = f"{cancel_rate_prev:.2f}%" if cancel_rate_prev is not None else "∞"
        cancel_rate_delta = calc_delta(cancel_rate_month if cancel_rate_month is not None else 0,
                                       cancel_rate_prev if cancel_rate_prev is not None else 0)
        cancel_rate_delta_text = fmt_pct(cancel_rate_delta)

        return (
            f"🔹 *Текущий месяц*\n"
            f"  🛒 Заказано: \n  {ordered_sum} ₽ / {ordered_units} шт.\n"
            f"    vs предыдущий месяц: \n  {delta_ord_sum_m} ₽ / {delta_ord_units_m} шт.\n\n"
            f"  📦 Доставлено: \n  {delivered_sum} ₽ / {delivered_units} шт.\n"
            f"    vs предыдущий месяц: \n  {delta_del_sum_m} ₽ / {delta_del_units_m} шт.\n\n"
            f"  ❌ Отменено: \n  {canceled_sum} ₽ / {canceled_units} шт.\n"
            f"    vs предыдущий месяц: \n  {delta_can_sum_m} ₽ / {delta_can_units_m} шт.\n"
            f"  Доля отмен: {cancel_rate_month_text} | vs предыдущий месяц: {cancel_rate_prev_text} ({cancel_rate_delta_text})\n\n"
            f"  📢 Реклама: \n  {ad_expense} ₽ | vs предыдущий месяц: {ad_prev} ₽\n"
            f"  ДРР (общий): {drr_str} | vs предыдущий месяц: {prev_drr_str}\n"
            f"  ДРР (по доставленным): {eff_drr_str} | vs предыдущий месяц: {prev_eff_drr_str}"
        )

    parts = []
    parts.append(format_today_block())
    parts.append(format_month_block())

    parts.append(format_expense_block(expenses_today, "Расходы сегодня"))
    parts.append(format_expense_block(expenses_month, "Расходы за текущий месяц"))

    if progress_callback:
        await progress_callback("Готово", 100)
    return "📊 *Продажи за сегодня*\n\n\n" + "\n\n".join(parts)

# ==================== ТОВАРНЫЕ ОТЧЁТЫ ====================
async def get_product_data_for_date(date_str):
    """Возвращает агрегированные данные по товарам за конкретную дату."""
    today = get_moscow_today()
    start = (today - datetime.timedelta(days=183)).strftime("%Y-%m-%d")
    end = today.strftime("%Y-%m-%d")
    postings = await fetch_postings(start, end)
    products = aggregate_products(postings, date_from=date_str, date_to=date_str)
    return products

async def get_product_data_for_period(date_from, date_to):
    """Возвращает агрегированные данные по товарам за период."""
    postings = await fetch_postings(date_from, date_to)
    products = aggregate_products(postings, date_from=date_from, date_to=date_to)
    return products

async def get_product_data_today():
    now = get_current_time_msk()
    today_str = now.date().isoformat()
    postings = await fetch_postings(today_str, today_str)
    products = aggregate_products(postings, date_from=today_str, date_to=today_str,
                                  time_limit=now.time(), apply_limit_on_day=today_str)
    return products

async def get_product_data_month():
    now = get_current_time_msk()
    today_date = now.date()
    current_month_start = today_date.replace(day=1).isoformat()
    today_str = today_date.isoformat()
    postings = await fetch_postings(current_month_start, today_str)
    products = aggregate_products(postings, date_from=current_month_start, date_to=today_str,
                                  time_limit=now.time(), apply_limit_on_day=today_str)
    return products

async def get_product_data_prev_month():
    now = get_current_time_msk()
    today_date = now.date()
    current_month_start = today_date.replace(day=1)
    previous_month_start = (current_month_start - datetime.timedelta(days=1)).replace(day=1)
    days_passed = (today_date - current_month_start).days + 1
    prev_period_end = previous_month_start + datetime.timedelta(days=days_passed - 1)
    prev_start_str = previous_month_start.isoformat()
    prev_end_str = prev_period_end.isoformat()
    postings = await fetch_postings(prev_start_str, prev_end_str)
    products = aggregate_products(postings, date_from=prev_start_str, date_to=prev_end_str,
                                  time_limit=now.time(), apply_limit_on_day=prev_end_str)
    return products

def format_top_products(products, title, limit=15):
    if not products:
        return f"📦 {title}\n\n❌ Нет данных за указанный период."

    sorted_items = sorted(products.items(), key=lambda x: x[1]["ordered_sum"], reverse=True)[:limit]
    lines = [f"📦 {title}", ""]
    for idx, (sku, stats) in enumerate(sorted_items, 1):
        name = stats["name"][:40]
        offer_id = stats.get("offer_id", "")
        ordered_sum = f"{stats['ordered_sum']:,.2f}".replace(",", " ")
        ordered_units = stats["ordered_units"]
        delivered_sum = f"{stats['delivered_sum']:,.2f}".replace(",", " ")
        delivered_units = stats["delivered_units"]
        canceled_sum = f"{stats['canceled_sum']:,.2f}".replace(",", " ")
        canceled_units = stats["canceled_units"]
        avg_check = (stats["ordered_sum"] / stats["order_count"]) if stats["order_count"] > 0 else 0
        avg_check_str = f"{avg_check:,.2f}".replace(",", " ")
        lines.append(f"{idx}. SKU: {sku} | {name} | Арт: {offer_id}" if offer_id else f"{idx}. SKU: {sku} | {name}")
        lines.append(f"   🛒 Заказано: {ordered_sum} ₽ / {ordered_units} шт.")
        lines.append(f"   📦 Доставлено: {delivered_sum} ₽ / {delivered_units} шт.")
        lines.append(f"   ❌ Отменено: {canceled_sum} ₽ / {canceled_units} шт.")
        lines.append(f"   💰 Средний чек: {avg_check_str} ₽")
        lines.append("")
    return "\n".join(lines)

def format_products_summary(products):
    if not products:
        return "Нет данных"
    total_revenue = sum(p["ordered_sum"] for p in products.values())
    total_units = sum(p["ordered_units"] for p in products.values())
    total_orders = sum(p["order_count"] for p in products.values())
    avg_check = (total_revenue / total_orders) if total_orders > 0 else 0
    return (
        f"Сводка\n"
        f"  Уникальных товаров: {len(products)}\n"
        f"  Общая выручка: {total_revenue:,.2f} ₽\n"
        f"  Всего единиц: {total_units}\n"
        f"  Всего заказов: {total_orders}\n"
        f"  Средний чек: {avg_check:,.2f} ₽"
    )

async def format_product_combined():
    products_today, products_month, products_prev_month = await asyncio.gather(
        get_product_data_today(),
        get_product_data_month(),
        get_product_data_prev_month()
    )

    parts = []
    parts.append(format_top_products(products_today, "Топ товаров за сегодня", limit=15))
    parts.append("")
    parts.append(format_top_products(products_month, "Топ товаров за текущий месяц (аналог. период)", limit=15))
    if products_prev_month:
        parts.append("")
        parts.append("Сравнение с предыдущим месяцем (аналог. период)")
        total_rev_current = sum(p["ordered_sum"] for p in products_month.values())
        total_rev_prev = sum(p["ordered_sum"] for p in products_prev_month.values())
        total_units_current = sum(p["ordered_units"] for p in products_month.values())
        total_units_prev = sum(p["ordered_units"] for p in products_prev_month.values())
        delta_rev = ((total_rev_current - total_rev_prev) / total_rev_prev * 100) if total_rev_prev > 0 else None
        delta_units = ((total_units_current - total_units_prev) / total_units_prev * 100) if total_units_prev > 0 else None
        parts.append(f"  Выручка: {total_rev_current:,.2f} ₽ vs {total_rev_prev:,.2f} ₽ (Δ {delta_rev:.1f}%)" if delta_rev is not None else "  Выручка: нет данных")
        parts.append(f"  Единиц: {total_units_current} vs {total_units_prev} (Δ {delta_units:.1f}%)" if delta_units is not None else "  Единиц: нет данных")

    return "📦 Отчёт по товарам\n\n\n" + "\n\n".join(parts)
