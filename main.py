import asyncio
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    CallbackQueryHandler, ConversationHandler
)
from config import (
    TELEGRAM_BOT_TOKEN, VERSION,
    OZON_CLIENT_ID, OZON_API_KEY,
    OZON_PERFORMANCE_CLIENT_ID, OZON_PERFORMANCE_CLIENT_SECRET
)
from api.client import init_http_session, close_http_session
from bot.handlers.sales import (
    start, help_command, handle_main_menu, handle_sales_reports,
    handle_callback_query, dynamics_range_start, dynamics_range_end
)
from bot.handlers.products import (
    handle_products_reports, top_products_command, version_command,
    product_select_callback, product_metric_callback,
    product_period_callback, product_chart_interactive_callback,
    product_range_start, product_range_end,
    handle_product_date_callback, handle_product_period_callback
)
from bot.handlers.admin import (
    handle_admin_menu, add_manager_start, add_manager_input,
    add_manager_phone, remove_manager_start, remove_manager_input,
    cancel
)
from bot.states import (
    WAITING_DATE_SINGLE, WAITING_PERIOD_TYPE, WAITING_PERIOD_START,
    WAITING_PERIOD_END, WAITING_ADD_MANAGER, WAITING_REMOVE_MANAGER,
    WAITING_MANAGER_PHONE, WAITING_PERIOD_YEAR, WAITING_PERIOD_MONTH,
    WAITING_PERIOD_QUARTER, WAITING_YEAR_SELECT, WAITING_DYNAMICS_SELECT,
    WAITING_DYNAMICS_RANGE_START, WAITING_DYNAMICS_RANGE_END,
    WAITING_PRODUCT_DATE, WAITING_PRODUCT_PERIOD_TYPE,
    WAITING_PRODUCT_PERIOD_START, WAITING_PRODUCT_PERIOD_END,
    WAITING_PRODUCT_YEAR, WAITING_PRODUCT_MONTH, WAITING_PRODUCT_QUARTER,
    WAITING_PRODUCT_YEAR_SELECT, WAITING_PRODUCT_SELECT,
    WAITING_PRODUCT_METRIC, WAITING_PRODUCT_PERIOD_CHOICE,
    WAITING_PRODUCT_SINGLE_YEAR, WAITING_PRODUCT_RANGE_START,
    WAITING_PRODUCT_RANGE_END
)
from services.scheduler import scheduled_report
from utils.logger import write_log

async def post_init(app):
    await init_http_session()

async def post_shutdown(app):
    await close_http_session()

def main():
    write_log(f"🚀 Бот запускается (версия {VERSION})")
    if not all([OZON_CLIENT_ID, OZON_API_KEY, TELEGRAM_BOT_TOKEN]):
        write_log("❌ ОШИБКА: Не все переменные окружения установлены!")
        return
    if not OZON_PERFORMANCE_CLIENT_ID or not OZON_PERFORMANCE_CLIENT_SECRET:
        write_log("⚠️ ВНИМАНИЕ: OZON_PERFORMANCE_CLIENT_ID или CLIENT_SECRET не заданы. Рекламные расходы не будут отображаться.")

    application = (Application.builder()
                   .token(TELEGRAM_BOT_TOKEN)
                   .connect_timeout(30.0)
                   .read_timeout(30.0)
                   .write_timeout(30.0)
                   .post_init(post_init)
                   .post_shutdown(post_shutdown)
                   .build())

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("top", top_products_command))
    application.add_handler(CommandHandler("version", version_command))
    application.add_handler(CommandHandler("help", help_command))

    # Обработчики главного меню и подменю
    application.add_handler(MessageHandler(
        filters.Text(["📊 Отчёт по продажам", "📦 Отчёт по товарам", "⚙️ Администрирование", "📖 Справка"]),
        handle_main_menu
    ))
    application.add_handler(MessageHandler(
        filters.Text(["📅 Продажи за сегодня", "📆 Выбрать дату", "📊 Выбрать период", "📈 Динамика продаж", "🔙 Назад"]),
        handle_sales_reports
    ))
    application.add_handler(MessageHandler(
        filters.Text(["📅 Топ товаров за сегодня", "📆 Выбрать дату (товары)", "📊 Выбрать период (товары)", "📈 Динамика по товару", "🔙 Назад"]),
        handle_products_reports
    ))
    application.add_handler(MessageHandler(
        filters.Text(["📋 Список менеджеров", "🔙 Назад"]),
        handle_admin_menu
    ))

    # ConversationHandler для продаж (выбор даты)
    conv_date = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("📆 Выбрать дату"), handle_sales_reports)],
        states={WAITING_DATE_SINGLE: [CallbackQueryHandler(handle_callback_query)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    # ConversationHandler для продаж (выбор периода)
    conv_period = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("📊 Выбрать период"), handle_sales_reports)],
        states={
            WAITING_PERIOD_TYPE: [CallbackQueryHandler(handle_callback_query)],
            WAITING_PERIOD_START: [CallbackQueryHandler(handle_callback_query)],
            WAITING_PERIOD_END: [CallbackQueryHandler(handle_callback_query)],
            WAITING_PERIOD_YEAR: [CallbackQueryHandler(handle_callback_query)],
            WAITING_PERIOD_MONTH: [CallbackQueryHandler(handle_callback_query)],
            WAITING_PERIOD_QUARTER: [CallbackQueryHandler(handle_callback_query)],
            WAITING_YEAR_SELECT: [CallbackQueryHandler(handle_callback_query)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    # ConversationHandler для динамики продаж (диапазон лет)
    conv_dynamics = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("📈 Динамика продаж"), handle_sales_reports)],
        states={
            WAITING_DYNAMICS_SELECT: [CallbackQueryHandler(handle_callback_query)],
            WAITING_DYNAMICS_RANGE_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, dynamics_range_start)],
            WAITING_DYNAMICS_RANGE_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, dynamics_range_end)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler для товаров (выбор даты)
    conv_product_date = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("📆 Выбрать дату (товары)"), handle_products_reports)],
        states={WAITING_PRODUCT_DATE: [CallbackQueryHandler(handle_product_date_callback)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    # ConversationHandler для товаров (выбор периода)
    conv_product_period = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("📊 Выбрать период (товары)"), handle_products_reports)],
        states={
            WAITING_PRODUCT_PERIOD_TYPE: [CallbackQueryHandler(handle_product_period_callback)],
            WAITING_PRODUCT_PERIOD_START: [CallbackQueryHandler(handle_product_period_callback)],
            WAITING_PRODUCT_PERIOD_END: [CallbackQueryHandler(handle_product_period_callback)],
            WAITING_PRODUCT_YEAR: [CallbackQueryHandler(handle_product_period_callback)],
            WAITING_PRODUCT_MONTH: [CallbackQueryHandler(handle_product_period_callback)],
            WAITING_PRODUCT_QUARTER: [CallbackQueryHandler(handle_product_period_callback)],
            WAITING_PRODUCT_YEAR_SELECT: [CallbackQueryHandler(handle_product_period_callback)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    # ConversationHandler для динамики по товару
    conv_product_chart = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("📈 Динамика по товару"), handle_products_reports)],
        states={
            WAITING_PRODUCT_SELECT: [CallbackQueryHandler(product_select_callback)],
            WAITING_PRODUCT_METRIC: [CallbackQueryHandler(product_metric_callback)],
            WAITING_PRODUCT_PERIOD_CHOICE: [CallbackQueryHandler(product_period_callback)],
            WAITING_PRODUCT_SINGLE_YEAR: [CallbackQueryHandler(product_chart_interactive_callback)],
            WAITING_PRODUCT_RANGE_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_range_start)],
            WAITING_PRODUCT_RANGE_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_range_end)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    # ConversationHandler для администрирования (добавление менеджера)
    conv_add = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("➕ Добавить менеджера"), add_manager_start)],
        states={
            WAITING_ADD_MANAGER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_manager_input)],
            WAITING_MANAGER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_manager_phone)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    # ConversationHandler для администрирования (удаление менеджера)
    conv_remove = ConversationHandler(
        entry_points=[MessageHandler(filters.Text("➖ Удалить менеджера"), remove_manager_start)],
        states={WAITING_REMOVE_MANAGER: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_manager_input)]},
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv_date)
    application.add_handler(conv_period)
    application.add_handler(conv_dynamics)
    application.add_handler(conv_product_date)
    application.add_handler(conv_product_period)
    application.add_handler(conv_product_chart)
    application.add_handler(conv_add)
    application.add_handler(conv_remove)

    # Общий обработчик callback_query (для продаж и товаров, которые не вошли в диалоги)
    application.add_handler(CallbackQueryHandler(handle_callback_query))

    # Планировщик
    job_queue = application.job_queue
    if job_queue:
        job_queue.run_repeating(scheduled_report, interval=3600, first=0)
        write_log("✅ Планировщик запущен (отправка в 10:00 и 22:00 МСК).")
    else:
        write_log("⚠️ JobQueue недоступен.")

    write_log("🚀 Бот готов.")
    application.run_polling(allowed_updates=Update.ALL_TYPES, timeout=30)

if __name__ == "__main__":
    main()
