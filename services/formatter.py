{\rtf1\ansi\ansicpg1251\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw3288\paperh2267\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import datetime\
import asyncio\
from config import MOSCOW_TZ\
from utils.validators import get_current_time_msk, get_moscow_today\
from api.seller import fetch_postings, fetch_finance_transactions\
from api.performance import fetch_advertising_expense\
from services.aggregator import aggregate_postings, aggregate_finance_expenses, aggregate_products\
from utils.logger import write_log\
\
# ==================== \uc0\u1042 \u1057 \u1055 \u1054 \u1052 \u1054 \u1043 \u1040 \u1058 \u1045 \u1051 \u1068 \u1053 \u1067 \u1045  \u1060 \u1059 \u1053 \u1050 \u1062 \u1048 \u1048  \u1060 \u1054 \u1056 \u1052 \u1040 \u1058 \u1048 \u1056 \u1054 \u1042 \u1040 \u1053 \u1048 \u1071  ====================\
def fmt_num(val):\
    return f"\{val:,.2f\}".replace(",", " ") if val else "0.00"\
\
def fmt_int(val):\
    return str(val) if val else "0"\
\
def fmt_pct(val):\
    if val is None:\
        return "\uc0\u8734 "\
    if val > 0:\
        return f"+\{val:.1f\}%"\
    elif val < 0:\
        return f"\{val:.1f\}%"\
    else:\
        return f"\{val:.1f\}%"\
\
def calc_delta(current, previous):\
    if previous == 0:\
        return None\
    try:\
        return ((current - previous) / abs(previous)) * 100\
    except:\
        return None\
\
def indicator(value_current, value_prev, better_is_higher):\
    """\
    \uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1097 \u1072 \u1077 \u1090  \u55357 \u57314  \u1077 \u1089 \u1083 \u1080  \u1091 \u1083 \u1091 \u1095 \u1096 \u1077 \u1085 \u1080 \u1077 , \u55357 \u56628  \u1077 \u1089 \u1083 \u1080  \u1091 \u1093 \u1091 \u1076 \u1096 \u1077 \u1085 \u1080 \u1077 , \u1080 \u1085 \u1072 \u1095 \u1077  \u1087 \u1091 \u1089 \u1090 \u1091 \u1102  \u1089 \u1090 \u1088 \u1086 \u1082 \u1091 .\
    """\
    if value_prev is None or value_current is None:\
        return ""\
    if value_prev == 0:\
        return "\uc0\u55357 \u57314 " if value_current > 0 else ""\
    delta = calc_delta(value_current, value_prev)\
    if delta is None:\
        return ""\
    if better_is_higher:\
        return "\uc0\u55357 \u57314 " if delta > 0 else ("\u55357 \u56628 " if delta < 0 else "")\
    else:\
        return "\uc0\u55357 \u57314 " if delta < 0 else ("\u55357 \u56628 " if delta > 0 else "")\
\
# ==================== \uc0\u1060 \u1054 \u1056 \u1052 \u1040 \u1058 \u1048 \u1056 \u1054 \u1042 \u1040 \u1053 \u1048 \u1045  \u1056 \u1040 \u1057 \u1061 \u1054 \u1044 \u1054 \u1042  ====================\
def format_expense_block(expenses_by_type, title):\
    if not expenses_by_type:\
        return f"\uc0\u55357 \u56633  *\{title\}*\\n\u1053 \u1077 \u1090  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093  \u1086  \u1088 \u1072 \u1089 \u1093 \u1086 \u1076 \u1072 \u1093 .\\n"\
\
    total = sum(expenses_by_type.values())\
    lines = [f"\uc0\u55357 \u56633  *\{title\}*", f"  *\u1048 \u1090 \u1086 \u1075 \u1086  \u1088 \u1072 \u1089 \u1093 \u1086 \u1076 \u1086 \u1074 :* \{total:,.2f\} \u8381 "]\
\
    name_map = \{\
        "\uc0\u1050 \u1086 \u1084 \u1080 \u1089 \u1089 \u1080 \u1103  Ozon": "\u1050 \u1086 \u1084 \u1080 \u1089 \u1089 \u1080 \u1103 ",\
        "\uc0\u1054 \u1087 \u1083 \u1072 \u1090 \u1072  \u1101 \u1082 \u1074 \u1072 \u1081 \u1088 \u1080 \u1085 \u1075 \u1072 ": "\u1069 \u1082 \u1074 \u1072 \u1081 \u1088 \u1080 \u1085 \u1075 ",\
        "\uc0\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072  \u1087 \u1086 \u1082 \u1091 \u1087 \u1072 \u1090 \u1077 \u1083 \u1102 ": "\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072  \u1087 \u1086 \u1082 \u1091 \u1087 \u1072 \u1090 \u1077 \u1083 \u1102 ",\
        "\uc0\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072  \u1080  \u1086 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1072 , \u1086 \u1090 \u1084 \u1077 \u1085 \u1099 , \u1085 \u1077 \u1074 \u1099 \u1082 \u1091 \u1087 \u1072 ": "\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072 /\u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1099 ",\
        "\uc0\u1050 \u1088 \u1086 \u1089 \u1089 -\u1076 \u1086 \u1082 \u1080 \u1085 \u1075 ": "\u1050 \u1088 \u1086 \u1089 \u1089 -\u1076 \u1086 \u1082 \u1080 \u1085 \u1075 ",\
        "\uc0\u1057 \u1090 \u1088 \u1072 \u1093 \u1086 \u1074 \u1072 \u1085 \u1080 \u1077  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1086 \u1090  \u1084 \u1072 \u1089 \u1089 \u1086 \u1074 \u1099 \u1093  \u1087 \u1086 \u1074 \u1088 \u1077 \u1078 \u1076 \u1077 \u1085 \u1080 \u1081 ": "\u1057 \u1090 \u1088 \u1072 \u1093 \u1086 \u1074 \u1072 \u1085 \u1080 \u1077 ",\
        "\uc0\u1054 \u1073 \u1077 \u1089 \u1087 \u1077 \u1095 \u1077 \u1085 \u1080 \u1077  \u1084 \u1072 \u1090 \u1077 \u1088 \u1080 \u1072 \u1083 \u1072 \u1084 \u1080  \u1076 \u1083 \u1103  \u1091 \u1087 \u1072 \u1082 \u1086 \u1074 \u1082 \u1080  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 ": "\u1054 \u1073 \u1077 \u1089 \u1087 \u1077 \u1095 \u1077 \u1085 \u1080 \u1077  \u1091 \u1087 \u1072 \u1082 \u1086 \u1074 \u1082 \u1086 \u1081 ",\
        "\uc0\u1059 \u1087 \u1072 \u1082 \u1086 \u1074 \u1082 \u1072  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1087 \u1072 \u1088 \u1090 \u1085 \u1105 \u1088 \u1072 \u1084 \u1080 ": "\u1059 \u1087 \u1072 \u1082 \u1086 \u1074 \u1082 \u1072 ",\
        "\uc0\u1055 \u1086 \u1076 \u1087 \u1080 \u1089 \u1082 \u1072  \u1059 \u1087 \u1088 \u1072 \u1074 \u1083 \u1077 \u1085 \u1080 \u1077  \u1086 \u1090 \u1079 \u1099 \u1074 \u1072 \u1084 \u1080 ": "\u1055 \u1086 \u1076 \u1087 \u1080 \u1089 \u1082 \u1072 ",\
        "\uc0\u1054 \u1087 \u1083 \u1072 \u1090 \u1072  \u1079 \u1072  \u1082 \u1083 \u1080 \u1082 ": "\u1054 \u1087 \u1083 \u1072 \u1090 \u1072  \u1079 \u1072  \u1082 \u1083 \u1080 \u1082 ",\
        "\uc0\u1055 \u1086 \u1083 \u1091 \u1095 \u1077 \u1085 \u1080 \u1077  \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1072 , \u1086 \u1090 \u1084 \u1077 \u1085 \u1099 , \u1085 \u1077 \u1074 \u1099 \u1082 \u1091 \u1087 \u1072  \u1086 \u1090  \u1087 \u1086 \u1082 \u1091 \u1087 \u1072 \u1090 \u1077 \u1083 \u1103 ": "\u1055 \u1086 \u1083 \u1091 \u1095 \u1077 \u1085 \u1080 \u1077  \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1086 \u1074 ",\
        "MarketplaceServiceItemDirectFlowLogistic": "\uc0\u1051 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072  \u1087 \u1088 \u1103 \u1084 \u1072 \u1103 ",\
        "MarketplaceServiceItemRedistributionLastMileCourier": "\uc0\u1051 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072  \u1087 \u1086 \u1089 \u1083 \u1077 \u1076 \u1085 \u1103 \u1103  \u1084 \u1080 \u1083 \u1103 ",\
        "MarketplaceServiceItemReturnFlowLogistic": "\uc0\u1051 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072  \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 ",\
        "MarketplaceServiceItemDeliveryToHandoverPlaceOzon": "\uc0\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072  \u1076 \u1086  \u1055 \u1042 \u1047 ",\
        "MarketplaceRedistributionOfAcquiringOperation": "\uc0\u1069 \u1082 \u1074 \u1072 \u1081 \u1088 \u1080 \u1085 \u1075 ",\
        "MarketplaceServiceItemRedistributionReturnsPVZ": "\uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1086 \u1074  (\u1055 \u1042 \u1047 )",\
        "MarketplaceServiceItemPackageRedistribution": "\uc0\u1055 \u1077 \u1088 \u1077 \u1091 \u1087 \u1072 \u1082 \u1086 \u1074 \u1082 \u1072 ",\
        "MarketplaceServiceItemPackageMaterialsProvision": "\uc0\u1054 \u1073 \u1077 \u1089 \u1087 \u1077 \u1095 \u1077 \u1085 \u1080 \u1077  \u1091 \u1087 \u1072 \u1082 \u1086 \u1074 \u1082 \u1086 \u1081 ",\
        "MarketplaceServiceItemProductReviewsManagementSubscription": "\uc0\u1055 \u1086 \u1076 \u1087 \u1080 \u1089 \u1082 \u1072 ",\
        "MarketplaceServiceItemRedistributionLastMilePVZ": "\uc0\u1051 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072  \u1087 \u1086 \u1089 \u1083 \u1077 \u1076 \u1085 \u1103 \u1103  \u1084 \u1080 \u1083 \u1103  (\u1055 \u1042 \u1047 )",\
        "MarketplaceServiceItemDirectFlowLogisticFBS": "\uc0\u1051 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072  \u1087 \u1088 \u1103 \u1084 \u1072 \u1103  (FBS)",\
        "MarketplaceServiceItemReturnFlowLogisticFBS": "\uc0\u1051 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072  \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090  (FBS)",\
        "ItemAgentServiceStarsMembership": "\uc0\u1047 \u1074 \u1105 \u1079 \u1076 \u1085 \u1099 \u1077  \u1090 \u1086 \u1074 \u1072 \u1088 \u1099 ",\
        "MarketplaceServiceSellerReturnsCargoAssortment": "\uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1086 \u1074  \u1087 \u1072 \u1088 \u1090 \u1085 \u1105 \u1088 \u1072 \u1084 \u1080 ",\
        "MarketplaceServiceItemTemporaryStorageRedistribution": "\uc0\u1042 \u1088 \u1077 \u1084 \u1077 \u1085 \u1085 \u1086 \u1077  \u1088 \u1072 \u1079 \u1084 \u1077 \u1097 \u1077 \u1085 \u1080 \u1077 ",\
        "MarketplaceServiceProductMovementFromWarehouse": "\uc0\u1042 \u1099 \u1074 \u1086 \u1079  \u1076 \u1086  \u1055 \u1042 \u1047 ",\
        "MarketplaceServiceItemDisposalDetailed": "\uc0\u1059 \u1090 \u1080 \u1083 \u1080 \u1079 \u1072 \u1094 \u1080 \u1103 ",\
        "\uc0\u1047 \u1074 \u1105 \u1079 \u1076 \u1085 \u1099 \u1077  \u1090 \u1086 \u1074 \u1072 \u1088 \u1099 ": "\u1047 \u1074 \u1105 \u1079 \u1076 \u1085 \u1099 \u1077  \u1090 \u1086 \u1074 \u1072 \u1088 \u1099 ",\
        "\uc0\u1042 \u1088 \u1077 \u1084 \u1077 \u1085 \u1085 \u1086 \u1077  \u1088 \u1072 \u1079 \u1084 \u1077 \u1097 \u1077 \u1085 \u1080 \u1077  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1087 \u1072 \u1088 \u1090 \u1085 \u1077 \u1088 \u1072 \u1084 \u1080 ": "\u1042 \u1088 \u1077 \u1084 \u1077 \u1085 \u1085 \u1086 \u1077  \u1088 \u1072 \u1079 \u1084 \u1077 \u1097 \u1077 \u1085 \u1080 \u1077 ",\
        "\uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1074  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1077  \u1075 \u1088 \u1091 \u1079 \u1086 \u1084 \u1077 \u1089 \u1090 \u1072 : \u1055 \u1086 \u1096 \u1090 \u1091 \u1095 \u1085 \u1072 \u1103  \u1087 \u1088 \u1080 \u1105 \u1084 \u1082 \u1072 ": "\u1055 \u1086 \u1096 \u1090 \u1091 \u1095 \u1085 \u1072 \u1103  \u1087 \u1088 \u1080 \u1105 \u1084 \u1082 \u1072 ",\
        "\uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1074  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1077  \u1075 \u1088 \u1091 \u1079 \u1086 \u1084 \u1077 \u1089 \u1090 \u1072  \u1085 \u1072  FBO": "\u1055 \u1086 \u1096 \u1090 \u1091 \u1095 \u1085 \u1072 \u1103  \u1087 \u1088 \u1080 \u1105 \u1084 \u1082 \u1072 ",\
        "\uc0\u1055 \u1086 \u1076 \u1075 \u1086 \u1090 \u1086 \u1074 \u1082 \u1072  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1082  \u1074 \u1099 \u1074 \u1086 \u1079 \u1091 : \u1041 \u1088 \u1072 \u1082 ": "\u1055 \u1086 \u1076 \u1075 \u1086 \u1090 \u1086 \u1074 \u1082 \u1072  \u1082  \u1074 \u1099 \u1074 \u1086 \u1079 \u1091  (\u1073 \u1088 \u1072 \u1082 )",\
        "\uc0\u1042 \u1099 \u1074 \u1086 \u1079  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1089 \u1086  \u1089 \u1082 \u1083 \u1072 \u1076 \u1072  \u1089 \u1080 \u1083 \u1072 \u1084 \u1080  Ozon: \u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072  \u1076 \u1086  \u1055 \u1042 \u1047 ": "\u1042 \u1099 \u1074 \u1086 \u1079  \u1076 \u1086  \u1055 \u1042 \u1047 ",\
        "\uc0\u1042 \u1099 \u1074 \u1086 \u1079  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1089 \u1086  \u1057 \u1082 \u1083 \u1072 \u1076 \u1072  \u1089 \u1080 \u1083 \u1072 \u1084 \u1080  Ozon: \u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072  \u1076 \u1086  \u1055 \u1042 \u1047 ": "\u1042 \u1099 \u1074 \u1086 \u1079  \u1076 \u1086  \u1055 \u1042 \u1047 ",\
        "\uc0\u1041 \u1088 \u1086 \u1085 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1080 \u1077  \u1084 \u1077 \u1089 \u1090 \u1072  \u1080  \u1087 \u1077 \u1088 \u1089 \u1086 \u1085 \u1072 \u1083 \u1072  \u1076 \u1083 \u1103  \u1087 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1080  \u1089  \u1085 \u1077 \u1087 \u1086 \u1083 \u1085 \u1099 \u1084  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1086 \u1084  \u1074  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1077  \u1075 \u1088 \u1091 \u1079 \u1086 \u1084 \u1077 \u1089 \u1090 \u1072 ": "\u1041 \u1088 \u1086 \u1085 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1080 \u1077  \u1084 \u1077 \u1089 \u1090 \u1072 ",\
        "\uc0\u1059 \u1089 \u1083 \u1091 \u1075 \u1072  \u1087 \u1086  \u1073 \u1088 \u1086 \u1085 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1080 \u1102  \u1084 \u1077 \u1089 \u1090 \u1072  \u1080  \u1087 \u1077 \u1088 \u1089 \u1086 \u1085 \u1072 \u1083 \u1072  \u1076 \u1083 \u1103  \u1087 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1080  \u1089  \u1085 \u1077 \u1087 \u1086 \u1083 \u1085 \u1099 \u1084  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1086 \u1084  \u1074  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1077  \u1043 \u1052 ": "\u1041 \u1088 \u1086 \u1085 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1080 \u1077  \u1084 \u1077 \u1089 \u1090 \u1072 ",\
        "\uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1086 \u1087 \u1086 \u1079 \u1085 \u1072 \u1085 \u1085 \u1099 \u1093  \u1080 \u1079 \u1083 \u1080 \u1096 \u1082 \u1086 \u1074  \u1074  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1077  \u1075 \u1088 \u1091 \u1079 \u1086 \u1084 \u1077 \u1089 \u1090 \u1072 ": "\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1080 \u1079 \u1083 \u1080 \u1096 \u1082 \u1086 \u1074 ",\
        "\uc0\u1059 \u1089 \u1083 \u1091 \u1075 \u1072  \u1087 \u1086  \u1086 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1077  \u1086 \u1087 \u1086 \u1079 \u1085 \u1072 \u1085 \u1085 \u1099 \u1093  \u1080 \u1079 \u1083 \u1080 \u1096 \u1082 \u1086 \u1074  \u1074  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1077  \u1043 \u1052 ": "\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1080 \u1079 \u1083 \u1080 \u1096 \u1082 \u1086 \u1074 ",\
        "\uc0\u1059 \u1090 \u1080 \u1083 \u1080 \u1079 \u1072 \u1094 \u1080 \u1103  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 : \u1055 \u1088 \u1086 \u1083 \u1080 \u1083 \u1080 \u1089 \u1100 /\u1087 \u1088 \u1086 \u1089 \u1099 \u1087 \u1072 \u1083 \u1080 \u1089 \u1100  \u1080 \u1079 -\u1079 \u1072  \u1091 \u1087 \u1072 \u1082 \u1086 \u1074 \u1082 \u1080 ": "\u1059 \u1090 \u1080 \u1083 \u1080 \u1079 \u1072 \u1094 \u1080 \u1103 ",\
        "\uc0\u1055 \u1086 \u1090 \u1077 \u1088 \u1103  \u1087 \u1086  \u1074 \u1080 \u1085 \u1077  Ozon \u1085 \u1072  \u1089 \u1082 \u1083 \u1072 \u1076 \u1077 ": "\u1055 \u1086 \u1090 \u1077 \u1088 \u1103  (\u1089 \u1082 \u1083 \u1072 \u1076 )",\
        "\uc0\u1055 \u1086 \u1090 \u1077 \u1088 \u1103  \u1087 \u1086  \u1074 \u1080 \u1085 \u1077  Ozon \u1074  \u1083 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1077 ": "\u1055 \u1086 \u1090 \u1077 \u1088 \u1103  (\u1083 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072 )",\
        "\uc0\u1042 \u1086 \u1079 \u1085 \u1072 \u1075 \u1088 \u1072 \u1078 \u1076 \u1077 \u1085 \u1080 \u1077  \u1079 \u1072  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1091 ": "\u1042 \u1086 \u1079 \u1085 \u1072 \u1075 \u1088 \u1072 \u1078 \u1076 \u1077 \u1085 \u1080 \u1077 ",\
        "\uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090  \u1074 \u1086 \u1079 \u1085 \u1072 \u1075 \u1088 \u1072 \u1078 \u1076 \u1077 \u1085 \u1080 \u1103 ": "\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090  \u1074 \u1086 \u1079 \u1085 \u1072 \u1075 \u1088 \u1072 \u1078 \u1076 \u1077 \u1085 \u1080 \u1103 ",\
        "\uc0\u1055 \u1088 \u1086 \u1075 \u1088 \u1072 \u1084 \u1084 \u1099  \u1087 \u1072 \u1088 \u1090 \u1085 \u1105 \u1088 \u1086 \u1074 ": "\u1055 \u1088 \u1086 \u1075 \u1088 \u1072 \u1084 \u1084 \u1099  \u1087 \u1072 \u1088 \u1090 \u1085 \u1105 \u1088 \u1086 \u1074 ",\
        "\uc0\u1041 \u1072 \u1083 \u1083 \u1099  \u1079 \u1072  \u1089 \u1082 \u1080 \u1076 \u1082 \u1080 ": "\u1041 \u1072 \u1083 \u1083 \u1099  \u1079 \u1072  \u1089 \u1082 \u1080 \u1076 \u1082 \u1080 ",\
        "\uc0\u1042 \u1099 \u1088 \u1091 \u1095 \u1082 \u1072 ": "\u1042 \u1099 \u1088 \u1091 \u1095 \u1082 \u1072 ",\
        "\uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090  \u1074 \u1099 \u1088 \u1091 \u1095 \u1082 \u1080 ": "\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090  \u1074 \u1099 \u1088 \u1091 \u1095 \u1082 \u1080 ",\
    \}\
\
    sorted_items = sorted(expenses_by_type.items(), key=lambda x: x[1], reverse=True)\
\
    for category, amount in sorted_items:\
        if category in name_map:\
            short_name = name_map[category]\
        else:\
            found = False\
            for key, value in name_map.items():\
                if key in category or category in key:\
                    short_name = value\
                    found = True\
                    break\
            if not found:\
                short_name = category[:40]\
                write_log(f"\uc0\u9888 \u65039  \u1053 \u1077  \u1085 \u1072 \u1081 \u1076 \u1077 \u1085 \u1086  \u1089 \u1086 \u1086 \u1090 \u1074 \u1077 \u1090 \u1089 \u1090 \u1074 \u1080 \u1077  \u1076 \u1083 \u1103  \u1082 \u1072 \u1090 \u1077 \u1075 \u1086 \u1088 \u1080 \u1080 : \{category\}")\
        lines.append(f"    \{short_name\}: \{amount:,.2f\} \uc0\u8381 ")\
\
    return "\\n".join(lines)\
\
def format_expense_comparison(expenses_current, expenses_prev, title):\
    """\uc0\u1060 \u1086 \u1088 \u1084 \u1072 \u1090 \u1080 \u1088 \u1091 \u1077 \u1090  \u1073 \u1083 \u1086 \u1082  \u1088 \u1072 \u1089 \u1093 \u1086 \u1076 \u1086 \u1074  \u1089  \u1089 \u1088 \u1072 \u1074 \u1085 \u1077 \u1085 \u1080 \u1077 \u1084  \u1076 \u1074 \u1091 \u1093  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1086 \u1074 ."""\
    if not expenses_current and not expenses_prev:\
        return f"\uc0\u55357 \u56633  *\{title\}*\\n\u1053 \u1077 \u1090  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093  \u1086  \u1088 \u1072 \u1089 \u1093 \u1086 \u1076 \u1072 \u1093 .\\n"\
    \
    total_current = sum(expenses_current.values()) if expenses_current else 0\
    total_prev = sum(expenses_prev.values()) if expenses_prev else 0\
    total_indicator = indicator(total_current, total_prev, False)\
    lines = [f"\uc0\u55357 \u56633  *\{title\}*"]\
    lines.append(f"  \uc0\u1048 \u1090 \u1086 \u1075 \u1086  \u1088 \u1072 \u1089 \u1093 \u1086 \u1076 \u1086 \u1074 : \{fmt_num(total_current)\} \u8381  / \{fmt_num(total_prev)\} \u8381  \{total_indicator\}")\
    \
    all_categories = set(expenses_current.keys()) | set(expenses_prev.keys())\
    sorted_categories = sorted(all_categories, key=lambda x: expenses_current.get(x, 0), reverse=True)\
    \
    name_map = \{\
        "\uc0\u1050 \u1086 \u1084 \u1080 \u1089 \u1089 \u1080 \u1103  Ozon": "\u1050 \u1086 \u1084 \u1080 \u1089 \u1089 \u1080 \u1103 ",\
        "\uc0\u1054 \u1087 \u1083 \u1072 \u1090 \u1072  \u1101 \u1082 \u1074 \u1072 \u1081 \u1088 \u1080 \u1085 \u1075 \u1072 ": "\u1069 \u1082 \u1074 \u1072 \u1081 \u1088 \u1080 \u1085 \u1075 ",\
        "\uc0\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072  \u1087 \u1086 \u1082 \u1091 \u1087 \u1072 \u1090 \u1077 \u1083 \u1102 ": "\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072  \u1087 \u1086 \u1082 \u1091 \u1087 \u1072 \u1090 \u1077 \u1083 \u1102 ",\
        "\uc0\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072  \u1080  \u1086 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1072 , \u1086 \u1090 \u1084 \u1077 \u1085 \u1099 , \u1085 \u1077 \u1074 \u1099 \u1082 \u1091 \u1087 \u1072 ": "\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072 /\u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1099 ",\
        "\uc0\u1050 \u1088 \u1086 \u1089 \u1089 -\u1076 \u1086 \u1082 \u1080 \u1085 \u1075 ": "\u1050 \u1088 \u1086 \u1089 \u1089 -\u1076 \u1086 \u1082 \u1080 \u1085 \u1075 ",\
        "\uc0\u1057 \u1090 \u1088 \u1072 \u1093 \u1086 \u1074 \u1072 \u1085 \u1080 \u1077  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1086 \u1090  \u1084 \u1072 \u1089 \u1089 \u1086 \u1074 \u1099 \u1093  \u1087 \u1086 \u1074 \u1088 \u1077 \u1078 \u1076 \u1077 \u1085 \u1080 \u1081 ": "\u1057 \u1090 \u1088 \u1072 \u1093 \u1086 \u1074 \u1072 \u1085 \u1080 \u1077 ",\
        "\uc0\u1054 \u1073 \u1077 \u1089 \u1087 \u1077 \u1095 \u1077 \u1085 \u1080 \u1077  \u1084 \u1072 \u1090 \u1077 \u1088 \u1080 \u1072 \u1083 \u1072 \u1084 \u1080  \u1076 \u1083 \u1103  \u1091 \u1087 \u1072 \u1082 \u1086 \u1074 \u1082 \u1080  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 ": "\u1054 \u1073 \u1077 \u1089 \u1087 \u1077 \u1095 \u1077 \u1085 \u1080 \u1077  \u1091 \u1087 \u1072 \u1082 \u1086 \u1074 \u1082 \u1086 \u1081 ",\
        "\uc0\u1059 \u1087 \u1072 \u1082 \u1086 \u1074 \u1082 \u1072  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1087 \u1072 \u1088 \u1090 \u1085 \u1105 \u1088 \u1072 \u1084 \u1080 ": "\u1059 \u1087 \u1072 \u1082 \u1086 \u1074 \u1082 \u1072 ",\
        "\uc0\u1055 \u1086 \u1076 \u1087 \u1080 \u1089 \u1082 \u1072  \u1059 \u1087 \u1088 \u1072 \u1074 \u1083 \u1077 \u1085 \u1080 \u1077  \u1086 \u1090 \u1079 \u1099 \u1074 \u1072 \u1084 \u1080 ": "\u1055 \u1086 \u1076 \u1087 \u1080 \u1089 \u1082 \u1072 ",\
        "\uc0\u1054 \u1087 \u1083 \u1072 \u1090 \u1072  \u1079 \u1072  \u1082 \u1083 \u1080 \u1082 ": "\u1054 \u1087 \u1083 \u1072 \u1090 \u1072  \u1079 \u1072  \u1082 \u1083 \u1080 \u1082 ",\
        "\uc0\u1055 \u1086 \u1083 \u1091 \u1095 \u1077 \u1085 \u1080 \u1077  \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1072 , \u1086 \u1090 \u1084 \u1077 \u1085 \u1099 , \u1085 \u1077 \u1074 \u1099 \u1082 \u1091 \u1087 \u1072  \u1086 \u1090  \u1087 \u1086 \u1082 \u1091 \u1087 \u1072 \u1090 \u1077 \u1083 \u1103 ": "\u1055 \u1086 \u1083 \u1091 \u1095 \u1077 \u1085 \u1080 \u1077  \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1086 \u1074 ",\
        "MarketplaceServiceItemDirectFlowLogistic": "\uc0\u1051 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072  \u1087 \u1088 \u1103 \u1084 \u1072 \u1103 ",\
        "MarketplaceServiceItemRedistributionLastMileCourier": "\uc0\u1051 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072  \u1087 \u1086 \u1089 \u1083 \u1077 \u1076 \u1085 \u1103 \u1103  \u1084 \u1080 \u1083 \u1103 ",\
        "MarketplaceServiceItemReturnFlowLogistic": "\uc0\u1051 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072  \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 ",\
        "MarketplaceServiceItemDeliveryToHandoverPlaceOzon": "\uc0\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072  \u1076 \u1086  \u1055 \u1042 \u1047 ",\
        "MarketplaceRedistributionOfAcquiringOperation": "\uc0\u1069 \u1082 \u1074 \u1072 \u1081 \u1088 \u1080 \u1085 \u1075 ",\
        "MarketplaceServiceItemRedistributionReturnsPVZ": "\uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1086 \u1074  (\u1055 \u1042 \u1047 )",\
        "MarketplaceServiceItemPackageRedistribution": "\uc0\u1055 \u1077 \u1088 \u1077 \u1091 \u1087 \u1072 \u1082 \u1086 \u1074 \u1082 \u1072 ",\
        "MarketplaceServiceItemPackageMaterialsProvision": "\uc0\u1054 \u1073 \u1077 \u1089 \u1087 \u1077 \u1095 \u1077 \u1085 \u1080 \u1077  \u1091 \u1087 \u1072 \u1082 \u1086 \u1074 \u1082 \u1086 \u1081 ",\
        "MarketplaceServiceItemProductReviewsManagementSubscription": "\uc0\u1055 \u1086 \u1076 \u1087 \u1080 \u1089 \u1082 \u1072 ",\
        "MarketplaceServiceItemRedistributionLastMilePVZ": "\uc0\u1051 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072  \u1087 \u1086 \u1089 \u1083 \u1077 \u1076 \u1085 \u1103 \u1103  \u1084 \u1080 \u1083 \u1103  (\u1055 \u1042 \u1047 )",\
        "MarketplaceServiceItemDirectFlowLogisticFBS": "\uc0\u1051 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072  \u1087 \u1088 \u1103 \u1084 \u1072 \u1103  (FBS)",\
        "MarketplaceServiceItemReturnFlowLogisticFBS": "\uc0\u1051 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072  \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090  (FBS)",\
        "ItemAgentServiceStarsMembership": "\uc0\u1047 \u1074 \u1105 \u1079 \u1076 \u1085 \u1099 \u1077  \u1090 \u1086 \u1074 \u1072 \u1088 \u1099 ",\
        "MarketplaceServiceSellerReturnsCargoAssortment": "\uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1074 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1086 \u1074  \u1087 \u1072 \u1088 \u1090 \u1085 \u1105 \u1088 \u1072 \u1084 \u1080 ",\
        "MarketplaceServiceItemTemporaryStorageRedistribution": "\uc0\u1042 \u1088 \u1077 \u1084 \u1077 \u1085 \u1085 \u1086 \u1077  \u1088 \u1072 \u1079 \u1084 \u1077 \u1097 \u1077 \u1085 \u1080 \u1077 ",\
        "MarketplaceServiceProductMovementFromWarehouse": "\uc0\u1042 \u1099 \u1074 \u1086 \u1079  \u1076 \u1086  \u1055 \u1042 \u1047 ",\
        "MarketplaceServiceItemDisposalDetailed": "\uc0\u1059 \u1090 \u1080 \u1083 \u1080 \u1079 \u1072 \u1094 \u1080 \u1103 ",\
        "\uc0\u1047 \u1074 \u1105 \u1079 \u1076 \u1085 \u1099 \u1077  \u1090 \u1086 \u1074 \u1072 \u1088 \u1099 ": "\u1047 \u1074 \u1105 \u1079 \u1076 \u1085 \u1099 \u1077  \u1090 \u1086 \u1074 \u1072 \u1088 \u1099 ",\
        "\uc0\u1042 \u1088 \u1077 \u1084 \u1077 \u1085 \u1085 \u1086 \u1077  \u1088 \u1072 \u1079 \u1084 \u1077 \u1097 \u1077 \u1085 \u1080 \u1077  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1087 \u1072 \u1088 \u1090 \u1085 \u1077 \u1088 \u1072 \u1084 \u1080 ": "\u1042 \u1088 \u1077 \u1084 \u1077 \u1085 \u1085 \u1086 \u1077  \u1088 \u1072 \u1079 \u1084 \u1077 \u1097 \u1077 \u1085 \u1080 \u1077 ",\
        "\uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1074  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1077  \u1075 \u1088 \u1091 \u1079 \u1086 \u1084 \u1077 \u1089 \u1090 \u1072 : \u1055 \u1086 \u1096 \u1090 \u1091 \u1095 \u1085 \u1072 \u1103  \u1087 \u1088 \u1080 \u1105 \u1084 \u1082 \u1072 ": "\u1055 \u1086 \u1096 \u1090 \u1091 \u1095 \u1085 \u1072 \u1103  \u1087 \u1088 \u1080 \u1105 \u1084 \u1082 \u1072 ",\
        "\uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1074  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1077  \u1075 \u1088 \u1091 \u1079 \u1086 \u1084 \u1077 \u1089 \u1090 \u1072  \u1085 \u1072  FBO": "\u1055 \u1086 \u1096 \u1090 \u1091 \u1095 \u1085 \u1072 \u1103  \u1087 \u1088 \u1080 \u1105 \u1084 \u1082 \u1072 ",\
        "\uc0\u1055 \u1086 \u1076 \u1075 \u1086 \u1090 \u1086 \u1074 \u1082 \u1072  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1082  \u1074 \u1099 \u1074 \u1086 \u1079 \u1091 : \u1041 \u1088 \u1072 \u1082 ": "\u1055 \u1086 \u1076 \u1075 \u1086 \u1090 \u1086 \u1074 \u1082 \u1072  \u1082  \u1074 \u1099 \u1074 \u1086 \u1079 \u1091  (\u1073 \u1088 \u1072 \u1082 )",\
        "\uc0\u1042 \u1099 \u1074 \u1086 \u1079  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1089 \u1086  \u1089 \u1082 \u1083 \u1072 \u1076 \u1072  \u1089 \u1080 \u1083 \u1072 \u1084 \u1080  Ozon: \u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072  \u1076 \u1086  \u1055 \u1042 \u1047 ": "\u1042 \u1099 \u1074 \u1086 \u1079  \u1076 \u1086  \u1055 \u1042 \u1047 ",\
        "\uc0\u1042 \u1099 \u1074 \u1086 \u1079  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072  \u1089 \u1086  \u1057 \u1082 \u1083 \u1072 \u1076 \u1072  \u1089 \u1080 \u1083 \u1072 \u1084 \u1080  Ozon: \u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072  \u1076 \u1086  \u1055 \u1042 \u1047 ": "\u1042 \u1099 \u1074 \u1086 \u1079  \u1076 \u1086  \u1055 \u1042 \u1047 ",\
        "\uc0\u1041 \u1088 \u1086 \u1085 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1080 \u1077  \u1084 \u1077 \u1089 \u1090 \u1072  \u1080  \u1087 \u1077 \u1088 \u1089 \u1086 \u1085 \u1072 \u1083 \u1072  \u1076 \u1083 \u1103  \u1087 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1080  \u1089  \u1085 \u1077 \u1087 \u1086 \u1083 \u1085 \u1099 \u1084  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1086 \u1084  \u1074  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1077  \u1075 \u1088 \u1091 \u1079 \u1086 \u1084 \u1077 \u1089 \u1090 \u1072 ": "\u1041 \u1088 \u1086 \u1085 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1080 \u1077  \u1084 \u1077 \u1089 \u1090 \u1072 ",\
        "\uc0\u1059 \u1089 \u1083 \u1091 \u1075 \u1072  \u1087 \u1086  \u1073 \u1088 \u1086 \u1085 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1080 \u1102  \u1084 \u1077 \u1089 \u1090 \u1072  \u1080  \u1087 \u1077 \u1088 \u1089 \u1086 \u1085 \u1072 \u1083 \u1072  \u1076 \u1083 \u1103  \u1087 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1080  \u1089  \u1085 \u1077 \u1087 \u1086 \u1083 \u1085 \u1099 \u1084  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1086 \u1084  \u1074  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1077  \u1043 \u1052 ": "\u1041 \u1088 \u1086 \u1085 \u1080 \u1088 \u1086 \u1074 \u1072 \u1085 \u1080 \u1077  \u1084 \u1077 \u1089 \u1090 \u1072 ",\
        "\uc0\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1086 \u1087 \u1086 \u1079 \u1085 \u1072 \u1085 \u1085 \u1099 \u1093  \u1080 \u1079 \u1083 \u1080 \u1096 \u1082 \u1086 \u1074  \u1074  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1077  \u1075 \u1088 \u1091 \u1079 \u1086 \u1084 \u1077 \u1089 \u1090 \u1072 ": "\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1080 \u1079 \u1083 \u1080 \u1096 \u1082 \u1086 \u1074 ",\
        "\uc0\u1059 \u1089 \u1083 \u1091 \u1075 \u1072  \u1087 \u1086  \u1086 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1077  \u1086 \u1087 \u1086 \u1079 \u1085 \u1072 \u1085 \u1085 \u1099 \u1093  \u1080 \u1079 \u1083 \u1080 \u1096 \u1082 \u1086 \u1074  \u1074  \u1089 \u1086 \u1089 \u1090 \u1072 \u1074 \u1077  \u1043 \u1052 ": "\u1054 \u1073 \u1088 \u1072 \u1073 \u1086 \u1090 \u1082 \u1072  \u1080 \u1079 \u1083 \u1080 \u1096 \u1082 \u1086 \u1074 ",\
        "\uc0\u1059 \u1090 \u1080 \u1083 \u1080 \u1079 \u1072 \u1094 \u1080 \u1103  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 : \u1055 \u1088 \u1086 \u1083 \u1080 \u1083 \u1080 \u1089 \u1100 /\u1087 \u1088 \u1086 \u1089 \u1099 \u1087 \u1072 \u1083 \u1080 \u1089 \u1100  \u1080 \u1079 -\u1079 \u1072  \u1091 \u1087 \u1072 \u1082 \u1086 \u1074 \u1082 \u1080 ": "\u1059 \u1090 \u1080 \u1083 \u1080 \u1079 \u1072 \u1094 \u1080 \u1103 ",\
        "\uc0\u1055 \u1086 \u1090 \u1077 \u1088 \u1103  \u1087 \u1086  \u1074 \u1080 \u1085 \u1077  Ozon \u1085 \u1072  \u1089 \u1082 \u1083 \u1072 \u1076 \u1077 ": "\u1055 \u1086 \u1090 \u1077 \u1088 \u1103  (\u1089 \u1082 \u1083 \u1072 \u1076 )",\
        "\uc0\u1055 \u1086 \u1090 \u1077 \u1088 \u1103  \u1087 \u1086  \u1074 \u1080 \u1085 \u1077  Ozon \u1074  \u1083 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1077 ": "\u1055 \u1086 \u1090 \u1077 \u1088 \u1103  (\u1083 \u1086 \u1075 \u1080 \u1089 \u1090 \u1080 \u1082 \u1072 )",\
        "\uc0\u1042 \u1086 \u1079 \u1085 \u1072 \u1075 \u1088 \u1072 \u1078 \u1076 \u1077 \u1085 \u1080 \u1077  \u1079 \u1072  \u1087 \u1088 \u1086 \u1076 \u1072 \u1078 \u1091 ": "\u1042 \u1086 \u1079 \u1085 \u1072 \u1075 \u1088 \u1072 \u1078 \u1076 \u1077 \u1085 \u1080 \u1077 ",\
        "\uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090  \u1074 \u1086 \u1079 \u1085 \u1072 \u1075 \u1088 \u1072 \u1078 \u1076 \u1077 \u1085 \u1080 \u1103 ": "\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090  \u1074 \u1086 \u1079 \u1085 \u1072 \u1075 \u1088 \u1072 \u1078 \u1076 \u1077 \u1085 \u1080 \u1103 ",\
        "\uc0\u1055 \u1088 \u1086 \u1075 \u1088 \u1072 \u1084 \u1084 \u1099  \u1087 \u1072 \u1088 \u1090 \u1085 \u1105 \u1088 \u1086 \u1074 ": "\u1055 \u1088 \u1086 \u1075 \u1088 \u1072 \u1084 \u1084 \u1099  \u1087 \u1072 \u1088 \u1090 \u1085 \u1105 \u1088 \u1086 \u1074 ",\
        "\uc0\u1041 \u1072 \u1083 \u1083 \u1099  \u1079 \u1072  \u1089 \u1082 \u1080 \u1076 \u1082 \u1080 ": "\u1041 \u1072 \u1083 \u1083 \u1099  \u1079 \u1072  \u1089 \u1082 \u1080 \u1076 \u1082 \u1080 ",\
        "\uc0\u1042 \u1099 \u1088 \u1091 \u1095 \u1082 \u1072 ": "\u1042 \u1099 \u1088 \u1091 \u1095 \u1082 \u1072 ",\
        "\uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090  \u1074 \u1099 \u1088 \u1091 \u1095 \u1082 \u1080 ": "\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090  \u1074 \u1099 \u1088 \u1091 \u1095 \u1082 \u1080 ",\
    \}\
    \
    for category in sorted_categories:\
        amount_cur = expenses_current.get(category, 0)\
        amount_prev = expenses_prev.get(category, 0)\
        ind = indicator(amount_cur, amount_prev, False)\
        short_name = name_map.get(category, category)\
        lines.append(f"    \{short_name\}: \{fmt_num(amount_cur)\} \uc0\u8381  / \{fmt_num(amount_prev)\} \u8381  \{ind\}")\
    \
    return "\\n".join(lines)\
\
# ==================== \uc0\u1060 \u1054 \u1056 \u1052 \u1040 \u1058 \u1048 \u1056 \u1054 \u1042 \u1040 \u1053 \u1048 \u1045  \u1054 \u1058 \u1063 \u1025 \u1058 \u1054 \u1042  \u1057 \u1056 \u1040 \u1042 \u1053 \u1045 \u1053 \u1048 \u1071  ====================\
def format_period_comparison_metrics(metrics_current, metrics_prev, period_name):\
    """\
    \uc0\u1060 \u1086 \u1088 \u1084 \u1080 \u1088 \u1091 \u1077 \u1090  \u1086 \u1090 \u1095 \u1105 \u1090  \u1089  \u1089 \u1088 \u1072 \u1074 \u1085 \u1077 \u1085 \u1080 \u1077 \u1084  \u1090 \u1077 \u1082 \u1091 \u1097 \u1077 \u1075 \u1086  \u1080  \u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1077 \u1075 \u1086  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 \u1086 \u1074  (\u1084 \u1077 \u1089 \u1103 \u1094 /\u1082 \u1074 \u1072 \u1088 \u1090 \u1072 \u1083 /\u1075 \u1086 \u1076 ).\
    """\
    cur_ordered_sum = metrics_current.get('ordered_sum', 0)\
    cur_ordered_units = metrics_current.get('ordered_units', 0)\
    cur_delivered_sum = metrics_current.get('delivered_sum', 0)\
    cur_delivered_units = metrics_current.get('delivered_units', 0)\
    cur_canceled_sum = metrics_current.get('canceled_sum', 0)\
    cur_canceled_units = metrics_current.get('canceled_units', 0)\
    cur_ad_expense = metrics_current.get('ad_expense', 0)\
    cur_drr = metrics_current.get('drr')\
    cur_eff_drr = metrics_current.get('effective_drr')\
    cur_expenses = metrics_current.get('expenses', \{\})\
\
    prev_ordered_sum = metrics_prev.get('ordered_sum', 0)\
    prev_ordered_units = metrics_prev.get('ordered_units', 0)\
    prev_delivered_sum = metrics_prev.get('delivered_sum', 0)\
    prev_delivered_units = metrics_prev.get('delivered_units', 0)\
    prev_canceled_sum = metrics_prev.get('canceled_sum', 0)\
    prev_canceled_units = metrics_prev.get('canceled_units', 0)\
    prev_ad_expense = metrics_prev.get('ad_expense', 0)\
    prev_drr = metrics_prev.get('drr')\
    prev_eff_drr = metrics_prev.get('effective_drr')\
    prev_expenses = metrics_prev.get('expenses', \{\})\
\
    cur_cancel_rate = (cur_canceled_units / cur_delivered_units * 100) if cur_delivered_units > 0 else None\
    prev_cancel_rate = (prev_canceled_units / prev_delivered_units * 100) if prev_delivered_units > 0 else None\
\
    ind_ordered_sum = indicator(cur_ordered_sum, prev_ordered_sum, True)\
    ind_ordered_units = indicator(cur_ordered_units, prev_ordered_units, True)\
    ind_delivered_sum = indicator(cur_delivered_sum, prev_delivered_sum, True)\
    ind_delivered_units = indicator(cur_delivered_units, prev_delivered_units, True)\
    ind_canceled_sum = indicator(cur_canceled_sum, prev_canceled_sum, False)\
    ind_canceled_units = indicator(cur_canceled_units, prev_canceled_units, False)\
    ind_cancel_rate = indicator(cur_cancel_rate, prev_cancel_rate, False)\
    ind_ad_expense = indicator(cur_ad_expense, prev_ad_expense, False)\
    ind_drr = indicator(cur_drr, prev_drr, False)\
    ind_eff_drr = indicator(cur_eff_drr, prev_eff_drr, False)\
\
    lines = []\
    lines.append(f"\uc0\u55357 \u56522  *\u1055 \u1088 \u1086 \u1076 \u1072 \u1078 \u1080  \u1079 \u1072  \{period_name\}*")\
    lines.append("")\
\
    lines.append(f"\uc0\u55357 \u57042  *\u1047 \u1072 \u1082 \u1072 \u1079 \u1072 \u1085 \u1086 *")\
    lines.append(f"  \uc0\u1053 \u1072  \u1089 \u1091 \u1084 \u1084 \u1091 : \{fmt_num(cur_ordered_sum)\} \u8381  \{ind_ordered_sum\}")\
    lines.append(f"  \uc0\u1064 \u1090 \u1091 \u1082 : \{fmt_int(cur_ordered_units)\} \{ind_ordered_units\}")\
    lines.append("vs \uc0\u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1080 \u1081  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 :")\
    lines.append(f"  \uc0\u1053 \u1072  \u1089 \u1091 \u1084 \u1084 \u1091 : \{fmt_num(prev_ordered_sum)\} \u8381 ")\
    lines.append(f"  \uc0\u1064 \u1090 \u1091 \u1082 : \{fmt_int(prev_ordered_units)\}")\
    lines.append("")\
\
    lines.append(f"\uc0\u55357 \u56550  *\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1086 *")\
    lines.append(f"  \uc0\u1053 \u1072  \u1089 \u1091 \u1084 \u1084 \u1091 : \{fmt_num(cur_delivered_sum)\} \u8381  \{ind_delivered_sum\}")\
    lines.append(f"  \uc0\u1064 \u1090 \u1091 \u1082 : \{fmt_int(cur_delivered_units)\} \{ind_delivered_units\}")\
    lines.append("vs \uc0\u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1080 \u1081  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 :")\
    lines.append(f"  \uc0\u1053 \u1072  \u1089 \u1091 \u1084 \u1084 \u1091 : \{fmt_num(prev_delivered_sum)\} \u8381 ")\
    lines.append(f"  \uc0\u1064 \u1090 \u1091 \u1082 : \{fmt_int(prev_delivered_units)\}")\
    lines.append("")\
\
    lines.append(f"\uc0\u10060  *\u1054 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086 *")\
    lines.append(f"  \uc0\u1053 \u1072  \u1089 \u1091 \u1084 \u1084 \u1091 : \{fmt_num(cur_canceled_sum)\} \u8381  \{ind_canceled_sum\}")\
    lines.append(f"  \uc0\u1064 \u1090 \u1091 \u1082 : \{fmt_int(cur_canceled_units)\} \{ind_canceled_units\}")\
    cur_cancel_rate_text = f"\{cur_cancel_rate:.2f\}%" if cur_cancel_rate is not None else "\uc0\u8734 "\
    prev_cancel_rate_text = f"\{prev_cancel_rate:.2f\}%" if prev_cancel_rate is not None else "\uc0\u8734 "\
    lines.append(f"  \uc0\u1044 \u1086 \u1083 \u1103  \u1086 \u1090 \u1084 \u1077 \u1085 : \{cur_cancel_rate_text\} \{ind_cancel_rate\}")\
    lines.append("vs \uc0\u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1080 \u1081  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 :")\
    lines.append(f"  \uc0\u1053 \u1072  \u1089 \u1091 \u1084 \u1084 \u1091 : \{fmt_num(prev_canceled_sum)\} \u8381 ")\
    lines.append(f"  \uc0\u1064 \u1090 \u1091 \u1082 : \{fmt_int(prev_canceled_units)\}")\
    lines.append(f"  \uc0\u1044 \u1086 \u1083 \u1103  \u1086 \u1090 \u1084 \u1077 \u1085 : \{prev_cancel_rate_text\}")\
    lines.append("")\
\
    lines.append(f"\uc0\u55357 \u56546  *\u1056 \u1077 \u1082 \u1083 \u1072 \u1084 \u1072 *")\
    lines.append(f"  \uc0\u1056 \u1072 \u1089 \u1093 \u1086 \u1076 \u1099 : \{fmt_num(cur_ad_expense)\} \u8381  \{ind_ad_expense\}")\
    cur_drr_text = f"\{cur_drr:.2f\}%" if cur_drr is not None else "\uc0\u8734 "\
    cur_eff_drr_text = f"\{cur_eff_drr:.2f\}%" if cur_eff_drr is not None else "\uc0\u8734 "\
    prev_drr_text = f"\{prev_drr:.2f\}%" if prev_drr is not None else "\uc0\u8734 "\
    prev_eff_drr_text = f"\{prev_eff_drr:.2f\}%" if prev_eff_drr is not None else "\uc0\u8734 "\
    lines.append(f"  \uc0\u1044 \u1056 \u1056  (\u1086 \u1073 \u1097 \u1080 \u1081 ): \{cur_drr_text\} \{ind_drr\}")\
    lines.append(f"  \uc0\u1044 \u1056 \u1056  (\u1087 \u1086  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1084 ): \{cur_eff_drr_text\} \{ind_eff_drr\}")\
    lines.append("vs \uc0\u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1080 \u1081  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 :")\
    lines.append(f"  \uc0\u1056 \u1072 \u1089 \u1093 \u1086 \u1076 \u1099 : \{fmt_num(prev_ad_expense)\} \u8381 ")\
    lines.append(f"  \uc0\u1044 \u1056 \u1056  (\u1086 \u1073 \u1097 \u1080 \u1081 ): \{prev_drr_text\}")\
    lines.append(f"  \uc0\u1044 \u1056 \u1056  (\u1087 \u1086  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1084 ): \{prev_eff_drr_text\}")\
    lines.append("")\
\
    expense_block = format_expense_comparison(cur_expenses, prev_expenses, "\uc0\u1056 \u1072 \u1089 \u1093 \u1086 \u1076 \u1099  \u1079 \u1072  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 ")\
    lines.append(expense_block)\
\
    return "\\n".join(lines)\
\
# ==================== \uc0\u1060 \u1054 \u1056 \u1052 \u1040 \u1058 \u1048 \u1056 \u1054 \u1042 \u1040 \u1053 \u1048 \u1045  \u1054 \u1058 \u1063 \u1025 \u1058 \u1040  \u1055 \u1054  \u1054 \u1044 \u1053 \u1054 \u1049  \u1044 \u1040 \u1058 \u1045 /\u1055 \u1045 \u1056 \u1048 \u1054 \u1044 \u1059  ====================\
def format_single_metrics(metrics, title):\
    if not metrics:\
        return f"\uc0\u55357 \u56522  *\{title\}*\\n\\n\u10060  \u1053 \u1077 \u1090  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072  \u1091 \u1082 \u1072 \u1079 \u1072 \u1085 \u1085 \u1099 \u1081  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 ."\
    has_data = False\
    for key, val in metrics.items():\
        if key in ["drr", "effective_drr", "ad_expense", "expenses"]:\
            continue\
        if isinstance(val, (int, float)) and val != 0:\
            has_data = True\
            break\
    if not has_data:\
        return f"\uc0\u55357 \u56522  *\{title\}*\\n\\n\u10060  \u1053 \u1077 \u1090  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072  \u1091 \u1082 \u1072 \u1079 \u1072 \u1085 \u1085 \u1099 \u1081  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 ."\
\
    ad_expense = metrics.get("ad_expense", 0)\
    drr = metrics.get("drr")\
    eff_drr = metrics.get("effective_drr")\
    drr_text = f"\{drr:.2f\}%" if drr is not None else "\uc0\u8734 "\
    eff_drr_text = f"\{eff_drr:.2f\}%" if eff_drr is not None else "\uc0\u8734 "\
\
    canceled_units = metrics.get('canceled_units', 0)\
    delivered_units = metrics.get('delivered_units', 0)\
    cancel_rate = (canceled_units / delivered_units * 100) if delivered_units > 0 else None\
    cancel_rate_text = f"\{cancel_rate:.2f\}%" if cancel_rate is not None else "\uc0\u8734 "\
\
    main_text = (\
        f"\uc0\u55357 \u56522  *\{title\}*\\n\\n"\
        f"\uc0\u55357 \u57042  *\u1047 \u1072 \u1082 \u1072 \u1079 \u1072 \u1085 \u1086 *\\n  \u1053 \u1072  \u1089 \u1091 \u1084 \u1084 \u1091 : \{metrics.get('ordered_sum', 0):,.2f\} \u8381 \\n"\
        f"  \uc0\u1064 \u1090 \u1091 \u1082 : \{metrics.get('ordered_units', 0)\}\\n\\n"\
        f"\uc0\u55357 \u56550  *\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1086 *\\n  \u1053 \u1072  \u1089 \u1091 \u1084 \u1084 \u1091 : \{metrics.get('delivered_sum', 0):,.2f\} \u8381 \\n"\
        f"  \uc0\u1064 \u1090 \u1091 \u1082 : \{metrics.get('delivered_units', 0)\}\\n\\n"\
        f"\uc0\u10060  *\u1054 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086 *\\n  \u1053 \u1072  \u1089 \u1091 \u1084 \u1084 \u1091 : \{metrics.get('canceled_sum', 0):,.2f\} \u8381 \\n"\
        f"  \uc0\u1064 \u1090 \u1091 \u1082 : \{metrics.get('canceled_units', 0)\}\\n"\
        f"  \uc0\u1044 \u1086 \u1083 \u1103  \u1086 \u1090 \u1084 \u1077 \u1085 : \{cancel_rate_text\}\\n\\n"\
        f"\uc0\u55357 \u56546  *\u1056 \u1077 \u1082 \u1083 \u1072 \u1084 \u1072 *\\n"\
        f"  \uc0\u1056 \u1072 \u1089 \u1093 \u1086 \u1076 \u1099 : \{ad_expense:,.2f\} \u8381 \\n"\
        f"  \uc0\u1044 \u1056 \u1056  (\u1086 \u1073 \u1097 \u1080 \u1081 ): \{drr_text\}\\n"\
        f"  \uc0\u1044 \u1056 \u1056  (\u1087 \u1086  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1084 ): \{eff_drr_text\}"\
    )\
\
    expenses = metrics.get("expenses", \{\})\
    if expenses:\
        expense_block = format_expense_block(expenses, "\uc0\u1056 \u1072 \u1089 \u1093 \u1086 \u1076 \u1099  \u1079 \u1072  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 ")\
        main_text += "\\n\\n" + expense_block\
\
    return main_text\
\
# ==================== \uc0\u1050 \u1054 \u1052 \u1041 \u1048 \u1053 \u1048 \u1056 \u1054 \u1042 \u1040 \u1053 \u1053 \u1067 \u1049  \u1054 \u1058 \u1063 \u1025 \u1058  "\u1055 \u1056 \u1054 \u1044 \u1040 \u1046 \u1048  \u1047 \u1040  \u1057 \u1045 \u1043 \u1054 \u1044 \u1053 \u1071 " ====================\
async def format_combined_metrics_with_deltas(include_yesterday=False, progress_callback=None):\
    now = get_current_time_msk()\
    today_date = now.date()\
    current_time = now.time()\
    today_str = today_date.isoformat()\
    yesterday_date = today_date - datetime.timedelta(days=1)\
    yesterday_str = yesterday_date.isoformat()\
\
    current_month_start = today_date.replace(day=1)\
    current_month_start_str = current_month_start.isoformat()\
    current_month_end_str = today_str\
\
    previous_month_start = (current_month_start - datetime.timedelta(days=1)).replace(day=1)\
    previous_month_start_str = previous_month_start.isoformat()\
    previous_month_end = current_month_start - datetime.timedelta(days=1)\
    previous_month_end_str = previous_month_end.isoformat()\
\
    days_passed = (today_date - current_month_start).days + 1\
    prev_period_end = previous_month_start + datetime.timedelta(days=days_passed - 1)\
    prev_period_end_str = prev_period_end.isoformat()\
\
    if progress_callback:\
        await progress_callback("\uc0\u1047 \u1072 \u1075 \u1088 \u1091 \u1079 \u1082 \u1072  \u1086 \u1090 \u1075 \u1088 \u1091 \u1079 \u1086 \u1082  \u1079 \u1072  \u1090 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 ...", 10)\
    postings_current_task = fetch_postings(current_month_start_str, current_month_end_str)\
    postings_prev_task = fetch_postings(previous_month_start_str, previous_month_end_str)\
    postings_current, postings_prev = await asyncio.gather(postings_current_task, postings_prev_task)\
    if progress_callback:\
        await progress_callback("\uc0\u1054 \u1090 \u1075 \u1088 \u1091 \u1079 \u1082 \u1080  \u1079 \u1072 \u1075 \u1088 \u1091 \u1078 \u1077 \u1085 \u1099 , \u1072 \u1075 \u1088 \u1077 \u1075 \u1080 \u1088 \u1091 \u1077 \u1084 ...", 30)\
\
    agg_yesterday_full = aggregate_postings(\
        postings_current,\
        date_from=yesterday_str,\
        date_to=yesterday_str\
    )\
    yesterday_full_metrics = agg_yesterday_full.get(yesterday_str, \{\}) if yesterday_str in agg_yesterday_full else \{\}\
\
    agg_today = aggregate_postings(\
        postings_current,\
        date_from=today_str,\
        date_to=today_str,\
        time_limit=current_time,\
        apply_limit_on_day=today_str\
    )\
    today_metrics = agg_today.get(today_str, \{\}) if today_str in agg_today else \{\}\
\
    agg_yesterday = aggregate_postings(\
        postings_current,\
        date_from=yesterday_str,\
        date_to=yesterday_str,\
        time_limit=current_time,\
        apply_limit_on_day=yesterday_str\
    )\
    yesterday_metrics = agg_yesterday.get(yesterday_str, \{\}) if yesterday_str in agg_yesterday else \{\}\
\
    agg_current_month = aggregate_postings(\
        postings_current,\
        date_from=current_month_start_str,\
        date_to=current_month_end_str,\
        time_limit=current_time,\
        apply_limit_on_day=today_str\
    )\
    month_metrics = \{\
        "ordered_units": 0,\
        "ordered_sum": 0.0,\
        "delivered_units": 0,\
        "delivered_sum": 0.0,\
        "canceled_units": 0,\
        "canceled_sum": 0.0,\
    \}\
    for vals in agg_current_month.values():\
        for key in month_metrics:\
            month_metrics[key] += vals.get(key, 0)\
\
    agg_prev_month = aggregate_postings(\
        postings_prev,\
        date_from=previous_month_start_str,\
        date_to=prev_period_end_str,\
        time_limit=current_time,\
        apply_limit_on_day=prev_period_end_str\
    )\
    prev_month_metrics = \{\
        "ordered_units": 0,\
        "ordered_sum": 0.0,\
        "delivered_units": 0,\
        "delivered_sum": 0.0,\
        "canceled_units": 0,\
        "canceled_sum": 0.0,\
    \}\
    for vals in agg_prev_month.values():\
        for key in prev_month_metrics:\
            prev_month_metrics[key] += vals.get(key, 0)\
\
    if progress_callback:\
        await progress_callback("\uc0\u1047 \u1072 \u1075 \u1088 \u1091 \u1079 \u1082 \u1072  \u1088 \u1077 \u1082 \u1083 \u1072 \u1084 \u1099  \u1080  \u1092 \u1080 \u1085 \u1072 \u1085 \u1089 \u1086 \u1074 ...", 50)\
\
    ad_today_task = fetch_advertising_expense(today_str, today_str)\
    ad_yesterday_task = fetch_advertising_expense(yesterday_str, yesterday_str)\
    ad_month_task = fetch_advertising_expense(current_month_start_str, today_str)\
    ad_prev_task = fetch_advertising_expense(previous_month_start_str, prev_period_end_str)\
    fin_today_task = fetch_finance_transactions(today_str, today_str)\
    fin_month_task = fetch_finance_transactions(current_month_start_str, today_str)\
\
    ad_today, ad_yesterday, ad_month, ad_prev_period, fin_today, fin_month = await asyncio.gather(\
        ad_today_task, ad_yesterday_task, ad_month_task, ad_prev_task,\
        fin_today_task, fin_month_task\
    )\
    if progress_callback:\
        await progress_callback("\uc0\u1044 \u1072 \u1085 \u1085 \u1099 \u1077  \u1079 \u1072 \u1075 \u1088 \u1091 \u1078 \u1077 \u1085 \u1099 , \u1092 \u1086 \u1088 \u1084 \u1080 \u1088 \u1091 \u1077 \u1084  \u1086 \u1090 \u1095 \u1105 \u1090 ...", 80)\
\
    expenses_today = aggregate_finance_expenses(fin_today)\
    expenses_month = aggregate_finance_expenses(fin_month)\
\
    if ad_today > 0:\
        expenses_today["\uc0\u1054 \u1087 \u1083 \u1072 \u1090 \u1072  \u1079 \u1072  \u1082 \u1083 \u1080 \u1082 "] = ad_today\
        expenses_today.pop("\uc0\u1056 \u1077 \u1082 \u1083 \u1072 \u1084 \u1072 ", None)\
    if ad_month > 0:\
        expenses_month["\uc0\u1054 \u1087 \u1083 \u1072 \u1090 \u1072  \u1079 \u1072  \u1082 \u1083 \u1080 \u1082 "] = ad_month\
        expenses_month.pop("\uc0\u1056 \u1077 \u1082 \u1083 \u1072 \u1084 \u1072 ", None)\
\
    d_ord_sum = calc_delta(today_metrics.get("ordered_sum", 0), yesterday_metrics.get("ordered_sum", 0))\
    d_ord_units = calc_delta(today_metrics.get("ordered_units", 0), yesterday_metrics.get("ordered_units", 0))\
    d_ad = calc_delta(ad_today, ad_yesterday)\
\
    d_ord_sum_m = calc_delta(month_metrics.get("ordered_sum", 0), prev_month_metrics.get("ordered_sum", 0))\
    d_ord_units_m = calc_delta(month_metrics.get("ordered_units", 0), prev_month_metrics.get("ordered_units", 0))\
    d_del_sum_m = calc_delta(month_metrics.get("delivered_sum", 0), prev_month_metrics.get("delivered_sum", 0))\
    d_del_units_m = calc_delta(month_metrics.get("delivered_units", 0), prev_month_metrics.get("delivered_units", 0))\
    d_can_sum_m = calc_delta(month_metrics.get("canceled_sum", 0), prev_month_metrics.get("canceled_sum", 0))\
    d_can_units_m = calc_delta(month_metrics.get("canceled_units", 0), prev_month_metrics.get("canceled_units", 0))\
    d_ad_m = calc_delta(ad_month, ad_prev_period)\
\
    cancel_rate_today = (today_metrics.get("canceled_units", 0) / today_metrics.get("delivered_units", 0) * 100) if today_metrics.get("delivered_units", 0) > 0 else None\
    cancel_rate_month = (month_metrics["canceled_units"] / month_metrics["delivered_units"] * 100) if month_metrics["delivered_units"] > 0 else None\
    cancel_rate_prev = (prev_month_metrics["canceled_units"] / prev_month_metrics["delivered_units"] * 100) if prev_month_metrics["delivered_units"] > 0 else None\
\
    def format_today_block():\
        ordered_sum = fmt_num(today_metrics.get("ordered_sum", 0))\
        ordered_units = fmt_int(today_metrics.get("ordered_units", 0))\
        canceled_sum = fmt_num(today_metrics.get("canceled_sum", 0))\
        canceled_units = fmt_int(today_metrics.get("canceled_units", 0))\
\
        delta_ord_sum = fmt_pct(d_ord_sum)\
        delta_ord_units = fmt_pct(d_ord_units)\
        delta_can_sum = fmt_pct(calc_delta(today_metrics.get("canceled_sum", 0), yesterday_metrics.get("canceled_sum", 0)))\
        delta_can_units = fmt_pct(calc_delta(today_metrics.get("canceled_units", 0), yesterday_metrics.get("canceled_units", 0)))\
\
        cancel_rate_text = f"\{cancel_rate_today:.2f\}%" if cancel_rate_today is not None else "\uc0\u8734 "\
\
        return (\
            f"\uc0\u55357 \u56633  *\u1057 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103  (\u1085 \u1072  \{now.strftime('%H:%M')\} \u1052 \u1057 \u1050 )*\\n"\
            f"  \uc0\u55357 \u57042  \u1047 \u1072 \u1082 \u1072 \u1079 \u1072 \u1085 \u1086 : \\n  \{ordered_sum\} \u8381  / \{ordered_units\} \u1096 \u1090 .\\n"\
            f"    vs \uc0\u1042 \u1095 \u1077 \u1088 \u1072 : \\n  \{delta_ord_sum\} \u8381  / \{delta_ord_units\} \u1096 \u1090 .\\n\\n"\
            f"  \uc0\u10060  \u1054 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086 : \\n  \{canceled_sum\} \u8381  / \{canceled_units\} \u1096 \u1090 .\\n"\
            f"    vs \uc0\u1042 \u1095 \u1077 \u1088 \u1072 : \\n  \{delta_can_sum\} \u8381  / \{delta_can_units\} \u1096 \u1090 .\\n"\
            f"  \uc0\u1044 \u1086 \u1083 \u1103  \u1086 \u1090 \u1084 \u1077 \u1085 : \{cancel_rate_text\}\\n"\
        )\
\
    def format_month_block():\
        ordered_sum = fmt_num(month_metrics.get("ordered_sum", 0))\
        ordered_units = fmt_int(month_metrics.get("ordered_units", 0))\
        delivered_sum = fmt_num(month_metrics.get("delivered_sum", 0))\
        delivered_units = fmt_int(month_metrics.get("delivered_units", 0))\
        canceled_sum = fmt_num(month_metrics.get("canceled_sum", 0))\
        canceled_units = fmt_int(month_metrics.get("canceled_units", 0))\
        ad_expense = fmt_num(ad_month)\
        ad_prev = fmt_num(ad_prev_period)\
\
        revenue = month_metrics.get("ordered_sum", 0)\
        drr = (ad_month / revenue * 100) if revenue > 0 else None\
        delivered_revenue = month_metrics.get("delivered_sum", 0)\
        eff_drr = (ad_month / delivered_revenue * 100) if delivered_revenue > 0 else None\
\
        prev_rev = prev_month_metrics.get("ordered_sum", 0)\
        prev_del_rev = prev_month_metrics.get("delivered_sum", 0)\
        prev_drr_val = (ad_prev_period / prev_rev * 100) if prev_rev > 0 else None\
        prev_eff_drr_val = (ad_prev_period / prev_del_rev * 100) if prev_del_rev > 0 else None\
\
        drr_str = f"\{drr:.2f\}%" if drr is not None else "\uc0\u8734 "\
        eff_drr_str = f"\{eff_drr:.2f\}%" if eff_drr is not None else "\uc0\u8734 "\
        prev_drr_str = f"\{prev_drr_val:.2f\}%" if prev_drr_val is not None else "\uc0\u8734 "\
        prev_eff_drr_str = f"\{prev_eff_drr_val:.2f\}%" if prev_eff_drr_val is not None else "\uc0\u8734 "\
\
        delta_ord_sum_m = fmt_pct(d_ord_sum_m)\
        delta_ord_units_m = fmt_pct(d_ord_units_m)\
        delta_del_sum_m = fmt_pct(d_del_sum_m)\
        delta_del_units_m = fmt_pct(d_del_units_m)\
        delta_can_sum_m = fmt_pct(d_can_sum_m)\
        delta_can_units_m = fmt_pct(d_can_units_m)\
\
        cancel_rate_month_text = f"\{cancel_rate_month:.2f\}%" if cancel_rate_month is not None else "\uc0\u8734 "\
        cancel_rate_prev_text = f"\{cancel_rate_prev:.2f\}%" if cancel_rate_prev is not None else "\uc0\u8734 "\
        cancel_rate_delta = calc_delta(cancel_rate_month if cancel_rate_month is not None else 0,\
                                       cancel_rate_prev if cancel_rate_prev is not None else 0)\
        cancel_rate_delta_text = fmt_pct(cancel_rate_delta)\
\
        return (\
            f"\uc0\u55357 \u56633  *\u1058 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 *\\n"\
            f"  \uc0\u55357 \u57042  \u1047 \u1072 \u1082 \u1072 \u1079 \u1072 \u1085 \u1086 : \\n  \{ordered_sum\} \u8381  / \{ordered_units\} \u1096 \u1090 .\\n"\
            f"    vs \uc0\u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 : \\n  \{delta_ord_sum_m\} \u8381  / \{delta_ord_units_m\} \u1096 \u1090 .\\n\\n"\
            f"  \uc0\u55357 \u56550  \u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1086 : \\n  \{delivered_sum\} \u8381  / \{delivered_units\} \u1096 \u1090 .\\n"\
            f"    vs \uc0\u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 : \\n  \{delta_del_sum_m\} \u8381  / \{delta_del_units_m\} \u1096 \u1090 .\\n\\n"\
            f"  \uc0\u10060  \u1054 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086 : \\n  \{canceled_sum\} \u8381  / \{canceled_units\} \u1096 \u1090 .\\n"\
            f"    vs \uc0\u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 : \\n  \{delta_can_sum_m\} \u8381  / \{delta_can_units_m\} \u1096 \u1090 .\\n"\
            f"  \uc0\u1044 \u1086 \u1083 \u1103  \u1086 \u1090 \u1084 \u1077 \u1085 : \{cancel_rate_month_text\} | vs \u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 : \{cancel_rate_prev_text\} (\{cancel_rate_delta_text\})\\n\\n"\
            f"  \uc0\u55357 \u56546  \u1056 \u1077 \u1082 \u1083 \u1072 \u1084 \u1072 : \\n  \{ad_expense\} \u8381  | vs \u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 : \{ad_prev\} \u8381 \\n"\
            f"  \uc0\u1044 \u1056 \u1056  (\u1086 \u1073 \u1097 \u1080 \u1081 ): \{drr_str\} | vs \u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 : \{prev_drr_str\}\\n"\
            f"  \uc0\u1044 \u1056 \u1056  (\u1087 \u1086  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1085 \u1099 \u1084 ): \{eff_drr_str\} | vs \u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 : \{prev_eff_drr_str\}"\
        )\
\
    parts = []\
    parts.append(format_today_block())\
    parts.append(format_month_block())\
\
    parts.append(format_expense_block(expenses_today, "\uc0\u1056 \u1072 \u1089 \u1093 \u1086 \u1076 \u1099  \u1089 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 "))\
    parts.append(format_expense_block(expenses_month, "\uc0\u1056 \u1072 \u1089 \u1093 \u1086 \u1076 \u1099  \u1079 \u1072  \u1090 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094 "))\
\
    if progress_callback:\
        await progress_callback("\uc0\u1043 \u1086 \u1090 \u1086 \u1074 \u1086 ", 100)\
    return "\uc0\u55357 \u56522  *\u1055 \u1088 \u1086 \u1076 \u1072 \u1078 \u1080  \u1079 \u1072  \u1089 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 *\\n\\n\\n" + "\\n\\n".join(parts)\
\
# ==================== \uc0\u1060 \u1054 \u1056 \u1052 \u1040 \u1058 \u1048 \u1056 \u1054 \u1042 \u1040 \u1053 \u1048 \u1045  \u1058 \u1054 \u1042 \u1040 \u1056 \u1053 \u1067 \u1061  \u1054 \u1058 \u1063 \u1025 \u1058 \u1054 \u1042  ====================\
def format_top_products(products, title, limit=15):\
    if not products:\
        return f"\uc0\u55357 \u56550  \{title\}\\n\\n\u10060  \u1053 \u1077 \u1090  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093  \u1079 \u1072  \u1091 \u1082 \u1072 \u1079 \u1072 \u1085 \u1085 \u1099 \u1081  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 ."\
\
    sorted_items = sorted(products.items(), key=lambda x: x[1]["ordered_sum"], reverse=True)[:limit]\
    lines = [f"\uc0\u55357 \u56550  \{title\}", ""]\
    for idx, (sku, stats) in enumerate(sorted_items, 1):\
        name = stats["name"][:40]\
        offer_id = stats.get("offer_id", "")\
        ordered_sum = f"\{stats['ordered_sum']:,.2f\}".replace(",", " ")\
        ordered_units = stats["ordered_units"]\
        delivered_sum = f"\{stats['delivered_sum']:,.2f\}".replace(",", " ")\
        delivered_units = stats["delivered_units"]\
        canceled_sum = f"\{stats['canceled_sum']:,.2f\}".replace(",", " ")\
        canceled_units = stats["canceled_units"]\
        avg_check = (stats["ordered_sum"] / stats["order_count"]) if stats["order_count"] > 0 else 0\
        avg_check_str = f"\{avg_check:,.2f\}".replace(",", " ")\
        lines.append(f"\{idx\}. SKU: \{sku\} | \{name\} | \uc0\u1040 \u1088 \u1090 : \{offer_id\}" if offer_id else f"\{idx\}. SKU: \{sku\} | \{name\}")\
        lines.append(f"   \uc0\u55357 \u57042  \u1047 \u1072 \u1082 \u1072 \u1079 \u1072 \u1085 \u1086 : \{ordered_sum\} \u8381  / \{ordered_units\} \u1096 \u1090 .")\
        lines.append(f"   \uc0\u55357 \u56550  \u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1083 \u1077 \u1085 \u1086 : \{delivered_sum\} \u8381  / \{delivered_units\} \u1096 \u1090 .")\
        lines.append(f"   \uc0\u10060  \u1054 \u1090 \u1084 \u1077 \u1085 \u1077 \u1085 \u1086 : \{canceled_sum\} \u8381  / \{canceled_units\} \u1096 \u1090 .")\
        lines.append(f"   \uc0\u55357 \u56496  \u1057 \u1088 \u1077 \u1076 \u1085 \u1080 \u1081  \u1095 \u1077 \u1082 : \{avg_check_str\} \u8381 ")\
        lines.append("")\
    return "\\n".join(lines)\
\
def format_products_summary(products):\
    if not products:\
        return "\uc0\u1053 \u1077 \u1090  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093 "\
    total_revenue = sum(p["ordered_sum"] for p in products.values())\
    total_units = sum(p["ordered_units"] for p in products.values())\
    total_orders = sum(p["order_count"] for p in products.values())\
    avg_check = (total_revenue / total_orders) if total_orders > 0 else 0\
    return (\
        f"\uc0\u1057 \u1074 \u1086 \u1076 \u1082 \u1072 \\n"\
        f"  \uc0\u1059 \u1085 \u1080 \u1082 \u1072 \u1083 \u1100 \u1085 \u1099 \u1093  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074 : \{len(products)\}\\n"\
        f"  \uc0\u1054 \u1073 \u1097 \u1072 \u1103  \u1074 \u1099 \u1088 \u1091 \u1095 \u1082 \u1072 : \{total_revenue:,.2f\} \u8381 \\n"\
        f"  \uc0\u1042 \u1089 \u1077 \u1075 \u1086  \u1077 \u1076 \u1080 \u1085 \u1080 \u1094 : \{total_units\}\\n"\
        f"  \uc0\u1042 \u1089 \u1077 \u1075 \u1086  \u1079 \u1072 \u1082 \u1072 \u1079 \u1086 \u1074 : \{total_orders\}\\n"\
        f"  \uc0\u1057 \u1088 \u1077 \u1076 \u1085 \u1080 \u1081  \u1095 \u1077 \u1082 : \{avg_check:,.2f\} \u8381 "\
    )\
\
# ==================== \uc0\u1042 \u1057 \u1055 \u1054 \u1052 \u1054 \u1043 \u1040 \u1058 \u1045 \u1051 \u1068 \u1053 \u1067 \u1045  \u1060 \u1059 \u1053 \u1050 \u1062 \u1048 \u1048  \u1044 \u1051 \u1071  \u1058 \u1054 \u1042 \u1040 \u1056 \u1053 \u1054 \u1043 \u1054  \u1054 \u1058 \u1063 \u1025 \u1058 \u1040  ====================\
async def get_product_data_today():\
    now = get_current_time_msk()\
    today_str = now.date().isoformat()\
    postings = await fetch_postings(today_str, today_str)\
    products = aggregate_products(postings, date_from=today_str, date_to=today_str,\
                                  time_limit=now.time(), apply_limit_on_day=today_str)\
    return products\
\
async def get_product_data_month():\
    now = get_current_time_msk()\
    today_date = now.date()\
    current_month_start = today_date.replace(day=1).isoformat()\
    today_str = today_date.isoformat()\
    postings = await fetch_postings(current_month_start, today_str)\
    products = aggregate_products(postings, date_from=current_month_start, date_to=today_str,\
                                  time_limit=now.time(), apply_limit_on_day=today_str)\
    return products\
\
async def get_product_data_prev_month():\
    now = get_current_time_msk()\
    today_date = now.date()\
    current_month_start = today_date.replace(day=1)\
    previous_month_start = (current_month_start - datetime.timedelta(days=1)).replace(day=1)\
    days_passed = (today_date - current_month_start).days + 1\
    prev_period_end = previous_month_start + datetime.timedelta(days=days_passed - 1)\
    prev_start_str = previous_month_start.isoformat()\
    prev_end_str = prev_period_end.isoformat()\
    postings = await fetch_postings(prev_start_str, prev_end_str)\
    products = aggregate_products(postings, date_from=prev_start_str, date_to=prev_end_str,\
                                  time_limit=now.time(), apply_limit_on_day=prev_end_str)\
    return products\
\
async def format_product_combined():\
    products_today, products_month, products_prev_month = await asyncio.gather(\
        get_product_data_today(),\
        get_product_data_month(),\
        get_product_data_prev_month()\
    )\
\
    parts = []\
    parts.append(format_top_products(products_today, "\uc0\u1058 \u1086 \u1087  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  \u1079 \u1072  \u1089 \u1077 \u1075 \u1086 \u1076 \u1085 \u1103 ", limit=15))\
    parts.append("")\
    parts.append(format_top_products(products_month, "\uc0\u1058 \u1086 \u1087  \u1090 \u1086 \u1074 \u1072 \u1088 \u1086 \u1074  \u1079 \u1072  \u1090 \u1077 \u1082 \u1091 \u1097 \u1080 \u1081  \u1084 \u1077 \u1089 \u1103 \u1094  (\u1072 \u1085 \u1072 \u1083 \u1086 \u1075 . \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 )", limit=15))\
    if products_prev_month:\
        parts.append("")\
        parts.append("\uc0\u1057 \u1088 \u1072 \u1074 \u1085 \u1077 \u1085 \u1080 \u1077  \u1089  \u1087 \u1088 \u1077 \u1076 \u1099 \u1076 \u1091 \u1097 \u1080 \u1084  \u1084 \u1077 \u1089 \u1103 \u1094 \u1077 \u1084  (\u1072 \u1085 \u1072 \u1083 \u1086 \u1075 . \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 )")\
        total_rev_current = sum(p["ordered_sum"] for p in products_month.values())\
        total_rev_prev = sum(p["ordered_sum"] for p in products_prev_month.values())\
        total_units_current = sum(p["ordered_units"] for p in products_month.values())\
        total_units_prev = sum(p["ordered_units"] for p in products_prev_month.values())\
        delta_rev = ((total_rev_current - total_rev_prev) / total_rev_prev * 100) if total_rev_prev > 0 else None\
        delta_units = ((total_units_current - total_units_prev) / total_units_prev * 100) if total_units_prev > 0 else None\
        parts.append(f"  \uc0\u1042 \u1099 \u1088 \u1091 \u1095 \u1082 \u1072 : \{total_rev_current:,.2f\} \u8381  vs \{total_rev_prev:,.2f\} \u8381  (\u916  \{delta_rev:.1f\}%)" if delta_rev is not None else "  \u1042 \u1099 \u1088 \u1091 \u1095 \u1082 \u1072 : \u1085 \u1077 \u1090  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093 ")\
        parts.append(f"  \uc0\u1045 \u1076 \u1080 \u1085 \u1080 \u1094 : \{total_units_current\} vs \{total_units_prev\} (\u916  \{delta_units:.1f\}%)" if delta_units is not None else "  \u1045 \u1076 \u1080 \u1085 \u1080 \u1094 : \u1085 \u1077 \u1090  \u1076 \u1072 \u1085 \u1085 \u1099 \u1093 ")\
\
    return "\uc0\u55357 \u56550  \u1054 \u1090 \u1095 \u1105 \u1090  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 \u1084 \\n\\n\\n" + "\\n\\n".join(parts)}