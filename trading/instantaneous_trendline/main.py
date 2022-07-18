from gevent import monkey; monkey.patch_all()

import gevent
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), *(['..' + os.sep] * 2))))

from morning_server import message
from clients.instantaneous_trendline import logger
from clients.instantaneous_trendline.stockindex import StockIndex
from datetime import datetime
from . import config
from . import TradeETF
from . import TradeGapETF
from . import trade
from clients.instantaneous_trendline import record
from clients.common import morning_client

if config.IS_SIMULATION:
    import datagenerator
    from mock import stock_api
else:
    from morning_server import stock_api


trader = None


def heart_beat(today):
    close_time = datetime.combine(today, config.CLOSE_TIME)
    while(True):
        if datetime.now() >= close_time:
            break
        
        if trader is not None:
            trader.timer_event()
        gevent.sleep(1)


def start_trader(vendor=message.CYBOS):
    global trader
    logger.setup_log(vendor)

    if vendor == message.KIWOOM:
        handle_codes = [config.KOSDAQ_ETF] # etf codes, not index
    else:
        handle_codes = [config.KOSDAQ_LEVERAGE] # etf codes, not index

    if config.IS_SIMULATION:
        today = config.SIMUL_DATE
    else:
        today = datetime.now().date()

    logger.info('START TRADER %s', today)

    trader = trade.Trader(vendor)
    if config.IS_SIMULATION:
        long_list = stock_api.request_long_list(None)
    else:
        long_list = morning_client.get_long_list(vendor)
        print(long_list)

    for l in long_list:
        if l['code'] in handle_codes:
            index_point = record.load_trade(today, l['code'])
            trader.create_initial_order(l['code'], l['price'], l['sell_available'], index_point)

    #kospi_index = StockIndex(config.IS_SIMULATION, today, KOSPI_INDEX, trader.get_progress_order_count([KOSPI_LEVERAGE]))
    #kospi_index.start_index_listening()

    kosdaq_index = StockIndex(config.IS_SIMULATION, trader, today, config.KOSDAQ_INDEX, trader.get_progress_order_count([config.KOSDAQ_LEVERAGE]))
    kosdaq_index.start_listening()
    
    if vendor == message.KIWOOM:
        kosdaq_etf = TradeGapETF(config.IS_SIMULATION, config.BUY_OVER_SELL_UNDER, config.KOSDAQ_ETF, trader)
        kosdaq_etf.start_listening()
    else:
        #kospi_leverage = TradeETF(config.IS_SIMULATION, config.BUY_OVER_SELL_UNDER, KOSPI_LEVERAGE, trader)
        kosdaq_etf = TradeETF(config.IS_SIMULATION, config.BUY_OVER_SELL_UNDER, config.KOSDAQ_LEVERAGE, trader)
        #kospi_leverage.start_listening()
        kosdaq_etf.start_listening()

    #kospi_index.add_watcher(kospi_leverage)
    kosdaq_index.add_watcher(kosdaq_etf)

    if config.IS_SIMULATION:
        datagenerator.run_simulation(config.SIMUL_FROM, config.SIMUL_UNTIL, trader)
    else:
        gevent.joinall([gevent.spawn(heart_beat, today)])

    record.save_trade(trader)
    trader.summary()

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'kiwoom':
        start_trader(message.KIWOOM)
    else:
        start_trader()
