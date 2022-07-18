import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..' + os.sep + '..')))


import win32com.client
from datetime import datetime

class _CpEvent:
    def set_params(self, obj, callback):
        self.obj = obj
        self.callback = callback

    def OnReceived(self):
        d = {}
        for i in range(10):
            d[str(i)] = self.obj.GetHeaderValue(i)
        d['date'] = datetime.now()
        self.callback([d])


class _AlarmRealtime:
    def __init__(self, callback):
        self.obj = win32com.client.gencache.EnsureDispatch("CpSysDib.CpSvr9619S")
        self.handler = win32com.client.WithEvents(self.obj, _CpEvent)
        self.handler.set_params(self.obj, callback)

    def subscribe(self):
        self.obj.Subscribe()

    def unsubscribe(self):
        self.obj.Unsubscribe()


class StockAlarm:
    def __init__(self, callback):
        self.alarm_realtime = _AlarmRealtime(callback)
        self.started = False

    def start_subscribe(self):
        if not self.started:
            self.started = True
            self.alarm_realtime.subscribe()
            print('START SUBSCRIBE STOCK ALARM')

    def stop_subscribe(self):
        if self.started:
            self.started = False
            self.alarm_realtime.unsubscribe()
            print('STOP SUBSCRIBE STOCK ALARM')
