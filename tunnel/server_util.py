from gevent import monkey; monkey.patch_all()
import sys
import gevent
from datetime import timedelta, datetime

from krosslib import stream_readwriter
from krosslib import message
from krosslib import time_converter
from krosslib import krossdb
import krosslog

from . import cyboscode

def stream_write(sock, header, body, manager = None):
    try:
        stream_readwriter.write(sock, header, body)
    except Exception as e:
        krosslog.log('Stream write error ' + str(e))
        if manager is not None:
            manager.handle_disconnect(e.args[1])


class _Collector:
    def __init__(self, sock, client_name, capability, vendor):
        self.sock = sock
        self.client_name = client_name
        self.capability = capability
        self.vendor = vendor
        self.subscribe_code = []
        self.latest_request_process_time = datetime.now()
        self.request = {
            'pending': False,
            'id': None,
            'socket': None,
            'count': 0}

    def __repr__(self):
        return 'latest_process_time:' + str(self.latest_request_process_time) + '\t' + str(self.request)

    def request_id(self):
        return self.request['id']

    def request_pending(self):
        return self.request['pending']

    def request_socket(self):
        return self.request['socket']

    def subscribe_count(self):
        return len(self.subscribe_code)

    def get_vendor(self):
        return self.vendor

    def get_collector_name(self):
        return self.client_name

    def set_pending(self, is_pending):
        #print('set_pending', is_pending)
        self.request['pending'] = is_pending
        if not is_pending:
            self.request['id'] = None

    def append_subscribe_code(self, code):
        self.subscribe_code.append(code)

    def remove_subscribe_code(self, code):
        self.subscribe_code.remove(code)

    def set_request(self, sock, msg_id, is_pending):
        self.request['socket'] = sock
        self.request['id'] = msg_id
        self.set_pending(is_pending)


class CollectorList:
    def __init__(self):
        self.collectors = []

    def add_collector(self, sock, header, body):
        self.collectors.append(_Collector(sock, body['name'], body['capability'], header['vendor']))

    def reset(self):
        self.collectors.clear()

    def handle_disconnect(self, sock):
        krosslog.log('HANDLE DISCONNECT: CollectorList')
        collector = None
        for c in self.collectors:
            if c.sock == sock:
                krosslog.log('Collector Removed')
                collector = c
                krosslog.send_msg('Collector REMOVED:' + c.get_collector_name())
                break

        if collector is not None:
            # TODO: Notify collector disconnected events to clients
            # Remove subscribes in SubsbscribeClient
            self.collectors.remove(collector)

    def get_available_trade_collector(self):
        collector = None
        while True:
            collector = self.find_trade_collector()
            if collector is not None:
                break
            gevent.sleep()
        return collector

    def get_available_request_collector(self, vendor=message.CYBOS):
        while True:
            collector = self.find_request_collector(vendor)
            if collector is not None:
                break
            gevent.sleep()
        return collector

    def find_by_id(self, msg_id):
        for c in self.collectors:
            if c.request_id() == msg_id:
                return c
        return None

    def get_vendor_collector(self, vendor):
        collectors = []
        for c in self.collectors:
            if c.get_vendor() == vendor:
                collectors.append(c)
        return collectors

    def find_request_collector(self, vendor):
        available_collectors = []
        collectors = self.get_vendor_collector(vendor)
        for c in collectors:
            if c.capability & message.CAPABILITY_REQUEST_RESPONSE and not c.request_pending():
                available_collectors.append(c)

        if len(available_collectors) == 0:
            return None
        
        available_collectors = sorted(available_collectors, key=lambda x: x.latest_request_process_time)
        available_collectors[0].latest_request_process_time = datetime.now()
        return available_collectors[0]

    def find_subscribe_collector(self):
        collector = None
        for c in self.collectors:
            max_count = 380 if c.capability & message.CAPABILITY_TRADE else 400
            if c.capability & message.CAPABILITY_COLLECT_SUBSCRIBE and c.subscribe_count() < max_count:
                if collector is None:
                    collector = c
                else:
                    if collector.subscribe_count() > c.subscribe_count():
                        collector = c
        return collector

    def find_trade_collector(self):
        collector = None
        for c in self.collectors:
            if c.capability & message.CAPABILITY_TRADE and not c.request_pending():
                collector = c
                break

        return collector


class SubscribeClient:
    def __init__(self):
        # Key: code, Values: (collector_socket, [subscribe_client_socket, ])
        self.clients = dict()
        self.trade_clients = []
        self.trader_sock = None
        self.collector = dict()

    def reset(self):
        self.clients = dict()
        self.trade_clients = []
        self.trader_sock = None

    def code_in_clients(self, code):
        return code in self.clients

    def add_trade_to_clients(self, sock, trader_sock):
        self.trader_sock = trader_sock
        if sock not in self.trade_clients:
            self.trade_clients.append(sock)

    def remove_trade_from_clients(self, sock):
        if sock in self.trade_clients:
            self.trade_clients.remove(sock)
        else:
            print('No trade subscribe client')
        # Handle count zero at handle_trade_request

    def count_of_trade_client(self):
        return len(self.trade_clients)

    def send_to_clients(self, code, header, body):
        if self.code_in_clients(code):
            #logger.info('Subscribe socket count %d', len(self.clients[code][1]))
            for s in self.clients[code][1]:
                stream_write(s, header, body, self)

    def send_trade_to_client(self, header, body):
        for s in self.trade_clients:
            stream_write(s, header, body, self)

    def handle_disconnect(self, sock):
        krosslog.log('HANDLE DISCONNECT: SubscribeClient')
        for v in self.clients.values():
            for s in v[1]:
                if s == sock:
                    v[1].remove(sock)

        # Handle trade subscriber
        if sock in self.trade_clients:
            self.trade_clients.remove(sock)
            if len(self.trade_clients) == 0:
                if self.trader_sock is not None:
                    header = stream_readwriter.create_header(message.REQUEST_TRADE, message.MARKET_STOCK, message.STOP_TRADE_DATA)
                    body = []
                    stream_write(self.trader_sock, header, body)

        remove_codes = []
        stop_methods = {message.STOCK_ALARM_CODE: message.STOP_ALARM_DATA,
                        message.BIDASK_SUFFIX: message.STOP_BIDASK_DATA,
                        message.SUBJECT_SUFFIX: message.STOP_SUBJECT_DATA,
                        message.WORLD_SUFFIX: message.STOP_WORLD_DATA,
                        message.INDEX_SUFFIX: message.STOP_INDEX_DATA,}
        # Handle other subscriber
        for k, v in self.clients.items():
            if len(v[1]) == 0:
                self.collector[k].remove_subscribe_code(k)
                self.collector.pop(k, None)
                for stop_k, stop_v in stop_methods.items():
                    if k.endswith(stop_k):
                        header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, stop_v)
                        body = []
                        header['code'] = k
                        stream_write(v[0], header, body)
                        remove_codes.append(k)
                if k not in remove_codes:
                    header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, message.STOP_STOCK_DATA)
                    body = []
                    header['code'] = k
                    stream_write(v[0], header, body)
                    remove_codes.append(k)
                   
        for code in remove_codes:
            self.clients.pop(code, None)

    def add_to_clients(self, code, sock, header, body, collectors):
        if self.code_in_clients(code):
            found = False
            for s in self.clients[code][1]:
                if s == sock:
                    found = True
                    break
            if not found:
                self.clients[code][1].append(sock)
        else:
            collector = collectors.find_subscribe_collector()
            if collector is None:
                krosslog.log('NO AVAILABLE Subscribe collector')
                # TODO return FULL
            else:
                collector.append_subscribe_code(code)
                self.clients[code] = (collector.sock, [sock])
                self.collector[code] = collector
                krosslog.log('ADD NEW SUBSCRIBE %s', code)
                stream_write(collector.sock, header, body, collectors)

    def remove_from_clients(self, code, sock, header, body, collectors):
        if self.code_in_clients(code):
            self.clients[code][1].remove(sock)
            if len(self.clients[code][1]) == 0:
                self.collector[code].remove_subscribe_code(code)
                self.collector.pop(code, None)

                stream_write(self.clients[code][0], header, body, collectors)
                self.clients.pop(code, None)
        else:
            print('No subscribe client for ' + code)

class _Partial:
    def __init__(self, header, db_data, count):
        self.header = header
        self.count = count
        self.data = []
        self.db_data = db_data

    def add_body(self, body, header):
        self.data.append(body)

        if len(body) == 0:
            stock_db = krossdb.db('stock')
            code = cyboscode.tr_code(header['code'])
            from_date = header['from']
            until_date = header['until']
            while from_date <= until_date:
                stock_db[code + '_V'].insert_one({'0': time_converter.datetime_to_intdate(from_date)})
                from_date += timedelta(days=1)
            #print('RECORD DATA to DB as EMPTY', header['method'], header['code'], header['from'], header['until'])
        else:
            stock_db = krossdb.db('stock')
            code = cyboscode.tr_code(header['code'])
            if header['method'] == message.DAY_DATA:
                stock_db[code + '_D'].insert_many(body)
            elif header['method'] == message.MINUTE_DATA:
                stock_db[code + '_M'].insert_many(body)
            elif header['method'] == message.INVESTOR_DATA:
                stock_db[code + '_INVESTOR'].insert_many(body)
            
            #print('RECORD DATA to DB', header['method'], header['code'], header['from'], header['until'])

        return len(self.data) == self.count

    def get_whole_message(self):
        datas = []
        if len(self.db_data) > 0:
            datas.append(self.db_data)

        for d in self.data:
            if len(d) > 0:
                datas.append(d)

        if len(datas) == 0:
            return datas
        elif len(datas) == 1:
            return datas[0]

        dates = []
        for i, d in enumerate(datas): # TODO: check error when Key '0' not exist
            dates.append((i, d[0]['0']))

        dates = sorted(dates, key=lambda d: d[1])
        final_data = []
        for d in dates:
            final_data.extend(datas[d[0]])
        return final_data


class PartialRequest:
    def __init__(self):
        self.client = dict()

    def reset(self):
        self.client = dict()

    def start_partial_request(self, header, data, count):
        self.client[header['_id']] = _Partial(header, data, count)

    def get_item(self, msg_id):
        if msg_id in self.client:
            return self.client[msg_id]

        return None

    def pop_item(self, msg_id):
        if msg_id in self.client:
            self.client.pop(msg_id, None)
