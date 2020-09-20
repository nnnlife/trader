import numpy as np


FRAME_COUNT = 3

def get_trend_frame(second_ticks):
    trend_frame = int(len(second_ticks) / FRAME_COUNT)
    if trend_frame % 2 != 0:
        trend_frame -= 1
    return trend_frame


def get_resistance_points(second_ticks):
    trend_frame = get_trend_frame(second_ticks)
    half = int(trend_frame / 2)
    is_resistance = np.full((len(second_ticks),), False)

    resistances = []

    for i, stick in enumerate(second_ticks):
        left_index = i - half
        right_index = left_index + trend_frame
        if left_index < 0:
            left_index = 0
        if right_index > len(second_ticks):
            right_index = len(second_ticks)
        
        arr = second_ticks[left_index:right_index]
        max_price = max([st.high for st in arr])
        if stick.high == max_price and not np.any(is_resistance[left_index:right_index]):
            is_resistance[i] = True
            resistances.append((stick.time, stick.high))

    return resistances


def get_support_points(second_ticks):
    trend_frame = get_trend_frame(second_ticks)
    half = int(trend_frame / 2)
    is_support = np.full((len(second_ticks),), False)

    supports = []

    for i, stick in enumerate(second_ticks):
        left_index = i - half
        right_index = left_index + trend_frame
        if left_index < 0:
            left_index = 0
        if right_index > len(second_ticks):
            right_index = len(second_ticks)
        
        arr = second_ticks[left_index:right_index]
        min_price = min([st.low for st in arr])
        if stick.low == min_price and not np.any(is_support[left_index:right_index]):
            is_support[i] = True
            supports.append((stick.time, stick.low))

    return supports


def is_support_up_trend(points):
    low_prices = []
    prev_price = 0

    for p in points:
        if p[1] == prev_price:
            continue
        low_prices.append(p[1])
        prev_price = p[1]
    
    if len(low_prices) >= 2:
        prev_price = 0
        for l in low_prices:
            if l < prev_price:
                return False
            prev_price = l
        return True
    return False


def is_resistance_up_trend(points):
    if len(points) < 2:
        return False

    arr_time = np.arange(0, len(points))
    prices = [p[1] for p in points]
    m, _ = np.polyfit(arr_time, prices, 1)
    return m > 0


def get_safe_seconds(second_ticks):
    trend_frame = int(len(second_ticks) / FRAME_COUNT)
    return int(trend_frame / 10)


if __name__ == '__main__':
    import pandas as pd
    #df = pd.read_excel('A013810_sec_tick.xlsx')
    #get_support_points(df.values.tolist())

    a = [(0,1), (0,2), (0,2), (0,3)]
    print(is_support_up_trend(a))

