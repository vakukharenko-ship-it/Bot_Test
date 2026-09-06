import datetime
from config import MOSCOW_TZ
from utils.logger import write_log
from utils.managers import load_managers
from services.formatter import format_combined_metrics_with_deltas

async def scheduled_report(context):
    """
    Планировщик: отправляет отчёт менеджерам в 10:00 и 22:00 МСК.
    В 10:00 – отчёт с блоком «Вчера», в 22:00 – без.
    """
    moscow_tz = MOSCOW_TZ
    now = datetime.datetime.now(moscow_tz)
    hour = now.hour
    if hour not in (10, 22):
        return
    include_yesterday = (hour == 10)
    report = await format_combined_metrics_with_deltas(include_yesterday=include_yesterday, progress_callback=None)
    managers = load_managers()
    if not managers:
        return
    for m in managers:
        try:
            await context.bot.send_message(chat_id=m['id'], text=report, parse_mode="Markdown")
        except Exception as e:
            write_log(f"Ошибка отправки {m['id']}: {e}")
