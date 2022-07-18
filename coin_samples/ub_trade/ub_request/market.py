import requests

from . import constants

url = constants.URL + "/v1/market/all"

# {"market_warning":"NONE","market":"KRW-BTC","korean_name":"비트코인","english_name":"Bitcoin"}

def get_market_symbol(search_prefix='KRW'):
    querystring = {"isDetails":"true"}
    response = requests.request("GET", url, params=querystring)
    market_list = eval(response.text)
    market_list = list(filter(lambda x: x['market_warning'] == 'NONE' and x['market'].startswith(search_prefix), market_list))
    symbols = [m['market'] for m in market_list]
    return symbols
