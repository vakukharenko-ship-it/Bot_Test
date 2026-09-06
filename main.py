{\rtf1\ansi\ansicpg1251\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw3288\paperh2267\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 ```python\
import asyncio\
from telegram import Update\
from telegram.ext import (\
    Application, CommandHandler, MessageHandler, filters,\
    CallbackQueryHandler, ConversationHandler\
)\
from config import (\
    TELEGRAM_BOT_TOKEN, VERSION,\
    OZON_CLIENT_ID, OZON_API_KEY,\
    OZON_PERFORMANCE_CLIENT_ID, OZON_PERFORMANCE_CLIENT_SECRET\
)\
from api.client import init_http_session, close_http_session\
from bot.handlers.sales import (\
    start, help_command, handle_main_menu, handle_sales_reports,\
    handle_callback_query, dynamics_range_start, dynamics_range_end\
)\
from bot.handlers.products import (\
    handle_products_reports, top_products_command, version_command,\
    product_select_callback, product_metric_callback,\
    product_period_callback, product_chart_interactive_callback,\
    product_range_start, product_range_end,\
    handle_product_date_callback, handle_product_period_callback\
)\
from bot.handlers.admin import (\
    handle_admin_menu, add_manager_start, add_manager_input,\
    add_manager_phone, remove_manager_start, remove_manager_input,\
    cancel\
)\
from bot.states import (\
    WAITING_DATE_SINGLE, WAITING_PERIOD_TYPE, WAITING_PERIOD_START,\
    WAITING_PERIOD_END, WAITING_ADD_MANAGER, WAITING_REMOVE_MANAGER,\
    WAITING_MANAGER_PHONE, WAITING_PERIOD_YEAR, WAITING_PERIOD_MONTH,\
    WAITING_PERIOD_QUARTER, WAITING_YEAR_SELECT, WAITING_DYNAMICS_SELECT,\
    WAITING_DYNAMICS_RANGE_START, WAITING_DYNAMICS_RANGE_END,\
    WAITING_PRODUCT_DATE, WAITING_PRODUCT_PERIOD_TYPE,\
    WAITING_PRODUCT_PERIOD_START, WAITING_PRODUCT_PERIOD_END,\
    WAITING_PRODUCT_YEAR, WAITING_PRODUCT_MONTH, WAITING_PRODUCT_QUARTER,\
    WAITING_PRODUCT_YEAR_SELECT, WAITING_PRODUCT_SELECT,\
    WAITING_PRODUCT_METRIC, WAITING_PRODUCT_PERIOD_CHOICE,\
    WAITING_PRODUCT_SINGLE_YEAR, WAITING_PRODUCT_RANGE_START,\
    WAITING_PRODUCT_RANGE_END\
)\
from services.scheduler import scheduled_report\
from utils.logger import write_log\
\
async def post_init(app):\
    await init_http_session()\
\
async def post_shutdown(app):\
    await close_http_session()\
\
def main():\
    write_log(f"\uc0\u55357 \u56960  \u1041 \u1086 \u1090  \u1079 \u1072 \u1087 \u1091 \u1089 \u1082 \u1072 \u1077 \u1090 \u1089 \u1103  (\u1074 \u1077 \u1088 \u1089 \u1080 \u1103  \{VERSION\})")\
    if not all([OZON_CLIENT_ID, OZON_API_KEY, TELEGRAM_BOT_TOKEN]):\
        write_log("\uc0\u10060  \u1054 \u1064 \u1048 \u1041 \u1050 \u1040 : \u1053 \u1077  \u1074 \u1089 \u1077  \u1087 \u1077 \u1088 \u1077 \u1084 \u1077 \u1085 \u1085 \u1099 \u1077  \u1086 \u1082 \u1088 \u1091 \u1078 \u1077 \u1085 \u1080 \u1103  \u1091 \u1089 \u1090 \u1072 \u1085 \u1086 \u1074 \u1083 \u1077 \u1085 \u1099 !")\
        return\
    if not OZON_PERFORMANCE_CLIENT_ID or not OZON_PERFORMANCE_CLIENT_SECRET:\
        write_log("\uc0\u9888 \u65039  \u1042 \u1053 \u1048 \u1052 \u1040 \u1053 \u1048 \u1045 : OZON_PERFORMANCE_CLIENT_ID \u1080 \u1083 \u1080  CLIENT_SECRET \u1085 \u1077  \u1079 \u1072 \u1076 \u1072 \u1085 \u1099 . \u1056 \u1077 \u1082 \u1083 \u1072 \u1084 \u1085 \u1099 \u1077  \u1088 \u1072 \u1089 \u1093 \u1086 \u1076 \u1099  \u1085 \u1077  \u1073 \u1091 \u1076 \u1091 \u1090  \u1086 \u1090 \u1086 \u1073 \u1088 \u1072 \u1078 \u1072 \u1090 \u1100 \u1089 \u1103 .")\
\
    application = (Application.builder()\
                   .token(TELEGRAM_BOT_TOKEN)\
                   .connect_timeout(30.0)\
                   .read_timeout(30.0)\
                   .write_timeout(30.0)\
                   .post_init(post_init)\
                   .post_shutdown(post_shutdown)\
                   .build())\
\
    # \uc0\u1056 \u1077 \u1075 \u1080 \u1089 \u1090 \u1088 \u1072 \u1094 \u1080 \u1103  \u1082 \u1086 \u1084 \u1072 \u1085 \u1076 \
    application.add_handler(CommandHandler("start", start))\
    application.add_handler(CommandHandler("top", top_products_command))\
    application.add_handler(CommandHandler("version", version_command))\
    application.add_handler(CommandHandler("help", help_command))\
\
    # \uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1095 \u1080 \u1082 \u1080  \u1075 \u1083 \u1072 \u1074 \u1085 \u1086 \u1075 \u1086  \u1084 \u1077 \u1085 \u1102  \u1080  \u1087 \u1086 \u1076 \u1084 \u1077 \u1085 \u1102 \
    application.add_handler(MessageHandler(\
        filters.Text(["\uc0\u55357 \u56522  \u1054 \u1090 \u1095 \u1105 \u1090  \u1087 \u1086  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1072 \u1084 ", "\u55357 \u56550  \u1054 \u1090 \u1095 \u1105 \u1090  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 \u1084 ", "\u9881 \u65039  \u1040 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1080 \u1077 ", "\u55357 \u56534  \u1057 \u1087 \u1088 \u1072 \u1074 \u1082 \u1072 "]),\
        handle_main_menu\
    ))\
    application.add_handler(MessageHandler(\
        filters.Text(["\uc0\u55357 \u56517  \u1055 \u1088 \u1086 \u1076 \u1072 \u1078 \u1080  \u1079 \u1072  \u1089 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 ", "\u55357 \u56518  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1076 \u1072 \u1090 \u1091 ", "\u55357 \u56522  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 ", "\u55357 \u56520  \u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 ", "\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 "]),\
        handle_sales_reports\
    ))\
    application.add_handler(MessageHandler(\
        filters.Text(["\uc0\u55357 \u56517  \u1058 \u1086 \u1087  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  \u1079 \u1072  \u1089 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 ", "\u55357 \u56518  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1076 \u1072 \u1090 \u1091  (\u1090 \u1086 \u1074 \u1072 \u1088 \u1099 )", "\u55357 \u56522  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076  (\u1090 \u1086 \u1074 \u1072 \u1088 \u1099 )", "\u55357 \u56520  \u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1091 ", "\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 "]),\
        handle_products_reports\
    ))\
    application.add_handler(MessageHandler(\
        filters.Text(["\uc0\u55357 \u56523  \u1057 \u1087 \u1080 \u1089 \u1086 \u1082  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1086 \u1074 ", "\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 "]),\
        handle_admin_menu\
    ))\
\
    # ConversationHandler \uc0\u1076 \u1083 \u1103  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078  (\u1074 \u1099 \u1073 \u1086 \u1088  \u1076 \u1072 \u1090 \u1099 )\
    conv_date = ConversationHandler(\
        entry_points=[MessageHandler(filters.Text("\uc0\u55357 \u56518  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1076 \u1072 \u1090 \u1091 "), handle_sales_reports)],\
        states=\{WAITING_DATE_SINGLE: [CallbackQueryHandler(handle_callback_query)]\},\
        fallbacks=[CommandHandler("cancel", cancel)],\
    )\
    # ConversationHandler \uc0\u1076 \u1083 \u1103  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078  (\u1074 \u1099 \u1073 \u1086 \u1088  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1072 )\
    conv_period = ConversationHandler(\
        entry_points=[MessageHandler(filters.Text("\uc0\u55357 \u56522  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 "), handle_sales_reports)],\
        states=\{\
            WAITING_PERIOD_TYPE: [CallbackQueryHandler(handle_callback_query)],\
            WAITING_PERIOD_START: [CallbackQueryHandler(handle_callback_query)],\
            WAITING_PERIOD_END: [CallbackQueryHandler(handle_callback_query)],\
            WAITING_PERIOD_YEAR: [CallbackQueryHandler(handle_callback_query)],\
            WAITING_PERIOD_MONTH: [CallbackQueryHandler(handle_callback_query)],\
            WAITING_PERIOD_QUARTER: [CallbackQueryHandler(handle_callback_query)],\
            WAITING_YEAR_SELECT: [CallbackQueryHandler(handle_callback_query)],\
        \},\
        fallbacks=[CommandHandler("cancel", cancel)],\
    )\
    # ConversationHandler \uc0\u1076 \u1083 \u1103  \u1076 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1080  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078  (\u1076 \u1080 \u1072 \u1087 \u1072 \u1079 \u1086 \u1085  \u1083 \u1077 \u1090 )\
    conv_dynamics = ConversationHandler(\
        entry_points=[MessageHandler(filters.Text("\uc0\u55357 \u56520  \u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 "), handle_sales_reports)],\
        states=\{\
            WAITING_DYNAMICS_SELECT: [CallbackQueryHandler(handle_callback_query)],\
            WAITING_DYNAMICS_RANGE_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, dynamics_range_start)],\
            WAITING_DYNAMICS_RANGE_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, dynamics_range_end)],\
        \},\
        fallbacks=[CommandHandler("cancel", cancel)],\
    )\
\
    # ConversationHandler \uc0\u1076 \u1083 \u1103  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  (\u1074 \u1099 \u1073 \u1086 \u1088  \u1076 \u1072 \u1090 \u1099 )\
    conv_product_date = ConversationHandler(\
        entry_points=[MessageHandler(filters.Text("\uc0\u55357 \u56518  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1076 \u1072 \u1090 \u1091  (\u1090 \u1086 \u1074 \u1072 \u1088 \u1099 )"), handle_products_reports)],\
        states=\{WAITING_PRODUCT_DATE: [CallbackQueryHandler(handle_product_date_callback)]\},\
        fallbacks=[CommandHandler("cancel", cancel)],\
    )\
    # ConversationHandler \uc0\u1076 \u1083 \u1103  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  (\u1074 \u1099 \u1073 \u1086 \u1088  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1072 )\
    conv_product_period = ConversationHandler(\
        entry_points=[MessageHandler(filters.Text("\uc0\u55357 \u56522  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076  (\u1090 \u1086 \u1074 \u1072 \u1088 \u1099 )"), handle_products_reports)],\
        states=\{\
            WAITING_PRODUCT_PERIOD_TYPE: [CallbackQueryHandler(handle_product_period_callback)],\
            WAITING_PRODUCT_PERIOD_START: [CallbackQueryHandler(handle_product_period_callback)],\
            WAITING_PRODUCT_PERIOD_END: [CallbackQueryHandler(handle_product_period_callback)],\
            WAITING_PRODUCT_YEAR: [CallbackQueryHandler(handle_product_period_callback)],\
            WAITING_PRODUCT_MONTH: [CallbackQueryHandler(handle_product_period_callback)],\
            WAITING_PRODUCT_QUARTER: [CallbackQueryHandler(handle_product_period_callback)],\
            WAITING_PRODUCT_YEAR_SELECT: [CallbackQueryHandler(handle_product_period_callback)],\
        \},\
        fallbacks=[CommandHandler("cancel", cancel)],\
    )\
    # ConversationHandler \uc0\u1076 \u1083 \u1103  \u1076 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1080  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1091 \
    conv_product_chart = ConversationHandler(\
        entry_points=[MessageHandler(filters.Text("\uc0\u55357 \u56520  \u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1091 "), handle_products_reports)],\
        states=\{\
            WAITING_PRODUCT_SELECT: [CallbackQueryHandler(product_select_callback)],\
            WAITING_PRODUCT_METRIC: [CallbackQueryHandler(product_metric_callback)],\
            WAITING_PRODUCT_PERIOD_CHOICE: [CallbackQueryHandler(product_period_callback)],\
            WAITING_PRODUCT_SINGLE_YEAR: [CallbackQueryHandler(product_chart_interactive_callback)],\
            WAITING_PRODUCT_RANGE_START: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_range_start)],\
            WAITING_PRODUCT_RANGE_END: [MessageHandler(filters.TEXT & ~filters.COMMAND, product_range_end)],\
        \},\
        fallbacks=[CommandHandler("cancel", cancel)],\
    )\
\
    # ConversationHandler \uc0\u1076 \u1083 \u1103  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1080 \u1103  (\u1076 \u1086 \u1073 \u1072 \u1074 \u1083 \u1077 \u1085 \u1080 \u1077  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072 )\
    conv_add = ConversationHandler(\
        entry_points=[MessageHandler(filters.Text("\uc0\u10133  \u1044 \u1086 \u1073 \u1072 \u1074 \u1080 \u1090 \u1100  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072 "), add_manager_start)],\
        states=\{\
            WAITING_ADD_MANAGER: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_manager_input)],\
            WAITING_MANAGER_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_manager_phone)],\
        \},\
        fallbacks=[CommandHandler("cancel", cancel)],\
    )\
    # ConversationHandler \uc0\u1076 \u1083 \u1103  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1080 \u1103  (\u1091 \u1076 \u1072 \u1083 \u1077 \u1085 \u1080 \u1077  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072 )\
    conv_remove = ConversationHandler(\
        entry_points=[MessageHandler(filters.Text("\uc0\u10134  \u1059 \u1076 \u1072 \u1083 \u1080 \u1090 \u1100  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072 "), remove_manager_start)],\
        states=\{WAITING_REMOVE_MANAGER: [MessageHandler(filters.TEXT & ~filters.COMMAND, remove_manager_input)]\},\
        fallbacks=[CommandHandler("cancel", cancel)],\
    )\
\
    application.add_handler(conv_date)\
    application.add_handler(conv_period)\
    application.add_handler(conv_dynamics)\
    application.add_handler(conv_product_date)\
    application.add_handler(conv_product_period)\
    application.add_handler(conv_product_chart)\
    application.add_handler(conv_add)\
    application.add_handler(conv_remove)\
\
    # \uc0\u1054 \u1073 \u1097 \u1080 \u1081  \u1086 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1095 \u1080 \u1082  callback_query (\u1076 \u1083 \u1103  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078  \u1080  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074 , \u1082 \u1086 \u1090 \u1086 \u1088 \u1099 \u1077  \u1085 \u1077  \u1074 \u1086 \u1096 \u1083 \u1080  \u1074  \u1076 \u1080 \u1072 \u1083 \u1086 \u1075 \u1080 )\
    application.add_handler(CallbackQueryHandler(handle_callback_query))\
\
    # \uc0\u1055 \u1083 \u1072 \u1085 \u1080 \u1088 \u1086 \u1074 \u1097 \u1080 \u1082 \
    job_queue = application.job_queue\
    if job_queue:\
        job_queue.run_repeating(scheduled_report, interval=3600, first=0)\
        write_log("\uc0\u9989  \u1055 \u1083 \u1072 \u1085 \u1080 \u1088 \u1086 \u1074 \u1097 \u1080 \u1082  \u1079 \u1072 \u1087 \u1091 \u1097 \u1077 \u1085  (\u1086 \u1090 \u1087 \u1088 \u1072 \u1074 \u1082 \u1072  \u1074  10:00 \u1080  22:00 \u1052 \u1057 \u1050 ).")\
    else:\
        write_log("\uc0\u9888 \u65039  JobQueue \u1085 \u1077 \u1076 \u1086 \u1089 \u1090 \u1091 \u1087 \u1077 \u1085 .")\
\
    write_log("\uc0\u55357 \u56960  \u1041 \u1086 \u1090  \u1075 \u1086 \u1090 \u1086 \u1074 .")\
    application.run_polling(allowed_updates=Update.ALL_TYPES, timeout=30)\
\
if __name__ == "__main__":\
    main()\
```}