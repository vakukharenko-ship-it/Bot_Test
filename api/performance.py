{\rtf1\ansi\ansicpg1251\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw3288\paperh2267\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import datetime\
from config import API_MAX_DAYS_PER_REQUEST, OZON_PERFORMANCE_CLIENT_ID, OZON_PERFORMANCE_CLIENT_SECRET\
from api.client import api_request_with_retry\
from api.cache import get_from_cache, save_to_cache\
from utils.logger import write_log\
from utils.validators import get_moscow_today\
\
async def get_performance_token():\
    if not OZON_PERFORMANCE_CLIENT_ID or not OZON_PERFORMANCE_CLIENT_SECRET:\
        write_log("\uc0\u9888 \u65039  OZON_PERFORMANCE_CLIENT_ID \u1080 \u1083 \u1080  CLIENT_SECRET \u1085 \u1077  \u1079 \u1072 \u1076 \u1072 \u1085 \u1099 !")\
        return None\
\
    url = "https://api-performance.ozon.ru/api/client/token"\
    headers = \{\
        "Content-Type": "application/json",\
        "Accept": "application/json",\
    \}\
    payload = \{\
        "client_id": OZON_PERFORMANCE_CLIENT_ID,\
        "client_secret": OZON_PERFORMANCE_CLIENT_SECRET,\
        "grant_type": "client_credentials"\
    \}\
    try:\
        token_data = await api_request_with_retry(url, headers, payload, method='POST')\
        token = token_data.get("access_token")\
        if token:\
            write_log("\uc0\u9989  \u1058 \u1086 \u1082 \u1077 \u1085  Performance API \u1091 \u1089 \u1087 \u1077 \u1096 \u1085 \u1086  \u1087 \u1086 \u1083 \u1091 \u1095 \u1077 \u1085 .")\
            return token\
        else:\
            write_log(f"\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1087 \u1086 \u1083 \u1091 \u1095 \u1077 \u1085 \u1080 \u1103  \u1090 \u1086 \u1082 \u1077 \u1085 \u1072 : \{token_data\}")\
            return None\
    except Exception as e:\
        write_log(f"\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1087 \u1088 \u1080  \u1079 \u1072 \u1087 \u1088 \u1086 \u1089 \u1077  \u1090 \u1086 \u1082 \u1077 \u1085 \u1072 : \{e\}")\
        return None\
\
async def fetch_advertising_expense_single(date_from, date_to):\
    cache_key = f"fetch_advertising_expense_single_\{date_from\}_\{date_to\}"\
    cached = await get_from_cache(cache_key)\
    if cached is not None:\
        return cached\
\
    token = await get_performance_token()\
    if not token:\
        return 0.0\
\
    url = "https://api-performance.ozon.ru/api/client/statistics/expense/json"\
    headers = \{\
        "Authorization": f"Bearer \{token\}",\
        "Content-Type": "application/json",\
    \}\
    params = \{\
        "dateFrom": date_from,\
        "dateTo": date_to,\
    \}\
    try:\
        data = await api_request_with_retry(url, headers, params, method='GET')\
        total_expense = 0.0\
        if isinstance(data, dict) and "rows" in data:\
            rows = data["rows"]\
            if isinstance(rows, list):\
                for item in rows:\
                    item_date = item.get("date")\
                    if item_date and len(item_date) >= 10:\
                        item_date_str = item_date[:10]\
                        if date_from <= item_date_str <= date_to:\
                            money_spent_str = item.get("moneySpent")\
                            if money_spent_str is not None:\
                                try:\
                                    money_spent = float(money_spent_str.replace(",", "."))\
                                    total_expense += money_spent\
                                except:\
                                    pass\
        await save_to_cache(cache_key, total_expense)\
        return total_expense\
    except Exception as e:\
        write_log(f"\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1087 \u1086 \u1083 \u1091 \u1095 \u1077 \u1085 \u1080 \u1103  \u1088 \u1077 \u1082 \u1083 \u1072 \u1084 \u1085 \u1099 \u1093  \u1088 \u1072 \u1089 \u1093 \u1086 \u1076 \u1086 \u1074 : \{e\}")\
        return 0.0\
\
async def fetch_advertising_expense(date_from, date_to, progress_callback=None):\
    cache_key = f"fetch_advertising_expense_\{date_from\}_\{date_to\}"\
    cached = await get_from_cache(cache_key)\
    if cached is not None:\
        return cached\
\
    start_dt = datetime.datetime.strptime(date_from, "%Y-%m-%d")\
    end_dt = datetime.datetime.strptime(date_to, "%Y-%m-%d")\
    today = get_moscow_today()\
    if start_dt.date() > today:\
        return 0.0\
    if end_dt.date() > today:\
        end_dt = datetime.datetime.combine(today, datetime.time(23, 59, 59))\
\
    delta = (end_dt - start_dt).days\
    if delta <= API_MAX_DAYS_PER_REQUEST:\
        result = await fetch_advertising_expense_single(date_from, end_dt.strftime("%Y-%m-%d"))\
        await save_to_cache(cache_key, result)\
        if progress_callback:\
            await progress_callback("\uc0\u1056 \u1077 \u1082 \u1083 \u1072 \u1084 \u1072  \u1079 \u1072 \u1075 \u1088 \u1091 \u1078 \u1077 \u1085 \u1072 ", 100)\
        return result\
\
    total = 0.0\
    months = []\
    current = start_dt.replace(day=1)\
    while current <= end_dt:\
        month_start = current.strftime("%Y-%m-%d")\
        next_month = current.replace(day=28) + datetime.timedelta(days=4)\
        month_end = (next_month - datetime.timedelta(days=next_month.day)).strftime("%Y-%m-%d")\
        if month_end > end_dt.strftime("%Y-%m-%d"):\
            month_end = end_dt.strftime("%Y-%m-%d")\
        if current.date() > today:\
            break\
        months.append((month_start, month_end))\
        current = current.replace(day=28) + datetime.timedelta(days=4)\
        current = current.replace(day=1)\
    total_months = len(months)\
    for i, (m_start, m_end) in enumerate(months):\
        if progress_callback:\
            progress = int((i / total_months) * 100) if total_months > 0 else 100\
            await progress_callback(f"\uc0\u1047 \u1072 \u1075 \u1088 \u1091 \u1079 \u1082 \u1072  \u1088 \u1077 \u1082 \u1083 \u1072 \u1084 \u1099  \{m_start\}\'96\{m_end\}", progress)\
        total += await fetch_advertising_expense_single(m_start, m_end)\
    await save_to_cache(cache_key, total)\
    if progress_callback:\
        await progress_callback("\uc0\u1056 \u1077 \u1082 \u1083 \u1072 \u1084 \u1072  \u1079 \u1072 \u1075 \u1088 \u1091 \u1078 \u1077 \u1085 \u1072 ", 100)\
    return total}