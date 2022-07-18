from datetime import datetime, time, date, timedelta


IS_SIMULATION = False

MIN_INTERVAL = 3

ASSET_DIVIDER = 5

KOSDAQ_INDEX = 'U390'
KOSPI_INDEX = 'U180'
KOSDAQ_LEVERAGE = 'A233740'
KOSPI_LEVERAGE = 'A122630'
KOSDAQ_ETF = 'A229200'


START_HOUR = 9
FINISH_HOUR = (9 + 6)

CUT_UNI_INT = (FINISH_HOUR * 100 + 20)

OPEN_TIME = time(START_HOUR, 0)
CLOSE_TIME = time(FINISH_HOUR, 31)
DAY_FINAL_CANDLE_TIME = time(FINISH_HOUR, 19, 40)
DAY_END_TIME = time(FINISH_HOUR, 20)
CANDLE_W = timedelta(seconds=(60*MIN_INTERVAL))

SIMUL_FROM = datetime(2020, 12, 1, 9, 0)
SIMUL_UNTIL = datetime(2020, 12, 1, 15, 31)
SIMUL_DATE = SIMUL_FROM.date()

STATUS_UNKNOWN = 0
STATUS_OVER = 1
STATUS_UNDER = 2
STATUS_OVER_BODY = 3
STATUS_UNDER_BODY = 4
STATUS_FINAL_CANDLE = 5
STATUS_DAY_END = 6
STATUS_TEST = 7

BUY_OVER_SELL_UNDER = 0
BUY_UNDER_SELL_OVER = 1


BUY_ORDER = 0
BUY_CONFIRM = 1
BUY_SOME = 2
BUY_CANCEL_START = 3
BUY_CANCEL_CONFIRM = 4
BUY_DONE = 5
SELL_ORDER = 6
SELL_CONFIRM = 7
SELL_SOME = 8
SELL_MODIFY_START = 9
SELL_DONE = 10

EMERGENCY_CUT = -0.5

code_info = dict()
code_info[KOSDAQ_LEVERAGE] = {'index': KOSDAQ_INDEX, 'type': BUY_OVER_SELL_UNDER}
code_info[KOSPI_LEVERAGE] = {'index': KOSPI_INDEX, 'type': BUY_OVER_SELL_UNDER}


def status_to_str(status):
    if status == STATUS_OVER:
        return "STATUS_OVER"
    elif status == STATUS_UNDER:
        return "STATUS_UNDER"
    elif status == STATUS_OVER_BODY:
        return "STATUS_OVER_BODY"
    elif status == STATUS_UNDER_BODY:
        return "STATUS_UNDER_BODY"
    elif status == STATUS_DAY_END:
        return "STATUS_DAY_END"
    
    return "STATUS_UNKNOWN"


def order_status_to_str(status):
    if status == BUY_ORDER:
        return 'BUY_ORDER'
    elif status == BUY_CONFIRM:
        return 'BUY_CONFIRM'
    elif status == BUY_SOME:
        return 'BUY_SOME'
    elif status == BUY_CANCEL_START:
        return 'BUY_CANCEL_START'
    elif status == BUY_CANCEL_CONFIRM:
        return 'BUY_CANCEL_CONFIRM'
    elif status == BUY_DONE:
        return 'BUY_DONE'
    elif status == SELL_ORDER:
        return 'SELL_ORDER'
    elif status == SELL_CONFIRM:
        return 'SELL_CONFIRM'
    elif status == SELL_SOME:
        return 'SELL_SOME'
    elif status == SELL_MODIFY_START:
        return 'SELL_MODFIY_START'
    elif status == SELL_DONE:
        return 'SELL_DONE'
    return 'ORDER UNKNOWN STATUS'
