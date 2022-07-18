from . import memcache
from . import cyboscode
from krosslib import cybosdb, message


def pre_handle_request(sock, header, body):
    method = header['method']
    if method == message.DAY_DATA:
        from_date = header['from']
        until_date = header['until']
        code = cyboscode.tr_code(header['code'])
        return cybosdb.get_data_from_db(code, from_date, until_date, '_D')
    elif method == message.MINUTE_DATA:
        from_date = header['from']
        until_date = header['until']
        code = cyboscode.tr_code(header['code'])
        return cybosdb.get_data_from_db(code, from_date, until_date, '_M')
    elif method == message.INVESTOR_DATA:
        from_date = header['from']
        until_date = header['until']
        code = cyboscode.tr_code(header['code'])
        return cybosdb.get_data_from_db(code, from_date, until_date, '_INVESTOR')

    return memcache.get_cached_data(header, body)
