import win32com.client
from datetime import datetime


class _CpEvent:
    def set_params(self, obj, code, callback):
        self.obj = obj
        self.code = code
        self.callback = callback

    def OnReceived(self):
        d = {}
        for i in range(13):
            d[str(i)] = self.obj.GetHeaderValue(i)
        d['date'] = datetime.now()
        self.callback(self.code, [d])


class _WorldRealtime:
    def __init__(self, code, callback):
        self.obj = win32com.client.gencache.EnsureDispatch("CpSysDib.WorldCur")
        self.handler = win32com.client.WithEvents(self.obj, _CpEvent)
        self.obj.SetInputValue(0, code)
        self.handler.set_params(self.obj, code, callback)

    def subscribe(self):
        self.obj.Subscribe()

    def unsubscribe(self):
        self.obj.Unsubscribe()


class WorldSubscribe:
    def __init__(self, code, callback):
        self.started = False
        self.code = code
        self.world_realtime = _WorldRealtime(code, callback)

    def start_subscribe(self, callback):
        if not self.started:
            self.started = True
            self.world_realtime.subscribe()
            print('START world subscribe stock', self.code)

    def stop_subscribe(self):
        if self.started:
            self.started = False
            self.world_realtime.unsubscribe()
            print('STOP world subscribe stock', self.code)
