import win32com.client
from datetime import datetime


class _CpEvent:
    def set_params(self, obj, code, callback):
        self.obj = obj
        self.code = code
        self.callback = callback

    def OnReceived(self):
        d = {}
        #for i in range(69):
        #    d[str(i)] = self.obj.GetHeaderValue(i)
        d['date'] = datetime.now()
        d['code'] = self.code
        d['time'] = self.obj.GetHeaderValue(1)
        d['volume'] = self.obj.GetHeaderValue(2)
        d['total_ask_remain'] = self.obj.GetHeaderValue(23)
        d['total_bid_remain'] = self.obj.GetHeaderValue(24)
        d['total_lp_ask_remain'] = self.obj.GetHeaderValue(67)
        d['total_lp_bid_remain'] = self.obj.GetHeaderValue(68)
        d['uni_ask_remain'] = self.obj.GetHeaderValue(25)
        d['uni_bid_remain'] = self.obj.GetHeaderValue(26)
        d['bid_prices'] = []
        d['ask_prices'] = []
        d['bid_remains'] = []
        d['ask_remains'] = []
        d['lp_bid_remains'] = []
        d['lp_ask_remains'] = []

        for i in range(3, 19+1, 4):
            ask = self.obj.GetHeaderValue(i)
            bid = self.obj.GetHeaderValue(i+1)
            if bid > 0:
                d['bid_prices'].append(bid)
                d['bid_remains'].append(self.obj.GetHeaderValue(i+3))

            if ask > 0:
                d['ask_prices'].append(ask)
                d['ask_remains'].append(self.obj.GetHeaderValue(i+2))

        for i in range(27, 43+1, 4):
            ask = self.obj.GetHeaderValue(i)
            bid = self.obj.GetHeaderValue(i+1)
            if bid > 0:
                d['bid_prices'].append(bid)
                d['bid_remains'].append(self.obj.GetHeaderValue(i+3))

            if ask > 0:
                d['ask_prices'].append(ask)
                d['ask_remains'].append(self.obj.GetHeaderValue(i+2))

        self.callback(self.code, [d])


class _BidAskRealtime:
    def __init__(self, code, callback):
        self.obj = win32com.client.gencache.EnsureDispatch("DsCbo1.StockJpBid")
        self.handler = win32com.client.WithEvents(self.obj, _CpEvent)
        self.obj.SetInputValue(0, code)
        self.handler.set_params(self.obj, code, callback)

    def subscribe(self):
        self.obj.Subscribe()

    def unsubscribe(self):
        self.obj.Unsubscribe()


class BidAskSubscribe:
    def __init__(self, code, callback):
        self.started = False
        self.code = code
        self.bidask_realtime = _BidAskRealtime(code, callback)

    def start_subscribe(self):
        if not self.started:
            self.bidask_realtime.subscribe()
            self.started = True
            print('START subscribe bidask ', self.code)

    def stop_subscribe(self):
        if self.started:
            self.bidask_realtime.unsubscribe()
            self.started = False
            print('STOP subscribe bidask ', self.code)


if __name__ == '__main__':
    from pymongo import MongoClient
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.join(*(['..' + os.sep] * 3)))))
    from configs import client_info
    from datetime import datetime, timedelta

    class TestObj:
        def __init__(self, data):
            self.data = data

        def GetHeaderValue(self, i):
            return self.data[str(i)]

        def test_callback(self, code, d):
            print(code, d)

    code = 'A005930'
    db = MongoClient('mongodb://' + client_info.get_mongo_id() + ':' + client_info.get_mongo_password() + '@' + client_info.get_server_ip() + ':27017')['trade_alarm']
    target_date = datetime(2020, 8, 14, 9, 5, 0)
    until_date = target_date + timedelta(seconds=3)
    data = list(db[code + '_BA'].find({'date': {'$gte': target_date, '$lte': until_date}}))
    print('DATA LEN', len(data))
    testObj = TestObj(data[0])
    cpEvent = _CpEvent()
    cpEvent.set_params(testObj, code, testObj.test_callback)
    cpEvent.OnReceived()
    print(data[0])
