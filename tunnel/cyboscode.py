


def tr_code(code):
    special_code = {'.DJI': 'DJI',
                    'JP#NI225': 'JPNI225',
                    '399102': 'U399102',
                    'CZ#399106': 'CZ399106',
                    '95079': 'U95079',
                    'HK#HS': 'HKHS',
                    'GR#DAX': 'GR#DAX'}
    if code in special_code:
        return special_code[code]

    return code

