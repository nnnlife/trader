from gevent import monkey
monkey.patch_all()

import grpc.experimental.gevent as grpc_gevent
grpc_gevent.init_gevent()

import grpc
import gevent

import os
import sys

from concurrent import futures
from datetime import datetime, timedelta
from pymongo import MongoClient
from gevent.queue import Queue

from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf.empty_pb2 import Empty

import krosslog
from stock_service import stock_provider_pb2_grpc
from stock_service import stock_provider_pb2
from stock_service import preload
from krosslib import morning_client
from krosslib import holiday
from krosslib import stock_api

from stock_service.candidate import favorite



RATIO_MIN_AMOUNT = 100000000
SLEEP_DURATION = 0.0001
recent_search_codes = []
is_subscribe_alarm = False
is_subscribe_trade = False
is_subscribe_tick = {}
is_subscribe_bidask = {}
is_subscribe_subject = {}
vi_price_info = {}
subject_summary = {}
broker_minute_tick = {}




class StockServicer(stock_provider_pb2_grpc.StockServicer):
    def __init__(self, is_skip_ydata):
        krosslog.info('StockService init start')
        morning_client.get_reader()
        morning_client.get_broadcast_receiver()
        self.skip_ydata = is_skip_ydata

        self.stock_subscribe_clients = []
        self.bidask_subscribe_clients = []
        self.subject_subscribe_clients = []
        self.current_time_subscribe_clients = []
        self.alarm_subscribe_clients = []
        self.list_changed_subscribe_clients = []
        self.subject_summary_subscribe_clients = []
        self.subject_minute_tick_subscribe_clients = []
        self.current_stock_selection_subscribe_clients = []
        self.simulation_changed_subscribe_clients = []
        self.order_result_subscribe_clients  = []
        self.cybos_order_result_subscribe_clients = []
        self.trader_clients = []
        self.current_stock_code = ""
        self.simulation_operators = []
        self.amount_gauge = {} # {'code': [buy_amount, sell_amount, market_type]}

        self.current_datetime = None
        self.simulation_on = False
        self.today_top_list = {'momentum': [], 'ratio': [], 'amount': []}
        self.strategy_list = []
        preload.load(datetime.now(), self.skip_ydata)

        krosslog.info('StockService init ready')

    def SayHello(self, request, context):
        krosslog.info('Say Hello')
        return Empty()

    def GetDayData(self, request, context):
        krosslog.info('GetDayData %s, %s, %s', request.code,
                            request.from_datetime.ToDatetime() + timedelta(hours=9),
                            request.until_datetime.ToDatetime() + timedelta(hours=9))
        day_datas = morning_client.get_past_day_data(
            request.code,
            request.from_datetime.ToDatetime() + timedelta(hours=9),
            request.until_datetime.ToDatetime() + timedelta(hours=9))
        protoc_converted = []
        for d in day_datas:
            protoc_converted.append(stock_provider_pb2.CybosDayData(
                date = d['0'],
                time = d['time'],
                start_price = int(d['start_price']),
                highest_price = int(d['highest_price']),
                lowest_price = int(d['lowest_price']),
                close_price = int(d['close_price']),
                volume = d['volume'],
                amount = d['amount'],
                cum_sell_volume = d['cum_sell_volume'],
                cum_buy_volume = d['cum_buy_volume'],
                foreigner_hold_volume = d['foreigner_hold_volume'],
                foreigner_hold_rate = d['foreigner_hold_rate'],
                institution_buy_volume = d['institution_buy_volume'],
                institution_cum_buy_volume = d['institution_cum_buy_volume']))
        return stock_provider_pb2.CybosDayDatas(day_data=protoc_converted)

    def GetMinuteData(self, request, context):
        krosslog.info('GetMinuteData %s %s %s', request.code,
                               request.from_datetime.ToDatetime() + timedelta(hours=9),
                               request.until_datetime.ToDatetime() + timedelta(hours=9))
        minute_datas = morning_client.get_minute_data(
            request.code,
            request.from_datetime.ToDatetime() + timedelta(hours=9),
            request.until_datetime.ToDatetime() + timedelta(hours=9))
        protoc_converted = []
        for m in minute_datas:
            protoc_converted.append(stock_provider_pb2.CybosDayData(
                date = m['0'],
                time = m['time'],
                start_price = int(m['start_price']),
                highest_price = int(m['highest_price']),
                lowest_price = int(m['lowest_price']),
                close_price = int(m['close_price']),
                volume = m['volume'],
                amount = m['amount'],
                cum_sell_volume = m['cum_sell_volume'],
                cum_buy_volume = m['cum_buy_volume'],
                foreigner_hold_volume = m['foreigner_hold_volume'],
                foreigner_hold_rate = m['foreigner_hold_rate'],
                institution_buy_volume = m['institution_buy_volume'],
                institution_cum_buy_volume = m['institution_cum_buy_volume']))

        return stock_provider_pb2.CybosDayDatas(day_data=protoc_converted)

    def GetTodayMinuteData(self, request, context):
        krosslog.info("GetTodayMinuteData %s", request)
        minute_datas = morning_client.get_today_minute_data(request.code)
        protoc_converted = []
        for m in minute_datas:
            protoc_converted.append(stock_provider_pb2.CybosDayData(
                date = m['0'],
                time = m['time'],
                start_price = int(m['start_price']),
                highest_price = int(m['highest_price']),
                lowest_price = int(m['lowest_price']),
                close_price = int(m['close_price']),
                volume = m['volume'],
                amount = m['amount'],
                cum_sell_volume = m['cum_sell_volume'],
                cum_buy_volume = m['cum_buy_volume'],
                foreigner_hold_volume = m['foreigner_hold_volume'],
                foreigner_hold_rate = m['foreigner_hold_rate'],
                institution_buy_volume = m['institution_buy_volume'],
                institution_cum_buy_volume = m['institution_cum_buy_volume']))

        return stock_provider_pb2.CybosDayDatas(day_data=protoc_converted)


    def GetPastMinuteData(self, request, context):
        krosslog.info('GetPastMinuteData %s', request)
        today = request.today.ToDatetime()
        yesterday = holiday.get_yesterday(today)
        from_date = holiday.get_date_by_previous_working_day_count(yesterday, request.count_of_days - 1)
        minute_datas = morning_client.get_minute_data(request.code, from_date, yesterday)
        protoc_converted = []
        for m in minute_datas:
            protoc_converted.append(stock_provider_pb2.CybosDayData(
                date = m['0'],
                time = m['time'],
                start_price = int(m['start_price']),
                highest_price = int(m['highest_price']),
                lowest_price = int(m['lowest_price']),
                close_price = int(m['close_price']),
                volume = m['volume'],
                amount = m['amount'],
                cum_sell_volume = m['cum_sell_volume'],
                cum_buy_volume = m['cum_buy_volume'],
                foreigner_hold_volume = m['foreigner_hold_volume'],
                foreigner_hold_rate = m['foreigner_hold_rate'],
                institution_buy_volume = m['institution_buy_volume'],
                institution_cum_buy_volume = m['institution_cum_buy_volume']))

        return stock_provider_pb2.CybosDayDatas(day_data=protoc_converted)
      
    def GetYearHigh(self, request, context):
        price = preload.get_yesterday_year_high(request.code)
        distance = 0
        if price > 0:
            hdate = preload.get_yesterday_year_high_datetime(request.code)
            if self.current_datetime is not None:
                distance = (self.current_datetime - hdate).days
            else:
                distance = (datetime.now() - hdate).days
            high_date = Timestamp()
            high_date.FromDatetime(hdate)
        krosslog.info('GetYearHigh %s, %d %d', request.code, price, distance)
        return stock_provider_pb2.YearHighInfo(price=price, high_date=high_date, days_distance=distance)

    def IsKospi(self, request, context):
        return stock_provider_pb2.Bool(ret=preload.is_kospi(request.code))

    def GetCompanyName(self, request, context):
        return stock_provider_pb2.CompanyName(company_name=preload.get_corp_name(request.code))

    def GetSubscribeCodes(self, request, context):
        codes_filtered = []
        codes = morning_client.get_subscribe_codes()
        for code in codes:
            if (code.startswith('A') or code.startswith('U')) and len(code) <= 7:
                codes_filtered.append(code)
        return stock_provider_pb2.CodeList(codelist=codes_filtered)

    def ReportOrderResult(self, request, context):
        for o in self.order_result_subscribe_clients:
            o.put_nowait(request)
        return Empty()

    def RequestCybosTickData(self, request, context):
        global is_subscribe_tick
        if request.code not in is_subscribe_tick:
            stock_api.subscribe_stock(morning_client.get_broadcast_receiver(),
                                    request.code, self.handle_stock_tick)
            krosslog.info('Start SubscribeStock %s', request.code)
            is_subscribe_tick[request.code] = True
        else:
            krosslog.info('Already SubscribeStock %s', request.code)
        return Empty()

    def RequestCybosBidAsk(self, request, context):
        global is_subscribe_bidask
        if request.code not in is_subscribe_bidask:
            stock_api.subscribe_stock_bidask(morning_client.get_broadcast_receiver(),
                                            request.code, self.handle_bidask_tick)
            krosslog.info('Start Subscribe BidAsk %s', request.code)
            is_subscribe_bidask[request.code] = True
        else:
            krosslog.info('Already Subscribe BidAsk %s', request.code)
        return Empty()

    def RequestCybosSubject(self, request, context):
        global is_subscribe_subject
        if request.code not in is_subscribe_subject:
            stock_api.subscribe_stock_subject(morning_client.get_broadcast_receiver(),
                                            request.code, self.handle_subject_tick) 
            krosslog.info('Start Subscribe Subject %s', request.code)
            is_subscribe_subject[request.code] = True
        else:
            krosslog.info('Already Subscribe Subject %s', request.code)
        return Empty()

    def RequestCybosAlarm(self, request, context):
        global is_subscribe_alarm

        if not is_subscribe_alarm:
            stock_api.subscribe_alarm(morning_client.get_broadcast_receiver(),
                                        self.handle_alarm_tick)
            krosslog.info('Start Subscribe alarm')
            is_subscribe_alarm = True
        else:
            krosslog.info('Already subscribe alarm')
        return Empty()

    def RequestCybosTradeResult(self, request, context):
        global is_subscribe_trade

        if not is_subscribe_trade:
            krosslog.info('Start Trade Result')
            stock_api.subscribe_trade(morning_client.get_trade_broadcast_receiver(),
                                        self.handle_trade_result)
            is_subscribe_trade = True
        else:
            krosslog.info('Already subscribe trade')
        return Empty()

    def GetBalance(self, request, context):
        balance = morning_client.get_balance()
        return stock_provider_pb2.Balance(balance=balance)

    def ClearRecentList(self, request, context):
        if len(recent_search_codes) > 0:
            recent_search_codes.clear()
            self.send_list_changed('recent')

    def send_list_changed(self, type_name):
        for c in self.list_changed_subscribe_clients:
            c.put_nowait(stock_provider_pb2.ListType(type_name=type_name))

    def RequestToTrader(self, request, context):
        for o in self.trader_clients:
            o.put_nowait(request)
        return Empty()

    def SetViPriceInfo(self, request, context):
        #krosslog.debug('SetViPriceInfo %s(%s)', request.code, request.price)
        vi_price_info[request.code] = request.price
        return Empty()

    def GetViPrice(self, request, context):
        if request.code in vi_price_info:
            print('GetViPrice', request.code, vi_price_info[request.code])
            return stock_provider_pb2.Prices(price=vi_price_info[request.code])
        return stock_provider_pb2.Prices(price=[])

    def AddBrokerMinuteTick(self, request, context):
        if request.code not in broker_minute_tick:
            broker_minute_tick[request.code] = []

        broker_minute_tick[request.code].append(request)

        for q in self.subject_minute_tick_subscribe_clients:
            q.put_nowait(request)

        return Empty()

    def GetBrokerMinuteTick(self, request, context):
        if request.code in broker_minute_tick:
            return stock_provider_pb2.BrokerMinuteTickList(code=request.code, minute_tick=broker_minute_tick[request.code])
        return stock_provider_pb2.BrokerMinuteTickList(code=request.code)


    def GetBrokerSummary(self, request, context):
        if request.code in subject_summary:
            return subject_summary[request.code]

        return stock_provider_pb2.BrokerSummary()

    def SetBrokerSummary(self, request, context):
        #print('SetBrokerSummary', request.code)
        subject_summary[request.code] = request

        for c in self.subject_summary_subscribe_clients:
            c.put_nowait(request)
        return Empty()

    def SetCurrentStock(self, request, context):
        global recent_search_codes

        if len(request.code) == 0:
            return Empty()

        parsed_code = preload.parse_code(request.code)

        if len(parsed_code) == 0:
            return Empty()

        self.current_stock_code = parsed_code

        for q in self.current_stock_selection_subscribe_clients:
            q.put_nowait(stock_provider_pb2.StockCodeQuery(code=parsed_code))

        if request.code not in recent_search_codes: # TODO: when code is selected in recent list then?
            recent_search_codes.insert(0, parsed_code)
            self.send_list_changed('recent')

        krosslog.debug('SetCurrentStock %s', parsed_code)
        return Empty()

    def SetCurrentDateTime(self, request ,context):
        if not self.simulation_on:
            preload.load(request.ToDatetime() + timedelta(hours=9), self.skip_ydata)
            vi_price_info.clear()
            subject_summary.clear()
            self.amount_gauge.clear()
            self.today_top_list['momentum'] = []
            self.today_top_list['ratio'] = []
            self.today_top_list['amount'] = []
            print('clear strategy_list', self.strategy_list)
            self.strategy_list = []
            self.send_list_changed('ttopamount')
            self.send_list_changed('strategy')

        self.handle_time(request.ToDatetime())
        return Empty()

    def AddFavorite(self, request, context):
        krosslog.debug('AddFavorite %s', request.code)
        if favorite.add_to_favorite(request.code):
            self.send_list_changed('favorite')
        return Empty()

    def RemoveFavorite(self, request, context):
        krosslog.debug('RemoveFavorite %s', request.code)
        if favorite.remove_from_favorite(request.code):
            self.send_list_changed('favorite')
        return Empty()

    def GetViList(self, request, context):
        krosslog.info('GetViList')
        return stock_provider_pb2.CodeList(codelist=[])

    def GetTodayTopAmountList(self, request, context):
        krosslog.info('GetTodayTopAmountList')
        codelist = None
        if request.selection == stock_provider_pb2.TodayTopSelection.TOP_BY_RATIO:
            codelist = self.today_top_list['ratio']
        elif request.selection == stock_provider_pb2.TodayTopSelection.TOP_BY_MOMENTUM:
            codelist = self.today_top_list['momentum']
        elif request.selection == stock_provider_pb2.TodayTopSelection.TOP_BY_AMOUNT:
            codelist = self.today_top_list['amount']

        if codelist is None:
            codelist = []
        return stock_provider_pb2.CodeList(codelist=codelist)


    def SetSimulationStatus(self, request, context):
        if self.simulation_on ^ request.simulation_on:
            krosslog.info('Simulation status changed %s', request.simulation_on)
            self.simulation_on = request.simulation_on
            for q in self.simulation_changed_subscribe_clients:
                q.put_nowait(stock_provider_pb2.SimulationStatus(simulation_on=self.simulation_on))

        return Empty()


    def GetSimulationStatus(self, request, context):
        return stock_provider_pb2.SimulationStatus(simulation_on=self.simulation_on)

    def handle_bidask_tick(self, code, data_arr):
        if len(data_arr) != 1:
            return

        if '_BA' in code:
            code = code[:code.index('_')]

        data = data_arr[0]
        tick_date = Timestamp()
        tick_date.FromDatetime(data['date'])
        bidask = stock_provider_pb2.CybosBidAskTickData(tick_date=tick_date,
                                                    code=code,
                                                    time=data['time'],
                                                    volume=data['volume'],
                                                    bid_prices=data['bid_prices'],
                                                    ask_prices=data['ask_prices'],
                                                    bid_remains=data['bid_remains'],
                                                    ask_remains=data['ask_remains'],
                                                    total_ask_remain=data['total_ask_remain'],
                                                    total_bid_remain=data['total_bid_remain'],
                                                    out_time_total_ask_remain=data['uni_ask_remain'],
                                                    out_time_total_bid_remain=data['uni_bid_remain'])

        for q in self.bidask_subscribe_clients:
            q.put_nowait(bidask)

    def handle_stock_tick(self, code, data_arr):
        if len(data_arr) != 1:
            return

        data = data_arr[0]
        tick_date = Timestamp()
        tick_date.FromDatetime(data['date'] - timedelta(hours=9))
        if code not in self.amount_gauge:
            self.amount_gauge[code] = [0, 0, 49]

        if data['20'] == 50:
            if self.amount_gauge[code][2] != 50:
                self.amount_gauge[code] = [0, 0, 50]
            else:
                if data['14'] == ord('1'):
                    self.amount_gauge[code][0] += int(data['13']) * data['17']
                else:
                    self.amount_gauge[code][1] += int(data['13']) * data['17']
        else:
            self.amount_gauge[code] = [0, 0, data['20']]

        amount_ratio = 0.0
        if self.amount_gauge[code][0] > RATIO_MIN_AMOUNT and self.amount_gauge[code][1] > RATIO_MIN_AMOUNT:
            amount_ratio = self.amount_gauge[code][0] / (self.amount_gauge[code][0] + self.amount_gauge[code][1])

        try:
            tick_data = stock_provider_pb2.CybosTickData(tick_date=tick_date,
                                                    code=code,
                                                    company_name=data['1'],
                                                    yesterday_diff=data['2'],
                                                    time=data['3'],
                                                    start_price=int(data['4']),
                                                    highest_price=int(data['5']),
                                                    lowest_price=int(data['6']),
                                                    ask_price=int(data['7']),
                                                    bid_price=int(data['8']),
                                                    cum_volume=data['9'],
                                                    cum_amount=data['10'],
                                                    current_price=int(data['13']),
                                                    buy_or_sell=(data['14'] == ord('1')),
                                                    cum_sell_volume_by_price=data['15'],
                                                    cum_buy_volume_by_price=data['16'],
                                                    volume=data['17'],
                                                    time_with_sec=data['18'],
                                                    market_type_exp=data['19'],
                                                    market_type=data['20'],
                                                    out_time_volume=data['21'],
                                                    cum_sell_volume=data['27'],
                                                    cum_buy_volume=data['28'],
                                                    is_kospi=preload.is_kospi(code),
                                                    amount_ratio=amount_ratio)
        except ValueError as e:
            print('Tick ValueError', e)
            return


        for q in self.stock_subscribe_clients:
            q.put_nowait(tick_data)

    def handle_subject_tick(self, code, data_arr):
        if len(data_arr) != 1:
            return

        if '_' in code:
            code = code[:code.index('_')]

        data = data_arr[0]

        tick_date = Timestamp()
        tick_date.FromDatetime(data['date'] - timedelta(hours=9))
        tick_data = stock_provider_pb2.CybosSubjectTickData(tick_date=tick_date,
                                                        time=data['0'],
                                                        name=data['1'],
                                                        code=code,
                                                        company_name=data['3'],
                                                        buy_or_sell=(data['4'] == ord('2')),
                                                        volume=data['5'],
                                                        total_volume=data['6'],
                                                        foreigner_total_volume=data['8'])

        for q in self.subject_subscribe_clients:
            q.put_nowait(tick_data)
        gevent.sleep(SLEEP_DURATION)

    def handle_alarm_tick(self, _, data_arr):
        if len(data_arr) != 1:
            return

        data = data_arr[0]
        tick_date = Timestamp()
        tick_date.FromDatetime(data['date'] - timedelta(hours=9))
        code = data['code'] if 'code' in data else data['3']

        tick_data = stock_provider_pb2.CybosStockAlarm(tick_date=tick_date,
                                                time=data['0'],
                                                type_category=data['1'],
                                                market_category=data['2'],
                                                code=code,
                                                alarm_category=data['4'],
                                                title=data['5'],
                                                content=data['6'])
        for q in self.alarm_subscribe_clients:
            q.put_nowait(tick_data)

        gevent.sleep(SLEEP_DURATION)

    def handle_trade_result(self, data):
        """
        result = {
            'flag': flag,
            'code': code,
            'order_number': order_num,
            'quantity': quantity,
            'price': price,
            'order_type': order_type,
            'total_quantity': total_quantity
        }
        """
        if 'flag' not in data or 'quantity' not in data or 'code' not in data:
            krosslog.warning('RESULT without flag or quantity %s', str(data))
        else:
            data = stock_provider_pb2.CybosOrderResult(flag=ord(data['flag']),
                                                        code=data['code'],
                                                        order_number=str(data['order_number']),
                                                        price=data['price'],
                                                        is_buy=(data['order_type'] == '2'),
                                                        quantity=data['quantity'],
                                                        total_quantity=data['total_quantity'])
            krosslog.info('TRADE RESULT %s', data)
            for q in self.cybos_order_result_subscribe_clients:
                q.put_nowait(data)

    def handle_time(self, d):
        self.current_datetime = d
        data_date = Timestamp()
        data_date.FromDatetime(d)
        for q in self.current_time_subscribe_clients:
            q.put_nowait(data_date)

    def ListenCurrentTime(self, request, context):
        title = 'ListenCurrentTime' 
        client_list = self.current_time_subscribe_clients
        q = Queue()
        client_list.append(q)
        krosslog.info('%s %d', title, len(client_list))

        current = Timestamp()
        if self.current_datetime is None:
            current.FromDatetime(datetime.now() - timedelta(hours=9))
        else:
            current.FromDatetime(self.current_datetime)

        yield current

        while True:
            try:
                data = q.get(True, 1)
                yield data
            except gevent.queue.Empty as ge:
                if not context.is_active():
                    break

        client_list.remove(q)
        krosslog.info('Done %s %d', title, len(client_list))

    def handle_queue_based_listener(self, title, client_list, context):
        q = Queue()
        client_list.append(q)
        krosslog.info('%s %d', title, len(client_list))

        while True:
            try:
                data = q.get(True, 1)
                yield data
            except gevent.queue.Empty as ge:
                if not context.is_active():
                    break
     
        client_list.remove(q)
        krosslog.info('Done %s %d', title, len(client_list))

    def ListenCurrentStock(self, request, context):
        if len(self.current_stock_code) > 0:
            yield stock_provider_pb2.StockCodeQuery(code=self.current_stock_code)

        data = self.handle_queue_based_listener('ListenCurrentStock',
                                                self.current_stock_selection_subscribe_clients,
                                                context)
        for d in data:
            yield d

    def ListenListChanged(self, request, context):
        data = self.handle_queue_based_listener('ListenListChanged',
                                                self.list_changed_subscribe_clients,
                                                context)
        for d in data:
            yield d

    def ListenBrokerSummary(self, request, context):
        data = self.handle_queue_based_listener('ListenBrokerSummary',
                                                self.subject_summary_subscribe_clients,
                                                context)
        for d in data:
            yield d

    def ListenBrokerMinuteTick(self, request, context):
        data = self.handle_queue_based_listener('ListenBrokerMinuteTick', self.subject_minute_tick_subscribe_clients, context)
        for d in data:
            yield d



    def ListenCybosTickData(self, request, context):
        q = Queue()
        self.stock_subscribe_clients.append(q)
        krosslog.info('%s %d', 'ListenCybosTickData', len(self.stock_subscribe_clients))

        while True:
            data = q.get(True)
            yield data
     
        self.stock_subscribe_clients.remove(q)
        krosslog.info('Done %s %d', 'ListenCybosTickData', len(self.stock_subscribe_clients))

    def ListenCybosBidAsk(self, request, context):
        q = Queue()
        self.bidask_subscribe_clients.append(q)
        krosslog.info('%s %d', 'ListenCybosBidAsk', len(self.bidask_subscribe_clients))

        while True:
            data = q.get(True)
            yield data
     
        self.bidask_subscribe_clients.remove(q)
        krosslog.info('Done %s %d', 'ListenCybosBidAsk', len(self.bidask_subscribe_clients))

    def ListenCybosSubject(self, request, context):
        data = self.handle_queue_based_listener('ListenCybosSubject',
                                                self.subject_subscribe_clients,
                                                context)
        for d in data:
            yield d

    def ListenCybosAlarm(self, request, context):
        data = self.handle_queue_based_listener('ListenCybosAlarm',
                                                self.alarm_subscribe_clients,
                                                context)
        for d in data:
            yield d

    def ListenOrderResult(self, request, context):
        data = self.handle_queue_based_listener('ListenOrderResult',
                                                self.order_result_subscribe_clients,
                                                context)
        for d in data:
            yield d

    def ListenCybosOrderResult(self, request, context):
        data = self.handle_queue_based_listener('ListenCybosOrderResult',
                                                self.cybos_order_result_subscribe_clients,
                                                context)
        for d in data:
            yield d

    def ListenSimulationStatusChanged(self, request, context):
        data = self.handle_queue_based_listener('ListenSimulationStatusChanged',
                                                self.simulation_changed_subscribe_clients,
                                                context)
        for d in data:
            yield d

    def ListenSimulationOperation(self, request, context):
        data = self.handle_queue_based_listener('ListenSimulationOperation',
                                                self.simulation_operators,
                                                context)
        for d in data:
            yield d


    def ListenTraderMsg(self, request, context):
        data = self.handle_queue_based_listener('ListenTraderMsg',
                                                self.trader_clients,
                                                context)
        for d in data:
            yield d

    def GetRecentSearch(self, request, context):
        return stock_provider_pb2.CodeList(codelist=recent_search_codes)

    def GetFavoriteList(self, request, context):
        return stock_provider_pb2.CodeList(codelist=favorite.get_favorite())

    def GetStrategyList(self, request, context):
        return stock_provider_pb2.CodeList(codelist=self.strategy_list)

    def SetStrategyList(self, request, context):
        krosslog.info('STRATEGY LIST %d', len(request.codelist))
        self.strategy_list = request.codelist
        self.send_list_changed('strategy')

        return Empty()

    def SetTodayAmountTopList(self, request, context):
        krosslog.info('AMOUNT LIST %d', len(request.codelist))
        self.today_top_list['amount'] = request.codelist
        # this is last one in today_bull, only call list changed in here to avoid duplication
        self.send_list_changed('ttopamount')
        return Empty()

    def SetTodayAmountRatioList(self, request, context):
        krosslog.info('RATIO LIST %d', len(request.codelist))
        self.today_top_list['ratio'] = request.codelist
        return Empty()

    def SetTodayAmountMomentumList(self, request, context):
        krosslog.info('MOMENTUM LIST %d', len(request.codelist))
        self.today_top_list['momentum'] = request.codelist
        return Empty()

    def GetYesterdayTopAmountList(self, request, context):
        dt = request.ToDatetime() + timedelta(hours=9)
        top_list = morning_client.get_yesterday_top_amount(dt) 
        krosslog.info('GetYesterdayTopAmountList %s count:%d %s %s', dt, len(top_list[0]), top_list[1], top_list[2])
        return stock_provider_pb2.TopList(codelist=top_list[0], is_today_data=top_list[1], date=top_list[2])

    def GetYesterdayUpperLimitList(self, request, context):
        upper_limit_list = preload.get_yesterday_upper_limit()
        krosslog.info('GetYesterdayUpperLimitList count:%d', len(upper_limit_list))
        return stock_provider_pb2.CodeList(codelist=upper_limit_list)

    def OrderStock(self, request, context):
        ret = stock_api.order_stock(morning_client.get_reader(), request.code, request.price, request.quantity, request.is_buy)
        krosslog.info('OrderStock %s, RET: %s', request, ret)
        return stock_provider_pb2.CybosOrderReturn(result=ret['status'], msg=ret['msg'])

    def ChangeOrder(self, request, context):
        try:
            order_num = int(request.order_num)
            ret = stock_api.modify_order(morning_client.get_reader(), order_num, request.code, request.price)
            krosslog.info('ChangeOrder %s, RET: %s', request, ret)
        except ValueError as ve:
            krosslog.warning('ValueError %s', ve)
            return stock_provider_pb2.CybosOrderReturn(order_num=0, msg='Value Error ' + str(request.order_num))

        return stock_provider_pb2.CybosOrderReturn(order_num=ret['order_number'])

    def CancelOrder(self, request, context):
        try:
            order_num = int(request.order_num)
            ret = stock_api.cancel_order(morning_client.get_reader(), order_num, request.code, request.quantity)
            krosslog.info('CancelOrder %s RET: %s', request, ret)
        except ValueError as ve:
            krosslog.warning('ValueError %s', ve)
            return stock_provider_pb2.CybosOrderReturn(result=['result'], msg='Value Error ' + request.order_num)

        return stock_provider_pb2.CybosOrderReturn(result=ret['result'])

    def StartSimulation(self, request, context):
        if preload.loading:
            krosslog.info('Preloading data, cannot start simulation')
            return stock_provider_pb2.Bool(ret=False)
        elif len(self.simulation_operators) == 0:
            krosslog.info('No Simulation Exist')
            return stock_provider_pb2.Bool(ret=False)

        krosslog.info('Start Simulation %s', request)
        for q in self.simulation_operators:
            q.put_nowait(request)    
        return stock_provider_pb2.Bool(ret=True)

    def StopSimulation(self, request, context):
        if len(self.simulation_operators) == 0:
            krosslog.info('No simulator running')
        else:
            krosslog.info('StopSimulation')

        msg = stock_provider_pb2.SimulationOperation(is_on=False)
        for q in self.simulation_operators:
            q.put_nowait(msg)
        return Empty()

    def SimulationData(self, request_iterator, context):
        krosslog.info('Simulation Data')
        for smsg in request_iterator:
            if smsg.msgtype == stock_provider_pb2.SimulationMsgType.MSG_TICK:
                code = smsg.tick.code
                smsg.tick.is_kospi = preload.is_kospi(code)
                if code not in self.amount_gauge:
                    self.amount_gauge[code] = [0, 0, 49]

                if smsg.tick.market_type == 50:
                    if self.amount_gauge[code][2] != 50:
                        self.amount_gauge[code] = [0, 0, 50]
                    else:
                        if smsg.tick.buy_or_sell:
                            self.amount_gauge[code][0] += smsg.tick.volume * smsg.tick.current_price
                        else:
                            self.amount_gauge[code][1] += smsg.tick.volume * smsg.tick.current_price
                else:
                    self.amount_gauge[code] = [0, 0, smsg.tick.market_type]

                amount_ratio = 0.0
                if self.amount_gauge[code][0] > RATIO_MIN_AMOUNT and self.amount_gauge[code][1] > RATIO_MIN_AMOUNT:
                    amount_ratio = self.amount_gauge[code][0] / (self.amount_gauge[code][0] + self.amount_gauge[code][1])
                smsg.tick.amount_ratio = amount_ratio

                for q in self.stock_subscribe_clients:
                    q.put_nowait(smsg.tick)
            elif smsg.msgtype == stock_provider_pb2.SimulationMsgType.MSG_BIDASK:
                for q in self.bidask_subscribe_clients:
                    q.put_nowait(smsg.bidask)
            elif smsg.msgtype == stock_provider_pb2.SimulationMsgType.MSG_SUBJECT:
                for q in self.subject_subscribe_clients:
                    q.put_nowait(smsg.subject)
                gevent.sleep(SLEEP_DURATION)
            elif smsg.msgtype == stock_provider_pb2.SimulationMsgType.MSG_ALARM:
                for q in self.alarm_subscribe_clients:
                    q.put_nowait(smsg.alarm)
                gevent.sleep(SLEEP_DURATION)
        krosslog.info('Simulation Data done')
        yield Empty()


def serve(is_skip_ydata):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=100))
    stock_provider_pb2_grpc.add_StockServicer_to_server(StockServicer(is_skip_ydata), server)
    server.add_insecure_port('[::]:50052')
    server.start()

    print('Start GRPC Server')
    server.wait_for_termination()


if __name__ == '__main__':
    skip_ydata_loading = False
    if len(sys.argv) > 1 and sys.argv[1] == 'skip':
        skip_ydata_loading = True

    serve(skip_ydata_loading)
