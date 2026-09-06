import datetime
from config import API_MAX_DAYS_PER_REQUEST, OZON_PERFORMANCE_CLIENT_ID, OZON_PERFORMANCE_CLIENT_SECRET
from api.client import api_request_with_retry
from api.cache import get_from_cache, save_to_cache
from utils.logger import write_log
from utils.validators import get_moscow_today

async def get_performance_token():
    if not OZON_PERFORMANCE_CLIENT_ID or not OZON_PERFORMANCE_CLIENT_SECRET:
        write_log("⚠️ OZON_PERFORMANCE_CLIENT_ID или CLIENT_SECRET не заданы!")
        return None

    url = "https://api-performance.ozon.ru/api/client/token"
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "client_id": OZON_PERFORMANCE_CLIENT_ID,
        "client_secret": OZON_PERFORMANCE_CLIENT_SECRET,
        "grant_type": "client_credentials"
    }
    try:
        token_data = await api_request_with_retry(url, headers, payload, method='POST')
        token = token_data.get("access_token")
        if token:
            write_log("✅ Токен Performance API успешно получен.")
            return token
        else:
            write_log(f"❌ Ошибка получения токена: {token_data}")
            return None
    except Exception as e:
        write_log(f"❌ Ошибка при запросе токена: {e}")
        return None

async def fetch_advertising_expense_single(date_from, date_to):
    cache_key = f"fetch_advertising_expense_single_{date_from}_{date_to}"
    cached = await get_from_cache(cache_key)
    if cached is not None:
        return cached

    token = await get_performance_token()
    if not token:
        return 0.0

    url = "https://api-performance.ozon.ru/api/client/statistics/expense/json"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    params = {
        "dateFrom": date_from,
        "dateTo": date_to,
    }
    try:
        data = await api_request_with_retry(url, headers, params, method='GET')
        total_expense = 0.0
        if isinstance(data, dict) and "rows" in data:
            rows = data["rows"]
            if isinstance(rows, list):
                for item in rows:
                    item_date = item.get("date")
                    if item_date and len(item_date) >= 10:
                        item_date_str = item_date[:10]
                        if date_from <= item_date_str <= date_to:
                            money_spent_str = item.get("moneySpent")
                            if money_spent_str is not None:
                                try:
                                    money_spent = float(money_spent_str.replace(",", "."))
                                    total_expense += money_spent
                                except:
                                    pass
        await save_to_cache(cache_key, total_expense)
        return total_expense
    except Exception as e:
        write_log(f"❌ Ошибка получения рекламных расходов: {e}")
        return 0.0

async def fetch_advertising_expense(date_from, date_to, progress_callback=None):
    cache_key = f"fetch_advertising_expense_{date_from}_{date_to}"
    cached = await get_from_cache(cache_key)
    if cached is not None:
        return cached

    start_dt = datetime.datetime.strptime(date_from, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(date_to, "%Y-%m-%d")
    today = get_moscow_today()
    if start_dt.date() > today:
        return 0.0
    if end_dt.date() > today:
        end_dt = datetime.datetime.combine(today, datetime.time(23, 59, 59))

    delta = (end_dt - start_dt).days
    if delta <= API_MAX_DAYS_PER_REQUEST:
        result = await fetch_advertising_expense_single(date_from, end_dt.strftime("%Y-%m-%d"))
        await save_to_cache(cache_key, result)
        if progress_callback:
            await progress_callback("Реклама загружена", 100)
        return result

    total = 0.0
    months = []
    current = start_dt.replace(day=1)
    while current <= end_dt:
        month_start = current.strftime("%Y-%m-%d")
        next_month = current.replace(day=28) + datetime.timedelta(days=4)
        month_end = (next_month - datetime.timedelta(days=next_month.day)).strftime("%Y-%m-%d")
        if month_end > end_dt.strftime("%Y-%m-%d"):
            month_end = end_dt.strftime("%Y-%m-%d")
        if current.date() > today:
            break
        months.append((month_start, month_end))
        current = current.replace(day=28) + datetime.timedelta(days=4)
        current = current.replace(day=1)
    total_months = len(months)
    for i, (m_start, m_end) in enumerate(months):
        if progress_callback:
            progress = int((i / total_months) * 100) if total_months > 0 else 100
            await progress_callback(f"Загрузка рекламы {m_start}–{m_end}", progress)
        total += await fetch_advertising_expense_single(m_start, m_end)
    await save_to_cache(cache_key, total)
    if progress_callback:
        await progress_callback("Реклама загружена", 100)
    return total
