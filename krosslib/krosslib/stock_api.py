from datetime import datetime, timedelta

from . import stream_readwriter
from . import message


def request_subscribe_stat(reader):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.SUBSCRIBE_STATS)
    body = []
    return reader.block_write(header, body)


def request_collector_stat(reader):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.COLLECTOR_STATS)
    body = []
    return reader.block_write(header, body)


def request_subscribe_codes(reader):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.SUBSCRIBE_CODES)
    body = []
    return reader.block_write(header, body)


def request_stock_day_data(reader, code, from_date, until_date, method=message.DAY_DATA):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, method)
    header['code'] = code
    header['from'] = from_date
    header['until'] = until_date
    body = []
    return reader.block_write(header, body)


def request_stock_month_data(reader, code, from_date, until_date, method=message.MONTH_DATA):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, method)
    header['code'] = code
    header['from'] = from_date
    header['until'] = until_date
    body = []
    return reader.block_write(header, body)


def request_stock_today_data(reader, code, method=message.TODAY_MINUTE_DATA):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, method)
    header['code'] = code
    body = []
    return reader.block_write(header, body)


def request_stock_uni_current_data(reader, code):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.UNI_CURRENT_DATA)
    header['code'] = code
    body = []
    return reader.block_write(header, body)


def request_stock_uni_current_period_data(reader, code, from_date, until_date):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.UNI_CURRENT_PERIOD_DATA)
    header['code'] = code
    header['from'] = from_date
    header['until'] = until_date
    body = []
    return reader.block_write(header, body)


def request_stock_uni_day_period_data(reader, code, from_date, until_date):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.UNI_PERIOD_DATA)
    header['code'] = code
    header['from'] = from_date
    header['until'] = until_date
    body = []
    return reader.block_write(header, body)


def request_stock_uni_day_data(reader, code):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.UNI_DATA)
    header['code'] = code
    body = []
    return reader.block_write(header, body)


def request_stock_investor_current_data(reader, code):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.INVESTOR_CURRENT_DATA)
    header['code'] = code
    body = []
    return reader.block_write(header, body)


def request_stock_today_tick_data(reader, code):
    return request_stock_today_data(reader, code, message.TODAY_TICK_DATA)


def request_investor_data(reader, code, from_date, until_date):
    now = datetime.now().date()
    if now - from_date > timedelta(days=365):
        print('over before one year data is not available')
        return []

    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.INVESTOR_DATA)
    header['code'] = code
    header['from'] = from_date
    header['until'] = until_date
    body = []
    return reader.block_write(header, body)


def request_abroad_data(reader, code, period_type, count):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.ABROAD_DATA)
    header['code'] = code
    header['period_type'] = period_type
    header['count'] = count
    body = []
    return reader.block_write(header, body)


def _send_stop_subscribe(reader, code, method):
    header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, method)
    body = []
    reader.stop_subscribe_write(header, body, code)


def request_stock_minute_data(reader, code, from_date, until_date):
    return request_stock_day_data(reader, code, from_date, until_date, message.MINUTE_DATA)


def subscribe_stock(reader, code, handler):
    if '_' in code:
        return
    header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, message.STOCK_DATA)
    body = []
    reader.subscribe_write(header, body, code, handler)


def subscribe_stockfuture(reader, code, handler):
    if '_' in code:
        return

    header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, message.STOCKFUTURE_DATA)
    body = []
    reader.subscribe_write(header, body, code, handler)


def stop_subscribe_stockfuture(reader, code):
    _send_stop_subscribe(reader, code, message.STOP_STOCKFUTURE_DATA)


def stop_subscribe_stock(reader, code):
    _send_stop_subscribe(reader, code, message.STOP_STOCK_DATA)


def subscribe_stock_bidask(reader, code, handler):
    if '_' in code:
        return

    header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, message.BIDASK_DATA)
    body = []
    code += message.BIDASK_SUFFIX
    reader.subscribe_write(header, body, code, handler)


def stop_subscribe_stock_bidask(reader, code):
    _send_stop_subscribe(reader, code + message.BIDASK_SUFFIX, message.STOP_BIDASK_DATA)


def subscribe_stock_subject(reader, code, handler):
    if '_' in code:
        return

    header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, message.SUBJECT_DATA)
    body = []
    code += message.SUBJECT_SUFFIX
    reader.subscribe_write(header, body, code, handler)


def stop_subscribe_stock_subject(reader, code):
    _send_stop_subscribe(reader, code + message.SUBJECT_SUFFIX, message.STOP_SUBJECT_DATA)


def subscribe_world(reader, code, handler):
    if '_' in code:
        return

    header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, message.WORLD_DATA)
    body = []
    code += message.WORLD_SUFFIX
    reader.subscribe_write(header, body, code, handler)


def stop_subscribe_world(reader, code):
    _send_stop_subscribe(reader, code + message.WORLD_SUFFIX, message.STOP_WORLD_DATA)
    

def subscribe_industry_invest(reader, code, handler):
    if '_' in code:
        return

    header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, message.INDUSTRY_INVEST_DATA)
    body = []
    code += message.INDUSTRY_INVEST_SUFFIX
    reader.subscribe_write(header, body, code, handler)


def stop_subscribe_industry_invest(reader, code):
    _send_stop_subscribe(reader, code + message.INDUSTRY_INVEST_SUFFIX, message.STOP_INDUSTRY_INVEST_DATA)


def subscribe_index(reader, code, handler):
    if '_' in code:
        return

    header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, message.INDEX_DATA)
    body = []
    code += message.INDEX_SUFFIX
    reader.subscribe_write(header, body, code, handler)


def stop_subscribe_index(reader, code):
    _send_stop_subscribe(reader, code + message.INDEX_SUFFIX, message.STOP_INDEX_DATA)


def subscribe_alarm(reader, handler):
    header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, message.ALARM_DATA)
    body = []
    code = message.STOCK_ALARM_CODE
    reader.subscribe_write(header, body, code, handler)


def stop_subscribe_alarm(reader):
    header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, message.STOP_ALARM_DATA)
    body = []
    code = message.STOCK_ALARM_CODE
    reader.stop_subscribe_write(header, body, code)


def request_stock_code(reader, market_type):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.CODE_DATA)
    header['market_type'] = market_type
    body = []
    return reader.block_write(header, body)


def request_stockfuture_code(reader):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.STOCKFUTURE_LIST_DATA)
    body = []
    return reader.block_write(header, body)


def request_stockfuture_base(reader):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.STOCKFUTURE_BASE_LIST_DATA)
    body = []
    return reader.block_write(header, body)


def request_stockfuture_code_by_base(reader, base_code):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.STOCKFUTURE_LIST_BY_BASE_DATA)
    header['code'] = base_code
    body = []
    return reader.block_write(header, body)


def request_stockfuture_base_by_stock(reader, stock_code):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.STOCKFUTURE_BASE_BY_CODE_DATA)
    header['code'] = stock_code
    body = []
    return reader.block_write(header, body)


def request_code_to_name(reader, code):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.CODE_TO_NAME_DATA)
    header['code'] = code
    body = []
    return reader.block_write(header, body)


def request_us_stock_code(reader, us_type):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.USCODE_DATA)
    header['us_type'] = us_type
    body = []
    return reader.block_write(header, body)


def request_long_list(reader, vendor=message.CYBOS):
    header = stream_readwriter.create_header(message.REQUEST_TRADE, message.MARKET_STOCK, message.GET_LONG_LIST, vendor)
    body = []
    return reader.block_write(header, body)


def request_yesterday_top_amount(reader, date):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.YESTERDAY_TOP_AMOUNT_DATA)
    header['date'] = date
    body = []
    return reader.block_write(header, body)


def order_stock(reader, code, price, quantity, is_buy):
    header = stream_readwriter.create_header(message.REQUEST_TRADE, message.MARKET_STOCK, message.ORDER_STOCK)
    header['code'] = code
    header['price'] = price
    header['quantity'] = quantity
    header['trade_type'] = message.ORDER_BUY if is_buy else message.ORDER_SELL
    body = []
    return reader.block_write(header, body)


def kiwoom_order_stock(reader, code, price, quantity, is_buy):
    header = stream_readwriter.create_header(message.REQUEST_TRADE, message.MARKET_STOCK, message.ORDER_STOCK, message.KIWOOM)
    header['code'] = code
    header['price'] = price
    header['quantity'] = quantity
    header['trade_type'] = message.ORDER_BUY if is_buy else message.ORDER_SELL
    body = []
    return reader.block_write(header, body)


def subscribe_trade(reader, handler, vendor=message.CYBOS):
    header = stream_readwriter.create_header(message.TRADE_SUBSCRIBE, message.MARKET_STOCK, message.TRADE_DATA, vendor)
    body = []
    reader.subscribe_trade_write(header, body, handler)


def stop_subscribe_trade(reader, vendor=message.CYBOS):
    header = stream_readwriter.create_header(message.TRADE_SUBSCRIBE, message.MARKET_STOCK, message.STOP_TRADE_DATA, vendor)
    body = []
    reader.stop_subscribe_trade_write(header, body)


def modify_order(reader, order_num: int, code, price):
    header = stream_readwriter.create_header(message.REQUEST_TRADE, message.MARKET_STOCK, message.MODIFY_ORDER)
    header['code'] = code
    header['order_number'] = order_num
    header['price'] = price
    body = []
    return reader.block_write(header, body)


def kiwoom_modify_order(reader, order_num: str, code, price, quantity, is_buy):
    header = stream_readwriter.create_header(message.REQUEST_TRADE, message.MARKET_STOCK, message.MODIFY_ORDER, message.KIWOOM)
    header['code'] = code
    header['order_number'] = order_num
    header['price'] = price
    header['quantity'] = quantity
    header['trade_type'] = message.ORDER_BUY if is_buy else message.ORDER_SELL
    body = []
    return reader.block_write(header, body)


def cancel_order(reader, order_num: int, code, amount): # quantity
    header = stream_readwriter.create_header(message.REQUEST_TRADE, message.MARKET_STOCK, message.CANCEL_ORDER)
    header['code'] = code
    header['order_number'] = order_num
    header['amount'] = amount
    body = []
    return reader.block_write(header, body)


def kiwoom_cancel_order(reader, order_num: str, code, price, is_buy):
    header = stream_readwriter.create_header(message.REQUEST_TRADE, message.MARKET_STOCK, message.CANCEL_ORDER, message.KIWOOM)
    header['code'] = code
    header['order_number'] = order_num
    header['price'] = price
    header['trade_type'] = message.ORDER_BUY if is_buy else message.ORDER_SELL
    body = []
    return reader.block_write(header, body)


def request_order_in_queue(reader):
    header = stream_readwriter.create_header(message.REQUEST_TRADE, message.MARKET_STOCK, message.ORDER_IN_QUEUE)
    body = []
    return reader.block_write(header, body)


def get_balance(reader, vendor=message.CYBOS):
    header = stream_readwriter.create_header(message.REQUEST_TRADE, message.MARKET_STOCK, message.BALANCE, vendor)
    body = []
    return reader.block_write(header, body)


def request_investor_accumulate_data(reader, code, from_date, until_date):
    header = stream_readwriter.create_header(message.REQUEST, message.MARKET_STOCK, message.INVESTOR_ACCUMULATE_DATA, message.KIWOOM)
    header['code'] = code
    header['from'] = from_date
    header['until'] = until_date
    body = []
    return reader.block_write(header, body)
