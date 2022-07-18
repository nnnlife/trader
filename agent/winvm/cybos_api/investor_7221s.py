import win32com.client
from datetime import datetime

class _CpEvent:
    def set_params(self, obj, code, callback):
        self.obj = obj
        self.code = code
        self.callback = callback
        self.investors = ['individual',
                          'foreigner',
                          'organization',
                          'finance_invest',
                          'insurance',
                          'investment_trust',
                          'bank'
                          'etc_invest',
                          'pension',
                          'national_organization',
                          'etc_organization',
                          'foreginer_unregistered',
                          'private_equity']

    def OnReceived(self):
        d = {}
        d['market'] = self.obj.GetHeaderValue(0)
        d['date'] = datetime.now()
        d['time'] = self.obj.GetHeaderValue(1)
        d['code'] = self.code
        
        for i, investor in enumerate(self.investors):
            d[investor] = [self.obj.GetDataValue(0, i),
                           self.obj.GetDataValue(1, i),
                           self.obj.GetDataValue(2, i),
                           self.obj.GetDataValue(3, i)]

        self.callback(self.code, [d])


class _IndustryInvestRealtime:
    def __init__(self, code, callback):
        self.obj = win32com.client.gencache.EnsureDispatch('CpSysDib.CpSvrNew7221S')
        self.handler = win32com.client.WithEvents(self.obj, _CpEvent)
        self.obj.SetInputValue(0, code)
        self.handler.set_params(self.obj, code, callback)

    def subscribe(self):
        self.obj.Subscribe()

    def unsubscribe(self):
        self.obj.Unsubscribe()


class IndustryInvestSubscribe:
    def __init__(self, code, callback):
        self.started = False
        self.code = code
        self.industry_invest_realtime = _IndustryInvestRealtime(code, callback)

    def start_subscribe(self):
        if not self.started:
            self.started = True
            self.industry_invest_realtime.subscribe()
            print('START subscribe industry invest', self.code)

    def stop_subscribe(self):
        if self.started:
            self.started = False
            self.industry_invest_realtime.unsubscribe()
            print('STOP subscribe industry invest', self.code)
