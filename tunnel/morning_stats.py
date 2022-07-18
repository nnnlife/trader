from datetime import datetime, timedelta
import numpy as np

from krosslib import message


class MorningStats:
    def __init__(self, collectors):
        self.collectors = collectors
        self.subscribe_response_by_minute = {'bidask':[0], 'stock':[0], 'world':[0], 'index':[0], 'subject':[0]}
        self.latest_datatime = None

    def increment_subscribe_count(self, code):
        if self.latest_datatime is None:
            self.latest_datatime = datetime.now()

        if datetime.now() - self.latest_datatime > timedelta(seconds=60):
            self.subscribe_response_by_minute['bidask'].append(0)
            self.subscribe_response_by_minute['stock'].append(0)
            self.subscribe_response_by_minute['world'].append(0)
            self.subscribe_response_by_minute['index'].append(0)
            self.subscribe_response_by_minute['subject'].append(0)
            self.latest_datatime = datetime.now()
        else:
            if code.endswith(message.BIDASK_SUFFIX):
                self.subscribe_response_by_minute['bidask'][-1] += 1
            elif code.endswith(message.SUBJECT_SUFFIX):
                self.subscribe_response_by_minute['subject'][-1] += 1
            elif code.endswith(message.WORLD_SUFFIX):
                self.subscribe_response_by_minute['world'][-1] += 1
            elif code.endswith(message.INDEX_SUFFIX):
                self.subscribe_response_by_minute['index'][-1] += 1
            else:
                self.subscribe_response_by_minute['stock'][-1] += 1

    def get_subscribe_response_info(self):
        by_minute = [5, 10, 30, 60] 
        sr_info = dict() 
        keys = ['stock', 'bidask', 'world', 'index', 'subject']
        for bm in by_minute:
            for key in keys:
                sr_info[key + '_' + str(bm)] = sum(self.subscribe_response_by_minute[key][-(bm):])
        return sr_info

    def get_collector_info(self):
        msg = []
        for c in self.collectors:
            info = dict()
            info['name'] = c.get_name()
            info['vendor'] = c.get_vendor()
            info['subscribe_count'] = c.subscribe_count()
            info['subscribe_codes'] = c.subscribe_code
            info['lastest_process_time'] = c.latest_request_process_time
            capability = ''
            if c.capability & message.CAPABILITY_REQUEST_RESPONSE:
                capability += 'REQ/REP'
            if c.capability & message.CAPABILITY_COLLECT_SUBSCRIBE:
                capability += ' SUBSCRIBE'
            if c.capability & message.CAPABILITY_TRADE:
                capability += ' TRADE'
            if c.capability & message.CAPABILITY_TRADE_SUBSCRIBE:
                capability += ' TRADE_SUBSCRIBE'
            info['capability'] = capability
            msg.append(info)
        return msg

    def get_subscribe_codes(self):
        codes = []
        for c in self.collectors:
            codes.extend(c.subscribe_code)
        return codes
