from gevent import monkey; monkey.patch_all()
import preload # important not use from clients.grpc_converter
import config


_today_data = {}
_ninethirty_codes = []


def clear_all():
    _today_data.clear()
    _ninethirty_codes.clear()


def get_ninethirty_codes():
    return _ninethirty_codes


def handle_tick(code, d):
    if preload.loading or preload.is_skip_ydata():
        return config.CAND_NONE

    if preload.get_yesterday_amount(code) < 3000000000:
        return config.CAND_NONE

    year_high = preload.get_yesterday_year_high(code)
    if d['cum_amount'] == 0:
        amount = d['cum_volume'] * d['current_price']
    else:
        if preload.is_kospi(code):
            amount = d['cum_amount'] * 10000
        else:
            amount = d['cum_amount'] * 1000

    if year_high * 0.95 <= d['current_price'] <= year_high and d['current_price'] > preload.get_yesterday_close(code) and amount >= preload.get_yesterday_amount(code) * 0.5:
        if code not in _ninethirty_codes:
            print('ADD NINE', 'year high', year_high, 'current', d['current_price'], 'yesterday amount', preload.get_yesterday_amount(code), 'today amount', amount)
            _ninethirty_codes.insert(0, code)
            return config.CAND_NINETHIRTY
    else:
        if code in _today_data:
            del _today_data[code]

    return config.CAND_NONE
