from candidate import today_bull
from candidate import vi
from candidate import ninethirty
from morning.pipeline.converter import dt
import preload


def clear_all():
    vi.clear_all()
    today_bull.clear_all() 
    ninethirty.clear_all()


def handle_vi(code, data):
    return vi.handle_vi(code, data)


def get_vi_prices(code):
    return vi.get_vi_prices(code)


def get_vi(opt, catch_plus):
    return vi.get_vi(opt, catch_plus)


def get_today_list(opt, catch_plus, acculmulated):
    return today_bull.get_today_list(opt, catch_plus, acculmulated)


def get_ninethirty_list():
    return ninethirty.get_ninethirty_codes()


def handle_today_tick(code, d):
    d = dt.cybos_stock_tick_convert(d)
    vi.calculate_vi_price(code, d)
    ret = 0
    ret |= ninethirty.handle_tick(code, d)
    ret |= today_bull.handle_today_bull(code, d)
    return ret
