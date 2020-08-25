



_orders = {}
_bills = []
success_count = 0
fail_count = 0
CUT_RATE = 0.9728


def add_bill(code, tick, order, reason):
    global success_count, fail_count

    if order['bought'] < tick['bid_price']:
        success_count += 1
    else:
        fail_count += 1

    profit = "{0:.2f}".format((tick['bid_price'] * 0.9972 - order['bought']) / order['bought'] * 100.0)
    _bills.append({'code': code,
                   'btime': order['date'],
                   'stime': tick['date'],
                   'bought': order['bought'],
                   'sell': tick['bid_price'],
                   'profit': profit,
                   'reason': reason,
                   'scount': success_count,
                   'fcount': fail_count})
    print(_bills[-1])


def finalize(code, tick):
    global _orders

    keys = list(_orders.keys())
    if code in keys:
        for order in _orders[code]:
            add_bill(code, tick, order, 'TIMEOUT')
        del _orders[code]


def check_tick(code, tick):
    # cut at under -0.5%
    if code not in _orders:
        return False

    orders = _orders[code]
    removes = []
    for order in orders:
        if tick['current_price'] < order['bought'] * CUT_RATE: # use current, not bid because when go up, it can be possible bid_
            print('CUT', tick['current_price'], 'CUT_P', order['bought'] * CUT_RATE)
            add_bill(code, tick, order, 'CUT')
            removes.append(order)
        elif order['target'] <= tick['bid_price']:
            #print('target', order['target'], 'bid', tick['bid_price'])
            add_bill(code, tick, order, 'PROFIT')
            removes.append(order)
        #elif order['amount_point'] * 0.5 < amount_point:
        #    add_bill(code, tick, order, 'AMOUNT CUT')
        #    removes.append(order)

    for r in removes:
        orders.remove(r)

    if len(_orders[code]) == 0:
        del _orders[code]
    return True


def add_order(code, tick, prices):
    if code in _orders:
        print('ALREADY BOUGHT', code)
        return

    _orders[code] = []
    for p in prices:
        _orders[code].append({'code': code,
                         'date': tick['date'],
                         'bought': tick['ask_price'],
                         'target': p})
        print('ORDER', _orders[code][-1])


def is_bought(code):
    if code in _orders:
        return True
    return False


if __name__ == '__main__':
    from datetime import datetime
    add_order('A005930', {'date': datetime(2020,8,19,10,0,1), 'ask_price': 11100}, [11300, 11400], 1.0)
    for o in _orders['A005930']:
        print(o)

    check_tick('A005930', {'date': datetime(2020,8,19,10,0,3), 'bid_price': 10100}, 0.9)
    print(_bills)

