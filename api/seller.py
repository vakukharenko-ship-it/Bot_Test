import datetime
import asyncio
from config import (
    OZON_CLIENT_ID, OZON_API_KEY,
    OZON_POSTING_FBO_URL, OZON_FINANCE_URL,
    API_MAX_DAYS_PER_REQUEST,
    MOSCOW_TZ
)
from api.client import api_request_with_retry
from api.cache import get_from_cache, save_to_cache
from utils.logger import write_log

# ---------- ОТГРУЗКИ ----------
async def fetch_postings(date_from, date_to, progress_callback=None):
    cache_key = f"fetch_postings_{date_from}_{date_to}"
    cached = await get_from_cache(cache_key)
    if cached is not None:
        return cached

    headers = {
        "Client-Id": OZON_CLIENT_ID,
        "Api-Key": OZON_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "date_from": date_from,
        "date_to": date_to,
        "status": "",
        "limit": 1000,
        "offset": 0,
    }
    all_postings = []
    total_pages = None
    page = 0
    while True:
        page += 1
        try:
            data = await api_request_with_retry(OZON_POSTING_FBO_URL, headers, payload, method='POST')
            postings = data.get("result", [])
            if not postings:
                break
            all_postings.extend(postings)
            if total_pages is None and 'total' in data:
                total_pages = (data['total'] + payload['limit'] - 1) // payload['limit']
            if progress_callback:
                progress = min(100, int((page / (total_pages or 1)) * 100))
                await progress_callback(f"Загрузка отгрузок... {len(all_postings)} шт.", progress)
            if len(postings) < payload["limit"]:
                break
            payload["offset"] += payload["limit"]
        except Exception as e:
            write_log(f"❌ Ошибка получения отгрузок: {e}")
            break
    write_log(f"📦 Загружено отгрузок: {len(all_postings)} за {date_from}–{date_to}")
    await save_to_cache(cache_key, all_postings)
    return all_postings

# ---------- ФИНАНСОВЫЕ ТРАНЗАКЦИИ ----------
async def fetch_finance_transactions_single(date_from, date_to):
    cache_key = f"fetch_finance_transactions_single_{date_from}_{date_to}"
    cached = await get_from_cache(cache_key)
    if cached is not None:
        return cached

    today_str = get_moscow_today().isoformat()
    if date_from > today_str:
        return []
    if date_to > today_str:
        date_to = today_str

    headers = {
        "Client-Id": OZON_CLIENT_ID,
        "Api-Key": OZON_API_KEY,
        "Content-Type": "application/json",
    }

    from_iso = date_from + "T00:00:00.000Z"
    to_iso = date_to + "T23:59:59.999Z"

    all_transactions = []
    page = 1
    page_size = 1000

    while True:
        payload = {
            "filter": {
                "date": {
                    "from": from_iso,
                    "to": to_iso
                }
            },
            "page": page,
            "page_size": page_size,
        }

        try:
            data = await api_request_with_retry(OZON_FINANCE_URL, headers, payload, method='POST')
            items = data.get("result", {}).get("operations", [])
            if not items:
                break
            all_transactions.extend(items)
            if len(items) < page_size:
                break
            page += 1
        except Exception as e:
            write_log(f"❌ Ошибка получения финансовых транзакций: {e}")
            break

    await save_to_cache(cache_key, all_transactions)
    return all_transactions

async def fetch_finance_transactions(date_from, date_to, progress_callback=None):
    cache_key = f"fetch_finance_transactions_{date_from}_{date_to}"
    cached = await get_from_cache(cache_key)
    if cached is not None:
        return cached

    start_dt = datetime.datetime.strptime(date_from, "%Y-%m-%d")
    end_dt = datetime.datetime.strptime(date_to, "%Y-%m-%d")
    today = get_moscow_today()
    if start_dt.date() > today:
        return []
    if end_dt.date() > today:
        end_dt = datetime.datetime.combine(today, datetime.time(23, 59, 59))

    delta = (end_dt - start_dt).days
    if delta <= API_MAX_DAYS_PER_REQUEST:
        result = await fetch_finance_transactions_single(date_from, end_dt.strftime("%Y-%m-%d"))
        await save_to_cache(cache_key, result)
        if progress_callback:
            await progress_callback("Финансы загружены", 100)
        return result

    all_transactions = []
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
            await progress_callback(f"Загрузка финансов {m_start}–{m_end}", progress)
        all_transactions.extend(await fetch_finance_transactions_single(m_start, m_end))
    write_log(f"💰 Всего загружено финансовых транзакций: {len(all_transactions)} за {date_from}–{date_to}")
    await save_to_cache(cache_key, all_transactions)
    if progress_callback:
        await progress_callback("Финансы загружены", 100)
    return all_transactions

def get_moscow_today():
    return datetime.datetime.now(MOSCOW_TZ).date()