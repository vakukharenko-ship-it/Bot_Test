{\rtf1\ansi\ansicpg1251\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw3288\paperh2267\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 from telegram import ReplyKeyboardMarkup, KeyboardButton\
\
def main_admin_keyboard():\
    buttons = [\
        [KeyboardButton("\uc0\u55357 \u56522  \u1054 \u1090 \u1095 \u1105 \u1090  \u1087 \u1086  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1072 \u1084 ")],\
        [KeyboardButton("\uc0\u55357 \u56550  \u1054 \u1090 \u1095 \u1105 \u1090  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 \u1084 ")],\
        [KeyboardButton("\uc0\u9881 \u65039  \u1040 \u1076 \u1084 \u1080 \u1085 \u1080 \u1089 \u1090 \u1088 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1080 \u1077 ")],\
        [KeyboardButton("\uc0\u55357 \u56534  \u1057 \u1087 \u1088 \u1072 \u1074 \u1082 \u1072 ")]\
    ]\
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)\
\
def main_user_keyboard():\
    buttons = [\
        [KeyboardButton("\uc0\u55357 \u56522  \u1054 \u1090 \u1095 \u1105 \u1090  \u1087 \u1086  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1072 \u1084 ")],\
        [KeyboardButton("\uc0\u55357 \u56550  \u1054 \u1090 \u1095 \u1105 \u1090  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 \u1084 ")],\
        [KeyboardButton("\uc0\u55357 \u56534  \u1057 \u1087 \u1088 \u1072 \u1074 \u1082 \u1072 ")]\
    ]\
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)\
\
def sales_reports_keyboard():\
    buttons = [\
        [KeyboardButton("\uc0\u55357 \u56517  \u1055 \u1088 \u1086 \u1076 \u1072 \u1078 \u1080  \u1079 \u1072  \u1089 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 ")],\
        [KeyboardButton("\uc0\u55357 \u56518  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1076 \u1072 \u1090 \u1091 ")],\
        [KeyboardButton("\uc0\u55357 \u56522  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 ")],\
        [KeyboardButton("\uc0\u55357 \u56520  \u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 ")],\
        [KeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ")]\
    ]\
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)\
\
def products_reports_keyboard():\
    buttons = [\
        [KeyboardButton("\uc0\u55357 \u56517  \u1058 \u1086 \u1087  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  \u1079 \u1072  \u1089 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 ")],\
        [KeyboardButton("\uc0\u55357 \u56518  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1076 \u1072 \u1090 \u1091  (\u1090 \u1086 \u1074 \u1072 \u1088 \u1099 )")],\
        [KeyboardButton("\uc0\u55357 \u56522  \u1042 \u1099 \u1073 \u1088 \u1072 \u1090 \u1100  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076  (\u1090 \u1086 \u1074 \u1072 \u1088 \u1099 )")],\
        [KeyboardButton("\uc0\u55357 \u56520  \u1044 \u1080 \u1085 \u1072 \u1084 \u1080 \u1082 \u1072  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1091 ")],\
        [KeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ")]\
    ]\
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)\
\
def admin_keyboard():\
    buttons = [\
        [KeyboardButton("\uc0\u10133  \u1044 \u1086 \u1073 \u1072 \u1074 \u1080 \u1090 \u1100  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072 "), KeyboardButton("\u10134  \u1059 \u1076 \u1072 \u1083 \u1080 \u1090 \u1100  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072 ")],\
        [KeyboardButton("\uc0\u55357 \u56523  \u1057 \u1087 \u1080 \u1089 \u1086 \u1082  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1086 \u1074 ")],\
        [KeyboardButton("\uc0\u55357 \u56601  \u1053 \u1072 \u1079 \u1072 \u1076 ")]\
    ]\
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)}