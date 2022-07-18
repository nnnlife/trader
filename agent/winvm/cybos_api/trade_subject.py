import win32com.client
from datetime import datetime


class _CpEvent:
    def set_params(self, obj, code, callback):
        self.obj = obj
        self.code = code
        self.callback = callback

    def OnReceived(self):
        d = {}
        for i in range(9):
            d[str(i)] = self.obj.GetHeaderValue(i)
        d['date'] = datetime.now()
        self.callback(self.code, [d])


class _SubjectRealtime:
    def __init__(self, code, callback):
        self.code = code
        self.obj = win32com.client.gencache.EnsureDispatch("DsCbo1.CpSvr8091S")
        self.handler = win32com.client.WithEvents(self.obj, _CpEvent)
        self.obj.SetInputValue(0, "*")
        self.obj.SetInputValue(1, self.code)
        self.handler.set_params(self.obj, self.code, callback)

    def subscribe(self):
        self.obj.Subscribe()

    def unsubscribe(self):
        self.obj.Unsubscribe()


class TradeSubject:
    def __init__(self, code, callback):
        self.started = False
        self.code = code
        self.subject_realtime = _SubjectRealtime(code, callback)

    def start_subscribe(self):
        if not self.started:
            self.started = True
            self.subject_realtime.subscribe()
            print('START subject subscribe', self.code)

    def stop_subscribe(self):
        if self.started:
            self.started = False
            self.subject_realtime.unsubscribe()
            print('STOP subject subscribe', self.code)
