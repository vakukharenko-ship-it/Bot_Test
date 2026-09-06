{\rtf1\ansi\ansicpg1251\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw3288\paperh2267\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import datetime\
import re\
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton\
from telegram.ext import ContextTypes, ConversationHandler, CallbackQueryHandler\
from config import VERSION, ADMIN_CHAT_ID\
from utils.logger import write_log\
from utils.validators import (\
    validate_date, validate_period, create_calendar,\
    get_moscow_today, get_current_time_msk\
)\
from utils.managers import (\
    load_managers, is_admin, is_manager, has_access,\
    get_manager_info, add_manager, remove_manager\
)\
from services.formatter import (\
    format_combined_metrics_with_deltas,\
    format_single_metrics,\
    format_period_comparison_metrics\
)\
from api.seller import fetch_postings, fetch_finance_transactions\
from api.performance import fetch_advertising_expense\
from services.aggregator import aggregate_postings, aggregate_finance_expenses\
from bot.keyboards import (\
    main_admin_keyboard, main_user_keyboard,\
    sales_reports_keyboard, admin_keyboard\
)\
from bot.states import (\
    WAITING_DATE_SINGLE, WAITING_PERIOD_TYPE,\
    WAITING_PERIOD_START, WAITING_PERIOD_END,\
    WAITING_PERIOD_YEAR, WAITING_PERIOD_MONTH,\
    WAITING_PERIOD_QUARTER, WAITING_YEAR_SELECT,\
    WAITING_DYNAMICS_SELECT, WAITING_DYNAMICS_RANGE_START,\
    WAITING_DYNAMICS_RANGE_END,\
    # \uc0\u1057 \u1086 \u1089 \u1090 \u1086 \u1103 \u1085 \u1080 \u1103  \u1076 \u1083 \u1103  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  \u1085 \u1077  \u1080 \u1084 \u1087 \u1086 \u1088 \u1090 \u1080 \u1088 \u1091 \u1077 \u1084 , \u1086 \u1085 \u1080  \u1085 \u1077  \u1085 \u1091 \u1078 \u1085 \u1099  \u1079 \u1076 \u1077 \u1089 \u1100 \
)\
\
# ---------- \uc0\u1042 \u1057 \u1055 \u1054 \u1052 \u1054 \u1043 \u1040 \u1058 \u1045 \u1051 \u1068 \u1053 \u1067 \u1045  \u1060 \u1059 \u1053 \u1050 \u1062 \u1048 \u1048  ----------\
def get_greeting(name):\
    moscow_tz = datetime.timezone(datetime.timedelta(hours=3))\
    now = datetime.datetime.now(moscow_tz)\
    hour = now.hour\
    if 5 <= hour < 12:\
        part = "\uc0\u1044 \u1086 \u1073 \u1088 \u1086 \u1077  \u1091 \u1090 \u1088 \u1086 "\
    elif 12 <= hour < 18:\
        part = "\uc0\u1044 \u1086 \u1073 \u1088 \u1099 \u1081  \u1076 \u1077 \u1085 \u1100 "\
    elif 18 <= hour < 24:\
        part = "\uc0\u1044 \u1086 \u1073 \u1088 \u1099 \u1081  \u1074 \u1077 \u1095 \u1077 \u1088 "\
    else:\
        part = "\uc0\u1044 \u1086 \u1073 \u1088 \u1086 \u1081  \u1085 \u1086 \u1095 \u1080 "\
    if name:\
        return f"\{part\}, \{name\}!"\
    else:\
        return f"\{part\}, \uc0\u1091 \u1074 \u1072 \u1078 \u1072 \u1077 \u1084 \u1099 \u1081  \u1087 \u1086 \u1083 \u1100 \u1079 \u1086 \u1074 \u1072 \u1090 \u1077 \u1083 \u1100 !"\
\
# ---------- \uc0\u1054 \u1041 \u1056 \u1040 \u1041 \u1054 \u1058 \u1063 \u1048 \u1050 \u1048  \u1050 \u1054 \u1052 \u1040 \u1053 \u1044  ----------\
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    chat_id = update.effective_chat.id\
    user = update.effective_user\
    if is_admin(chat_id):\
        name = user.first_name if user.first_name else ""\
        greeting = get_greeting(name)\
        await update.message.reply_text(\
            f"\{greeting\}\\n\\n\uc0\u55358 \u56598  \u1042 \u1077 \u1088 \u1089 \u1080 \u1103  \u1073 \u1086 \u1090 \u1072 : \{VERSION\}",\
            reply_markup=main_admin_keyboard()\
        )\
    elif is_manager(chat_id):\
        manager = get_manager_info(chat_id)\
        name = manager.get("first_name") if manager and manager.get("first_name") else user.first_name or ""\
        greeting = get_greeting(name)\
        await update.message.reply_text(\
            f"\{greeting\}\\n\\n\uc0\u55358 \u56598  \u1042 \u1077 \u1088 \u1089 \u1080 \u1103  \u1073 \u1086 \u1090 \u1072 : \{VERSION\}",\
            reply_markup=main_user_keyboard()\
        )\
    else:\
        await update.message.reply_text("\uc0\u10060  \u1053 \u1077 \u1090  \u1076 \u1086 \u1089 \u1090 \u1091 \u1087 \u1072 ! \u1054 \u1073 \u1088 \u1072 \u1090 \u1080 \u1090 \u1077 \u1089 \u1100  \u1082  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088 \u1091 .", reply_markup=ReplyKeyboardRemove())\
\
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    chat_id = update.effective_chat.id\
    if is_admin(chat_id):\
        help_text = (\
            "\uc0\u55357 \u56534  *\u1057 \u1087 \u1088 \u1072 \u1074 \u1082 \u1072  \u1076 \u1083 \u1103  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088 \u1072 *\\n\\n"\
            "\uc0\u55357 \u56633  *\u1054 \u1089 \u1085 \u1086 \u1074 \u1085 \u1099 \u1077  \u1092 \u1091 \u1085 \u1082 \u1094 \u1080 \u1080 *\\n"\
            "\'95 \uc0\u55357 \u56522  \u1054 \u1090 \u1095 \u1105 \u1090  \u1087 \u1086  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1072 \u1084  \'96 \u1072 \u1082 \u1090 \u1091 \u1072 \u1083 \u1100 \u1085 \u1072 \u1103  \u1089 \u1074 \u1086 \u1076 \u1082 \u1072  \u1087 \u1086  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1072 \u1084  \u1079 \u1072  \u1089 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103  \u1080  \u1090 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 .\\n"\
            "\'95 \uc0\u55357 \u56550  \u1054 \u1090 \u1095 \u1105 \u1090  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 \u1084  \'96 \u1090 \u1086 \u1087  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  \u1087 \u1086  \u1074 \u1099 \u1088 \u1091 \u1095 \u1082 \u1077  \u1079 \u1072  \u1089 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103  \u1080  \u1090 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 .\\n"\
            "\'95 \uc0\u55357 \u56518  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1076 \u1072 \u1090 \u1091  \'96 \u1087 \u1088 \u1086 \u1089 \u1084 \u1086 \u1090 \u1088  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072  \u1082 \u1086 \u1085 \u1082 \u1088 \u1077 \u1090 \u1085 \u1099 \u1081  \u1076 \u1077 \u1085 \u1100  (\u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1080  \u1080 \u1083 \u1080  \u1090 \u1086 \u1074 \u1072 \u1088 \u1099 ).\\n"\
            "\'95 \uc0\u55357 \u56522  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076  \'96 \u1075 \u1080 \u1073 \u1082 \u1080 \u1081  \u1074 \u1099 \u1073 \u1086 \u1088  \u1086 \u1090 \u1095 \u1105 \u1090 \u1085 \u1086 \u1075 \u1086  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1072  (\u1084 \u1077 \u1089 \u1103 \u1094 , \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083 , \u1075 \u1086 \u1076 , \u1087 \u1088 \u1086 \u1080 \u1079 \u1074 \u1086 \u1083 \u1100 \u1085 \u1099 \u1081 ).\\n"\
            "\'95 \uc0\u55357 \u56520  \u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078  \'96 \u1075 \u1088 \u1072 \u1092 \u1080 \u1082  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074  \u1087 \u1086  \u1084 \u1077 \u1089 \u1103 \u1094 \u1072 \u1084  \u1079 \u1072  \u1074 \u1099 \u1073 \u1088 \u1072 \u1085 \u1085 \u1099 \u1081  \u1075 \u1086 \u1076  (\u1080 \u1083 \u1080  \u1085 \u1077 \u1089 \u1082 \u1086 \u1083 \u1100 \u1082 \u1086  \u1083 \u1077 \u1090 ).\\n"\
            "\'95 \uc0\u55357 \u56520  \u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1091  \'96 \u1075 \u1088 \u1072 \u1092 \u1080 \u1082  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078  \u1082 \u1086 \u1085 \u1082 \u1088 \u1077 \u1090 \u1085 \u1086 \u1075 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1087 \u1086  \u1084 \u1077 \u1089 \u1103 \u1094 \u1072 \u1084 .\\n"\
            "\'95 \uc0\u9881 \u65039  \u1040 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1080 \u1077  \'96 \u1091 \u1087 \u1088 \u1072 \u1074 \u1083 \u1077 \u1085 \u1080 \u1077  \u1076 \u1086 \u1089 \u1090 \u1091 \u1087 \u1086 \u1084  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1086 \u1074 .\\n\\n"\
            "\uc0\u55357 \u56633  *\u1059 \u1087 \u1088 \u1072 \u1074 \u1083 \u1077 \u1085 \u1080 \u1077  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072 \u1084 \u1080 *\\n"\
            "\'95 \uc0\u10133  \u1044 \u1086 \u1073 \u1072 \u1074 \u1080 \u1090 \u1100  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072  \'96 \u1074 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  Telegram ID \u1080 \u1083 \u1080  @username \u1087 \u1086 \u1083 \u1100 \u1079 \u1086 \u1074 \u1072 \u1090 \u1077 \u1083 \u1103 , \u1079 \u1072 \u1090 \u1077 \u1084  \u1085 \u1086 \u1084 \u1077 \u1088  \u1090 \u1077 \u1083 \u1077 \u1092 \u1086 \u1085 \u1072  (\u1080 \u1083 \u1080  '-' \u1076 \u1083 \u1103  \u1087 \u1088 \u1086 \u1087 \u1091 \u1089 \u1082 \u1072 ).\\n"\
            "\'95 \uc0\u10134  \u1059 \u1076 \u1072 \u1083 \u1080 \u1090 \u1100  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072  \'96 \u1074 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  Telegram ID \u1087 \u1086 \u1083 \u1100 \u1079 \u1086 \u1074 \u1072 \u1090 \u1077 \u1083 \u1103 .\\n"\
            "\'95 \uc0\u55357 \u56523  \u1057 \u1087 \u1080 \u1089 \u1086 \u1082  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1086 \u1074  \'96 \u1087 \u1088 \u1086 \u1089 \u1084 \u1086 \u1090 \u1088  \u1074 \u1089 \u1077 \u1093  \u1076 \u1086 \u1073 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1093  \u1087 \u1086 \u1083 \u1100 \u1079 \u1086 \u1074 \u1072 \u1090 \u1077 \u1083 \u1077 \u1081  (ID, username, \u1080 \u1084 \u1103 , \u1090 \u1077 \u1083 \u1077 \u1092 \u1086 \u1085 ).\\n\\n"\
            "\uc0\u55357 \u56633  *\u1040 \u1074 \u1090 \u1086 \u1084 \u1072 \u1090 \u1080 \u1095 \u1077 \u1089 \u1082 \u1080 \u1077  \u1086 \u1090 \u1095 \u1105 \u1090 \u1099 *\\n"\
            "\'95 \uc0\u1042  10:00 \u1052 \u1057 \u1050  \'96 \u1086 \u1090 \u1095 \u1105 \u1090  \u1089  \u1073 \u1083 \u1086 \u1082 \u1072 \u1084 \u1080  \'ab\u1042 \u1095 \u1077 \u1088 \u1072 \'bb, \'ab\u1057 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 \'bb \u1080  \'ab\u1058 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 \'bb.\\n"\
            "\'95 \uc0\u1042  22:00 \u1052 \u1057 \u1050  \'96 \u1086 \u1090 \u1095 \u1105 \u1090  \u1089  \u1073 \u1083 \u1086 \u1082 \u1072 \u1084 \u1080  \'ab\u1057 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 \'bb \u1080  \'ab\u1058 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 \'bb.\\n\\n"\
            "\uc0\u55357 \u56633  *\u1052 \u1077 \u1090 \u1088 \u1080 \u1082 \u1080 *\\n"\
            "\'95 \uc0\u55357 \u57042  \u1047 \u1072 \u1082 \u1072 \u1079 \u1072 \u1085 \u1086  \'96 \u1089 \u1091 \u1084 \u1084 \u1072  \u1080  \u1082 \u1086 \u1083 \u1080 \u1095 \u1077 \u1089 \u1090 \u1074 \u1086  \u1074 \u1089 \u1077 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074 .\\n"\
            "\'95 \uc0\u55357 \u56550  \u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1086  \'96 \u1089 \u1091 \u1084 \u1084 \u1072  \u1080  \u1082 \u1086 \u1083 \u1080 \u1095 \u1077 \u1089 \u1090 \u1074 \u1086  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074 .\\n"\
            "\'95 \uc0\u10060  \u1054 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086  \'96 \u1089 \u1091 \u1084 \u1084 \u1072  \u1080  \u1082 \u1086 \u1083 \u1080 \u1095 \u1077 \u1089 \u1090 \u1074 \u1086  \u1086 \u1090 \u1084 \u1077 \u1085 \u1105 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074 .\\n"\
            "\'95 \uc0\u55357 \u56546  \u1056 \u1077 \u1082 \u1083 \u1072 \u1084 \u1072  \'96 \u1088 \u1072 \u1089 \u1093 \u1086 \u1076 \u1099  \u1085 \u1072  \u1088 \u1077 \u1082 \u1083 \u1072 \u1084 \u1091 , \u1044 \u1056 \u1056  (\u1086 \u1073 \u1097 \u1080 \u1081 ) \u1080  \u1044 \u1056 \u1056  (\u1087 \u1086  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1084 ).\\n"\
            "\'95 \uc0\u55357 \u56496  \u1056 \u1072 \u1089 \u1093 \u1086 \u1076 \u1099  (\u1092 \u1080 \u1085 \u1072 \u1085 \u1089 \u1086 \u1074 \u1099 \u1077 ) \'96 \u1076 \u1077 \u1090 \u1072 \u1083 \u1100 \u1085 \u1072 \u1103  \u1088 \u1072 \u1079 \u1073 \u1080 \u1074 \u1082 \u1072 : \u1082 \u1086 \u1084 \u1080 \u1089 \u1089 \u1080 \u1080 , \u1083 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072 , \u1101 \u1082 \u1074 \u1072 \u1081 \u1088 \u1080 \u1085 \u1075 , \u1082 \u1088 \u1086 \u1089 \u1089 -\u1076 \u1086 \u1082 \u1080 \u1085 \u1075 , \u1093 \u1088 \u1072 \u1085 \u1077 \u1085 \u1080 \u1077 , \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1099  \u1080  \u1076 \u1088 .\\n\\n"\
            "\uc0\u55357 \u56633  *\u1057 \u1088 \u1072 \u1074 \u1085 \u1077 \u1085 \u1080 \u1077  \u1076 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1080 *\\n"\
            "\'95 \uc0\u1044 \u1083 \u1103  \'ab\u1057 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 \'bb \'96 \u1089 \u1088 \u1072 \u1074 \u1085 \u1077 \u1085 \u1080 \u1077  \u1089  \u1072 \u1085 \u1072 \u1083 \u1086 \u1075 \u1080 \u1095 \u1085 \u1099 \u1084  \u1074 \u1088 \u1077 \u1084 \u1077 \u1085 \u1077 \u1084  \u1074 \u1095 \u1077 \u1088 \u1072 .\\n"\
            "\'95 \uc0\u1044 \u1083 \u1103  \'ab\u1058 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 \'bb \'96 \u1089 \u1088 \u1072 \u1074 \u1085 \u1077 \u1085 \u1080 \u1077  \u1089  \u1072 \u1085 \u1072 \u1083 \u1086 \u1075 \u1080 \u1095 \u1085 \u1099 \u1084  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1086 \u1084  \u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1077 \u1075 \u1086  \u1084 \u1077 \u1089 \u1103 \u1094 \u1072  (\u1089  \u1091 \u1095 \u1105 \u1090 \u1086 \u1084  \u1074 \u1088 \u1077 \u1084 \u1077 \u1085 \u1080 ).\\n\\n"\
            "\uc0\u55357 \u56633  *\u1063 \u1072 \u1089 \u1086 \u1074 \u1086 \u1081  \u1087 \u1086 \u1103 \u1089 *\\n"\
            "\'95 \uc0\u1042 \u1089 \u1077  \u1088 \u1072 \u1089 \u1095 \u1105 \u1090 \u1099  \u1074 \u1077 \u1076 \u1091 \u1090 \u1089 \u1103  \u1087 \u1086  \u1084 \u1086 \u1089 \u1082 \u1086 \u1074 \u1089 \u1082 \u1086 \u1084 \u1091  \u1074 \u1088 \u1077 \u1084 \u1077 \u1085 \u1080  (\u1052 \u1057 \u1050 , UTC+3).\\n\\n"\
            f"\uc0\u55358 \u56598  \u1042 \u1077 \u1088 \u1089 \u1080 \u1103  \u1073 \u1086 \u1090 \u1072 : \{VERSION\}"\
        )\
    else:\
        help_text = (\
            "\uc0\u55357 \u56534  *\u1057 \u1087 \u1088 \u1072 \u1074 \u1082 \u1072  \u1076 \u1083 \u1103  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072 *\\n\\n"\
            "\uc0\u55357 \u56633  *\u1054 \u1089 \u1085 \u1086 \u1074 \u1085 \u1099 \u1077  \u1092 \u1091 \u1085 \u1082 \u1094 \u1080 \u1080 *\\n"\
            "\'95 \uc0\u55357 \u56522  \u1054 \u1090 \u1095 \u1105 \u1090  \u1087 \u1086  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1072 \u1084  \'96 \u1072 \u1082 \u1090 \u1091 \u1072 \u1083 \u1100 \u1085 \u1072 \u1103  \u1089 \u1074 \u1086 \u1076 \u1082 \u1072  \u1087 \u1086  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1072 \u1084  \u1079 \u1072  \u1089 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103  \u1080  \u1090 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 .\\n"\
            "\'95 \uc0\u55357 \u56550  \u1054 \u1090 \u1095 \u1105 \u1090  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 \u1084  \'96 \u1090 \u1086 \u1087  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  \u1087 \u1086  \u1074 \u1099 \u1088 \u1091 \u1095 \u1082 \u1077  \u1079 \u1072  \u1089 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103  \u1080  \u1090 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 .\\n"\
            "\'95 \uc0\u55357 \u56518  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1076 \u1072 \u1090 \u1091  \'96 \u1087 \u1088 \u1086 \u1089 \u1084 \u1086 \u1090 \u1088  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072  \u1082 \u1086 \u1085 \u1082 \u1088 \u1077 \u1090 \u1085 \u1099 \u1081  \u1076 \u1077 \u1085 \u1100  (\u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1080  \u1080 \u1083 \u1080  \u1090 \u1086 \u1074 \u1072 \u1088 \u1099 ).\\n"\
            "\'95 \uc0\u55357 \u56522  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076  \'96 \u1075 \u1080 \u1073 \u1082 \u1080 \u1081  \u1074 \u1099 \u1073 \u1086 \u1088  \u1086 \u1090 \u1095 \u1105 \u1090 \u1085 \u1086 \u1075 \u1086  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1072  (\u1084 \u1077 \u1089 \u1103 \u1094 , \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083 , \u1075 \u1086 \u1076 , \u1087 \u1088 \u1086 \u1080 \u1079 \u1074 \u1086 \u1083 \u1100 \u1085 \u1099 \u1081 ).\\n"\
            "\'95 \uc0\u55357 \u56520  \u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078  \'96 \u1075 \u1088 \u1072 \u1092 \u1080 \u1082  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074  \u1087 \u1086  \u1084 \u1077 \u1089 \u1103 \u1094 \u1072 \u1084  \u1079 \u1072  \u1074 \u1099 \u1073 \u1088 \u1072 \u1085 \u1085 \u1099 \u1081  \u1075 \u1086 \u1076  (\u1080 \u1083 \u1080  \u1085 \u1077 \u1089 \u1082 \u1086 \u1083 \u1100 \u1082 \u1086  \u1083 \u1077 \u1090 ).\\n"\
            "\'95 \uc0\u55357 \u56520  \u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1091  \'96 \u1075 \u1088 \u1072 \u1092 \u1080 \u1082  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078  \u1082 \u1086 \u1085 \u1082 \u1088 \u1077 \u1090 \u1085 \u1086 \u1075 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1087 \u1086  \u1084 \u1077 \u1089 \u1103 \u1094 \u1072 \u1084 .\\n\\n"\
            "\uc0\u55357 \u56633  *\u1040 \u1074 \u1090 \u1086 \u1084 \u1072 \u1090 \u1080 \u1095 \u1077 \u1089 \u1082 \u1080 \u1077  \u1086 \u1090 \u1095 \u1105 \u1090 \u1099 *\\n"\
            "\'95 \uc0\u1042  10:00 \u1052 \u1057 \u1050  \'96 \u1086 \u1090 \u1095 \u1105 \u1090  \u1089  \u1073 \u1083 \u1086 \u1082 \u1072 \u1084 \u1080  \'ab\u1042 \u1095 \u1077 \u1088 \u1072 \'bb, \'ab\u1057 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 \'bb \u1080  \'ab\u1058 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 \'bb.\\n"\
            "\'95 \uc0\u1042  22:00 \u1052 \u1057 \u1050  \'96 \u1086 \u1090 \u1095 \u1105 \u1090  \u1089  \u1073 \u1083 \u1086 \u1082 \u1072 \u1084 \u1080  \'ab\u1057 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 \'bb \u1080  \'ab\u1058 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 \'bb.\\n\\n"\
            "\uc0\u55357 \u56633  *\u1052 \u1077 \u1090 \u1088 \u1080 \u1082 \u1080 *\\n"\
            "\'95 \uc0\u55357 \u57042  \u1047 \u1072 \u1082 \u1072 \u1079 \u1072 \u1085 \u1086  \'96 \u1089 \u1091 \u1084 \u1084 \u1072  \u1080  \u1082 \u1086 \u1083 \u1080 \u1095 \u1077 \u1089 \u1090 \u1074 \u1086  \u1074 \u1089 \u1077 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074 .\\n"\
            "\'95 \uc0\u55357 \u56550  \u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1086  \'96 \u1089 \u1091 \u1084 \u1084 \u1072  \u1080  \u1082 \u1086 \u1083 \u1080 \u1095 \u1077 \u1089 \u1090 \u1074 \u1086  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074 .\\n"\
            "\'95 \uc0\u10060  \u1054 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086  \'96 \u1089 \u1091 \u1084 \u1084 \u1072  \u1080  \u1082 \u1086 \u1083 \u1080 \u1095 \u1077 \u1089 \u1090 \u1074 \u1086  \u1086 \u1090 \u1084 \u1077 \u1085 \u1105 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074 .\\n"\
            "\'95 \uc0\u55357 \u56546  \u1056 \u1077 \u1082 \u1083 \u1072 \u1084 \u1072  \'96 \u1088 \u1072 \u1089 \u1093 \u1086 \u1076 \u1099  \u1085 \u1072  \u1088 \u1077 \u1082 \u1083 \u1072 \u1084 \u1091 , \u1044 \u1056 \u1056  (\u1086 \u1073 \u1097 \u1080 \u1081 ) \u1080  \u1044 \u1056 \u1056  (\u1087 \u1086  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1084 ).\\n"\
            "\'95 \uc0\u55357 \u56496  \u1056 \u1072 \u1089 \u1093 \u1086 \u1076 \u1099  (\u1092 \u1080 \u1085 \u1072 \u1085 \u1089 \u1086 \u1074 \u1099 \u1077 ) \'96 \u1076 \u1077 \u1090 \u1072 \u1083 \u1100 \u1085 \u1072 \u1103  \u1088 \u1072 \u1079 \u1073 \u1080 \u1074 \u1082 \u1072 : \u1082 \u1086 \u1084 \u1080 \u1089 \u1089 \u1080 \u1080 , \u1083 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072 , \u1101 \u1082 \u1074 \u1072 \u1081 \u1088 \u1080 \u1085 \u1075 , \u1082 \u1088 \u1086 \u1089 \u1089 -\u1076 \u1086 \u1082 \u1080 \u1085 \u1075 , \u1093 \u1088 \u1072 \u1085 \u1077 \u1085 \u1080 \u1077 , \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1099  \u1080  \u1076 \u1088 .\\n\\n"\
            "\uc0\u55357 \u56633  *\u1057 \u1088 \u1072 \u1074 \u1085 \u1077 \u1085 \u1080 \u1077  \u1076 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1080 *\\n"\
            "\'95 \uc0\u1044 \u1083 \u1103  \'ab\u1057 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 \'bb \'96 \u1089 \u1088 \u1072 \u1074 \u1085 \u1077 \u1085 \u1080 \u1077  \u1089  \u1072 \u1085 \u1072 \u1083 \u1086 \u1075 \u1080 \u1095 \u1085 \u1099 \u1084  \u1074 \u1088 \u1077 \u1084 \u1077 \u1085 \u1077 \u1084  \u1074 \u1095 \u1077 \u1088 \u1072 .\\n"\
            "\'95 \uc0\u1044 \u1083 \u1103  \'ab\u1058 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 \'bb \'96 \u1089 \u1088 \u1072 \u1074 \u1085 \u1077 \u1085 \u1080 \u1077  \u1089  \u1072 \u1085 \u1072 \u1083 \u1086 \u1075 \u1080 \u1095 \u1085 \u1099 \u1084  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1086 \u1084  \u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1077 \u1075 \u1086  \u1084 \u1077 \u1089 \u1103 \u1094 \u1072  (\u1089  \u1091 \u1095 \u1105 \u1090 \u1086 \u1084  \u1074 \u1088 \u1077 \u1084 \u1077 \u1085 \u1080 ).\\n\\n"\
            "\uc0\u55357 \u56633  *\u1063 \u1072 \u1089 \u1086 \u1074 \u1086 \u1081  \u1087 \u1086 \u1103 \u1089 *\\n"\
            "\'95 \uc0\u1042 \u1089 \u1077  \u1088 \u1072 \u1089 \u1095 \u1105 \u1090 \u1099  \u1074 \u1077 \u1076 \u1091 \u1090 \u1089 \u1103  \u1087 \u1086  \u1084 \u1086 \u1089 \u1082 \u1086 \u1074 \u1089 \u1082 \u1086 \u1084 \u1091  \u1074 \u1088 \u1077 \u1084 \u1077 \u1085 \u1080  (\u1052 \u1057 \u1050 , UTC+3).\\n\\n"\
            f"\uc0\u55358 \u56598  \u1042 \u1077 \u1088 \u1089 \u1080 \u1103  \u1073 \u1086 \u1090 \u1072 : \{VERSION\}"\
        )\
    await update.message.reply_text(help_text, parse_mode="Markdown")\
\
async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    text = update.message.text\
    chat_id = update.effective_chat.id\
\
    if text == "\uc0\u55357 \u56522  \u1054 \u1090 \u1095 \u1105 \u1090  \u1087 \u1086  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1072 \u1084 ":\
        if not has_access(chat_id):\
            await update.message.reply_text("\uc0\u10060  \u1053 \u1077 \u1090  \u1076 \u1086 \u1089 \u1090 \u1091 \u1087 \u1072 ! \u1054 \u1073 \u1088 \u1072 \u1090 \u1080 \u1090 \u1077 \u1089 \u1100  \u1082  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088 \u1091 .")\
            return\
        await update.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1090 \u1080 \u1087  \u1086 \u1090 \u1095 \u1105 \u1090 \u1072  \u1087 \u1086  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1072 \u1084 :", reply_markup=sales_reports_keyboard())\
        return\
\
    if text == "\uc0\u55357 \u56550  \u1054 \u1090 \u1095 \u1105 \u1090  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 \u1084 ":\
        if not has_access(chat_id):\
            await update.message.reply_text("\uc0\u10060  \u1053 \u1077 \u1090  \u1076 \u1086 \u1089 \u1090 \u1091 \u1087 \u1072 ! \u1054 \u1073 \u1088 \u1072 \u1090 \u1080 \u1090 \u1077 \u1089 \u1100  \u1082  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088 \u1091 .")\
            return\
        # \uc0\u1058 \u1086 \u1074 \u1072 \u1088 \u1085 \u1099 \u1081  \u1088 \u1072 \u1079 \u1076 \u1077 \u1083  \u1086 \u1073 \u1088 \u1072 \u1073 \u1072 \u1090 \u1099 \u1074 \u1072 \u1077 \u1090 \u1089 \u1103  \u1074  products.py, \u1085 \u1086  \u1079 \u1076 \u1077 \u1089 \u1100  \u1084 \u1099  \u1087 \u1088 \u1086 \u1089 \u1090 \u1086  \u1087 \u1077 \u1088 \u1077 \u1089 \u1099 \u1083 \u1072 \u1077 \u1084 \
        # \uc0\u1044 \u1083 \u1103  \u1101 \u1090 \u1086 \u1075 \u1086  \u1085 \u1091 \u1078 \u1077 \u1085  \u1080 \u1084 \u1087 \u1086 \u1088 \u1090  \u1080 \u1079  products, \u1085 \u1086  \u1084 \u1099  \u1085 \u1077  \u1084 \u1086 \u1078 \u1077 \u1084  \u1077 \u1075 \u1086  \u1089 \u1076 \u1077 \u1083 \u1072 \u1090 \u1100  \u1080 \u1079 -\u1079 \u1072  \u1094 \u1080 \u1082 \u1083 \u1080 \u1095 \u1077 \u1089 \u1082 \u1086 \u1081  \u1079 \u1072 \u1074 \u1080 \u1089 \u1080 \u1084 \u1086 \u1089 \u1090 \u1080 .\
        # \uc0\u1055 \u1086 \u1101 \u1090 \u1086 \u1084 \u1091  \u1086 \u1089 \u1090 \u1072 \u1074 \u1080 \u1084  \u1082 \u1072 \u1082  \u1077 \u1089 \u1090 \u1100 : \u1087 \u1086 \u1083 \u1100 \u1079 \u1086 \u1074 \u1072 \u1090 \u1077 \u1083 \u1100  \u1089 \u1072 \u1084  \u1087 \u1077 \u1088 \u1077 \u1081 \u1076 \u1105 \u1090  \u1074  \u1088 \u1072 \u1079 \u1076 \u1077 \u1083  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  \u1095 \u1077 \u1088 \u1077 \u1079  \u1082 \u1083 \u1072 \u1074 \u1080 \u1072 \u1090 \u1091 \u1088 \u1091 .\
        # \uc0\u1053 \u1086  handle_main_menu \u1074 \u1099 \u1079 \u1099 \u1074 \u1072 \u1077 \u1090 \u1089 \u1103  \u1090 \u1086 \u1083 \u1100 \u1082 \u1086  \u1076 \u1083 \u1103  \u1075 \u1083 \u1072 \u1074 \u1085 \u1086 \u1075 \u1086  \u1084 \u1077 \u1085 \u1102 .\
        await update.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1090 \u1080 \u1087  \u1086 \u1090 \u1095 \u1105 \u1090 \u1072  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 \u1084 :", reply_markup=products_reports_keyboard())\
        return\
\
    if text == "\uc0\u9881 \u65039  \u1040 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1080 \u1077 ":\
        if not is_admin(chat_id):\
            await update.message.reply_text("\uc0\u9940  \u1058 \u1086 \u1083 \u1100 \u1082 \u1086  \u1076 \u1083 \u1103  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088 \u1072 .")\
            return\
        await update.message.reply_text("\uc0\u1059 \u1087 \u1088 \u1072 \u1074 \u1083 \u1077 \u1085 \u1080 \u1077  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072 \u1084 \u1080 :", reply_markup=admin_keyboard())\
        return\
\
    if text == "\uc0\u55357 \u56534  \u1057 \u1087 \u1088 \u1072 \u1074 \u1082 \u1072 ":\
        await help_command(update, context)\
        return\
\
    await update.message.reply_text("\uc0\u1048 \u1089 \u1087 \u1086 \u1083 \u1100 \u1079 \u1091 \u1081 \u1090 \u1077  \u1082 \u1085 \u1086 \u1087 \u1082 \u1080  \u1084 \u1077 \u1085 \u1102 .")\
\
# ---------- \uc0\u1054 \u1041 \u1056 \u1040 \u1041 \u1054 \u1058 \u1063 \u1048 \u1050 \u1048  \u1055 \u1054 \u1044 \u1052 \u1045 \u1053 \u1070  \u1055 \u1056 \u1054 \u1044 \u1040 \u1046  ----------\
async def handle_sales_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    text = update.message.text\
    chat_id = update.effective_chat.id\
\
    if text == "\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ":\
        if is_admin(chat_id):\
            await update.message.reply_text(\
                f"\uc0\u1043 \u1083 \u1072 \u1074 \u1085 \u1086 \u1077  \u1084 \u1077 \u1085 \u1102 \\n\\n\u55358 \u56598  \u1042 \u1077 \u1088 \u1089 \u1080 \u1103  \u1073 \u1086 \u1090 \u1072 : \{VERSION\}",\
                reply_markup=main_admin_keyboard()\
            )\
        else:\
            await update.message.reply_text(\
                f"\uc0\u1043 \u1083 \u1072 \u1074 \u1085 \u1086 \u1077  \u1084 \u1077 \u1085 \u1102 \\n\\n\u55358 \u56598  \u1042 \u1077 \u1088 \u1089 \u1080 \u1103  \u1073 \u1086 \u1090 \u1072 : \{VERSION\}",\
                reply_markup=main_user_keyboard()\
            )\
        return\
\
    if not has_access(chat_id):\
        await update.message.reply_text("\uc0\u10060  \u1053 \u1077 \u1090  \u1076 \u1086 \u1089 \u1090 \u1091 \u1087 \u1072 ! \u1054 \u1073 \u1088 \u1072 \u1090 \u1080 \u1090 \u1077 \u1089 \u1100  \u1082  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088 \u1091 .")\
        return\
\
    if text == "\uc0\u55357 \u56517  \u1055 \u1088 \u1086 \u1076 \u1072 \u1078 \u1080  \u1079 \u1072  \u1089 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 ":\
        progress_msg = await update.message.reply_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077  \u1079 \u1072  \u1089 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 ...")\
        report = await format_combined_metrics_with_deltas(include_yesterday=False, progress_callback=None)\
        await progress_msg.delete()\
        await update.message.reply_text(report, parse_mode="Markdown")\
        return\
\
    if text == "\uc0\u55357 \u56518  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1076 \u1072 \u1090 \u1091 ":\
        now = get_moscow_today()\
        keyboard = create_calendar(now.year, now.month, "date_")\
        await update.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1072 \u1090 \u1091  (\u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1080 ):", reply_markup=keyboard)\
        return WAITING_DATE_SINGLE\
\
    if text == "\uc0\u55357 \u56522  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 ":\
        keyboard = InlineKeyboardMarkup([\
            [InlineKeyboardButton("\uc0\u55357 \u56787 \u65039  \u1055 \u1086  \u1084 \u1077 \u1089 \u1103 \u1094 \u1072 \u1084 ", callback_data="period_month")],\
            [InlineKeyboardButton("\uc0\u55357 \u56517  \u1055 \u1086  \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083 \u1072 \u1084 ", callback_data="period_quarter")],\
            [InlineKeyboardButton("\uc0\u55357 \u56518  \u1055 \u1086  \u1075 \u1086 \u1076 \u1072 \u1084 ", callback_data="period_year")],\
            [InlineKeyboardButton("\uc0\u55357 \u56522  \u1055 \u1088 \u1086 \u1080 \u1079 \u1074 \u1086 \u1083 \u1100 \u1085 \u1099 \u1081  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 ", callback_data="period_custom")],\
            [InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="period_cancel")]\
        ])\
        await update.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1090 \u1080 \u1087  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1072 :", reply_markup=keyboard)\
        return WAITING_PERIOD_TYPE\
\
    if text == "\uc0\u55357 \u56520  \u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 ":\
        current_year = get_moscow_today().year\
        years = list(range(current_year - 9, current_year + 1))\
        buttons = [\
            [InlineKeyboardButton("\uc0\u55357 \u56517  \u1058 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1075 \u1086 \u1076 ", callback_data="dynamics_current")],\
            [InlineKeyboardButton("\uc0\u55357 \u56518  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1075 \u1086 \u1076 ", callback_data="dynamics_select")],\
            [InlineKeyboardButton("\uc0\u55357 \u56522  \u1044 \u1080 \u1072 \u1087 \u1072 \u1079 \u1086 \u1085  \u1083 \u1077 \u1090 ", callback_data="dynamics_range")],\
            [InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="dynamics_cancel")]\
        ]\
        await update.message.reply_text(\
            "\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1074 \u1072 \u1088 \u1080 \u1072 \u1085 \u1090  \u1076 \u1083 \u1103  \u1087 \u1086 \u1089 \u1090 \u1088 \u1086 \u1077 \u1085 \u1080 \u1103  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 \u1072 :\\n"\
            "\'95 \uc0\u1058 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1075 \u1086 \u1076  \'96 \u1089 \u1088 \u1072 \u1079 \u1091  \u1087 \u1086 \u1082 \u1072 \u1078 \u1077 \u1090  \u1076 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1091  \u1079 \u1072  \u1090 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1075 \u1086 \u1076 .\\n"\
            "\'95 \uc0\u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1075 \u1086 \u1076  \'96 \u1087 \u1086 \u1082 \u1072 \u1078 \u1077 \u1090  \u1089 \u1087 \u1080 \u1089 \u1086 \u1082  \u1075 \u1086 \u1076 \u1086 \u1074  (\u1087 \u1086 \u1089 \u1083 \u1077 \u1076 \u1085 \u1080 \u1077  10).\\n"\
            "\'95 \uc0\u1044 \u1080 \u1072 \u1087 \u1072 \u1079 \u1086 \u1085  \u1083 \u1077 \u1090  \'96 \u1074 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  \u1085 \u1072 \u1095 \u1072 \u1083 \u1100 \u1085 \u1099 \u1081  \u1080  \u1082 \u1086 \u1085 \u1077 \u1095 \u1085 \u1099 \u1081  \u1075 \u1086 \u1076 .",\
            reply_markup=InlineKeyboardMarkup(buttons)\
        )\
        return WAITING_DYNAMICS_SELECT\
\
    await update.message.reply_text("\uc0\u1053 \u1077 \u1080 \u1079 \u1074 \u1077 \u1089 \u1090 \u1085 \u1072 \u1103  \u1082 \u1086 \u1084 \u1072 \u1085 \u1076 \u1072 .")\
\
# ---------- INLINE CALLBACK (\uc0\u1090 \u1086 \u1083 \u1100 \u1082 \u1086  \u1088 \u1072 \u1079 \u1076 \u1077 \u1083  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 ) ----------\
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    query = update.callback_query\
    await query.answer()\
    data = query.data\
    chat_id = update.effective_chat.id\
\
    if not has_access(chat_id):\
        await query.edit_message_text("\uc0\u10060  \u1053 \u1077 \u1090  \u1076 \u1086 \u1089 \u1090 \u1091 \u1087 \u1072 ! \u1054 \u1073 \u1088 \u1072 \u1090 \u1080 \u1090 \u1077 \u1089 \u1100  \u1082  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088 \u1091 .")\
        return ConversationHandler.END\
\
    # -------------------- \uc0\u1042 \u1067 \u1041 \u1054 \u1056  \u1044 \u1040 \u1058 \u1067  (\u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1080 ) --------------------\
    if data.startswith("date_"):\
        if data == "date_cancel":\
            await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1086 \u1088  \u1076 \u1072 \u1090 \u1099  \u1086 \u1090 \u1084 \u1077 \u1085 \u1105 \u1085 .")\
            await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=sales_reports_keyboard())\
            return ConversationHandler.END\
\
        if "prev_month" in data or "next_month" in data:\
            match = re.search(r'prev_month_(\\d+)_(\\d+)|next_month_(\\d+)_(\\d+)', data)\
            if match:\
                if match.group(1) and match.group(2):\
                    year = int(match.group(1)); month = int(match.group(2)); action = "prev_month"\
                else:\
                    year = int(match.group(3)); month = int(match.group(4)); action = "next_month"\
            else:\
                await query.edit_message_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1092 \u1086 \u1088 \u1084 \u1072 \u1090 \u1072  \u1085 \u1072 \u1074 \u1080 \u1075 \u1072 \u1094 \u1080 \u1080 .")\
                return WAITING_DATE_SINGLE\
\
            if action == "prev_month":\
                month -= 1\
                if month == 0: month = 12; year -= 1\
            else:\
                month += 1\
                if month == 13: month = 1; year += 1\
            keyboard = create_calendar(year, month, "date_")\
            await query.edit_message_reply_markup(reply_markup=keyboard)\
            return WAITING_DATE_SINGLE\
\
        date_str = data[5:]  # \uc0\u1091 \u1073 \u1080 \u1088 \u1072 \u1077 \u1084  "date_"\
        if re.match(r"\\d\{4\}-\\d\{2\}-\\d\{2\}", date_str):\
            valid, result = validate_date(date_str)\
            if not valid:\
                await query.edit_message_text(result)\
                return WAITING_DATE_SINGLE\
            progress_msg = await query.message.reply_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...")\
            metrics = await get_metrics_for_date(date_str)  # \uc0\u1092 \u1091 \u1085 \u1082 \u1094 \u1080 \u1103  \u1076 \u1086 \u1083 \u1078 \u1085 \u1072  \u1073 \u1099 \u1090 \u1100  \u1086 \u1087 \u1088 \u1077 \u1076 \u1077 \u1083 \u1077 \u1085 \u1072  \u1074  \u1101 \u1090 \u1086 \u1084  \u1078 \u1077  \u1084 \u1086 \u1076 \u1091 \u1083 \u1077  \u1080 \u1083 \u1080  \u1080 \u1084 \u1087 \u1086 \u1088 \u1090 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1072 \
            await progress_msg.delete()\
            msg = format_single_metrics(metrics, f"\uc0\u1055 \u1088 \u1086 \u1076 \u1072 \u1078 \u1080  \u1079 \u1072  \{date_str\}")\
            await query.edit_message_text(msg, parse_mode="Markdown")\
            await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=sales_reports_keyboard())\
            return ConversationHandler.END\
        else:\
            await query.edit_message_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1092 \u1086 \u1088 \u1084 \u1072 \u1090 \u1072  \u1076 \u1072 \u1090 \u1099 .")\
            return WAITING_DATE_SINGLE\
\
    # -------------------- \uc0\u1042 \u1067 \u1041 \u1054 \u1056  \u1055 \u1045 \u1056 \u1048 \u1054 \u1044 \u1040  (\u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1080 ) --------------------\
    if data == "period_month":\
        current_year = get_moscow_today().year\
        years = list(range(current_year - 9, current_year + 1))\
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"period_year_month_\{y\}")] for y in years]\
        buttons.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="period_cancel")])\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1075 \u1086 \u1076 :", reply_markup=InlineKeyboardMarkup(buttons))\
        return WAITING_PERIOD_YEAR\
\
    if data == "period_quarter":\
        current_year = get_moscow_today().year\
        years = list(range(current_year - 9, current_year + 1))\
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"period_year_quarter_\{y\}")] for y in years]\
        buttons.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="period_cancel")])\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1075 \u1086 \u1076 :", reply_markup=InlineKeyboardMarkup(buttons))\
        return WAITING_PERIOD_YEAR\
\
    if data == "period_year":\
        current_year = get_moscow_today().year\
        years = list(range(current_year - 9, current_year + 1))\
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"period_year_only_\{y\}")] for y in years]\
        buttons.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="period_cancel")])\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1075 \u1086 \u1076 :", reply_markup=InlineKeyboardMarkup(buttons))\
        return WAITING_YEAR_SELECT\
\
    if data == "period_custom":\
        now = get_moscow_today()\
        keyboard = create_calendar(now.year, now.month, "start_")\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1085 \u1072 \u1095 \u1072 \u1083 \u1100 \u1085 \u1091 \u1102  \u1076 \u1072 \u1090 \u1091 :", reply_markup=keyboard)\
        return WAITING_PERIOD_START\
\
    if data == "period_cancel":\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1086 \u1088  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1072  \u1086 \u1090 \u1084 \u1077 \u1085 \u1105 \u1085 .")\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=sales_reports_keyboard())\
        return ConversationHandler.END\
\
    # \uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1074 \u1099 \u1073 \u1086 \u1088 \u1072  \u1075 \u1086 \u1076 \u1072  \u1076 \u1083 \u1103  \u1084 \u1077 \u1089 \u1103 \u1094 \u1077 \u1074 \
    if data.startswith("period_year_month_"):\
        year = int(data.split("_")[-1])\
        context.user_data['period_year'] = year\
        months = ["\uc0\u1071 \u1085 \u1074 \u1072 \u1088 \u1100 ", "\u1060 \u1077 \u1074 \u1088 \u1072 \u1083 \u1100 ", "\u1052 \u1072 \u1088 \u1090 ", "\u1040 \u1087 \u1088 \u1077 \u1083 \u1100 ", "\u1052 \u1072 \u1081 ", "\u1048 \u1102 \u1085 \u1100 ",\
                  "\uc0\u1048 \u1102 \u1083 \u1100 ", "\u1040 \u1074 \u1075 \u1091 \u1089 \u1090 ", "\u1057 \u1077 \u1085 \u1090 \u1103 \u1073 \u1088 \u1100 ", "\u1054 \u1082 \u1090 \u1103 \u1073 \u1088 \u1100 ", "\u1053 \u1086 \u1103 \u1073 \u1088 \u1100 ", "\u1044 \u1077 \u1082 \u1072 \u1073 \u1088 \u1100 "]\
        buttons = [[InlineKeyboardButton(name, callback_data=f"period_month_\{i\}_\{year\}")] for i, name in enumerate(months, 1)]\
        buttons.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="period_cancel")])\
        await query.edit_message_text(f"\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1084 \u1077 \u1089 \u1103 \u1094  \{year\}:", reply_markup=InlineKeyboardMarkup(buttons))\
        return WAITING_PERIOD_MONTH\
\
    # \uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1074 \u1099 \u1073 \u1086 \u1088 \u1072  \u1075 \u1086 \u1076 \u1072  \u1076 \u1083 \u1103  \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083 \u1086 \u1074 \
    if data.startswith("period_year_quarter_"):\
        year = int(data.split("_")[-1])\
        context.user_data['period_year'] = year\
        quarters = ["1 \uc0\u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083  (\u1103 \u1085 \u1074 -\u1084 \u1072 \u1088 )", "2 \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083  (\u1072 \u1087 \u1088 -\u1080 \u1102 \u1085 )", "3 \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083  (\u1080 \u1102 \u1083 -\u1089 \u1077 \u1085 )", "4 \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083  (\u1086 \u1082 \u1090 -\u1076 \u1077 \u1082 )"]\
        buttons = [[InlineKeyboardButton(name, callback_data=f"period_quarter_\{i\}_\{year\}")] for i, name in enumerate(quarters, 1)]\
        buttons.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="period_cancel")])\
        await query.edit_message_text(f"\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083  \{year\}:", reply_markup=InlineKeyboardMarkup(buttons))\
        return WAITING_PERIOD_QUARTER\
\
    # \uc0\u1054 \u1090 \u1095 \u1105 \u1090  \u1079 \u1072  \u1075 \u1086 \u1076 \
    if data.startswith("period_year_only_"):\
        year = int(data.split("_")[-1])\
        first_day = datetime.date(year, 1, 1)\
        last_day = datetime.date(year, 12, 31)\
        progress_msg = await query.message.reply_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...")\
        metrics_current = await get_metrics_for_period(first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d"))\
        prev_year = year - 1\
        prev_first_day = datetime.date(prev_year, 1, 1)\
        prev_last_day = datetime.date(prev_year, 12, 31)\
        metrics_prev = await get_metrics_for_period(prev_first_day.strftime("%Y-%m-%d"), prev_last_day.strftime("%Y-%m-%d"))\
        await progress_msg.delete()\
        period_name = str(year)\
        report = format_period_comparison_metrics(metrics_current, metrics_prev, period_name)\
        await query.edit_message_text(report, parse_mode="Markdown")\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=sales_reports_keyboard())\
        return ConversationHandler.END\
\
    # \uc0\u1054 \u1090 \u1095 \u1105 \u1090  \u1079 \u1072  \u1084 \u1077 \u1089 \u1103 \u1094 \
    if data.startswith("period_month_"):\
        parts = data.split("_")\
        month_num, year = int(parts[2]), int(parts[3])\
        first_day = datetime.date(year, month_num, 1)\
        if month_num == 12:\
            last_day = datetime.date(year, 12, 31)\
        else:\
            last_day = datetime.date(year, month_num+1, 1) - datetime.timedelta(days=1)\
        date_from, date_to = first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")\
        progress_msg = await query.message.reply_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...")\
        metrics_current = await get_metrics_for_period(date_from, date_to)\
        if month_num == 1:\
            prev_month_num = 12\
            prev_year = year - 1\
        else:\
            prev_month_num = month_num - 1\
            prev_year = year\
        prev_first_day = datetime.date(prev_year, prev_month_num, 1)\
        if prev_month_num == 12:\
            prev_last_day = datetime.date(prev_year, 12, 31)\
        else:\
            prev_last_day = datetime.date(prev_year, prev_month_num+1, 1) - datetime.timedelta(days=1)\
        metrics_prev = await get_metrics_for_period(prev_first_day.strftime("%Y-%m-%d"), prev_last_day.strftime("%Y-%m-%d"))\
        await progress_msg.delete()\
        month_names = ["\uc0\u1071 \u1085 \u1074 \u1072 \u1088 \u1100 ", "\u1060 \u1077 \u1074 \u1088 \u1072 \u1083 \u1100 ", "\u1052 \u1072 \u1088 \u1090 ", "\u1040 \u1087 \u1088 \u1077 \u1083 \u1100 ", "\u1052 \u1072 \u1081 ", "\u1048 \u1102 \u1085 \u1100 ",\
                       "\uc0\u1048 \u1102 \u1083 \u1100 ", "\u1040 \u1074 \u1075 \u1091 \u1089 \u1090 ", "\u1057 \u1077 \u1085 \u1090 \u1103 \u1073 \u1088 \u1100 ", "\u1054 \u1082 \u1090 \u1103 \u1073 \u1088 \u1100 ", "\u1053 \u1086 \u1103 \u1073 \u1088 \u1100 ", "\u1044 \u1077 \u1082 \u1072 \u1073 \u1088 \u1100 "]\
        period_name = f"\{month_names[month_num-1]\} \{year\}"\
        report = format_period_comparison_metrics(metrics_current, metrics_prev, period_name)\
        await query.edit_message_text(report, parse_mode="Markdown")\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=sales_reports_keyboard())\
        return ConversationHandler.END\
\
    # \uc0\u1054 \u1090 \u1095 \u1105 \u1090  \u1079 \u1072  \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083 \
    if data.startswith("period_quarter_"):\
        parts = data.split("_")\
        q, year = int(parts[2]), int(parts[3])\
        start_month = (q-1)*3 + 1\
        end_month = q*3\
        first_day = datetime.date(year, start_month, 1)\
        if end_month == 12:\
            last_day = datetime.date(year, 12, 31)\
        else:\
            last_day = datetime.date(year, end_month+1, 1) - datetime.timedelta(days=1)\
        date_from, date_to = first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")\
        progress_msg = await query.message.reply_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...")\
        metrics_current = await get_metrics_for_period(date_from, date_to)\
        if q == 1:\
            prev_q = 4\
            prev_year = year - 1\
            prev_start_month = (prev_q-1)*3 + 1\
            prev_end_month = prev_q*3\
        else:\
            prev_q = q - 1\
            prev_year = year\
            prev_start_month = (prev_q-1)*3 + 1\
            prev_end_month = prev_q*3\
        prev_first_day = datetime.date(prev_year, prev_start_month, 1)\
        if prev_end_month == 12:\
            prev_last_day = datetime.date(prev_year, 12, 31)\
        else:\
            prev_last_day = datetime.date(prev_year, prev_end_month+1, 1) - datetime.timedelta(days=1)\
        metrics_prev = await get_metrics_for_period(prev_first_day.strftime("%Y-%m-%d"), prev_last_day.strftime("%Y-%m-%d"))\
        await progress_msg.delete()\
        period_name = f"\{q\} \uc0\u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083  \{year\}"\
        report = format_period_comparison_metrics(metrics_current, metrics_prev, period_name)\
        await query.edit_message_text(report, parse_mode="Markdown")\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=sales_reports_keyboard())\
        return ConversationHandler.END\
\
    # \uc0\u1055 \u1088 \u1086 \u1080 \u1079 \u1074 \u1086 \u1083 \u1100 \u1085 \u1099 \u1081  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 : \u1085 \u1072 \u1095 \u1072 \u1083 \u1086 \
    if data.startswith("start_"):\
        if data == "start_cancel":\
            await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1086 \u1088  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1072  \u1086 \u1090 \u1084 \u1077 \u1085 \u1105 \u1085 .")\
            await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=sales_reports_keyboard())\
            return ConversationHandler.END\
\
        if "prev_month" in data or "next_month" in data:\
            match = re.search(r'prev_month_(\\d+)_(\\d+)|next_month_(\\d+)_(\\d+)', data)\
            if match:\
                if match.group(1) and match.group(2):\
                    year = int(match.group(1)); month = int(match.group(2)); action = "prev_month"\
                else:\
                    year = int(match.group(3)); month = int(match.group(4)); action = "next_month"\
            else:\
                await query.edit_message_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1092 \u1086 \u1088 \u1084 \u1072 \u1090 \u1072  \u1085 \u1072 \u1074 \u1080 \u1075 \u1072 \u1094 \u1080 \u1080 .")\
                return WAITING_PERIOD_START\
\
            if action == "prev_month":\
                month -= 1\
                if month == 0: month = 12; year -= 1\
            else:\
                month += 1\
                if month == 13: month = 1; year += 1\
            keyboard = create_calendar(year, month, "start_")\
            await query.edit_message_reply_markup(reply_markup=keyboard)\
            return WAITING_PERIOD_START\
\
        date_str = data[6:]  # \uc0\u1091 \u1073 \u1080 \u1088 \u1072 \u1077 \u1084  "start_"\
        if re.match(r"\\d\{4\}-\\d\{2\}-\\d\{2\}", date_str):\
            valid, result = validate_date(date_str)\
            if not valid:\
                await query.edit_message_text(result)\
                return WAITING_PERIOD_START\
            context.user_data['period_start_date'] = date_str\
            now = get_moscow_today()\
            keyboard = create_calendar(now.year, now.month, "end_")\
            await query.edit_message_text(f"\uc0\u1053 \u1072 \u1095 \u1072 \u1083 \u1086 : \{date_str\}\\n\u1058 \u1077 \u1087 \u1077 \u1088 \u1100  \u1074 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1082 \u1086 \u1085 \u1077 \u1095 \u1085 \u1091 \u1102  \u1076 \u1072 \u1090 \u1091 :", reply_markup=keyboard)\
            return WAITING_PERIOD_END\
        else:\
            await query.edit_message_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1092 \u1086 \u1088 \u1084 \u1072 \u1090 \u1072  \u1076 \u1072 \u1090 \u1099 .")\
            return WAITING_PERIOD_START\
\
    # \uc0\u1055 \u1088 \u1086 \u1080 \u1079 \u1074 \u1086 \u1083 \u1100 \u1085 \u1099 \u1081  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 : \u1082 \u1086 \u1085 \u1077 \u1094 \
    if data.startswith("end_"):\
        if data == "end_cancel":\
            await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1086 \u1088  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1072  \u1086 \u1090 \u1084 \u1077 \u1085 \u1105 \u1085 .")\
            await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=sales_reports_keyboard())\
            return ConversationHandler.END\
\
        if "prev_month" in data or "next_month" in data:\
            match = re.search(r'prev_month_(\\d+)_(\\d+)|next_month_(\\d+)_(\\d+)', data)\
            if match:\
                if match.group(1) and match.group(2):\
                    year = int(match.group(1)); month = int(match.group(2)); action = "prev_month"\
                else:\
                    year = int(match.group(3)); month = int(match.group(4)); action = "next_month"\
            else:\
                await query.edit_message_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1092 \u1086 \u1088 \u1084 \u1072 \u1090 \u1072  \u1085 \u1072 \u1074 \u1080 \u1075 \u1072 \u1094 \u1080 \u1080 .")\
                return WAITING_PERIOD_END\
\
            if action == "prev_month":\
                month -= 1\
                if month == 0: month = 12; year -= 1\
            else:\
                month += 1\
                if month == 13: month = 1; year += 1\
            keyboard = create_calendar(year, month, "end_")\
            await query.edit_message_reply_markup(reply_markup=keyboard)\
            return WAITING_PERIOD_END\
\
        end_date_str = data[4:]  # \uc0\u1091 \u1073 \u1080 \u1088 \u1072 \u1077 \u1084  "end_"\
        if re.match(r"\\d\{4\}-\\d\{2\}-\\d\{2\}", end_date_str):\
            valid, result = validate_date(end_date_str)\
            if not valid:\
                await query.edit_message_text(result)\
                return WAITING_PERIOD_END\
            start_date = context.user_data.get('period_start_date')\
            if not start_date:\
                await query.edit_message_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072 : \u1085 \u1072 \u1095 \u1072 \u1083 \u1100 \u1085 \u1072 \u1103  \u1076 \u1072 \u1090 \u1072  \u1085 \u1077  \u1085 \u1072 \u1081 \u1076 \u1077 \u1085 \u1072 . \u1055 \u1086 \u1087 \u1088 \u1086 \u1073 \u1091 \u1081 \u1090 \u1077  \u1089 \u1085 \u1086 \u1074 \u1072 .")\
                return ConversationHandler.END\
            valid_period, msg = validate_period(start_date, end_date_str)\
            if not valid_period:\
                await query.edit_message_text(msg)\
                now = get_moscow_today()\
                keyboard = create_calendar(now.year, now.month, "start_")\
                await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1085 \u1072 \u1095 \u1072 \u1083 \u1100 \u1085 \u1091 \u1102  \u1076 \u1072 \u1090 \u1091  \u1079 \u1072 \u1085 \u1086 \u1074 \u1086 :", reply_markup=keyboard)\
                return WAITING_PERIOD_START\
            progress_msg = await query.message.reply_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...")\
            metrics = await get_metrics_for_period(start_date, end_date_str)\
            await progress_msg.delete()\
            msg = format_single_metrics(metrics, f"\uc0\u1055 \u1088 \u1086 \u1076 \u1072 \u1078 \u1080  \u1079 \u1072  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076  \{start_date\} \'96 \{end_date_str\}")\
            await query.edit_message_text(msg, parse_mode="Markdown")\
            await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=sales_reports_keyboard())\
            context.user_data.pop('period_start_date', None)\
            return ConversationHandler.END\
        else:\
            await query.edit_message_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1092 \u1086 \u1088 \u1084 \u1072 \u1090 \u1072  \u1076 \u1072 \u1090 \u1099 .")\
            return WAITING_PERIOD_END\
\
    # -------------------- \uc0\u1044 \u1048 \u1053 \u1040 \u1052 \u1048 \u1050 \u1040  \u1055 \u1056 \u1054 \u1044 \u1040 \u1046  (\u1075 \u1088 \u1072 \u1092 \u1080 \u1082 ) --------------------\
    if data == "dynamics_current":\
        await query.edit_message_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...")\
        current_year = get_moscow_today().year\
        # \uc0\u1048 \u1084 \u1087 \u1086 \u1088 \u1090 \u1080 \u1088 \u1091 \u1077 \u1084  \u1092 \u1091 \u1085 \u1082 \u1094 \u1080 \u1102  \u1075 \u1077 \u1085 \u1077 \u1088 \u1072 \u1094 \u1080 \u1080  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 \u1072  \u1080 \u1079  charts\
        from bot.handlers.charts import generate_sales_chart\
        chart_buf = await generate_sales_chart([current_year])\
        if chart_buf:\
            await query.message.reply_photo(photo=chart_buf, caption=f"\uc0\u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074  \u1079 \u1072  \{current_year\} \u1075 \u1086 \u1076 ")\
        else:\
            await query.message.reply_text("\uc0\u10060  \u1053 \u1077  \u1091 \u1076 \u1072 \u1083 \u1086 \u1089 \u1100  \u1087 \u1086 \u1089 \u1090 \u1088 \u1086 \u1080 \u1090 \u1100  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 .")\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=sales_reports_keyboard())\
        return ConversationHandler.END\
\
    if data == "dynamics_select":\
        current_year = get_moscow_today().year\
        years = list(range(current_year - 9, current_year + 1))\
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"dynamics_year_\{y\}")] for y in years]\
        buttons.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="dynamics_cancel")])\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1075 \u1086 \u1076  \u1076 \u1083 \u1103  \u1086 \u1090 \u1086 \u1073 \u1088 \u1072 \u1078 \u1077 \u1085 \u1080 \u1103  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 \u1072 :", reply_markup=InlineKeyboardMarkup(buttons))\
        return WAITING_DYNAMICS_SELECT\
\
    if data == "dynamics_range":\
        await query.edit_message_text("\uc0\u1042 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  \u1085 \u1072 \u1095 \u1072 \u1083 \u1100 \u1085 \u1099 \u1081  \u1075 \u1086 \u1076  (\u1085 \u1072 \u1087 \u1088 \u1080 \u1084 \u1077 \u1088 , 2020):")\
        return WAITING_DYNAMICS_RANGE_START\
\
    if data == "dynamics_cancel":\
        await query.edit_message_text("\uc0\u1055 \u1086 \u1089 \u1090 \u1088 \u1086 \u1077 \u1085 \u1080 \u1077  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 \u1072  \u1086 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086 .")\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=sales_reports_keyboard())\
        return ConversationHandler.END\
\
    if data.startswith("dynamics_year_"):\
        year = int(data.split("_")[-1])\
        await query.edit_message_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...")\
        from bot.handlers.charts import generate_sales_chart\
        chart_buf = await generate_sales_chart([year])\
        if chart_buf:\
            await query.message.reply_photo(photo=chart_buf, caption=f"\uc0\u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074  \u1079 \u1072  \{year\} \u1075 \u1086 \u1076 ")\
        else:\
            await query.message.reply_text("\uc0\u10060  \u1053 \u1077  \u1091 \u1076 \u1072 \u1083 \u1086 \u1089 \u1100  \u1087 \u1086 \u1089 \u1090 \u1088 \u1086 \u1080 \u1090 \u1100  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 .")\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=sales_reports_keyboard())\
        return ConversationHandler.END\
\
    # \uc0\u1045 \u1089 \u1083 \u1080  \u1085 \u1080 \u1095 \u1077 \u1075 \u1086  \u1085 \u1077  \u1087 \u1086 \u1076 \u1086 \u1096 \u1083 \u1086  \'96 \u1080 \u1075 \u1085 \u1086 \u1088 \u1080 \u1088 \u1091 \u1077 \u1084  (\u1101 \u1090 \u1086  \u1084 \u1086 \u1075 \u1091 \u1090  \u1073 \u1099 \u1090 \u1100  callback'\u1080  \u1076 \u1083 \u1103  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074 )\
    await query.edit_message_text("\uc0\u10060  \u1053 \u1077 \u1080 \u1079 \u1074 \u1077 \u1089 \u1090 \u1085 \u1072 \u1103  \u1082 \u1086 \u1084 \u1072 \u1085 \u1076 \u1072 .")\
    return ConversationHandler.END\
\
# ---------- \uc0\u1044 \u1048 \u1040 \u1051 \u1054 \u1043  \u1044 \u1048 \u1053 \u1040 \u1052 \u1048 \u1050 \u1048  \u1055 \u1056 \u1054 \u1044 \u1040 \u1046  (\u1076 \u1080 \u1072 \u1087 \u1072 \u1079 \u1086 \u1085 ) ----------\
async def dynamics_range_start(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    text = update.message.text.strip()\
    if not text.isdigit():\
        await update.message.reply_text("\uc0\u10060  \u1055 \u1086 \u1078 \u1072 \u1083 \u1091 \u1081 \u1089 \u1090 \u1072 , \u1074 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  \u1095 \u1080 \u1089 \u1083 \u1086  (\u1075 \u1086 \u1076 ).")\
        return WAITING_DYNAMICS_RANGE_START\
    year = int(text)\
    if year < 2000 or year > get_moscow_today().year + 1:\
        await update.message.reply_text("\uc0\u10060  \u1053 \u1077 \u1082 \u1086 \u1088 \u1088 \u1077 \u1082 \u1090 \u1085 \u1099 \u1081  \u1075 \u1086 \u1076 . \u1042 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  \u1075 \u1086 \u1076  \u1086 \u1090  2000 \u1076 \u1086  \u1090 \u1077 \u1082 \u1091 \u1097 \u1077 \u1075 \u1086 .")\
        return WAITING_DYNAMICS_RANGE_START\
    context.user_data['dynamics_range_start'] = year\
    await update.message.reply_text("\uc0\u1042 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  \u1082 \u1086 \u1085 \u1077 \u1095 \u1085 \u1099 \u1081  \u1075 \u1086 \u1076  (\u1074 \u1082 \u1083 \u1102 \u1095 \u1080 \u1090 \u1077 \u1083 \u1100 \u1085 \u1086 ):")\
    return WAITING_DYNAMICS_RANGE_END\
\
async def dynamics_range_end(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    text = update.message.text.strip()\
    if not text.isdigit():\
        await update.message.reply_text("\uc0\u10060  \u1055 \u1086 \u1078 \u1072 \u1083 \u1091 \u1081 \u1089 \u1090 \u1072 , \u1074 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  \u1095 \u1080 \u1089 \u1083 \u1086  (\u1075 \u1086 \u1076 ).")\
        return WAITING_DYNAMICS_RANGE_END\
    year_end = int(text)\
    year_start = context.user_data.get('dynamics_range_start')\
    if year_start is None:\
        await update.message.reply_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072 : \u1085 \u1072 \u1095 \u1072 \u1083 \u1100 \u1085 \u1099 \u1081  \u1075 \u1086 \u1076  \u1085 \u1077  \u1085 \u1072 \u1081 \u1076 \u1077 \u1085 . \u1053 \u1072 \u1095 \u1085 \u1080 \u1090 \u1077  \u1079 \u1072 \u1085 \u1086 \u1074 \u1086 .")\
        return ConversationHandler.END\
    if year_end < year_start:\
        await update.message.reply_text("\uc0\u10060  \u1050 \u1086 \u1085 \u1077 \u1095 \u1085 \u1099 \u1081  \u1075 \u1086 \u1076  \u1076 \u1086 \u1083 \u1078 \u1077 \u1085  \u1073 \u1099 \u1090 \u1100  \u1085 \u1077  \u1084 \u1077 \u1085 \u1100 \u1096 \u1077  \u1085 \u1072 \u1095 \u1072 \u1083 \u1100 \u1085 \u1086 \u1075 \u1086 .")\
        return WAITING_DYNAMICS_RANGE_END\
    years = list(range(year_start, year_end + 1))\
    if len(years) > 10:\
        await update.message.reply_text("\uc0\u9888 \u65039  \u1057 \u1083 \u1080 \u1096 \u1082 \u1086 \u1084  \u1084 \u1085 \u1086 \u1075 \u1086  \u1083 \u1077 \u1090  (\u1084 \u1072 \u1082 \u1089 \u1080 \u1084 \u1091 \u1084  10). \u1055 \u1086 \u1078 \u1072 \u1083 \u1091 \u1081 \u1089 \u1090 \u1072 , \u1074 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1084 \u1077 \u1085 \u1100 \u1096 \u1080 \u1081  \u1076 \u1080 \u1072 \u1087 \u1072 \u1079 \u1086 \u1085 .")\
        return ConversationHandler.END\
    progress_msg = await update.message.reply_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...")\
    from bot.handlers.charts import generate_sales_chart\
    chart_buf = await generate_sales_chart(years)\
    await progress_msg.delete()\
    if chart_buf:\
        caption = f"\uc0\u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074  \u1079 \u1072  \{year_start\}-\{year_end\} \u1075 \u1075 ."\
        await update.message.reply_photo(photo=chart_buf, caption=caption)\
    else:\
        await update.message.reply_text("\uc0\u10060  \u1053 \u1077  \u1091 \u1076 \u1072 \u1083 \u1086 \u1089 \u1100  \u1087 \u1086 \u1089 \u1090 \u1088 \u1086 \u1080 \u1090 \u1100  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 .")\
    await update.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=sales_reports_keyboard())\
    context.user_data.pop('dynamics_range_start', None)\
    return ConversationHandler.END\
\
# ---------- \uc0\u1042 \u1057 \u1055 \u1054 \u1052 \u1054 \u1043 \u1040 \u1058 \u1045 \u1051 \u1068 \u1053 \u1067 \u1045  \u1060 \u1059 \u1053 \u1050 \u1062 \u1048 \u1048  \u1044 \u1051 \u1071  \u1055 \u1054 \u1051 \u1059 \u1063 \u1045 \u1053 \u1048 \u1071  \u1052 \u1045 \u1058 \u1056 \u1048 \u1050  (\u1080 \u1089 \u1087 \u1086 \u1083 \u1100 \u1079 \u1091 \u1102 \u1090 \u1089 \u1103  \u1074 \u1099 \u1096 \u1077 ) ----------\
# \uc0\u1069 \u1090 \u1080  \u1092 \u1091 \u1085 \u1082 \u1094 \u1080 \u1080  \u1087 \u1077 \u1088 \u1077 \u1085 \u1077 \u1089 \u1077 \u1085 \u1099  \u1080 \u1079  \u1089 \u1090 \u1072 \u1088 \u1086 \u1075 \u1086  bot.py (\u1088 \u1072 \u1079 \u1076 \u1077 \u1083  "\u1040 \u1057 \u1048 \u1053 \u1061 \u1056 \u1054 \u1053 \u1053 \u1067 \u1045  \u1060 \u1059 \u1053 \u1050 \u1062 \u1048 \u1048  \u1044 \u1051 \u1071  \u1055 \u1054 \u1051 \u1059 \u1063 \u1045 \u1053 \u1048 \u1071  \u1052 \u1045 \u1058 \u1056 \u1048 \u1050 ")\
# \uc0\u1054 \u1085 \u1080  \u1085 \u1091 \u1078 \u1085 \u1099  \u1076 \u1083 \u1103  \u1086 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1095 \u1080 \u1082 \u1086 \u1074  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \
\
async def get_metrics_for_date(date_str, progress_callback=None):\
    today = get_moscow_today()\
    start = (today - datetime.timedelta(days=183)).strftime("%Y-%m-%d")\
    end = today.strftime("%Y-%m-%d")\
    postings_task = fetch_postings(start, end, progress_callback)\
    ad_task = fetch_advertising_expense(date_str, date_str, progress_callback)\
    fin_task = fetch_finance_transactions(date_str, date_str, progress_callback)\
    postings, ad_expense, transactions = await asyncio.gather(postings_task, ad_task, fin_task)\
    if progress_callback:\
        await progress_callback("\uc0\u1040 \u1075 \u1088 \u1077 \u1075 \u1080 \u1088 \u1091 \u1077 \u1084  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...", 80)\
    agg = aggregate_postings(postings, date_from=date_str, date_to=date_str)\
    metrics = agg.get(date_str, \{\})\
    metrics["ad_expense"] = ad_expense if ad_expense is not None else 0.0\
    revenue = metrics.get("ordered_sum", 0)\
    if revenue > 0 and ad_expense is not None:\
        metrics["drr"] = (ad_expense / revenue) * 100\
    else:\
        metrics["drr"] = None\
    delivered_revenue = metrics.get("delivered_sum", 0)\
    if delivered_revenue > 0 and ad_expense is not None:\
        metrics["effective_drr"] = (ad_expense / delivered_revenue) * 100\
    else:\
        metrics["effective_drr"] = None\
\
    expenses = aggregate_finance_expenses(transactions)\
    metrics["expenses"] = expenses\
    if progress_callback:\
        await progress_callback("\uc0\u1043 \u1086 \u1090 \u1086 \u1074 \u1086 ", 100)\
    return metrics\
\
async def get_metrics_for_period(date_from, date_to, progress_callback=None):\
    # \uc0\u1048 \u1089 \u1087 \u1086 \u1083 \u1100 \u1079 \u1091 \u1077 \u1084  \u1087 \u1072 \u1088 \u1072 \u1083 \u1083 \u1077 \u1083 \u1100 \u1085 \u1091 \u1102  \u1079 \u1072 \u1075 \u1088 \u1091 \u1079 \u1082 \u1091  \u1080 \u1079  aggregator\
    from services.aggregator import fetch_metrics_for_period_parallel\
    return await fetch_metrics_for_period_parallel(date_from, date_to, progress_callback)}