{\rtf1\ansi\ansicpg1251\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw3288\paperh2267\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import datetime\
import re\
import asyncio\
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove\
from telegram.ext import ContextTypes, ConversationHandler\
\
from config import VERSION\
from utils.logger import write_log\
from utils.validators import (\
    validate_date, validate_period, create_calendar,\
    get_moscow_today, get_current_time_msk\
)\
from utils.managers import has_access, is_admin, is_manager, get_manager_info\
from services.aggregator import aggregate_products\
from services.formatter import (\
    format_top_products, format_products_summary,\
    format_product_combined, get_product_data_for_date,\
    get_product_data_for_period\
)\
from api.seller import fetch_postings\
from bot.keyboards import (\
    products_reports_keyboard, main_admin_keyboard, main_user_keyboard\
)\
from bot.states import (\
    WAITING_PRODUCT_DATE, WAITING_PRODUCT_PERIOD_TYPE,\
    WAITING_PRODUCT_PERIOD_START, WAITING_PRODUCT_PERIOD_END,\
    WAITING_PRODUCT_YEAR, WAITING_PRODUCT_MONTH,\
    WAITING_PRODUCT_QUARTER, WAITING_PRODUCT_YEAR_SELECT,\
    WAITING_PRODUCT_SELECT, WAITING_PRODUCT_METRIC,\
    WAITING_PRODUCT_PERIOD_CHOICE, WAITING_PRODUCT_SINGLE_YEAR,\
    WAITING_PRODUCT_RANGE_START, WAITING_PRODUCT_RANGE_END\
)\
\
# ---------- \uc0\u1042 \u1057 \u1055 \u1054 \u1052 \u1054 \u1043 \u1040 \u1058 \u1045 \u1051 \u1068 \u1053 \u1067 \u1045  \u1060 \u1059 \u1053 \u1050 \u1062 \u1048 \u1048  ----------\
async def get_top_products_for_select(days=30):\
    """\uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1097 \u1072 \u1077 \u1090  \u1090 \u1086 \u1087 -20 \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  \u1079 \u1072  \u1087 \u1086 \u1089 \u1083 \u1077 \u1076 \u1085 \u1080 \u1077  N \u1076 \u1085 \u1077 \u1081  \u1076 \u1083 \u1103  \u1074 \u1099 \u1073 \u1086 \u1088 \u1072 ."""\
    now = get_current_time_msk()\
    end_date = now.date().isoformat()\
    start_date = (now.date() - datetime.timedelta(days=days)).isoformat()\
    postings = await fetch_postings(start_date, end_date)\
    products = aggregate_products(\
        postings,\
        date_from=start_date,\
        date_to=end_date,\
        time_limit=now.time(),\
        apply_limit_on_day=end_date\
    )\
    sorted_items = sorted(products.items(), key=lambda x: x[1]["ordered_sum"], reverse=True)[:20]\
    return [(sku, stats) for sku, stats in sorted_items]\
\
# ---------- \uc0\u1054 \u1041 \u1056 \u1040 \u1041 \u1054 \u1058 \u1063 \u1048 \u1050 \u1048  \u1055 \u1054 \u1044 \u1052 \u1045 \u1053 \u1070  \u1058 \u1054 \u1042 \u1040 \u1056 \u1054 \u1042  ----------\
async def handle_products_reports(update: Update, context: ContextTypes.DEFAULT_TYPE):\
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
    if text == "\uc0\u55357 \u56517  \u1058 \u1086 \u1087  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  \u1079 \u1072  \u1089 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 ":\
        progress_msg = await update.message.reply_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...")\
        report = await format_product_combined()\
        await progress_msg.delete()\
        await update.message.reply_text(report)\
        return\
\
    if text == "\uc0\u55357 \u56518  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1076 \u1072 \u1090 \u1091  (\u1090 \u1086 \u1074 \u1072 \u1088 \u1099 )":\
        now = get_moscow_today()\
        keyboard = create_calendar(now.year, now.month, "pdate_")\
        await update.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1072 \u1090 \u1091  (\u1090 \u1086 \u1074 \u1072 \u1088 \u1099 ):", reply_markup=keyboard)\
        return WAITING_PRODUCT_DATE\
\
    if text == "\uc0\u55357 \u56522  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076  (\u1090 \u1086 \u1074 \u1072 \u1088 \u1099 )":\
        keyboard = InlineKeyboardMarkup([\
            [InlineKeyboardButton("\uc0\u55357 \u56787 \u65039  \u1055 \u1086  \u1084 \u1077 \u1089 \u1103 \u1094 \u1072 \u1084 ", callback_data="pmonth")],\
            [InlineKeyboardButton("\uc0\u55357 \u56517  \u1055 \u1086  \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083 \u1072 \u1084 ", callback_data="pquarter")],\
            [InlineKeyboardButton("\uc0\u55357 \u56518  \u1055 \u1086  \u1075 \u1086 \u1076 \u1072 \u1084 ", callback_data="pyear")],\
            [InlineKeyboardButton("\uc0\u55357 \u56522  \u1055 \u1088 \u1086 \u1080 \u1079 \u1074 \u1086 \u1083 \u1100 \u1085 \u1099 \u1081  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 ", callback_data="pcustom")],\
            [InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="pcancel")]\
        ])\
        await update.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1090 \u1080 \u1087  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1072  \u1076 \u1083 \u1103  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074 :", reply_markup=keyboard)\
        return WAITING_PRODUCT_PERIOD_TYPE\
\
    if text == "\uc0\u55357 \u56520  \u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1091 ":\
        progress_msg = await update.message.reply_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1089 \u1087 \u1080 \u1089 \u1086 \u1082  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  \u1079 \u1072  \u1087 \u1086 \u1089 \u1083 \u1077 \u1076 \u1085 \u1080 \u1077  30 \u1076 \u1085 \u1077 \u1081 ...")\
        top_products = await get_top_products_for_select(days=30)\
        await progress_msg.delete()\
        if not top_products:\
            await update.message.reply_text("\uc0\u10060  \u1053 \u1077 \u1090  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093  \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 \u1093  \u1079 \u1072  \u1087 \u1086 \u1089 \u1083 \u1077 \u1076 \u1085 \u1080 \u1077  30 \u1076 \u1085 \u1077 \u1081 .")\
            return ConversationHandler.END\
        context.user_data['product_list'] = top_products\
        keyboard = []\
        for idx, (sku, stats) in enumerate(top_products, 1):\
            name = stats['name']\
            short_name = name[:12] + "..." if len(name) > 12 else name\
            offer_id = stats.get('offer_id', '')\
            if offer_id:\
                button_text = f"\{offer_id\} \{sku\} \{short_name\}"\
            else:\
                button_text = f"\{sku\} \{short_name\}"\
            keyboard.append([InlineKeyboardButton(button_text, callback_data=f"prod_\{sku\}")])\
        keyboard.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="prod_cancel")])\
        await update.message.reply_text(\
            "\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1090 \u1086 \u1074 \u1072 \u1088 , \u1085 \u1072 \u1078 \u1072 \u1074  \u1085 \u1072  \u1089 \u1086 \u1086 \u1090 \u1074 \u1077 \u1090 \u1089 \u1090 \u1074 \u1091 \u1102 \u1097 \u1091 \u1102  \u1082 \u1085 \u1086 \u1087 \u1082 \u1091 :",\
            reply_markup=InlineKeyboardMarkup(keyboard)\
        )\
        return WAITING_PRODUCT_SELECT\
\
    await update.message.reply_text("\uc0\u1053 \u1077 \u1080 \u1079 \u1074 \u1077 \u1089 \u1090 \u1085 \u1072 \u1103  \u1082 \u1086 \u1084 \u1072 \u1085 \u1076 \u1072 .")\
\
# ---------- \uc0\u1050 \u1054 \u1052 \u1040 \u1053 \u1044 \u1040  /top ----------\
async def top_products_command(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    chat_id = update.effective_chat.id\
    if not has_access(chat_id):\
        await update.message.reply_text("\uc0\u10060  \u1053 \u1077 \u1090  \u1076 \u1086 \u1089 \u1090 \u1091 \u1087 \u1072 ! \u1054 \u1073 \u1088 \u1072 \u1090 \u1080 \u1090 \u1077 \u1089 \u1100  \u1082  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088 \u1091 .")\
        return\
\
    now = get_current_time_msk()\
    today_date = now.date()\
    month_start = today_date.replace(day=1).isoformat()\
    today_str = today_date.isoformat()\
    postings = await fetch_postings(month_start, today_str)\
    products = aggregate_products(\
        postings,\
        date_from=month_start,\
        date_to=today_str,\
        time_limit=now.time(),\
        apply_limit_on_day=today_str\
    )\
\
    if not products:\
        await update.message.reply_text("\uc0\u10060  \u1053 \u1077 \u1090  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093  \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 \u1093  \u1079 \u1072  \u1090 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 .")\
        return\
\
    sorted_items = sorted(products.items(), key=lambda x: x[1]["ordered_sum"], reverse=True)[:10]\
    lines = ["\uc0\u55356 \u57286  <b>\u1058 \u1054 \u1055 -10 \u1058 \u1054 \u1042 \u1040 \u1056 \u1054 \u1042  \u1047 \u1040  \u1058 \u1045 \u1050 \u1059 \u1065 \u1048 \u1049  \u1052 \u1045 \u1057 \u1071 \u1062 </b>\\n"]\
    for i, (sku, stats) in enumerate(sorted_items, 1):\
        medal = "\uc0\u55358 \u56647 " if i == 1 else "\u55358 \u56648 " if i == 2 else "\u55358 \u56649 " if i == 3 else f"\{i\}."\
        name = stats.get("name", "\uc0\u1041 \u1077 \u1079  \u1085 \u1072 \u1079 \u1074 \u1072 \u1085 \u1080 \u1103 ")[:40]\
        offer_id = stats.get("offer_id", "")\
        revenue = stats["ordered_sum"]\
        units = stats["ordered_units"]\
        line = f"\{medal\} <b>\{name\}</b>"\
        if offer_id:\
            line += f" (\uc0\u1040 \u1088 \u1090 : \{offer_id\})"\
        line += f"\\n   \uc0\u1042 \u1099 \u1088 \u1091 \u1095 \u1082 \u1072 : \{revenue:,.0f\} \u8381 , \u1096 \u1090 : \{units\}\\n"\
        lines.append(line)\
    await update.message.reply_text("\\n".join(lines), parse_mode='HTML')\
\
# ---------- \uc0\u1050 \u1054 \u1052 \u1040 \u1053 \u1044 \u1040  /version ----------\
async def version_command(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    chat_id = update.effective_chat.id\
    if not has_access(chat_id):\
        await update.message.reply_text("\uc0\u10060  \u1053 \u1077 \u1090  \u1076 \u1086 \u1089 \u1090 \u1091 \u1087 \u1072 .")\
        return\
    await update.message.reply_text(f"\uc0\u55358 \u56598  \u1042 \u1077 \u1088 \u1089 \u1080 \u1103  \u1073 \u1086 \u1090 \u1072 : \{VERSION\}")\
\
# ---------- \uc0\u1054 \u1041 \u1056 \u1040 \u1041 \u1054 \u1058 \u1063 \u1048 \u1050 \u1048  \u1044 \u1048 \u1053 \u1040 \u1052 \u1048 \u1050 \u1048  \u1055 \u1054  \u1058 \u1054 \u1042 \u1040 \u1056 \u1059  ----------\
async def product_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    query = update.callback_query\
    await query.answer()\
    data = query.data\
    if data == "prod_cancel":\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1086 \u1088  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1086 \u1090 \u1084 \u1077 \u1085 \u1105 \u1085 .")\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=products_reports_keyboard())\
        return ConversationHandler.END\
\
    if data.startswith("prod_"):\
        sku = data[5:]\
        context.user_data['product_sku'] = sku\
        product_list = context.user_data.get('product_list', [])\
        product_name = "\uc0\u1058 \u1086 \u1074 \u1072 \u1088 "\
        for p_sku, stats in product_list:\
            if p_sku == sku:\
                product_name = stats['name'][:40]\
                break\
        context.user_data['product_name'] = product_name\
\
        keyboard = [\
            [InlineKeyboardButton("\uc0\u1047 \u1072 \u1082 \u1072 \u1079 \u1072 \u1085 \u1086  (\u8381 )", callback_data="metric_ordered_sum")],\
            [InlineKeyboardButton("\uc0\u1047 \u1072 \u1082 \u1072 \u1079 \u1072 \u1085 \u1086  (\u1096 \u1090 .)", callback_data="metric_ordered_units")],\
            [InlineKeyboardButton("\uc0\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1086  (\u8381 )", callback_data="metric_delivered_sum")],\
            [InlineKeyboardButton("\uc0\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1086  (\u1096 \u1090 .)", callback_data="metric_delivered_units")],\
            [InlineKeyboardButton("\uc0\u1054 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086  (\u8381 )", callback_data="metric_canceled_sum")],\
            [InlineKeyboardButton("\uc0\u1054 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086  (\u1096 \u1090 .)", callback_data="metric_canceled_units")],\
            [InlineKeyboardButton("\uc0\u1057 \u1088 \u1077 \u1076 \u1085 \u1080 \u1081  \u1095 \u1077 \u1082  (\u8381 )", callback_data="metric_avg_check")],\
            [InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="metric_cancel")]\
        ]\
        await query.edit_message_text(\
            f"\uc0\u1042 \u1099 \u1073 \u1088 \u1072 \u1085  \u1090 \u1086 \u1074 \u1072 \u1088 : \{product_name\} (SKU: \{sku\})\\n\u1058 \u1077 \u1087 \u1077 \u1088 \u1100  \u1074 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1084 \u1077 \u1090 \u1088 \u1080 \u1082 \u1091  \u1076 \u1083 \u1103  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 \u1072 :",\
            reply_markup=InlineKeyboardMarkup(keyboard)\
        )\
        return WAITING_PRODUCT_METRIC\
\
async def product_metric_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    query = update.callback_query\
    await query.answer()\
    data = query.data\
    if data == "metric_cancel":\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1086 \u1088  \u1084 \u1077 \u1090 \u1088 \u1080 \u1082 \u1080  \u1086 \u1090 \u1084 \u1077 \u1085 \u1105 \u1085 .")\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=products_reports_keyboard())\
        return ConversationHandler.END\
\
    if data.startswith("metric_"):\
        metric = data[7:]\
        context.user_data['product_metric'] = metric\
\
        current_year = get_moscow_today().year\
        keyboard = [\
            [InlineKeyboardButton("\uc0\u55357 \u56517  \u1058 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1075 \u1086 \u1076 ", callback_data="period_current")],\
            [InlineKeyboardButton("\uc0\u55357 \u56518  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1075 \u1086 \u1076 ", callback_data="period_select_year")],\
            [InlineKeyboardButton("\uc0\u55357 \u56522  \u1044 \u1080 \u1072 \u1087 \u1072 \u1079 \u1086 \u1085  \u1083 \u1077 \u1090 ", callback_data="period_range")],\
            [InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="period_cancel")]\
        ]\
        await query.edit_message_text(\
            "\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076  \u1076 \u1083 \u1103  \u1087 \u1086 \u1089 \u1090 \u1088 \u1086 \u1077 \u1085 \u1080 \u1103  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 \u1072 :",\
            reply_markup=InlineKeyboardMarkup(keyboard)\
        )\
        return WAITING_PRODUCT_PERIOD_CHOICE\
\
async def product_period_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    query = update.callback_query\
    await query.answer()\
    data = query.data\
    if data == "period_cancel":\
        await query.edit_message_text("\uc0\u1055 \u1086 \u1089 \u1090 \u1088 \u1086 \u1077 \u1085 \u1080 \u1077  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 \u1072  \u1086 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086 .")\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=products_reports_keyboard())\
        return ConversationHandler.END\
\
    if data == "period_current":\
        current_year = get_moscow_today().year\
        sku = context.user_data.get('product_sku')\
        metric = context.user_data.get('product_metric')\
        if not sku or not metric:\
            await query.edit_message_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072 : \u1087 \u1086 \u1090 \u1077 \u1088 \u1103 \u1085 \u1099  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 . \u1053 \u1072 \u1095 \u1085 \u1080 \u1090 \u1077  \u1079 \u1072 \u1085 \u1086 \u1074 \u1086 .")\
            return ConversationHandler.END\
        await query.edit_message_text("\uc0\u9203  \u1057 \u1090 \u1088 \u1086 \u1102  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 ...")\
        from bot.handlers.charts import generate_product_chart_by_metric\
        chart_buf = await generate_product_chart_by_metric(sku, metric, [current_year])\
        if chart_buf:\
            context.user_data['product_year'] = current_year\
            caption = f"\uc0\u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1091  (SKU: \{sku\}) \u1079 \u1072  \{current_year\} \u1075 \u1086 \u1076 "\
            keyboard = [\
                [InlineKeyboardButton("\uc0\u1044 \u1088 \u1091 \u1075 \u1072 \u1103  \u1084 \u1077 \u1090 \u1088 \u1080 \u1082 \u1072 ", callback_data=f"change_metric_\{sku\}")],\
                [InlineKeyboardButton("\uc0\u1044 \u1088 \u1091 \u1075 \u1086 \u1081  \u1075 \u1086 \u1076 ", callback_data=f"change_year_\{sku\}")],\
                [InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="product_chart_back")]\
            ]\
            await query.message.reply_photo(photo=chart_buf, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))\
            await query.delete_message()\
        else:\
            await query.edit_message_text("\uc0\u10060  \u1053 \u1077 \u1090  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093  \u1076 \u1083 \u1103  \u1087 \u1086 \u1089 \u1090 \u1088 \u1086 \u1077 \u1085 \u1080 \u1103  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 \u1072 .")\
        return ConversationHandler.END\
\
    elif data == "period_select_year":\
        current_year = get_moscow_today().year\
        years = list(range(current_year - 9, current_year + 1))\
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"year_\{y\}")] for y in years]\
        buttons.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="period_cancel")])\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1075 \u1086 \u1076 :", reply_markup=InlineKeyboardMarkup(buttons))\
        return WAITING_PRODUCT_SINGLE_YEAR\
\
    elif data == "period_range":\
        await query.edit_message_text("\uc0\u1042 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  \u1085 \u1072 \u1095 \u1072 \u1083 \u1100 \u1085 \u1099 \u1081  \u1075 \u1086 \u1076  (\u1085 \u1072 \u1087 \u1088 \u1080 \u1084 \u1077 \u1088 , 2020):")\
        return WAITING_PRODUCT_RANGE_START\
\
# ---------- \uc0\u1044 \u1048 \u1040 \u1051 \u1054 \u1043 \u1048  \u1044 \u1048 \u1053 \u1040 \u1052 \u1048 \u1050 \u1048  \u1055 \u1054  \u1058 \u1054 \u1042 \u1040 \u1056 \u1059  (\u1076 \u1080 \u1072 \u1087 \u1072 \u1079 \u1086 \u1085 ) ----------\
async def product_range_start(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    text = update.message.text.strip()\
    if not text.isdigit():\
        await update.message.reply_text("\uc0\u10060  \u1055 \u1086 \u1078 \u1072 \u1083 \u1091 \u1081 \u1089 \u1090 \u1072 , \u1074 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  \u1095 \u1080 \u1089 \u1083 \u1086  (\u1075 \u1086 \u1076 ).")\
        return WAITING_PRODUCT_RANGE_START\
    year = int(text)\
    if year < 2000 or year > get_moscow_today().year + 1:\
        await update.message.reply_text("\uc0\u10060  \u1053 \u1077 \u1082 \u1086 \u1088 \u1088 \u1077 \u1082 \u1090 \u1085 \u1099 \u1081  \u1075 \u1086 \u1076 . \u1042 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  \u1075 \u1086 \u1076  \u1086 \u1090  2000 \u1076 \u1086  \u1090 \u1077 \u1082 \u1091 \u1097 \u1077 \u1075 \u1086 .")\
        return WAITING_PRODUCT_RANGE_START\
    context.user_data['product_range_start'] = year\
    await update.message.reply_text("\uc0\u1042 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  \u1082 \u1086 \u1085 \u1077 \u1095 \u1085 \u1099 \u1081  \u1075 \u1086 \u1076  (\u1074 \u1082 \u1083 \u1102 \u1095 \u1080 \u1090 \u1077 \u1083 \u1100 \u1085 \u1086 ):")\
    return WAITING_PRODUCT_RANGE_END\
\
async def product_range_end(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    text = update.message.text.strip()\
    if not text.isdigit():\
        await update.message.reply_text("\uc0\u10060  \u1055 \u1086 \u1078 \u1072 \u1083 \u1091 \u1081 \u1089 \u1090 \u1072 , \u1074 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  \u1095 \u1080 \u1089 \u1083 \u1086  (\u1075 \u1086 \u1076 ).")\
        return WAITING_PRODUCT_RANGE_END\
    year_end = int(text)\
    year_start = context.user_data.get('product_range_start')\
    if year_start is None:\
        await update.message.reply_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072 : \u1085 \u1072 \u1095 \u1072 \u1083 \u1100 \u1085 \u1099 \u1081  \u1075 \u1086 \u1076  \u1085 \u1077  \u1085 \u1072 \u1081 \u1076 \u1077 \u1085 . \u1053 \u1072 \u1095 \u1085 \u1080 \u1090 \u1077  \u1079 \u1072 \u1085 \u1086 \u1074 \u1086 .")\
        return ConversationHandler.END\
    if year_end < year_start:\
        await update.message.reply_text("\uc0\u10060  \u1050 \u1086 \u1085 \u1077 \u1095 \u1085 \u1099 \u1081  \u1075 \u1086 \u1076  \u1076 \u1086 \u1083 \u1078 \u1077 \u1085  \u1073 \u1099 \u1090 \u1100  \u1085 \u1077  \u1084 \u1077 \u1085 \u1100 \u1096 \u1077  \u1085 \u1072 \u1095 \u1072 \u1083 \u1100 \u1085 \u1086 \u1075 \u1086 .")\
        return WAITING_PRODUCT_RANGE_END\
    years = list(range(year_start, year_end + 1))\
    if len(years) > 10:\
        await update.message.reply_text("\uc0\u9888 \u65039  \u1057 \u1083 \u1080 \u1096 \u1082 \u1086 \u1084  \u1084 \u1085 \u1086 \u1075 \u1086  \u1083 \u1077 \u1090  (\u1084 \u1072 \u1082 \u1089 \u1080 \u1084 \u1091 \u1084  10). \u1055 \u1086 \u1078 \u1072 \u1083 \u1091 \u1081 \u1089 \u1090 \u1072 , \u1074 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1084 \u1077 \u1085 \u1100 \u1096 \u1080 \u1081  \u1076 \u1080 \u1072 \u1087 \u1072 \u1079 \u1086 \u1085 .")\
        return ConversationHandler.END\
\
    sku = context.user_data.get('product_sku')\
    metric = context.user_data.get('product_metric')\
    if not sku or not metric:\
        await update.message.reply_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072 : \u1087 \u1086 \u1090 \u1077 \u1088 \u1103 \u1085 \u1099  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 . \u1053 \u1072 \u1095 \u1085 \u1080 \u1090 \u1077  \u1079 \u1072 \u1085 \u1086 \u1074 \u1086 .")\
        return ConversationHandler.END\
    progress_msg = await update.message.reply_text("\uc0\u9203  \u1057 \u1090 \u1088 \u1086 \u1102  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 ...")\
    from bot.handlers.charts import generate_product_chart_by_metric\
    chart_buf = await generate_product_chart_by_metric(sku, metric, years)\
    await progress_msg.delete()\
    if chart_buf:\
        caption = f"\uc0\u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1091  (SKU: \{sku\}) \u1079 \u1072  \{year_start\}-\{year_end\} \u1075 \u1075 ."\
        keyboard = [\
            [InlineKeyboardButton("\uc0\u1044 \u1088 \u1091 \u1075 \u1072 \u1103  \u1084 \u1077 \u1090 \u1088 \u1080 \u1082 \u1072 ", callback_data=f"change_metric_\{sku\}")],\
            [InlineKeyboardButton("\uc0\u1044 \u1088 \u1091 \u1075 \u1086 \u1081  \u1075 \u1086 \u1076 ", callback_data=f"change_year_\{sku\}")],\
            [InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="product_chart_back")]\
        ]\
        await update.message.reply_photo(photo=chart_buf, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))\
    else:\
        await update.message.reply_text("\uc0\u10060  \u1053 \u1077 \u1090  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093  \u1076 \u1083 \u1103  \u1087 \u1086 \u1089 \u1090 \u1088 \u1086 \u1077 \u1085 \u1080 \u1103  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 \u1072 .")\
    await update.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=products_reports_keyboard())\
    context.user_data.pop('product_sku', None)\
    context.user_data.pop('product_metric', None)\
    context.user_data.pop('product_name', None)\
    context.user_data.pop('product_range_start', None)\
    return ConversationHandler.END\
\
# ---------- \uc0\u1048 \u1053 \u1058 \u1045 \u1056 \u1040 \u1050 \u1058 \u1048 \u1042 \u1053 \u1067 \u1045  \u1043 \u1056 \u1040 \u1060 \u1048 \u1050 \u1048  (\u1087 \u1077 \u1088 \u1077 \u1082 \u1083 \u1102 \u1095 \u1077 \u1085 \u1080 \u1077  \u1084 \u1077 \u1090 \u1088 \u1080 \u1082 /\u1075 \u1086 \u1076 \u1086 \u1074 ) ----------\
async def product_chart_interactive_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    query = update.callback_query\
    await query.answer()\
    data = query.data\
    if data == "product_chart_back":\
        await query.message.delete()\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=products_reports_keyboard())\
        return ConversationHandler.END\
\
    if data.startswith("change_metric_"):\
        sku = data.split("_")[-1]\
        await query.message.delete()\
        keyboard = [\
            [InlineKeyboardButton("\uc0\u1047 \u1072 \u1082 \u1072 \u1079 \u1072 \u1085 \u1086  (\u8381 )", callback_data="metric_ordered_sum")],\
            [InlineKeyboardButton("\uc0\u1047 \u1072 \u1082 \u1072 \u1079 \u1072 \u1085 \u1086  (\u1096 \u1090 .)", callback_data="metric_ordered_units")],\
            [InlineKeyboardButton("\uc0\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1086  (\u8381 )", callback_data="metric_delivered_sum")],\
            [InlineKeyboardButton("\uc0\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1086  (\u1096 \u1090 .)", callback_data="metric_delivered_units")],\
            [InlineKeyboardButton("\uc0\u1054 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086  (\u8381 )", callback_data="metric_canceled_sum")],\
            [InlineKeyboardButton("\uc0\u1054 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086  (\u1096 \u1090 .)", callback_data="metric_canceled_units")],\
            [InlineKeyboardButton("\uc0\u1057 \u1088 \u1077 \u1076 \u1085 \u1080 \u1081  \u1095 \u1077 \u1082  (\u8381 )", callback_data="metric_avg_check")],\
            [InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="product_chart_back")]\
        ]\
        await query.message.reply_text(f"\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1084 \u1077 \u1090 \u1088 \u1080 \u1082 \u1091  \u1076 \u1083 \u1103  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  SKU:\{sku\}:", reply_markup=InlineKeyboardMarkup(keyboard))\
        return WAITING_PRODUCT_METRIC\
\
    if data.startswith("change_year_"):\
        sku = data.split("_")[-1]\
        await query.message.delete()\
        current_year = get_moscow_today().year\
        years = list(range(current_year - 9, current_year + 1))\
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"year_\{y\}")] for y in years]\
        buttons.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="product_chart_back")])\
        await query.message.reply_text(f"\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1075 \u1086 \u1076  \u1076 \u1083 \u1103  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  SKU:\{sku\}:", reply_markup=InlineKeyboardMarkup(buttons))\
        return WAITING_PRODUCT_SINGLE_YEAR\
\
    if data.startswith("year_"):\
        year = int(data.split("_")[-1])\
        sku = context.user_data.get('product_sku')\
        metric = context.user_data.get('product_metric')\
        if not sku or not metric:\
            await query.message.reply_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072 : \u1087 \u1086 \u1090 \u1077 \u1088 \u1103 \u1085 \u1099  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 .")\
            return ConversationHandler.END\
        await query.message.delete()\
        progress_msg = await query.message.reply_text("\uc0\u9203  \u1057 \u1090 \u1088 \u1086 \u1102  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 ...")\
        from bot.handlers.charts import generate_product_chart_by_metric\
        chart_buf = await generate_product_chart_by_metric(sku, metric, [year])\
        await progress_msg.delete()\
        if chart_buf:\
            context.user_data['product_year'] = year\
            caption = f"\uc0\u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1091  (SKU: \{sku\}) \u1079 \u1072  \{year\} \u1075 \u1086 \u1076 "\
            keyboard = [\
                [InlineKeyboardButton("\uc0\u1044 \u1088 \u1091 \u1075 \u1072 \u1103  \u1084 \u1077 \u1090 \u1088 \u1080 \u1082 \u1072 ", callback_data=f"change_metric_\{sku\}")],\
                [InlineKeyboardButton("\uc0\u1044 \u1088 \u1091 \u1075 \u1086 \u1081  \u1075 \u1086 \u1076 ", callback_data=f"change_year_\{sku\}")],\
                [InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="product_chart_back")]\
            ]\
            await query.message.reply_photo(photo=chart_buf, caption=caption, reply_markup=InlineKeyboardMarkup(keyboard))\
        else:\
            await query.message.reply_text("\uc0\u10060  \u1053 \u1077 \u1090  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093  \u1076 \u1083 \u1103  \u1087 \u1086 \u1089 \u1090 \u1088 \u1086 \u1077 \u1085 \u1080 \u1103  \u1075 \u1088 \u1072 \u1092 \u1080 \u1082 \u1072 .")\
        return ConversationHandler.END\
\
# ---------- \uc0\u1054 \u1041 \u1056 \u1040 \u1041 \u1054 \u1058 \u1063 \u1048 \u1050 \u1048  INLINE CALLBACK \u1044 \u1051 \u1071  \u1058 \u1054 \u1042 \u1040 \u1056 \u1054 \u1042  ----------\
# \uc0\u1069 \u1090 \u1080  \u1086 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1095 \u1080 \u1082 \u1080  \u1080 \u1089 \u1087 \u1086 \u1083 \u1100 \u1079 \u1091 \u1102 \u1090 \u1089 \u1103  \u1074  handle_callback_query (\u1074  sales.py) \u1076 \u1083 \u1103  \u1090 \u1086 \u1074 \u1072 \u1088 \u1085 \u1099 \u1093  \u1088 \u1072 \u1079 \u1076 \u1077 \u1083 \u1086 \u1074 .\
# \uc0\u1052 \u1099  \u1073 \u1091 \u1076 \u1077 \u1084  \u1074 \u1099 \u1079 \u1099 \u1074 \u1072 \u1090 \u1100  \u1080 \u1093  \u1086 \u1090 \u1090 \u1091 \u1076 \u1072 , \u1087 \u1086 \u1101 \u1090 \u1086 \u1084 \u1091  \u1086 \u1085 \u1080  \u1076 \u1086 \u1083 \u1078 \u1085 \u1099  \u1073 \u1099 \u1090 \u1100  \u1076 \u1086 \u1089 \u1090 \u1091 \u1087 \u1085 \u1099 .\
# \uc0\u1044 \u1083 \u1103  \u1091 \u1076 \u1086 \u1073 \u1089 \u1090 \u1074 \u1072  \u1103  \u1076 \u1086 \u1073 \u1072 \u1074 \u1083 \u1102  \u1089 \u1102 \u1076 \u1072  \u1092 \u1091 \u1085 \u1082 \u1094 \u1080 \u1080  \u1076 \u1083 \u1103  \u1086 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1080  \u1090 \u1086 \u1074 \u1072 \u1088 \u1085 \u1099 \u1093  callback'\u1086 \u1074 ,\
# \uc0\u1072  \u1074  sales.py \u1080 \u1084 \u1087 \u1086 \u1088 \u1090 \u1080 \u1088 \u1091 \u1077 \u1084  \u1080 \u1093  \u1080  \u1074 \u1099 \u1079 \u1086 \u1074 \u1077 \u1084 .\
\
async def handle_product_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    """\uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1072 \u1090 \u1099 \u1074 \u1072 \u1077 \u1090  \u1074 \u1099 \u1073 \u1086 \u1088  \u1076 \u1072 \u1090 \u1099  \u1076 \u1083 \u1103  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  (pdate_)."""\
    query = update.callback_query\
    data = query.data\
    if data == "pdate_cancel":\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1086 \u1088  \u1076 \u1072 \u1090 \u1099  \u1086 \u1090 \u1084 \u1077 \u1085 \u1105 \u1085 .")\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=products_reports_keyboard())\
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
            return WAITING_PRODUCT_DATE\
        if action == "prev_month":\
            month -= 1\
            if month == 0: month = 12; year -= 1\
        else:\
            month += 1\
            if month == 13: month = 1; year += 1\
        keyboard = create_calendar(year, month, "pdate_")\
        await query.edit_message_reply_markup(reply_markup=keyboard)\
        return WAITING_PRODUCT_DATE\
\
    date_str = data[6:]  # \uc0\u1091 \u1073 \u1080 \u1088 \u1072 \u1077 \u1084  "pdate_"\
    if re.match(r"\\d\{4\}-\\d\{2\}-\\d\{2\}", date_str):\
        valid, result = validate_date(date_str)\
        if not valid:\
            await query.edit_message_text(result)\
            return WAITING_PRODUCT_DATE\
        progress_msg = await query.message.reply_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...")\
        products = await get_product_data_for_date(date_str)\
        await progress_msg.delete()\
        msg = format_top_products(products, f"\uc0\u1058 \u1086 \u1074 \u1072 \u1088 \u1099  \u1079 \u1072  \{date_str\}", limit=20)\
        summary = format_products_summary(products)\
        await query.edit_message_text(msg + "\\n\\n" + summary)\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=products_reports_keyboard())\
        return ConversationHandler.END\
    else:\
        await query.edit_message_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1092 \u1086 \u1088 \u1084 \u1072 \u1090 \u1072  \u1076 \u1072 \u1090 \u1099 .")\
        return WAITING_PRODUCT_DATE\
\
async def handle_product_period_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    """\uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1072 \u1090 \u1099 \u1074 \u1072 \u1077 \u1090  \u1074 \u1099 \u1073 \u1086 \u1088  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1072  \u1076 \u1083 \u1103  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  (pmonth, pquarter, pyear, pcustom)."""\
    query = update.callback_query\
    data = query.data\
    if data == "pmonth":\
        current_year = get_moscow_today().year\
        years = list(range(current_year - 9, current_year + 1))\
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"pyear_month_\{y\}")] for y in years]\
        buttons.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="pcancel")])\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1075 \u1086 \u1076 :", reply_markup=InlineKeyboardMarkup(buttons))\
        return WAITING_PRODUCT_YEAR\
    if data == "pquarter":\
        current_year = get_moscow_today().year\
        years = list(range(current_year - 9, current_year + 1))\
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"pyear_quarter_\{y\}")] for y in years]\
        buttons.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="pcancel")])\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1075 \u1086 \u1076 :", reply_markup=InlineKeyboardMarkup(buttons))\
        return WAITING_PRODUCT_YEAR\
    if data == "pyear":\
        current_year = get_moscow_today().year\
        years = list(range(current_year - 9, current_year + 1))\
        buttons = [[InlineKeyboardButton(str(y), callback_data=f"pyear_only_\{y\}")] for y in years]\
        buttons.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="pcancel")])\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1075 \u1086 \u1076 :", reply_markup=InlineKeyboardMarkup(buttons))\
        return WAITING_PRODUCT_YEAR_SELECT\
    if data == "pcustom":\
        now = get_moscow_today()\
        keyboard = create_calendar(now.year, now.month, "pstart_")\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1085 \u1072 \u1095 \u1072 \u1083 \u1100 \u1085 \u1091 \u1102  \u1076 \u1072 \u1090 \u1091 :", reply_markup=keyboard)\
        return WAITING_PRODUCT_PERIOD_START\
    if data == "pcancel":\
        await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1086 \u1088  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1072  \u1086 \u1090 \u1084 \u1077 \u1085 \u1105 \u1085 .")\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=products_reports_keyboard())\
        return ConversationHandler.END\
\
    if data.startswith("pyear_month_"):\
        year = int(data.split("_")[-1])\
        context.user_data['p_year'] = year\
        months = ["\uc0\u1071 \u1085 \u1074 \u1072 \u1088 \u1100 ", "\u1060 \u1077 \u1074 \u1088 \u1072 \u1083 \u1100 ", "\u1052 \u1072 \u1088 \u1090 ", "\u1040 \u1087 \u1088 \u1077 \u1083 \u1100 ", "\u1052 \u1072 \u1081 ", "\u1048 \u1102 \u1085 \u1100 ",\
                  "\uc0\u1048 \u1102 \u1083 \u1100 ", "\u1040 \u1074 \u1075 \u1091 \u1089 \u1090 ", "\u1057 \u1077 \u1085 \u1090 \u1103 \u1073 \u1088 \u1100 ", "\u1054 \u1082 \u1090 \u1103 \u1073 \u1088 \u1100 ", "\u1053 \u1086 \u1103 \u1073 \u1088 \u1100 ", "\u1044 \u1077 \u1082 \u1072 \u1073 \u1088 \u1100 "]\
        buttons = [[InlineKeyboardButton(name, callback_data=f"pmonth_\{i\}_\{year\}")] for i, name in enumerate(months, 1)]\
        buttons.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="pcancel")])\
        await query.edit_message_text(f"\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1084 \u1077 \u1089 \u1103 \u1094  \{year\}:", reply_markup=InlineKeyboardMarkup(buttons))\
        return WAITING_PRODUCT_MONTH\
    if data.startswith("pyear_quarter_"):\
        year = int(data.split("_")[-1])\
        context.user_data['p_year'] = year\
        quarters = ["1 \uc0\u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083  (\u1103 \u1085 \u1074 -\u1084 \u1072 \u1088 )", "2 \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083  (\u1072 \u1087 \u1088 -\u1080 \u1102 \u1085 )", "3 \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083  (\u1080 \u1102 \u1083 -\u1089 \u1077 \u1085 )", "4 \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083  (\u1086 \u1082 \u1090 -\u1076 \u1077 \u1082 )"]\
        buttons = [[InlineKeyboardButton(name, callback_data=f"pquarter_\{i\}_\{year\}")] for i, name in enumerate(quarters, 1)]\
        buttons.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data="pcancel")])\
        await query.edit_message_text(f"\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083  \{year\}:", reply_markup=InlineKeyboardMarkup(buttons))\
        return WAITING_PRODUCT_QUARTER\
\
    if data.startswith("pyear_only_"):\
        year = int(data.split("_")[-1])\
        first_day = datetime.date(year, 1, 1)\
        last_day = datetime.date(year, 12, 31)\
        progress_msg = await query.message.reply_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...")\
        products = await get_product_data_for_period(first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d"))\
        await progress_msg.delete()\
        msg = format_top_products(products, f"\uc0\u1058 \u1086 \u1074 \u1072 \u1088 \u1099  \u1079 \u1072  \{year\} \u1075 \u1086 \u1076 ", limit=20)\
        summary = format_products_summary(products)\
        await query.edit_message_text(msg + "\\n\\n" + summary)\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=products_reports_keyboard())\
        return ConversationHandler.END\
\
    if data.startswith("pmonth_"):\
        parts = data.split("_")\
        month_num, year = int(parts[1]), int(parts[2])\
        first_day = datetime.date(year, month_num, 1)\
        if month_num == 12:\
            last_day = datetime.date(year, 12, 31)\
        else:\
            last_day = datetime.date(year, month_num+1, 1) - datetime.timedelta(days=1)\
        date_from, date_to = first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")\
        progress_msg = await query.message.reply_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...")\
        products = await get_product_data_for_period(date_from, date_to)\
        await progress_msg.delete()\
        msg = format_top_products(products, f"\uc0\u1058 \u1086 \u1074 \u1072 \u1088 \u1099  \u1079 \u1072  \{first_day.strftime('%B %Y')\}", limit=20)\
        summary = format_products_summary(products)\
        await query.edit_message_text(msg + "\\n\\n" + summary)\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=products_reports_keyboard())\
        return ConversationHandler.END\
\
    if data.startswith("pquarter_"):\
        parts = data.split("_")\
        q, year = int(parts[1]), int(parts[2])\
        start_month = (q-1)*3 + 1\
        end_month = q*3\
        first_day = datetime.date(year, start_month, 1)\
        if end_month == 12:\
            last_day = datetime.date(year, 12, 31)\
        else:\
            last_day = datetime.date(year, end_month+1, 1) - datetime.timedelta(days=1)\
        date_from, date_to = first_day.strftime("%Y-%m-%d"), last_day.strftime("%Y-%m-%d")\
        progress_msg = await query.message.reply_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...")\
        products = await get_product_data_for_period(date_from, date_to)\
        await progress_msg.delete()\
        msg = format_top_products(products, f"\uc0\u1058 \u1086 \u1074 \u1072 \u1088 \u1099  \u1079 \u1072  \{q\} \u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083  \{year\}", limit=20)\
        summary = format_products_summary(products)\
        await query.edit_message_text(msg + "\\n\\n" + summary)\
        await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=products_reports_keyboard())\
        return ConversationHandler.END\
\
    if data.startswith("pstart_"):\
        if data == "pstart_cancel":\
            await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1086 \u1088  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1072  \u1086 \u1090 \u1084 \u1077 \u1085 \u1105 \u1085 .")\
            await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=products_reports_keyboard())\
            return ConversationHandler.END\
        if "prev_month" in data or "next_month" in data:\
            match = re.search(r'prev_month_(\\d+)_(\\d+)|next_month_(\\d+)_(\\d+)', data)\
            if match:\
                if match.group(1) and match.group(2):\
                    year = int(match.group(1)); month = int(match.group(2)); action = "prev_month"\
                else:\
                    year = int(match.group(3)); month = int(match.group(4)); action = "next_month"\
            else:\
                await query.edit_message_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1092 \u1086 \u1088 \u1084 \u1072 \u1090 \u1072  \u1085 \u1072 \u1074 \u1080 \u1075 \u1072 \u1094 \u1080 \u1080 .")\
                return WAITING_PRODUCT_PERIOD_START\
            if action == "prev_month":\
                month -= 1\
                if month == 0: month = 12; year -= 1\
            else:\
                month += 1\
                if month == 13: month = 1; year += 1\
            keyboard = create_calendar(year, month, "pstart_")\
            await query.edit_message_reply_markup(reply_markup=keyboard)\
            return WAITING_PRODUCT_PERIOD_START\
        date_str = data[7:]  # \uc0\u1091 \u1073 \u1080 \u1088 \u1072 \u1077 \u1084  "pstart_"\
        if re.match(r"\\d\{4\}-\\d\{2\}-\\d\{2\}", date_str):\
            valid, result = validate_date(date_str)\
            if not valid:\
                await query.edit_message_text(result)\
                return WAITING_PRODUCT_PERIOD_START\
            context.user_data['p_start_date'] = date_str\
            now = get_moscow_today()\
            keyboard = create_calendar(now.year, now.month, "pend_")\
            await query.edit_message_text(f"\uc0\u1053 \u1072 \u1095 \u1072 \u1083 \u1086 : \{date_str\}\\n\u1058 \u1077 \u1087 \u1077 \u1088 \u1100  \u1074 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1082 \u1086 \u1085 \u1077 \u1095 \u1085 \u1091 \u1102  \u1076 \u1072 \u1090 \u1091 :", reply_markup=keyboard)\
            return WAITING_PRODUCT_PERIOD_END\
        else:\
            await query.edit_message_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1092 \u1086 \u1088 \u1084 \u1072 \u1090 \u1072  \u1076 \u1072 \u1090 \u1099 .")\
            return WAITING_PRODUCT_PERIOD_START\
\
    if data.startswith("pend_"):\
        if data == "pend_cancel":\
            await query.edit_message_text("\uc0\u1042 \u1099 \u1073 \u1086 \u1088  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1072  \u1086 \u1090 \u1084 \u1077 \u1085 \u1105 \u1085 .")\
            await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=products_reports_keyboard())\
            return ConversationHandler.END\
        if "prev_month" in data or "next_month" in data:\
            match = re.search(r'prev_month_(\\d+)_(\\d+)|next_month_(\\d+)_(\\d+)', data)\
            if match:\
                if match.group(1) and match.group(2):\
                    year = int(match.group(1)); month = int(match.group(2)); action = "prev_month"\
                else:\
                    year = int(match.group(3)); month = int(match.group(4)); action = "next_month"\
            else:\
                await query.edit_message_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1092 \u1086 \u1088 \u1084 \u1072 \u1090 \u1072  \u1085 \u1072 \u1074 \u1080 \u1075 \u1072 \u1094 \u1080 \u1080 .")\
                return WAITING_PRODUCT_PERIOD_END\
            if action == "prev_month":\
                month -= 1\
                if month == 0: month = 12; year -= 1\
            else:\
                month += 1\
                if month == 13: month = 1; year += 1\
            keyboard = create_calendar(year, month, "pend_")\
            await query.edit_message_reply_markup(reply_markup=keyboard)\
            return WAITING_PRODUCT_PERIOD_END\
        end_date_str = data[5:]  # \uc0\u1091 \u1073 \u1080 \u1088 \u1072 \u1077 \u1084  "pend_"\
        if re.match(r"\\d\{4\}-\\d\{2\}-\\d\{2\}", end_date_str):\
            valid, result = validate_date(end_date_str)\
            if not valid:\
                await query.edit_message_text(result)\
                return WAITING_PRODUCT_PERIOD_END\
            start_date = context.user_data.get('p_start_date')\
            if not start_date:\
                await query.edit_message_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072 : \u1085 \u1072 \u1095 \u1072 \u1083 \u1100 \u1085 \u1072 \u1103  \u1076 \u1072 \u1090 \u1072  \u1085 \u1077  \u1085 \u1072 \u1081 \u1076 \u1077 \u1085 \u1072 . \u1055 \u1086 \u1087 \u1088 \u1086 \u1073 \u1091 \u1081 \u1090 \u1077  \u1089 \u1085 \u1086 \u1074 \u1072 .")\
                return ConversationHandler.END\
            valid_period, msg = validate_period(start_date, end_date_str)\
            if not valid_period:\
                await query.edit_message_text(msg)\
                now = get_moscow_today()\
                keyboard = create_calendar(now.year, now.month, "pstart_")\
                await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1085 \u1072 \u1095 \u1072 \u1083 \u1100 \u1085 \u1091 \u1102  \u1076 \u1072 \u1090 \u1091  \u1079 \u1072 \u1085 \u1086 \u1074 \u1086 :", reply_markup=keyboard)\
                return WAITING_PRODUCT_PERIOD_START\
            progress_msg = await query.message.reply_text("\uc0\u9203  \u1047 \u1072 \u1075 \u1088 \u1091 \u1078 \u1072 \u1102  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077 ...")\
            products = await get_product_data_for_period(start_date, end_date_str)\
            await progress_msg.delete()\
            msg = format_top_products(products, f"\uc0\u1058 \u1086 \u1074 \u1072 \u1088 \u1099  \u1079 \u1072  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076  \{start_date\} \'96 \{end_date_str\}", limit=20)\
            summary = format_products_summary(products)\
            await query.edit_message_text(msg + "\\n\\n" + summary)\
            await query.message.reply_text("\uc0\u1042 \u1099 \u1073 \u1077 \u1088 \u1080 \u1090 \u1077  \u1076 \u1077 \u1081 \u1089 \u1090 \u1074 \u1080 \u1077 :", reply_markup=products_reports_keyboard())\
            context.user_data.pop('p_start_date', None)\
            return ConversationHandler.END\
        else:\
            await query.edit_message_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1092 \u1086 \u1088 \u1084 \u1072 \u1090 \u1072  \u1076 \u1072 \u1090 \u1099 .")\
            return WAITING_PRODUCT_PERIOD_END\
\
    # \uc0\u1045 \u1089 \u1083 \u1080  \u1085 \u1080 \u1095 \u1077 \u1075 \u1086  \u1085 \u1077  \u1087 \u1086 \u1076 \u1086 \u1096 \u1083 \u1086  \'96 \u1080 \u1075 \u1085 \u1086 \u1088 \u1080 \u1088 \u1091 \u1077 \u1084 \
    await query.edit_message_text("\uc0\u10060  \u1053 \u1077 \u1080 \u1079 \u1074 \u1077 \u1089 \u1090 \u1085 \u1072 \u1103  \u1082 \u1086 \u1084 \u1072 \u1085 \u1076 \u1072 .")\
    return ConversationHandler.END}