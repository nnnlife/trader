import asyncio
import aiohttp
import json

"""
{'type': 'ticker',
'code': 'KRW-BTC',
'opening_price': 63816000.0,
'high_price': 64510000.0,
'low_price': 63500000.0,
'trade_price': 63784000.0,
'prev_closing_price': 63814000.0,
'acc_trade_price': 395552084046.8838,
'change': 'FALL',
'change_price': 30000.0,
'signed_change_price': -30000.0,
'change_rate': 0.0004701163,
'signed_change_rate': -0.0004701163,
'ask_bid': 'BID',
'trade_volume': 0.0059,
'acc_trade_volume': 6175.28774051,
'trade_date': '20210430',
'trade_time': '054055',
'trade_timestamp': 1619761255000,
'acc_ask_volume': 3228.70700843,
'acc_bid_volume': 2946.58073208,
'highest_52_week_price': 81994000.0,
'highest_52_week_date': '2021-04-14',
'lowest_52_week_price': 10121000.0,
'lowest_52_week_date': '2020-05-11',
'trade_status': None,
'market_state': 'ACTIVE',
'market_state_for_ios': None,
'is_trading_suspended': False,
'delisting_date': None,
'market_warning': 'NONE',
'timestamp': 1619761255446,
'acc_trade_price_24h': 831205401414.5348,
'acc_trade_volume_24h': 13010.35061695,
'stream_type': 'REALTIME'}


{'type': 'orderbook',
'code': 'KRW-ETH',
'timestamp': 1619769498796,
'total_ask_size': 212.14399221,
'total_bid_size': 524.62688694,
'orderbook_units': [{'ask_price': 3268000.0, 'bid_price': 3267000.0, 'ask_size': 18.10406094, 'bid_size': 22.61801701}, {'ask_price': 3269000.0, 'bid_price': 3266000.0, 'ask_size': 2.04809824, 'bid_size': 18.27941732}, {'ask_price': 3270000.0, 'bid_price': 3265000.0, 'ask_size': 12.52937291, 'bid_size': 31.75353014}, {'ask_price': 3271000.0, 'bid_price': 3264000.0, 'ask_size': 14.19335837, 'bid_size': 38.4059283}, {'ask_price': 3272000.0, 'bid_price': 3263000.0, 'ask_size': 3.01851053, 'bid_size': 38.81292109}, {'ask_price': 3273000.0, 'bid_price': 3262000.0, 'ask_size': 2.6071016, 'bid_size': 47.5477978}, {'ask_price': 3274000.0, 'bid_price': 3261000.0, 'ask_size': 4.54161044, 'bid_size': 55.9823083}, {'ask_price': 3275000.0, 'bid_price': 3260000.0, 'ask_size': 23.34297801, 'bid_size': 69.87485117}, {'ask_price': 3276000.0, 'bid_price': 3259000.0, 'ask_size': 6.3587397, 'bid_size': 36.42238879}, {'ask_price': 3277000.0, 'bid_price': 3258000.0, 'ask_size': 8.23665634, 'bid_size': 21.62937287}, {'ask_price': 3278000.0, 'bid_price': 3257000.0, 'ask_size': 4.46701952, 'bid_size': 24.63758182}, {'ask_price': 3279000.0, 'bid_price': 3256000.0, 'ask_size': 21.63263353, 'bid_size': 20.6918275}, {'ask_price': 3280000.0, 'bid_price': 3255000.0, 'ask_size': 47.14208167, 'bid_size': 38.43498752}, {'ask_price': 3281000.0, 'bid_price': 3254000.0, 'ask_size': 21.86341761, 'bid_size': 9.99220245}, {'ask_price': 3282000.0, 'bid_price': 3253000.0, 'ask_size': 22.0583528, 'bid_size': 49.54375486}], 'stream_type': 'SNAPSHOT'}
"""


# subscribe_type : ticker, trade, orderbook
async def run(subscribe_type, symbols, callback):
    session = aiohttp.ClientSession()
    async with session.ws_connect('wss://api.upbit.com/websocket/v1') as ws:
        req = [{"ticket": subscribe_type}, {"type": subscribe_type, "codes": symbols}]

        print('send ws', req)
        await ws.send_str(str(req).replace('\'', '\"'))
        async for msg in ws:
            msg = await ws.receive()

            if msg.type == aiohttp.WSMsgType.TEXT:
                if msg.data == 'close':
                    await ws.close()
                    break
                else:
                    print('receive ', msg.data)
            elif msg.type == aiohttp.WSMsgType.BINARY:
                print(msg.data)
                data = json.loads(msg.data)
                callback(subscribe_type, data)
            elif msg.type == aiohttp.WSMsgType.CLOSE:
                break
            elif msg.type == aiohttp.WSMsgType.ERROR:
                break
