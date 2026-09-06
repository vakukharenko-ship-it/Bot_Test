{\rtf1\ansi\ansicpg1251\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw3288\paperh2267\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import datetime\
from config import MOSCOW_TZ\
from utils.logger import write_log\
from utils.managers import load_managers\
from services.formatter import format_combined_metrics_with_deltas\
\
async def scheduled_report(context):\
    """\
    \uc0\u1055 \u1083 \u1072 \u1085 \u1080 \u1088 \u1086 \u1074 \u1097 \u1080 \u1082 : \u1086 \u1090 \u1087 \u1088 \u1072 \u1074 \u1083 \u1103 \u1077 \u1090  \u1086 \u1090 \u1095 \u1105 \u1090  \u1084 \u1077 \u1085 \u1077 \u1076 \u1078 \u1077 \u1088 \u1072 \u1084  \u1074  10:00 \u1080  22:00 \u1052 \u1057 \u1050 .\
    \uc0\u1042  10:00 \'96 \u1086 \u1090 \u1095 \u1105 \u1090  \u1089  \u1073 \u1083 \u1086 \u1082 \u1086 \u1084  \'ab\u1042 \u1095 \u1077 \u1088 \u1072 \'bb, \u1074  22:00 \'96 \u1073 \u1077 \u1079 .\
    """\
    moscow_tz = MOSCOW_TZ\
    now = datetime.datetime.now(moscow_tz)\
    hour = now.hour\
    if hour not in (10, 22):\
        return\
    include_yesterday = (hour == 10)\
    report = await format_combined_metrics_with_deltas(include_yesterday=include_yesterday, progress_callback=None)\
    managers = load_managers()\
    if not managers:\
        return\
    for m in managers:\
        try:\
            await context.bot.send_message(chat_id=m['id'], text=report, parse_mode="Markdown")\
        except Exception as e:\
            write_log(f"\uc0\u1054 \u1096 \u1080 \u1073 \u1082 \u1072  \u1086 \u1090 \u1087 \u1088 \u1072 \u1074 \u1082 \u1080  \{m['id']\}: \{e\}")}