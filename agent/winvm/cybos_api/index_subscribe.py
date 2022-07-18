import win32com.client
from datetime import datetime


class _CpEvent:
    def set_params(self, obj, code, callback):
        self.obj = obj
        self.code = code
        self.callback = callback

    def OnReceived(self):
        d = {}
        for i in range(8):
            d[str(i)] = self.obj.GetHeaderValue(i)
        d['date'] = datetime.now()
        self.callback(self.code, [d])


class _IndexRealtime:
    def __init__(self, code, callback):
        self.obj = win32com.client.gencache.EnsureDispatch("DsCbo1.StockIndexIS")
        self.handler = win32com.client.WithEvents(self.obj, _CpEvent)
        self.obj.SetInputValue(0, code)
        self.handler.set_params(self.obj, code, callback)

    def subscribe(self):
        self.obj.Subscribe()

    def unsubscribe(self):
        self.obj.Unsubscribe()


class IndexSubscribe:
    def __init__(self, code, callback):
        self.started = False
        self.code = code
        self.index_realtime = _IndexRealtime(code, callback)

    def start_subscribe(self):
        if not self.started:
            self.started = True
            self.index_realtime.subscribe()
            print('START index subscribe stock', self.code)

    def stop_subscribe(self):
        if self.started:
            self.started = False
            self.index_realtime.unsubscribe()
            print('STOP index subscribe stock', self.code)
