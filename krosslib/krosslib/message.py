# Server Info
CLIENT_SOCKET_PORT = 50001
CLIENT_WEB_PORT = 5000
SERVER_IP = '192.168.0.193'


# Vendor
CYBOS = 'cybos'
KIWOOM = 'kiwoom'

# Type
REQUEST='request'
RESPONSE='response'
SUBSCRIBE='subscribe'
COLLECTOR='collector'
SUBSCRIBE_RESPONSE='sresponse'
REQUEST_TRADE='request_trade'
RESPONSE_TRADE='response_trade'
TRADE_SUBSCRIBE='trade_subscribe'
TRADE_SUBSCRIBE_RESPONSE='trade_sresponse'

# Market
MARKET_STOCK = 'stock'


# Method
SHUTDOWN = 'shutdown'

SUBSCRIBE_STATS = 'subscribe_stats'
COLLECTOR_STATS = 'collector_stats'
SUBSCRIBE_CODES = 'subscribe_codes'


DAY_DATA = 'day_data'
TODAY_MINUTE_DATA = 'today_min_data'
TODAY_TICK_DATA = 'today_tick_data'
MINUTE_DATA = 'minute_data'
MONTH_DATA = 'month_data'
ABROAD_DATA = 'abroad_data'
CODE_DATA = 'code_data'
CODE_TO_NAME_DATA = 'code_name_data'
USCODE_DATA = 'uscode_data'
INVESTOR_DATA = 'investor_data'
INVESTOR_ACCUMULATE_DATA = 'investor_accumulate_data'
INVESTOR_CURRENT_DATA = 'investor_current'
STOCKFUTURE_LIST_DATA = 'stockfuture_code_data'
STOCKFUTURE_BASE_LIST_DATA = 'stockfuture_base_data'
STOCKFUTURE_LIST_BY_BASE_DATA = 'stockfuture_list_by_base_data'
STOCKFUTURE_BASE_BY_CODE_DATA = 'stockfuture_base_by_code_data'

UNI_DATA = 'uni_data'
UNI_PERIOD_DATA = 'uni_period_data'
UNI_CURRENT_DATA = 'unic_data'
UNI_CURRENT_PERIOD_DATA = 'unic_period_data'

GET_LONG_LIST = 'long_list'
ORDER_STOCK = 'order_stock'
MODIFY_ORDER = 'modify_order'
CANCEL_ORDER = 'cancel_order'
ORDER_IN_QUEUE = 'order_queue'
BALANCE = 'balance'

STOCK_DATA = 'stock_realtime'
BIDASK_DATA = 'bidask_realtime'
WORLD_DATA = 'world_realtime'
INDEX_DATA = 'index_realtime'
ALARM_DATA = 'alarm_realtime'
SUBJECT_DATA = 'subject_realtime'
STOCKFUTURE_DATA = 'stockfuture_realtime'
INDUSTRY_INVEST_DATA = 'invest_industry_realtime'

STOP_STOCK_DATA = 'stock_stop_realtime'
STOP_BIDASK_DATA = 'bidask_stop_realtime'
STOP_WORLD_DATA = 'world_stop_realtime'
STOP_INDEX_DATA = 'index_stop_realtime'
STOP_ALARM_DATA = 'stop_alarm_realtime'
STOP_SUBJECT_DATA = 'subject_stop_realtime'
STOP_STOCKFUTURE_DATA = 'future_stop_realtime'
STOP_INDUSTRY_INVEST_DATA = 'invest_industry_stop_realtime'

COLLECTOR_DATA = 'collector_data'
TRADE_DATA = 'trade_realtime'
STOP_TRADE_DATA = 'trade_stop_realtime'

YESTERDAY_TOP_AMOUNT_DATA = 'ytop_amount'

# codes
STOCK_ALARM_CODE = 'STOCK_ALARM'

# Suffix for subscribe
BIDASK_SUFFIX = '_BA'
SUBJECT_SUFFIX = '_S'
WORLD_SUFFIX = '_W'
INDEX_SUFFIX = '_I'
UNI_DAY_SUFFIX = '_UD'
UNI_CURRENT_SUFFIX = '_UC'
INDUSTRY_INVEST_SUFFIX = '_II'
INVESTOR_CURRENT_SUFFIX = '_IC' # only for db

# Period Type for abroad
PERIOD_DAY = 'D'
PERIOD_WEEK = 'W'
PERIOD_MONTH = 'M'

# Capability
CAPABILITY_REQUEST_RESPONSE=1
CAPABILITY_COLLECT_SUBSCRIBE=2
CAPABILITY_TRADE=4
CAPABILITY_TRADE_SUBSCRIBE=8


ORDER_BUY = 2
ORDER_SELL = 1

# CODE_DATA market_type
KOSPI = 1
KOSDAQ = 2

# US Code Type
USTYPE_ALL=1
USTYPE_COUNTY=2
USTYPE_UPJONG=3
USTYPE_JONGMOK=4
USTYPE_DR=5
USTYPE_RAW=6
USTYPE_EXCHANGE=7
