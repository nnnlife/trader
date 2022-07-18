from datetime import datetime
import gevent

import krosslog
from krosslib import message
from krosslib import stream_readwriter
from .server_util import stream_write


class _Collector:
    def __init__(self, sock, collector_name, capability, vendor):
        self.sock = sock
        self.capability = capability
        self.collector_name = collector_name
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

    def get_name(self):
        return self.collector_name

    def get_vendor(self):
        return self.vendor

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



class ClientManager:
    def __init__(self):
        self.collectors = []
        self.code_subscribe_info = dict()
        self.vendors = [message.CYBOS, message.KIWOOM]
        self.trade_subscribe_sockets = dict()
        for v in self.vendors:
            self.trade_subscribe_sockets[v] = []

    def _send_stop_msg(self, collector_sock, code):
        #TODO: no methods for STOP_STOCKFUTURE_DATA, because no suffix currently
        stop_methods = {message.STOCK_ALARM_CODE: message.STOP_ALARM_DATA,
                        message.BIDASK_SUFFIX: message.STOP_BIDASK_DATA,
                        message.SUBJECT_SUFFIX: message.STOP_SUBJECT_DATA,
                        message.WORLD_SUFFIX: message.STOP_WORLD_DATA,
                        message.INDEX_SUFFIX: message.STOP_INDEX_DATA,}
        processed = False
        for stop_k, stop_v in stop_methods.items():
            if code.endswith(stop_k):
                header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, stop_v)
                header['code'] = code
                stream_write(collector_sock, header, [])
                processed = True
        if not processed:
            header = stream_readwriter.create_header(message.SUBSCRIBE, message.MARKET_STOCK, message.STOP_STOCK_DATA)
            header['code'] = code
            stream_write(collector_sock, header, [])

    def _handle_code_subscribe_info_disconnection(self, sock):
        remove_code_list = []
        for k, v in self.code_subscribe_info.items():
            if sock in v[1]:
                v[1].remove(sock)
                if len(v[1]) == 0:
                    self._send_stop_msg(v[0].sock, k)
                    v[0].remove_subscribe_code(k)
                    remove_code_list.append(k)
        for code in remove_code_list:
            self.code_subscribe_info.pop(code, None)

    def _handle_trade_subscribe_disconnection(self, sock):
        for vendor in self.vendors:
            collector = self.get_trade_subscribe_collector(vendor)
            if collector is None:
                continue
            
            if sock in self.trade_subscribe_sockets[vendor]:
                self.trade_subscribe_sockets[vendor].remove(sock)
                krosslog.log('trade subscribe found and remove, left %d', len(self.trade_subscribe_sockets[vendor]))
                if len(self.trade_subscribe_sockets[vendor]) == 0:
                    header = stream_readwriter.create_header(message.TRADE_SUBSCRIBE, message.MARKET_STOCK, message.STOP_TRADE_DATA)
                    stream_write(collector.sock, header, [], self)

    def _handle_collector_disconnection(self, sock):
        remove_code_list = []
        for k, v in self.code_subscribe_info.items():
            if v[0].sock == sock:
                remove_code_list.append(k)
        found = True if len(remove_code_list) > 0 else False
        for code in remove_code_list:
            self.code_subscribe_info.pop(code, None)
            krosslog.log('remove code in code_subscribe_info %s', code)
        
        if found:
            krosslog.log('subscribe collector removed')

        collector_list = []
        for c in self.collectors:
            if c.sock == sock:
                collector_list.append(c)
        found = True if len(collector_list) > 0 else False
        for c in collector_list:
            self.collectors.remove(c)
        if found:
            krosslog.log('collector removed')

    def handle_disconnect(self, sock):
        krosslog.log('ClientManager handle disconnect')
        cybos_collectors = self.get_vendor_collector(message.CYBOS)
        kiwoom_collectors = self.get_vendor_collector(message.KIWOOM)
        for c in cybos_collectors:
            if c.sock == sock:
                self._handle_collector_disconnection(sock)
                krosslog.log('Remove collector: ' + c.get_name())
                krosslog.send_msg('Collector removed:' + c.get_name())

        for c in kiwoom_collectors:
            if c.sock == sock:
                self._handle_collector_disconnection(sock)
                krosslog.log('Remove collector: ' + c.get_name())
                krosslog.send_msg('Collector removed:' + c.get_name())

        self._handle_code_subscribe_info_disconnection(sock)
        self._handle_trade_subscribe_disconnection(sock)

    def add_client(self, sock, header, body):
        cap = body['capability']
        self.collectors.append(_Collector(sock, body['name'], cap, header['vendor']))

    def get_vendor_collector(self, vendor):
        collectors = []
        for c in self.collectors:
            if c.get_vendor() == vendor:
                collectors.append(c)
        return collectors

    def _get_collector(self, capability, vendor):
        for c in self.get_vendor_collector(vendor):
            if c.capability & capability:
                return c
        return None

    def _get_available_collector(self, capability, vendor):
        collector = None
        while True:
            available_collectors = []
            for c in self.get_vendor_collector(vendor):
                if c.capability & capability and not c.request_pending():
                    available_collectors.append(c)

            if len(available_collectors) > 0:
                available_collectors = sorted(available_collectors, key=lambda x: x.latest_request_process_time)
                available_collectors[0].latest_request_process_time = datetime.now()
                collector = available_collectors[0]
                break

            gevent.sleep()
        return collector

    def get_available_trade_collector(self, vendor=message.CYBOS):
        return self._get_available_collector(message.CAPABILITY_TRADE, vendor)

    def get_available_trade_subscribe_collector(self, vendor=message.CYBOS):
        return self._get_available_collector(message.CAPABILITY_TRADE_SUBSCRIBE, vendor)

    def get_trade_collector(self, vendor=message.CYBOS):
        # trader should be only one
        return self._get_collector(message.CAPABILITY_TRADE, vendor)

    def get_trade_subscribe_collector(self, vendor=message.CYBOS):
        return self._get_collector(message.CAPABILITY_TRADE_SUBSCRIBE, vendor)

    def get_available_request_collector(self, vendor=message.CYBOS):
        return self._get_available_collector(message.CAPABILITY_REQUEST_RESPONSE, vendor)

    def get_available_subscribe_collector(self, vendor=message.CYBOS):
        collector = None
        for c in self.get_vendor_collector(vendor):
            max_count = 400
            if c.capability & message.CAPABILITY_COLLECT_SUBSCRIBE and c.subscribe_count() < max_count:
                if collector is None:
                    collector = c
                else:
                    if collector.subscribe_count() > c.subscribe_count():
                        collector = c
        return collector

    def find_request_by_id(self, msg_id):
        for c in self.collectors:
            if c.request_id() == msg_id:
                return c
        return None

    def connect_to_subscribe(self, code, sock, header, body):
        """
        if code == 'Z000001' or code == 'T000001':
            for c in self.get_vendor_collector(message.CYBOS):
                stream_write(c.sock, header, body, None)
            return
        """
        if code in self.code_subscribe_info:
            found = False
            for s in self.code_subscribe_info[code][1]:
                if s == sock:
                    found = True
                    break
            if not found:
                self.code_subscribe_info[code][1].append(sock)
        else:
            collector = self.get_available_subscribe_collector()
            if collector is None:
                krosslog.log('NO AVAILABLE Subscribe collector')
            else:
                collector.append_subscribe_code(code)
                self.code_subscribe_info[code] = (collector, [sock])
                krosslog.log('ADD NEW SUBSCRIBE %s', code)
                stream_write(collector.sock, header, body, self)

    def connect_to_trade_subscribe(self, sock, header, body):
        vendor = header['vendor']
        collector = self.get_trade_subscribe_collector(vendor)
        if collector is None:
            krosslog.log('NO TRADE Subscribe collector %s', vendor)
            return

        if sock not in self.trade_subscribe_sockets[vendor]:
            self.trade_subscribe_sockets[vendor].append(sock)
            krosslog.log('ADD NEW TRADE SUBSCRIBE')
            stream_write(collector.sock, header, body, self)
        else:
            krosslog.log('Sock is already connected to trade subscriber %s', vendor)

    def disconnect_to_subscribe(self, code, sock, header, body):
        if code in self.code_subscribe_info:
            self.code_subscribe_info[code][1].remove(sock) 
            if len(self.code_subscribe_info[code][1]) == 0:
                collector = self.code_subscribe_info[code][0]
                collector.remove_subscribe_code(code)
                self.code_subscribe_info.pop(code, None)
                stream_write(collector.sock, header, body, self)
        else:
            krosslog.log('No subscribe but try to disconnect %s', code)

    def disconnect_to_trade_subscribe(self, sock, vendor=message.CYBOS):
        collector = self.get_trade_subscribe_collector(vendor)
        if collector is None:
            krosslog.log('NO TRADE collector %s', vendor)
            return
        if sock in self.trade_subscribe_sockets[vendor]:
            self.trade_subscribe_sockets[vendor].remove(sock)

            if len(self.trade_subscribe_sockets[vendor]) == 0:
                header = stream_readwriter.create_header(message.TRADE_SUBSCRIBE, message.MARKET_STOCK, message.STOP_TRADE_DATA)
                stream_write(collector.sock, header, [], self)

    def broadcast_subscribe_data(self, code, header, body):
        if code not in self.code_subscribe_info:
            krosslog.log('code is not in code_subscribe_info %s', code)
            return

        for s in self.code_subscribe_info[code][1]:
            stream_write(s, header, body, self)

    def broadcast_trade_data(self, header, body):
        vendor = header['vendor']
        for s in self.trade_subscribe_sockets[vendor]:
            stream_write(s, header, body, self)

    def reset(self):
        for v in self.vendors:
            self.trade_subscribe_sockets[v].clear()
        self.code_subscribe_info.clear()
        self.collectors.clear()

    def handle_block_request(self, sock, header, body, vendor=message.CYBOS):
        collector = self.get_available_request_collector(vendor)
        if collector is None:
            krosslog.log('Cannot find collector(request) %s', header)
            return
        collector.set_request(sock, header['_id'], True)
        stream_write(collector.sock, header, body, self)

    def handle_block_response(self, header, body):
        collector = self.find_request_by_id(header['_id'])
        if collector is None:
            # TODO: client will be locked, so need to return some value according to method
            krosslog.log('Cannot find collector(response) %s', header)    
            return
        collector.set_pending(False)
        stream_write(collector.request_socket(), header, body, self)

    def handle_trade_block_request(self, sock, header, body):
        collector = self.get_available_trade_collector(header['vendor'])
        if collector is None:
            krosslog.log('Cannot find collector(trade) %s', header)
            return
        collector.set_request(sock, header['_id'], True)
        # TODO: same with block, need to return some value to prevent block on client side
        stream_write(collector.sock, header, body, self)

    def handle_trade_block_response(self, header, body):
        collector = self.find_request_by_id(header['_id'])
        if collector is None:
            krosslog.log('Cannot find collector(trade response) %s', header)
            return
        collector.set_pending(False)
        stream_write(collector.request_socket(), header, body, self)
