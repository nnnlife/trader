import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.join(*(['..' + os.sep] * 2)))))


import socket
import time
from datetime import datetime
from PyQt5.QtWidgets import QApplication
from PyQt5 import QtCore
from PyQt5.QAxContainer import QAxWidget

from morning_server import message, stream_readwriter

from morning_server.collectors.kiwoom_api import investor_accumulate, login_info, order, account
from configs import client_info


socket_notifier = None
sock = None
_client_name = 'KIWOOM' # append suffix when regist on server
_account_num = client_info.get_kiwoom_account()


def receive_trade(gubun, count, fid_list):
    # receive whether trade is completed
    # axKHOpenAPI1.GetChejanData(10);
    print('-' * 10, 'receive_trade', '-' * 10)
    fid_list = list(map(lambda x: int(x), fid_list.split(';')))
    print('gubun', gubun, 'count', count, 'fids', fid_list)

    if gubun == '0': # 주문 접수, 체결시, '1': 국내주식 잔고 전달
        msg = order.encode_msg(ax_obj, fid_list)
        header = stream_readwriter.create_header(message.TRADE_SUBSCRIBE_RESPONSE, message.MARKET_STOCK, message.TRADE_DATA, message.KIWOOM)
        stream_readwriter.write(sock, header, msg)

    print('-' * 10, 'receive_trade end', '-' * 10)

def receive_trdata(screen_no, rqname, trcode, recordname, prev_next, data_len, err_code, msg1, msg2):
    if prev_next == '2': #TODO
        pass

    # receive order number after send order
    print('receive_trdata', 'rqname', rqname, 'trcode', trcode, 'recordname', recordname, 'prev_next', prev_next, 'data_len', data_len, 'err_code', err_code, 'msg1', msg1, 'msg2', msg2, 'screen_no', screen_no)
    if screen_no in request_dict:
        req = request_dict[screen_no]

        if req[0]['method'] == message.BALANCE:
            balance = account.get_balance(ax_obj, rqname, trcode)
            stream_readwriter.write(sock, req[0], {'balance': balance})
        elif req[0]['method'] == message.GET_LONG_LIST:
            long_list = account.get_long_list(ax_obj, rqname, trcode)
            stream_readwriter.write(sock, req[0], long_list)
       
        request_dict.pop(rqname, None)


def receive_msg(screen_no, rqname, code, msg):
    # system message
    print('receive_msg', screen_no, rqname, code, msg)


read_buf = stream_readwriter.ReadBuffer()


def handle_request(sock, header, body):
    print(_client_name, 'REQUEST ' + str(header))


def get_time_id():
    now = datetime.now()
    return now.hour * 1000000 + now.minute * 10000 + now.second * 100 + int(now.microsecond / 100000)


def handle_trade_request(sock, header, body):
    print(_client_name, 'TRADE REQUEST ' + str(header))
    header['type'] = message.RESPONSE_TRADE
    msg_id = str(get_time_id()) # use packet msg id as screen_no to identify msg
    if header['method'] == message.BALANCE:
        request_dict[msg_id] = (header, message.BALANCE)
        account.request_balance(ax_obj, _account_num, message.BALANCE, msg_id)
    elif header['method'] == message.GET_LONG_LIST:
        request_dict[msg_id] = (header, message.GET_LONG_LIST)
        account.request_long_list(ax_obj, _account_num, message.GET_LONG_LIST, msg_id)
    elif header['method'] == message.ORDER_STOCK:
        code = header['code']
        qty = header['quantity']
        price = header['price']
        is_buy = header['trade_type'] == message.ORDER_BUY
        if is_buy:
            result = order.buy(ax_obj, message.ORDER_STOCK, msg_id, _account_num, code, price, qty)
        else:
            result = order.sell(ax_obj, message.ORDER_STOCK, msg_id, _account_num, code, price, qty)
        print('result', result)
        stream_readwriter.write(sock, header, {'status': result, 'msg': ''})
    elif header['method'] == message.MODIFY_ORDER: # only support sell modify now
        order_num = header['order_number']
        code = header['code']
        price = header['price']
        qty = header['quantity'] # kiwoom need qty
        result = order.modify_sell_order(ax_obj, message.MODIFY_ORDER, msg_id, _account_num, code, price, qty, order_num)
        # after get new number then send packet
    elif header['method'] == message.CANCEL_ORDER:
        order_num = header['order_number']
        code = header['code']
        price = header['price']
        result = order.cancel_buy(ax_obj, message.CANCEL_ORDER, msg_id, _account_num, code, price, 0, order_num) 
        stream_readwriter.write(sock, header, {'result': result})
    elif header['method'] == message.ORDER_IN_QUEUE:
        pass


def handle_trade_subscribe(sock, header, body):
    print(_client_name, 'HANDLE TRADE SUBSCRIBE ' + str(header))
    # kiwoom does not have trade subscribe and handle it in callback functions


def handle_subscribe(sock, header, body):
    print(_client_name, 'HANDLE SUBSCRIBE ' + str(header))


@QtCore.pyqtSlot()
def dispatch_message():
    global read_buf, sock
    stream_readwriter.dispatch_message_for_collector(sock, read_buf,
                                                    request_handler=handle_request, 
                                                    subscribe_handler=handle_subscribe,
                                                    subscribe_trade_handler=handle_trade_subscribe,
                                                    request_trade_handler=handle_trade_request)


def event_connect(err_code):
    global socket_notifier, sock
    print('CP connected')
    if err_code == 0:
        ax_obj.dynamicCall("KOA_Functions(QString, QString)", "ShowAccountWindow", "")
        ax_obj.OnReceiveTrData.connect(receive_trdata)
        ax_obj.OnReceiveChejanData.connect(receive_trade)
        ax_obj.OnReceiveMsg.connect(receive_msg)

        while True:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_address = (message.SERVER_IP, message.CLIENT_SOCKET_PORT)
                sock.connect(server_address)
                sock.settimeout(None)
                print('Connected to apiserver')
                break
            except socket.error:
                print('Retrying connect to apiserver')
                time.sleep(1)
        
        socket_notifier = QtCore.QSocketNotifier(sock.fileno(), QtCore.QSocketNotifier.Read)
        socket_notifier.activated.connect(dispatch_message)

        header = stream_readwriter.create_header(message.COLLECTOR, message.MARKET_STOCK, message.COLLECTOR_DATA, message.KIWOOM)
        body = {'trade_count': 1, 'request_count': 0, 'collector_count': 0, 'trade_collector_count': 1}
        body['capability'] = message.CAPABILITY_TRADE | message.CAPABILITY_TRADE_SUBSCRIBE
        body['name'] = _client_name
        stream_readwriter.write(sock, header, body)


if __name__ == '__main__':
    app = QApplication([])
    request_dict = dict()

    ax_obj = QAxWidget("KHOPENAPI.KHOpenAPICtrl.1")
    ax_obj.OnEventConnect.connect(event_connect)

    ret = ax_obj.dynamicCall('CommConnect()')
    
    app.exec_()
