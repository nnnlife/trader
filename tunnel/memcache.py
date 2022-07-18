from krosslib import message


code_to_name_map = dict()



def get_cached_data(header, body):
    if header['method'] == message.CODE_TO_NAME_DATA:
        cname = get_code_to_name(header['code'])
        if len(cname) > 0:
            return [cname], []

    return None, None


def get_code_to_name(code):
    if code in code_to_name_map:
        return code_to_name_map[code]

    return ''


def cache_code_to_name(header, body):
    global code_to_name_map

    if 'code' in header and isinstance(body, list) and len(body) > 0:
        code_to_name_map[header['code']] = body[0]


def check_cacheable_data(header, body):
    if header['method'] == message.CODE_TO_NAME_DATA:
        cache_code_to_name(header, body)
