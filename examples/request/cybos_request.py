from datetime import datetime
from krosslib import morning_client


if __name__ == '__main__':
    #print(morning_client.get_highest_price_all('A005490', datetime(2022, 5, 1), datetime(2022, 7, 10)))
    print(morning_client.get_minute_data('A005930', datetime(2022, 7, 15), datetime(2022, 7, 16)))
    #print(morning_client.get_highest_price_in_year('A005490', datetime(2020, 9, 21)))
    #print(get_uni_current_data('A005930'))
    #print(get_uni_day_data('A005930'))
    #print(get_uni_current_period_data('A005930', date(2020, 7, 31), date(2020, 8, 1)))
    #codes = get_all_market_code()
    #print(len(codes))
    #print(get_balance())
    #print(get_long_list())
    #print(get_today_minute_data('A005930'))
    #print(get_yesterday_top_amount())
    #result = get_past_day_data('A005930', date(2020, 7, 1), date(2020, 7, 8))
    #for data in result:
    #    print(data)
