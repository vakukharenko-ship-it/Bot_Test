{\rtf1\ansi\ansicpg1251\cocoartf2870
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw3288\paperh2267\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx566\tx1133\tx1700\tx2267\tx2834\tx3401\tx3968\tx4535\tx5102\tx5669\tx6236\tx6803\pardirnatural\partightenfactor0

\f0\fs24 \cf0 import datetime\
from config import MOSCOW_TZ\
\
def aggregate_postings(postings, date_from=None, date_to=None, time_limit=None, apply_limit_on_day=None):\
    """\
    \uc0\u1040 \u1075 \u1088 \u1077 \u1075 \u1080 \u1088 \u1091 \u1077 \u1090  \u1086 \u1090 \u1075 \u1088 \u1091 \u1079 \u1082 \u1080  \u1087 \u1086  \u1076 \u1085 \u1103 \u1084  \u1089  \u1091 \u1095 \u1105 \u1090 \u1086 \u1084  \u1086 \u1087 \u1094 \u1080 \u1086 \u1085 \u1072 \u1083 \u1100 \u1085 \u1086 \u1075 \u1086  \u1086 \u1075 \u1088 \u1072 \u1085 \u1080 \u1095 \u1077 \u1085 \u1080 \u1103  \u1087 \u1086  \u1074 \u1088 \u1077 \u1084 \u1077 \u1085 \u1080  \u1076 \u1083 \u1103  \u1082 \u1086 \u1085 \u1082 \u1088 \u1077 \u1090 \u1085 \u1086 \u1075 \u1086  \u1076 \u1085 \u1103 .\
    """\
    aggregated = \{\}\
    for posting in postings:\
        created_at = posting.get("created_at", "")\
        if not created_at:\
            continue\
        try:\
            dt = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))\
            dt_msk = dt.astimezone(MOSCOW_TZ)\
        except:\
            continue\
        date_str = dt_msk.date().isoformat()\
        if date_from and date_str < date_from:\
            continue\
        if date_to and date_str > date_to:\
            continue\
\
        if time_limit is not None and apply_limit_on_day is not None and date_str == apply_limit_on_day:\
            if dt_msk.time() > time_limit:\
                continue\
\
        products = posting.get("products", [])\
        total_units = 0\
        total_sum = 0.0\
        for product in products:\
            qty = int(product.get("quantity", 0))\
            price_str = product.get("price", "0")\
            try:\
                price = float(price_str)\
            except:\
                price = 0.0\
            total_units += qty\
            total_sum += price * qty\
\
        status = posting.get("status", "")\
        if date_str not in aggregated:\
            aggregated[date_str] = \{\
                "ordered_units": 0,\
                "ordered_sum": 0.0,\
                "delivered_units": 0,\
                "delivered_sum": 0.0,\
                "canceled_units": 0,\
                "canceled_sum": 0.0,\
            \}\
\
        aggregated[date_str]["ordered_units"] += total_units\
        aggregated[date_str]["ordered_sum"] += total_sum\
\
        if status in ("cancelled", "canceled"):\
            aggregated[date_str]["canceled_units"] += total_units\
            aggregated[date_str]["canceled_sum"] += total_sum\
        elif status in ("delivered", "completed"):\
            aggregated[date_str]["delivered_units"] += total_units\
            aggregated[date_str]["delivered_sum"] += total_sum\
\
    return aggregated\
\
\
def aggregate_finance_expenses(transactions):\
    """\
    \uc0\u1040 \u1075 \u1088 \u1077 \u1075 \u1080 \u1088 \u1091 \u1077 \u1090  \u1088 \u1072 \u1089 \u1093 \u1086 \u1076 \u1099  \u1080 \u1079  \u1092 \u1080 \u1085 \u1072 \u1085 \u1089 \u1086 \u1074 \u1099 \u1093  \u1090 \u1088 \u1072 \u1085 \u1079 \u1072 \u1082 \u1094 \u1080 \u1081 .\
    \uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1097 \u1072 \u1077 \u1090  \u1089 \u1083 \u1086 \u1074 \u1072 \u1088 \u1100  \{\u1082 \u1072 \u1090 \u1077 \u1075 \u1086 \u1088 \u1080 \u1103 : \u1089 \u1091 \u1084 \u1084 \u1072 _\u1088 \u1072 \u1089 \u1093 \u1086 \u1076 \u1072 \}.\
    """\
    expense_by_type = \{\}\
\
    for t in transactions:\
        sale_comm = t.get("sale_commission", 0)\
        if sale_comm < 0:\
            expense_by_type["\uc0\u1050 \u1086 \u1084 \u1080 \u1089 \u1089 \u1080 \u1103  Ozon"] = expense_by_type.get("\u1050 \u1086 \u1084 \u1080 \u1089 \u1089 \u1080 \u1103  Ozon", 0) + abs(sale_comm)\
\
        accruals = t.get("accruals_for_sale", 0)\
        if accruals < 0:\
            expense_by_type["\uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090  \u1074 \u1099 \u1088 \u1091 \u1095 \u1082 \u1080 "] = expense_by_type.get("\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090  \u1074 \u1099 \u1088 \u1091 \u1095 \u1082 \u1080 ", 0) + abs(accruals)\
\
        delivery_charge = t.get("delivery_charge", 0)\
        if delivery_charge < 0:\
            expense_by_type["\uc0\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072  (\u1086 \u1090 \u1076 \u1077 \u1083 \u1100 \u1085 \u1086 )"] = expense_by_type.get("\u1044 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072  (\u1086 \u1090 \u1076 \u1077 \u1083 \u1100 \u1085 \u1086 )", 0) + abs(delivery_charge)\
\
        return_delivery = t.get("return_delivery_charge", 0)\
        if return_delivery < 0:\
            expense_by_type["\uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1085 \u1072 \u1103  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072 "] = expense_by_type.get("\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1090 \u1085 \u1072 \u1103  \u1076 \u1086 \u1089 \u1090 \u1072 \u1074 \u1082 \u1072 ", 0) + abs(return_delivery)\
\
        amount = t.get("amount", 0)\
        op_type = t.get("operation_type_name", "\uc0\u1053 \u1077 \u1080 \u1079 \u1074 \u1077 \u1089 \u1090 \u1085 \u1099 \u1081  \u1090 \u1080 \u1087 ")\
\
        services = t.get("services", [])\
        if services and isinstance(services, list):\
            has_negative_service = False\
            for service in services:\
                service_name = service.get("name", "\uc0\u1053 \u1077 \u1080 \u1079 \u1074 \u1077 \u1089 \u1090 \u1085 \u1072 \u1103  \u1091 \u1089 \u1083 \u1091 \u1075 \u1072 ")\
                service_amount = service.get("price", 0)\
                if service_amount == 0:\
                    service_amount = service.get("amount", 0)\
                if service_amount < 0:\
                    has_negative_service = True\
                    expense_by_type[service_name] = expense_by_type.get(service_name, 0) + abs(service_amount)\
            if not has_negative_service and amount < 0:\
                expense_by_type[op_type] = expense_by_type.get(op_type, 0) + abs(amount)\
        else:\
            if amount < 0:\
                expense_by_type[op_type] = expense_by_type.get(op_type, 0) + abs(amount)\
\
    return expense_by_type\
\
\
def aggregate_products(postings, date_from=None, date_to=None, time_limit=None, apply_limit_on_day=None):\
    """\
    \uc0\u1040 \u1075 \u1088 \u1077 \u1075 \u1080 \u1088 \u1091 \u1077 \u1090  \u1076 \u1072 \u1085 \u1085 \u1099 \u1077  \u1087 \u1086  \u1090 \u1086 \u1074 \u1072 \u1088 \u1072 \u1084  (\u1087 \u1088 \u1086 \u1076 \u1091 \u1082 \u1090 \u1072 \u1084 ) \u1079 \u1072  \u1087 \u1077 \u1088 \u1080 \u1086 \u1076 .\
    \uc0\u1042 \u1086 \u1079 \u1074 \u1088 \u1072 \u1097 \u1072 \u1077 \u1090  \u1089 \u1083 \u1086 \u1074 \u1072 \u1088 \u1100  \{sku: \{name, offer_id, ordered_units, ...\}\}.\
    """\
    product_stats = \{\}\
    for posting in postings:\
        created_at = posting.get("created_at", "")\
        if not created_at:\
            continue\
        try:\
            dt = datetime.datetime.fromisoformat(created_at.replace('Z', '+00:00'))\
            dt_msk = dt.astimezone(MOSCOW_TZ)\
        except:\
            continue\
        date_str = dt_msk.date().isoformat()\
        if date_from and date_str < date_from:\
            continue\
        if date_to and date_str > date_to:\
            continue\
        if time_limit is not None and apply_limit_on_day is not None and date_str == apply_limit_on_day:\
            if dt_msk.time() > time_limit:\
                continue\
\
        status = posting.get("status", "")\
        products = posting.get("products", [])\
        for product in products:\
            sku = str(product.get("sku", "0"))\
            name = product.get("name", "\uc0\u1041 \u1077 \u1079  \u1085 \u1072 \u1079 \u1074 \u1072 \u1085 \u1080 \u1103 ")\
            offer_id = product.get("offer_id", "")\
            qty = int(product.get("quantity", 0))\
            price_str = product.get("price", "0")\
            try:\
                price = float(price_str)\
            except:\
                price = 0.0\
\
            if sku not in product_stats:\
                product_stats[sku] = \{\
                    "name": name[:60],\
                    "offer_id": offer_id,\
                    "ordered_units": 0,\
                    "ordered_sum": 0.0,\
                    "delivered_units": 0,\
                    "delivered_sum": 0.0,\
                    "canceled_units": 0,\
                    "canceled_sum": 0.0,\
                    "order_count": 0,\
                \}\
            stats = product_stats[sku]\
            stats["ordered_units"] += qty\
            stats["ordered_sum"] += price * qty\
            stats["order_count"] += 1\
\
            if status in ("delivered", "completed"):\
                stats["delivered_units"] += qty\
                stats["delivered_sum"] += price * qty\
            elif status in ("cancelled", "canceled"):\
                stats["canceled_units"] += qty\
                stats["canceled_sum"] += price * qty\
\
    return product_stats}