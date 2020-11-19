import json
import os

_client_info = None
TEST_MODE = False

def _get_client_info():
    global _client_info
    if _client_info is None:
        filename = 'configs/client_info.json'

        try:
            filename = os.environ['MORNING_PATH'] + os.sep + filename
        except KeyError:
            print('NO MORNING_PATH SYSTEM ENVIRONMENT VARIABLE') 

        try:
            with open(filename) as json_file:
                _client_info = json.load(json_file)
        except FileNotFoundError:
            print('No Client Config File')
            _client_info = dict()
            _client_info['client_name'] = 'Unknown'
            _client_info['password'] = ''
            _client_info['certificate_password'] = ''
            _client_info['capability'] = 0
            _client_info['mongo_id'] = ''
            _client_info['mongo_password'] = ''
            _client_info['server_ip'] = 'localhost'
            _client_info['collector_count'] = 0
            _client_info['kiwoom_account'] = ''
    return _client_info


def add_client_name_suffix(suffix):
    client_name = get_client_name()
    _get_client_info()['client_name'] = client_name + '_' + suffix


def get_client_name():
    return _get_client_info()['client_name']

def get_kiwoom_account():
    if 'kiwwom_account' in _get_client_info():
        return _get_client_info()['kiwoom_account']
    return ''

def get_client_password():
    return _get_client_info()['password']

def get_client_certificate_password():
    return _get_client_info()['certificate_password']

def get_client_capability():
    capability = _get_client_info()['capability']
    request = 1 if 'request' in capability else 0
    subscribe = 2 if 'subscribe' in capability else 0
    trade = 4 if 'trade' in capability else 0
    return request | subscribe | trade


def get_collector_count():
    return _get_client_info()['collector_count']

def get_mongo_id():
    return _get_client_info()['mongo_id']

def get_mongo_password():
    return _get_client_info()['mongo_password']

def get_server_ip():
    return _get_client_info()['server_ip']

if __name__ == '__main__':
    print('client_name', get_client_name())
    print('client_password', get_client_password())
    print('client_certificate_password', get_client_certificate_password())
    print('client_capability', get_client_capability())
    print('client_mongo_id', get_mongo_id())
    print('client_mongo_password', get_mongo_password())
    print('client_server_ip', get_server_ip())
