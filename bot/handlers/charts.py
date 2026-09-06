{\rtf1\ansi\ansicpg1251\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw3288\paperh2267\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import datetime\
import io\
import matplotlib.pyplot as plt\
import matplotlib.dates as mdates\
from matplotlib.dates import MonthLocator, DateFormatter\
\
from config import MOSCOW_TZ\
from api.seller import fetch_postings\
from services.aggregator import aggregate_postings\
from utils.validators import get_moscow_today\
\
async def get_monthly_delivered_sum(year):\
    """\uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1097 \u1072 \u1077 \u1090  \u1089 \u1087 \u1080 \u1089 \u1086 \u1082  \u1080 \u1079  12 \u1095 \u1080 \u1089 \u1077 \u1083  \'96 \u1089 \u1091 \u1084 \u1084 \u1072  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074  \u1087 \u1086  \u1084 \u1077 \u1089 \u1103 \u1094 \u1072 \u1084  \u1079 \u1072  \u1091 \u1082 \u1072 \u1079 \u1072 \u1085 \u1085 \u1099 \u1081  \u1075 \u1086 \u1076 ."""\
    start_date = datetime.date(year, 1, 1).isoformat()\
    end_date = datetime.date(year, 12, 31).isoformat()\
    postings = await fetch_postings(start_date, end_date)\
    daily_agg = aggregate_postings(postings, date_from=start_date, date_to=end_date)\
    monthly = [0.0] * 12\
    for date_str, vals in daily_agg.items():\
        try:\
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")\
            month_idx = dt.month - 1\
            monthly[month_idx] += vals.get("delivered_sum", 0.0)\
        except:\
            continue\
    return monthly\
\
async def generate_sales_chart(years_list):\
    """\
    \uc0\u1057 \u1090 \u1088 \u1086 \u1080 \u1090  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082  \u1076 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1080  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074  (\u1089 \u1091 \u1084 \u1084 \u1072 ) \u1087 \u1086  \u1084 \u1077 \u1089 \u1103 \u1094 \u1072 \u1084  \u1076 \u1083 \u1103  \u1091 \u1082 \u1072 \u1079 \u1072 \u1085 \u1085 \u1099 \u1093  \u1083 \u1077 \u1090 .\
    \uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1097 \u1072 \u1077 \u1090  BytesIO \u1089  \u1080 \u1079 \u1086 \u1073 \u1088 \u1072 \u1078 \u1077 \u1085 \u1080 \u1077 \u1084  \u1080 \u1083 \u1080  None.\
    """\
    if not years_list:\
        return None\
    data = \{\}\
    for year in years_list:\
        data[year] = await get_monthly_delivered_sum(year)\
\
    fig, ax = plt.subplots(figsize=(10, 6))\
    months = [datetime.date(2000, m, 1) for m in range(1, 13)]\
    for year, values in data.items():\
        ax.plot(months, values, marker='o', label=str(year), linewidth=2)\
\
    ax.set_title("\uc0\u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074  (\u1089 \u1091 \u1084 \u1084 \u1072 , \u1088 \u1091 \u1073 .)", fontsize=14)\
    ax.set_xlabel("\uc0\u1052 \u1077 \u1089 \u1103 \u1094 ")\
    ax.set_ylabel("\uc0\u1057 \u1091 \u1084 \u1084 \u1072  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074 , \u8381 ")\
    ax.xaxis.set_major_locator(mdates.MonthLocator())\
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))\
    ax.grid(True, linestyle='--', alpha=0.7)\
    ax.legend()\
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'\{int(x):,\}'.replace(',', ' ')))\
    plt.tight_layout()\
\
    buf = io.BytesIO()\
    plt.savefig(buf, format='png', dpi=100)\
    buf.seek(0)\
    plt.close(fig)\
    return buf\
\
async def generate_product_chart_by_metric(sku, metric, years):\
    """\
    \uc0\u1057 \u1090 \u1088 \u1086 \u1080 \u1090  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082  \u1076 \u1083 \u1103  \u1086 \u1076 \u1085 \u1086 \u1075 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1087 \u1086  \u1091 \u1082 \u1072 \u1079 \u1072 \u1085 \u1085 \u1086 \u1081  \u1084 \u1077 \u1090 \u1088 \u1080 \u1082 \u1077  \u1079 \u1072  \u1091 \u1082 \u1072 \u1079 \u1072 \u1085 \u1085 \u1099 \u1077  \u1075 \u1086 \u1076 \u1099 .\
    metric: 'ordered_sum', 'ordered_units', 'delivered_sum', 'delivered_units',\
            'canceled_sum', 'canceled_units', 'avg_check'\
    years: \uc0\u1089 \u1087 \u1080 \u1089 \u1086 \u1082  \u1075 \u1086 \u1076 \u1086 \u1074 \
    \uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1097 \u1072 \u1077 \u1090  BytesIO \u1089  \u1080 \u1079 \u1086 \u1073 \u1088 \u1072 \u1078 \u1077 \u1085 \u1080 \u1077 \u1084  \u1080 \u1083 \u1080  None.\
    """\
    data = \{\}\
    for year in years:\
        start_date = datetime.date(year, 1, 1).isoformat()\
        end_date = datetime.date(year, 12, 31).isoformat()\
        postings = await fetch_postings(start_date, end_date)\
        monthly_data = \{m: 0.0 for m in range(12)\}\
        order_counts = \{m: 0 for m in range(12)\}\
        for posting in postings:\
            created_at = posting.get("created_at", "")\
            if not created_at:\
                continue\
            try:\
                dt = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))\
                dt_msk = dt.astimezone(MOSCOW_TZ)\
            except:\
                continue\
            if dt_msk.year != year:\
                continue\
            month_idx = dt_msk.month - 1\
            products = posting.get("products", [])\
            for product in products:\
                if str(product.get("sku", "0")) != sku:\
                    continue\
                qty = int(product.get("quantity", 0))\
                price_str = product.get("price", "0")\
                try:\
                    price = float(price_str)\
                except:\
                    price = 0.0\
                status = posting.get("status", "")\
                if metric == 'ordered_sum':\
                    monthly_data[month_idx] += price * qty\
                elif metric == 'ordered_units':\
                    monthly_data[month_idx] += qty\
                elif metric == 'delivered_sum' and status in ("delivered", "completed"):\
                    monthly_data[month_idx] += price * qty\
                elif metric == 'delivered_units' and status in ("delivered", "completed"):\
                    monthly_data[month_idx] += qty\
                elif metric == 'canceled_sum' and status in ("cancelled", "canceled"):\
                    monthly_data[month_idx] += price * qty\
                elif metric == 'canceled_units' and status in ("cancelled", "canceled"):\
                    monthly_data[month_idx] += qty\
                elif metric == 'avg_check':\
                    monthly_data[month_idx] += price * qty\
                    order_counts[month_idx] += 1\
        if metric == 'avg_check':\
            for m in range(12):\
                if order_counts[m] > 0:\
                    monthly_data[m] = monthly_data[m] / order_counts[m]\
                else:\
                    monthly_data[m] = 0.0\
        data[year] = [monthly_data[i] for i in range(12)]\
\
    if not any(any(v > 0 for v in vals) for vals in data.values()):\
        return None\
\
    fig, ax = plt.subplots(figsize=(10, 6))\
    months = [datetime.date(2000, m, 1) for m in range(1, 13)]\
\
    metric_labels = \{\
        'ordered_sum': '\uc0\u1047 \u1072 \u1082 \u1072 \u1079 \u1072 \u1085 \u1086  (\u8381 )',\
        'ordered_units': '\uc0\u1047 \u1072 \u1082 \u1072 \u1079 \u1072 \u1085 \u1086  (\u1096 \u1090 .)',\
        'delivered_sum': '\uc0\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1086  (\u8381 )',\
        'delivered_units': '\uc0\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1086  (\u1096 \u1090 .)',\
        'canceled_sum': '\uc0\u1054 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086  (\u8381 )',\
        'canceled_units': '\uc0\u1054 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086  (\u1096 \u1090 .)',\
        'avg_check': '\uc0\u1057 \u1088 \u1077 \u1076 \u1085 \u1080 \u1081  \u1095 \u1077 \u1082  (\u8381 )'\
    \}\
    ylabel = metric_labels.get(metric, '\uc0\u1047 \u1085 \u1072 \u1095 \u1077 \u1085 \u1080 \u1077 ')\
\
    for year, values in data.items():\
        ax.plot(months, values, marker='o', label=str(year), linewidth=2)\
\
    ax.set_title(f"\uc0\u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1091  (SKU: \{sku\})", fontsize=14)\
    ax.set_xlabel("\uc0\u1052 \u1077 \u1089 \u1103 \u1094 ")\
    ax.set_ylabel(ylabel)\
    ax.xaxis.set_major_locator(mdates.MonthLocator())\
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))\
    ax.grid(True, linestyle='--', alpha=0.7)\
    ax.legend()\
    if metric in ['ordered_sum', 'delivered_sum', 'canceled_sum', 'avg_check']:\
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'\{int(x):,\}'.replace(',', ' ')))\
    plt.tight_layout()\
\
    buf = io.BytesIO()\
    plt.savefig(buf, format='png', dpi=100)\
    buf.seek(0)\
    plt.close(fig)\
    return buf}