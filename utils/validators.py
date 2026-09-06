{\rtf1\ansi\ansicpg1251\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw3288\paperh2267\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import datetime\
import calendar\
from telegram import InlineKeyboardButton, InlineKeyboardMarkup\
from config import MOSCOW_TZ\
\
def get_moscow_today():\
    """\uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1097 \u1072 \u1077 \u1090  \u1090 \u1077 \u1082 \u1091 \u1097 \u1091 \u1102  \u1076 \u1072 \u1090 \u1091  \u1087 \u1086  \u1084 \u1086 \u1089 \u1082 \u1086 \u1074 \u1089 \u1082 \u1086 \u1084 \u1091  \u1074 \u1088 \u1077 \u1084 \u1077 \u1085 \u1080 ."""\
    return datetime.datetime.now(MOSCOW_TZ).date()\
\
def get_current_time_msk():\
    """\uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1097 \u1072 \u1077 \u1090  \u1090 \u1077 \u1082 \u1091 \u1097 \u1077 \u1077  \u1074 \u1088 \u1077 \u1084 \u1103  \u1087 \u1086  \u1084 \u1086 \u1089 \u1082 \u1086 \u1074 \u1089 \u1082 \u1086 \u1084 \u1091  \u1074 \u1088 \u1077 \u1084 \u1077 \u1085 \u1080 ."""\
    return datetime.datetime.now(MOSCOW_TZ)\
\
def validate_date(date_str):\
    """\
    \uc0\u1055 \u1088 \u1086 \u1074 \u1077 \u1088 \u1103 \u1077 \u1090  \u1082 \u1086 \u1088 \u1088 \u1077 \u1082 \u1090 \u1085 \u1086 \u1089 \u1090 \u1100  \u1076 \u1072 \u1090 \u1099  \u1074  \u1092 \u1086 \u1088 \u1084 \u1072 \u1090 \u1077  YYYY-MM-DD.\
    \uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1097 \u1072 \u1077 \u1090  (True, date) \u1080 \u1083 \u1080  (False, \u1089 \u1086 \u1086 \u1073 \u1097 \u1077 \u1085 \u1080 \u1077 _\u1086 \u1073 _\u1086 \u1096 \u1080 \u1073 \u1082 \u1077 ).\
    """\
    try:\
        date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()\
        today = get_moscow_today()\
        if date > today:\
            return False, "\uc0\u10060  \u1044 \u1072 \u1090 \u1072  \u1085 \u1077  \u1084 \u1086 \u1078 \u1077 \u1090  \u1073 \u1099 \u1090 \u1100  \u1074  \u1073 \u1091 \u1076 \u1091 \u1097 \u1077 \u1084 "\
        two_years_ago = today - datetime.timedelta(days=730)\
        if date < two_years_ago:\
            return False, "\uc0\u10060  \u1044 \u1072 \u1090 \u1072  \u1089 \u1083 \u1080 \u1096 \u1082 \u1086 \u1084  \u1089 \u1090 \u1072 \u1088 \u1072 \u1103  (\u1073 \u1086 \u1083 \u1077 \u1077  2 \u1083 \u1077 \u1090  \u1085 \u1072 \u1079 \u1072 \u1076 )"\
        return True, date\
    except ValueError:\
        return False, "\uc0\u10060  \u1053 \u1077 \u1074 \u1077 \u1088 \u1085 \u1099 \u1081  \u1092 \u1086 \u1088 \u1084 \u1072 \u1090  \u1076 \u1072 \u1090 \u1099 . \u1048 \u1089 \u1087 \u1086 \u1083 \u1100 \u1079 \u1091 \u1081 \u1090 \u1077  YYYY-MM-DD"\
\
def validate_period(date_from, date_to):\
    """\
    \uc0\u1055 \u1088 \u1086 \u1074 \u1077 \u1088 \u1103 \u1077 \u1090  \u1082 \u1086 \u1088 \u1088 \u1077 \u1082 \u1090 \u1085 \u1086 \u1089 \u1090 \u1100  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1072 : \u1076 \u1072 \u1090 \u1099  \u1076 \u1086 \u1083 \u1078 \u1085 \u1099  \u1073 \u1099 \u1090 \u1100  \u1074 \u1072 \u1083 \u1080 \u1076 \u1085 \u1099 \u1084 \u1080 , from <= to, \u1085 \u1077  \u1073 \u1086 \u1083 \u1077 \u1077  \u1075 \u1086 \u1076 \u1072 .\
    \uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1097 \u1072 \u1077 \u1090  (True, (from_date, to_date)) \u1080 \u1083 \u1080  (False, \u1089 \u1086 \u1086 \u1073 \u1097 \u1077 \u1085 \u1080 \u1077 _\u1086 \u1073 _\u1086 \u1096 \u1080 \u1073 \u1082 \u1077 ).\
    """\
    valid_from, from_date = validate_date(date_from)\
    if not valid_from:\
        return False, from_date\
    valid_to, to_date = validate_date(date_to)\
    if not valid_to:\
        return False, to_date\
    if from_date > to_date:\
        return False, "\uc0\u10060  \u1053 \u1072 \u1095 \u1072 \u1083 \u1100 \u1085 \u1072 \u1103  \u1076 \u1072 \u1090 \u1072  \u1085 \u1077  \u1084 \u1086 \u1078 \u1077 \u1090  \u1073 \u1099 \u1090 \u1100  \u1087 \u1086 \u1079 \u1078 \u1077  \u1082 \u1086 \u1085 \u1077 \u1095 \u1085 \u1086 \u1081 "\
    delta = (to_date - from_date).days\
    if delta > 365:\
        return False, "\uc0\u10060  \u1055 \u1077 \u1088 \u1080 \u1086 \u1076  \u1085 \u1077  \u1084 \u1086 \u1078 \u1077 \u1090  \u1073 \u1099 \u1090 \u1100  \u1073 \u1086 \u1083 \u1100 \u1096 \u1077  \u1075 \u1086 \u1076 \u1072 "\
    return True, (from_date, to_date)\
\
def create_calendar(year, month, callback_prefix):\
    """\
    \uc0\u1057 \u1086 \u1079 \u1076 \u1072 \u1105 \u1090  InlineKeyboardMarkup \u1076 \u1083 \u1103  \u1082 \u1072 \u1083 \u1077 \u1085 \u1076 \u1072 \u1088 \u1103 .\
    callback_prefix \uc0\u1080 \u1089 \u1087 \u1086 \u1083 \u1100 \u1079 \u1091 \u1077 \u1090 \u1089 \u1103  \u1076 \u1083 \u1103  \u1080 \u1076 \u1077 \u1085 \u1090 \u1080 \u1092 \u1080 \u1082 \u1072 \u1094 \u1080 \u1080  callback-\u1076 \u1072 \u1085 \u1085 \u1099 \u1093 .\
    \uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1097 \u1072 \u1077 \u1090  InlineKeyboardMarkup.\
    """\
    month_names = ["\uc0\u1071 \u1085 \u1074 \u1072 \u1088 \u1100 ", "\u1060 \u1077 \u1074 \u1088 \u1072 \u1083 \u1100 ", "\u1052 \u1072 \u1088 \u1090 ", "\u1040 \u1087 \u1088 \u1077 \u1083 \u1100 ", "\u1052 \u1072 \u1081 ", "\u1048 \u1102 \u1085 \u1100 ",\
                   "\uc0\u1048 \u1102 \u1083 \u1100 ", "\u1040 \u1074 \u1075 \u1091 \u1089 \u1090 ", "\u1057 \u1077 \u1085 \u1090 \u1103 \u1073 \u1088 \u1100 ", "\u1054 \u1082 \u1090 \u1103 \u1073 \u1088 \u1100 ", "\u1053 \u1086 \u1103 \u1073 \u1088 \u1100 ", "\u1044 \u1077 \u1082 \u1072 \u1073 \u1088 \u1100 "]\
    keyboard = []\
    # \uc0\u1047 \u1072 \u1075 \u1086 \u1083 \u1086 \u1074 \u1086 \u1082  \u1089  \u1084 \u1077 \u1089 \u1103 \u1094 \u1077 \u1084  \u1080  \u1075 \u1086 \u1076 \u1086 \u1084 \
    header = f"\{month_names[month-1]\} \{year\}"\
    keyboard.append([InlineKeyboardButton(header, callback_data="ignore")])\
    # \uc0\u1044 \u1085 \u1080  \u1085 \u1077 \u1076 \u1077 \u1083 \u1080 \
    week_days = ["\uc0\u1055 \u1085 ", "\u1042 \u1090 ", "\u1057 \u1088 ", "\u1063 \u1090 ", "\u1055 \u1090 ", "\u1057 \u1073 ", "\u1042 \u1089 "]\
    row = [InlineKeyboardButton(day, callback_data="ignore") for day in week_days]\
    keyboard.append(row)\
\
    first_day, num_days = calendar.monthrange(year, month)\
    row = []\
    # \uc0\u1055 \u1091 \u1089 \u1090 \u1099 \u1077  \u1103 \u1095 \u1077 \u1081 \u1082 \u1080  \u1076 \u1086  \u1087 \u1077 \u1088 \u1074 \u1086 \u1075 \u1086  \u1076 \u1085 \u1103 \
    for _ in range(first_day):\
        row.append(InlineKeyboardButton(" ", callback_data="ignore"))\
    for day in range(1, num_days + 1):\
        row.append(InlineKeyboardButton(str(day), callback_data=f"\{callback_prefix\}\{year\}-\{month:02d\}-\{day:02d\}"))\
        if len(row) == 7:\
            keyboard.append(row)\
            row = []\
    if row:\
        while len(row) < 7:\
            row.append(InlineKeyboardButton(" ", callback_data="ignore"))\
        keyboard.append(row)\
\
    # \uc0\u1053 \u1072 \u1074 \u1080 \u1075 \u1072 \u1094 \u1080 \u1103 \
    nav_row = [\
        InlineKeyboardButton("\uc0\u9664 \u65039 ", callback_data=f"\{callback_prefix\}prev_month_\{year\}_\{month\}"),\
        InlineKeyboardButton(" ", callback_data="ignore"),\
        InlineKeyboardButton("\uc0\u9654 \u65039 ", callback_data=f"\{callback_prefix\}next_month_\{year\}_\{month\}")\
    ]\
    keyboard.append(nav_row)\
    keyboard.append([InlineKeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ", callback_data=f"\{callback_prefix\}cancel")])\
    return InlineKeyboardMarkup(keyboard)}