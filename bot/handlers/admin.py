{\rtf1\ansi\ansicpg1251\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw3288\paperh2267\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 from telegram import Update, ReplyKeyboardRemove\
from telegram.ext import ContextTypes, ConversationHandler\
\
from config import VERSION, ADMIN_CHAT_ID\
from utils.managers import (\
    load_managers, save_managers, is_manager, add_manager, remove_manager,\
    is_admin, has_access\
)\
from bot.keyboards import main_admin_keyboard, admin_keyboard, main_user_keyboard\
from utils.logger import write_log\
\
# ---------- \uc0\u1054 \u1041 \u1056 \u1040 \u1041 \u1054 \u1058 \u1063 \u1048 \u1050  \u1052 \u1045 \u1053 \u1070  \u1040 \u1044 \u1052 \u1048 \u1053 \u1048 \u1057 \u1058 \u1056 \u1048 \u1056 \u1054 \u1042 \u1040 \u1053 \u1048 \u1071  ----------\
async def handle_admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    chat_id = update.effective_chat.id\
    if not is_admin(chat_id):\
        await update.message.reply_text("\uc0\u9940  \u1058 \u1086 \u1083 \u1100 \u1082 \u1086  \u1076 \u1083 \u1103  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088 \u1072 .")\
        return\
    text = update.message.text\
\
    if text == "\uc0\u55357 \u56523  \u1057 \u1087 \u1080 \u1089 \u1086 \u1082  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1086 \u1074 ":\
        managers = load_managers()\
        if not managers:\
            await update.message.reply_text("\uc0\u1057 \u1087 \u1080 \u1089 \u1086 \u1082  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1086 \u1074  \u1087 \u1091 \u1089 \u1090 .")\
        else:\
            lines = ["\uc0\u55357 \u56523  \u1057 \u1087 \u1080 \u1089 \u1086 \u1082  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1086 \u1074 :"]\
            for m in managers:\
                info = f"ID: \{m.get('id')\}"\
                if m.get('username'):\
                    info += f", @\{m.get('username')\}"\
                if m.get('first_name'):\
                    info += f", \{m.get('first_name')\}"\
                if m.get('phone'):\
                    info += f", \uc0\u55357 \u56542  \{m.get('phone')\}"\
                lines.append(info)\
            await update.message.reply_text("\\n".join(lines))\
    elif text == "\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ":\
        await update.message.reply_text(\
            f"\uc0\u1043 \u1083 \u1072 \u1074 \u1085 \u1086 \u1077  \u1084 \u1077 \u1085 \u1102 \\n\\n\u55358 \u56598  \u1042 \u1077 \u1088 \u1089 \u1080 \u1103  \u1073 \u1086 \u1090 \u1072 : \{VERSION\}",\
            reply_markup=main_admin_keyboard()\
        )\
    else:\
        await update.message.reply_text("\uc0\u1053 \u1077 \u1080 \u1079 \u1074 \u1077 \u1089 \u1090 \u1085 \u1072 \u1103  \u1082 \u1086 \u1084 \u1072 \u1085 \u1076 \u1072 .")\
\
# ---------- \uc0\u1044 \u1048 \u1040 \u1051 \u1054 \u1043  \u1044 \u1054 \u1041 \u1040 \u1042 \u1051 \u1045 \u1053 \u1048 \u1071  \u1052 \u1045 \u1053 \u1045 \u1044 \u1046 \u1045 \u1056 \u1040  ----------\
async def add_manager_start(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    await update.message.reply_text("\uc0\u1042 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  ID (\u1095 \u1080 \u1089 \u1083 \u1086 ) \u1080 \u1083 \u1080  username (\u1073 \u1077 \u1079  @):")\
    return ConversationHandler.WAITING_ADD_MANAGER  # \uc0\u1089 \u1086 \u1089 \u1090 \u1086 \u1103 \u1085 \u1080 \u1077  \u1076 \u1086 \u1083 \u1078 \u1085 \u1086  \u1073 \u1099 \u1090 \u1100  \u1086 \u1087 \u1088 \u1077 \u1076 \u1077 \u1083 \u1077 \u1085 \u1086  \u1074  bot/states.py\
\
async def add_manager_input(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    chat_id = update.effective_chat.id\
    if not is_admin(chat_id):\
        await update.message.reply_text("\uc0\u9940  \u1058 \u1086 \u1083 \u1100 \u1082 \u1086  \u1076 \u1083 \u1103  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088 \u1072 .")\
        return ConversationHandler.END\
    text = update.message.text.strip()\
    if not text:\
        await update.message.reply_text("\uc0\u10060  \u1042 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  ID \u1080 \u1083 \u1080  username.")\
        return ConversationHandler.WAITING_ADD_MANAGER\
    if text.isdigit():\
        user_id = int(text)\
        try:\
            user = await context.bot.get_chat(user_id)\
            username = user.username or ""\
            first_name = user.first_name or ""\
            last_name = user.last_name or ""\
        except Exception:\
            await update.message.reply_text(f"\uc0\u10060  \u1053 \u1077  \u1091 \u1076 \u1072 \u1083 \u1086 \u1089 \u1100  \u1085 \u1072 \u1081 \u1090 \u1080  \u1087 \u1086 \u1083 \u1100 \u1079 \u1086 \u1074 \u1072 \u1090 \u1077 \u1083 \u1103  \u1089  ID \{user_id\}. \u1059 \u1073 \u1077 \u1076 \u1080 \u1090 \u1077 \u1089 \u1100 , \u1095 \u1090 \u1086  \u1086 \u1085  \u1091 \u1078 \u1077  \u1085 \u1072 \u1087 \u1080 \u1089 \u1072 \u1083  \u1073 \u1086 \u1090 \u1091 .")\
            return ConversationHandler.WAITING_ADD_MANAGER\
    else:\
        username = text.lstrip('@')\
        try:\
            user = await context.bot.get_chat(username)\
            user_id = user.id\
            first_name = user.first_name or ""\
            last_name = user.last_name or ""\
        except Exception:\
            await update.message.reply_text(f"\uc0\u10060  \u1053 \u1077  \u1091 \u1076 \u1072 \u1083 \u1086 \u1089 \u1100  \u1085 \u1072 \u1081 \u1090 \u1080  \u1087 \u1086 \u1083 \u1100 \u1079 \u1086 \u1074 \u1072 \u1090 \u1077 \u1083 \u1103  @\{username\}. \u1059 \u1073 \u1077 \u1076 \u1080 \u1090 \u1077 \u1089 \u1100 , \u1095 \u1090 \u1086  \u1086 \u1085  \u1091 \u1078 \u1077  \u1085 \u1072 \u1087 \u1080 \u1089 \u1072 \u1083  \u1073 \u1086 \u1090 \u1091 .")\
            return ConversationHandler.WAITING_ADD_MANAGER\
    if user_id == ADMIN_CHAT_ID:\
        await update.message.reply_text("\uc0\u10060  \u1040 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088  \u1091 \u1078 \u1077  \u1080 \u1084 \u1077 \u1077 \u1090  \u1076 \u1086 \u1089 \u1090 \u1091 \u1087 .")\
        return ConversationHandler.WAITING_ADD_MANAGER\
    context.user_data['new_manager'] = \{\
        'id': user_id,\
        'username': username,\
        'first_name': first_name,\
        'last_name': last_name\
    \}\
    await update.message.reply_text("\uc0\u1042 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  \u1085 \u1086 \u1084 \u1077 \u1088  \u1090 \u1077 \u1083 \u1077 \u1092 \u1086 \u1085 \u1072  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072  (\u1080 \u1083 \u1080  '-' \u1095 \u1090 \u1086 \u1073 \u1099  \u1087 \u1088 \u1086 \u1087 \u1091 \u1089 \u1090 \u1080 \u1090 \u1100 ):")\
    return ConversationHandler.WAITING_MANAGER_PHONE\
\
async def add_manager_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    chat_id = update.effective_chat.id\
    if not is_admin(chat_id):\
        await update.message.reply_text("\uc0\u9940  \u1058 \u1086 \u1083 \u1100 \u1082 \u1086  \u1076 \u1083 \u1103  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088 \u1072 .")\
        return ConversationHandler.END\
    phone = update.message.text.strip()\
    if phone == "-":\
        phone = ""\
    data = context.user_data.get('new_manager')\
    if not data:\
        await update.message.reply_text("\uc0\u10060  \u1054 \u1096 \u1080 \u1073 \u1082 \u1072 : \u1076 \u1072 \u1085 \u1085 \u1099 \u1077  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072  \u1087 \u1086 \u1090 \u1077 \u1088 \u1103 \u1085 \u1099 . \u1053 \u1072 \u1095 \u1085 \u1080 \u1090 \u1077  \u1079 \u1072 \u1085 \u1086 \u1074 \u1086 .")\
        return ConversationHandler.END\
    user_id = data['id']; username = data['username']; first_name = data['first_name']; last_name = data['last_name']\
    if add_manager(user_id, username, first_name, last_name, phone):\
        await update.message.reply_text(f"\uc0\u9989  \u1052 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088  \u1089  ID \{user_id\} (username: @\{username\}) \u1076 \u1086 \u1073 \u1072 \u1074 \u1083 \u1077 \u1085 .")\
    else:\
        await update.message.reply_text(f"\uc0\u9888 \u65039  \u1052 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088  \u1089  ID \{user_id\} \u1091 \u1078 \u1077  \u1089 \u1091 \u1097 \u1077 \u1089 \u1090 \u1074 \u1091 \u1077 \u1090 .")\
    context.user_data.pop('new_manager', None)\
    await update.message.reply_text("\uc0\u1059 \u1087 \u1088 \u1072 \u1074 \u1083 \u1077 \u1085 \u1080 \u1077  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072 \u1084 \u1080 :", reply_markup=admin_keyboard())\
    return ConversationHandler.END\
\
# ---------- \uc0\u1044 \u1048 \u1040 \u1051 \u1054 \u1043  \u1059 \u1044 \u1040 \u1051 \u1045 \u1053 \u1048 \u1071  \u1052 \u1045 \u1053 \u1045 \u1044 \u1046 \u1045 \u1056 \u1040  ----------\
async def remove_manager_start(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    await update.message.reply_text("\uc0\u1042 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  ID \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072  (\u1094 \u1080 \u1092 \u1088 \u1099 ):")\
    return ConversationHandler.WAITING_REMOVE_MANAGER\
\
async def remove_manager_input(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    chat_id = update.effective_chat.id\
    if not is_admin(chat_id):\
        await update.message.reply_text("\uc0\u9940  \u1058 \u1086 \u1083 \u1100 \u1082 \u1086  \u1076 \u1083 \u1103  \u1072 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088 \u1072 .")\
        return ConversationHandler.END\
    try:\
        user_id = int(update.message.text.strip())\
    except ValueError:\
        await update.message.reply_text("\uc0\u10060  \u1042 \u1074 \u1077 \u1076 \u1080 \u1090 \u1077  \u1095 \u1080 \u1089 \u1083 \u1086 .")\
        return ConversationHandler.WAITING_REMOVE_MANAGER\
    if user_id == ADMIN_CHAT_ID:\
        await update.message.reply_text("\uc0\u10060  \u1040 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1072 \u1090 \u1086 \u1088 \u1072  \u1085 \u1077 \u1083 \u1100 \u1079 \u1103  \u1091 \u1076 \u1072 \u1083 \u1080 \u1090 \u1100 .")\
        return ConversationHandler.WAITING_REMOVE_MANAGER\
    if remove_manager(user_id):\
        await update.message.reply_text(f"\uc0\u9989  \u1052 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088  \u1089  ID \{user_id\} \u1091 \u1076 \u1072 \u1083 \u1105 \u1085 .")\
    else:\
        await update.message.reply_text(f"\uc0\u10060  \u1052 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088  \u1089  ID \{user_id\} \u1085 \u1077  \u1085 \u1072 \u1081 \u1076 \u1077 \u1085 .")\
    await update.message.reply_text("\uc0\u1059 \u1087 \u1088 \u1072 \u1074 \u1083 \u1077 \u1085 \u1080 \u1077  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072 \u1084 \u1080 :", reply_markup=admin_keyboard())\
    return ConversationHandler.END\
\
# ---------- \uc0\u1054 \u1041 \u1065 \u1040 \u1071  \u1054 \u1058 \u1052 \u1045 \u1053 \u1040  \u1044 \u1051 \u1071  \u1044 \u1048 \u1040 \u1051 \u1054 \u1043 \u1054 \u1042  ----------\
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):\
    chat_id = update.effective_chat.id\
    if is_admin(chat_id):\
        keyboard = main_admin_keyboard()\
        text = f"\uc0\u1043 \u1083 \u1072 \u1074 \u1085 \u1086 \u1077  \u1084 \u1077 \u1085 \u1102 \\n\\n\u55358 \u56598  \u1042 \u1077 \u1088 \u1089 \u1080 \u1103  \u1073 \u1086 \u1090 \u1072 : \{VERSION\}"\
    else:\
        keyboard = main_user_keyboard()\
        text = f"\uc0\u1043 \u1083 \u1072 \u1074 \u1085 \u1086 \u1077  \u1084 \u1077 \u1085 \u1102 \\n\\n\u55358 \u56598  \u1042 \u1077 \u1088 \u1089 \u1080 \u1103  \u1073 \u1086 \u1090 \u1072 : \{VERSION\}"\
    await update.message.reply_text(text, reply_markup=keyboard)\
    return ConversationHandler.END}