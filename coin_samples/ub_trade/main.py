import asyncio
from ub_request import market, quote
from ub_subscribe import subscribe
import coin

TICKER = 'ticker'
ORDERBOOK = 'orderbook'
TRADE = 'trade'
MID_TERM_COUNT = 24 * 2 * 5 # max 5 day using 30 min
SHORT_TERM_COUNT = 24 * 20 # max 1 day using 3 min

coins = dict()


def ticker_handler(data):
    coins[data['code']].set_current_tick(data)


def orderbook_handler(data):
    coins[data['code']].set_current_orderbook(data)


def callback(ticket, data):
    if ticket == TICKER:
        ticker_handler(data)


async def main():
    symbols = market.get_market_symbol()
    print(symbols[0])
    for symbol in symbols[:1]:
        coins[symbol] = coin.Coin(symbol)

        day_quotes = quote.get_day_quote(symbols[0], 100)

        print("day quotes count", len(day_quotes))
        if len(day_quotes) < 5: # check at least over 
            continue

        day_quotes = day_quotes[::-1] # last index will be today
        print(day_quotes[0], '\n', day_quotes[-1])
        coins[symbol].set_day_quote(day_quotes)

        mid_term = quote.get_minute_quote(symbol, 30, MID_TERM_COUNT)
        mid_term = mid_term[::-1]
        #mid_term = coins[symbol].set_minutes_quote(
        #    30, 
        #)

        print("minutes quotes count", len(day_quotes))
        print(mid_term[0], '\n', mid_term[-1])
        coins[symbol].set_minutes_quote(
            3, quote.get_minute_quote(symbol, 3, 100)
        )
        await asyncio.sleep(0.2) # restrction 8 req per a second, 900 req per a minute

    symbols = symbols[:1]
    quote_task = subscribe.run(TRADE, symbols, callback)
    orderbook_task = subscribe.run(ORDERBOOK, symbols, callback)
    await asyncio.gather(quote_task, orderbook_task)


asyncio.run(main())
