from gevent import monkey; monkey.patch_all()
from pymongo import MongoClient
from datetime import datetime, timedelta


from krosslib import morning_client
import krosslog

_code_info = {}
_name_info = {}


class CodeInfo:
    def __init__(self, code, corp_name, is_kospi):
        self.code = code
        self.corp_name = corp_name
        self.is_kospi = is_kospi


def load_code_info(codes):
    krosslog.log('collect code_info code count %d', len(codes))
    for progress, code in enumerate(codes):
        corp_name = morning_client.code_to_name(code)
        is_kospi = morning_client.is_kospi_code(code)
        _code_info[code] = CodeInfo(code, corp_name, is_kospi)
        _name_info[corp_name] = _code_info[code]

    krosslog.log('collect code_info done')


def is_kospi(code):
    if code in _code_info:
        return _code_info[code].is_kospi
    return False


def get_corp_name(code):
    if code in _code_info:
        return _code_info[code].corp_name
    return ''


def has_code_info(code):
    return code in _code_info


def get_name_to_code(name):
    if name in _name_info:
        return _name_info[name].code
    return ''
