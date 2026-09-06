import datetime
import io
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.dates import MonthLocator, DateFormatter

from config import MOSCOW_TZ
from api.seller import fetch_postings
from services.aggregator import aggregate_postings
from utils.validators import get_moscow_today

async def get_monthly_delivered_sum(year):
    """Возвращает список из 12 чисел – сумма доставленных заказов по месяцам за указанный год."""
    start_date = datetime.date(year, 1, 1).isoformat()
    end_date = datetime.date(year, 12, 31).isoformat()
    postings = await fetch_postings(start_date, end_date)
    daily_agg = aggregate_postings(postings, date_from=start_date, date_to=end_date)
    monthly = [0.0] * 12
    for date_str, vals in daily_agg.items():
        try:
            dt = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            month_idx = dt.month - 1
            monthly[month_idx] += vals.get("delivered_sum", 0.0)
        except:
            continue
    return monthly

async def generate_sales_chart(years_list):
    """
    Строит график динамики доставленных заказов (сумма) по месяцам для указанных лет.
    Возвращает BytesIO с изображением или None.
    """
    if not years_list:
        return None
    data = {}
    for year in years_list:
        data[year] = await get_monthly_delivered_sum(year)

    fig, ax = plt.subplots(figsize=(10, 6))
    months = [datetime.date(2000, m, 1) for m in range(1, 13)]
    for year, values in data.items():
        ax.plot(months, values, marker='o', label=str(year), linewidth=2)

    ax.set_title("Динамика доставленных заказов (сумма, руб.)", fontsize=14)
    ax.set_xlabel("Месяц")
    ax.set_ylabel("Сумма доставленных заказов, ₽")
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'.replace(',', ' ')))
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf

async def generate_product_chart_by_metric(sku, metric, years):
    """
    Строит график для одного товара по указанной метрике за указанные годы.
    metric: 'ordered_sum', 'ordered_units', 'delivered_sum', 'delivered_units',
            'canceled_sum', 'canceled_units', 'avg_check'
    years: список годов
    Возвращает BytesIO с изображением или None.
    """
    data = {}
    for year in years:
        start_date = datetime.date(year, 1, 1).isoformat()
        end_date = datetime.date(year, 12, 31).isoformat()
        postings = await fetch_postings(start_date, end_date)
        monthly_data = {m: 0.0 for m in range(12)}
        order_counts = {m: 0 for m in range(12)}
        for posting in postings:
            created_at = posting.get("created_at", "")
            if not created_at:
                continue
            try:
                dt = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                dt_msk = dt.astimezone(MOSCOW_TZ)
            except:
                continue
            if dt_msk.year != year:
                continue
            month_idx = dt_msk.month - 1
            products = posting.get("products", [])
            for product in products:
                if str(product.get("sku", "0")) != sku:
                    continue
                qty = int(product.get("quantity", 0))
                price_str = product.get("price", "0")
                try:
                    price = float(price_str)
                except:
                    price = 0.0
                status = posting.get("status", "")
                if metric == 'ordered_sum':
                    monthly_data[month_idx] += price * qty
                elif metric == 'ordered_units':
                    monthly_data[month_idx] += qty
                elif metric == 'delivered_sum' and status in ("delivered", "completed"):
                    monthly_data[month_idx] += price * qty
                elif metric == 'delivered_units' and status in ("delivered", "completed"):
                    monthly_data[month_idx] += qty
                elif metric == 'canceled_sum' and status in ("cancelled", "canceled"):
                    monthly_data[month_idx] += price * qty
                elif metric == 'canceled_units' and status in ("cancelled", "canceled"):
                    monthly_data[month_idx] += qty
                elif metric == 'avg_check':
                    monthly_data[month_idx] += price * qty
                    order_counts[month_idx] += 1
        if metric == 'avg_check':
            for m in range(12):
                if order_counts[m] > 0:
                    monthly_data[m] = monthly_data[m] / order_counts[m]
                else:
                    monthly_data[m] = 0.0
        data[year] = [monthly_data[i] for i in range(12)]

    if not any(any(v > 0 for v in vals) for vals in data.values()):
        return None

    fig, ax = plt.subplots(figsize=(10, 6))
    months = [datetime.date(2000, m, 1) for m in range(1, 13)]

    metric_labels = {
        'ordered_sum': 'Заказано (₽)',
        'ordered_units': 'Заказано (шт.)',
        'delivered_sum': 'Доставлено (₽)',
        'delivered_units': 'Доставлено (шт.)',
        'canceled_sum': 'Отменено (₽)',
        'canceled_units': 'Отменено (шт.)',
        'avg_check': 'Средний чек (₽)'
    }
    ylabel = metric_labels.get(metric, 'Значение')

    for year, values in data.items():
        ax.plot(months, values, marker='o', label=str(year), linewidth=2)

    ax.set_title(f"Динамика по товару (SKU: {sku})", fontsize=14)
    ax.set_xlabel("Месяц")
    ax.set_ylabel(ylabel)
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
    ax.grid(True, linestyle='--', alpha=0.7)
    ax.legend()
    if metric in ['ordered_sum', 'delivered_sum', 'canceled_sum', 'avg_check']:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x):,}'.replace(',', ' ')))
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    plt.close(fig)
    return buf
