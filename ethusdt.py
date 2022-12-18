# -*- coding: utf-8 -*-
import asyncio
import ccxt.pro
# import pandas as pd
import json
from termcolor import cprint

orderbooks = {}
symbols = ['ETH/USDT']

exchanges_list = [
    # 'ascendex', # wtf 0?
    'bequant',
    'binance',
    # 'binancecoinm', # what is that?
    # 'binanceus', # api is broken on binanceus side
    'binanceusdm',
    'bitcoincom',
    'bitfinex2', # no time
    # 'bitget', # wtf 0?
    'bitmart',
    # # 'bitmex', # there is no btc/usdt
    'bitopro',
    # 'bitrue', # wtf 0?
    'bitstamp',
    # 'bittrex', # api is broken
    # 'bitvavo', # there is no btc/usdt
    # 'bybit', # there is no btc/usdt
    # 'cex', # requires api key
    'coinbaseprime',
    'coinbasepro',
    'coinex',
    'cryptocom',
    'currencycom',
    # # 'deribit', # there is no btc/usdt
    'exmo',
    'gate',
    'gateio',
    'hitbtc',
    # 'hollaex', # strange time
    'huobi',
    # 'huobijp', # there is no btc/usdt
    'huobipro',
    # 'idex', # there is no btc/usdt
    'kraken',
    'kucoin', # no time
    'mexc',
    'ndax', # does not work
    # 'okcoin', # there is no btc/usdt
    'phemex',
    # 'ripio', # there is no btc/usdt
    'upbit',
    'wazirx',
    'whitebit',
    # 'woo', # uid cred
    # 'zb', # strange exchange
    # 'zipmex', # api does not work
]

exchanges = {
    ex:symbols for ex in exchanges_list
}

print("Total future connections:", len(exchanges_list))

def handle_all_orderbooks(orderbooks):
    print('We have the following orderbooks:')
    market_data_tmp_bid = {ticker:{exchange:float('-inf') for exchange in exchanges.keys()} for ticker in symbols}
    market_data_tmp_ask = {ticker:{exchange:float('inf') for exchange in exchanges.keys()} for ticker in symbols}
    print("Current connections:", len(orderbooks))
    for exchange_id, orderbooks_by_symbol in orderbooks.items():
        for symbol in orderbooks_by_symbol.keys():
            orderbook = orderbooks_by_symbol[symbol]
            market_data_tmp_bid[symbol][exchange_id] = orderbook['bids'][0][0]
            market_data_tmp_ask[symbol][exchange_id] = orderbook['asks'][0][0]
            print(ccxt.pro.Exchange.iso8601(orderbook['timestamp']), exchange_id, symbol, orderbook['bids'][0][0], orderbook['asks'][0][0],)
    
    for symbol in symbols:
        min_key = min(market_data_tmp_ask[symbol], key=market_data_tmp_ask[symbol].get)
        max_key = max(market_data_tmp_bid[symbol], key=market_data_tmp_bid[symbol].get)
        
        cprint(f"{symbol}: BID {market_data_tmp_bid[symbol][max_key]} on {max_key} | ASK {market_data_tmp_ask[symbol][min_key]} on {min_key}", 'blue')
        cprint(f"DIFF on {symbol}: BID {market_data_tmp_ask[symbol][min_key] - market_data_tmp_bid[symbol][max_key]}", "green")



async def symbol_loop(exchange, symbol, i):
    while True:
        try:
            orderbook = await exchange.watch_order_book(symbol)
            orderbooks[exchange.id] = orderbooks.get(exchange.id, {})
            orderbooks[exchange.id][symbol] = orderbook
            print('===========================================================', i)
            #
            # here you can do what you want
            # with the most recent versions of each orderbook you have so far
            #
            # you can also wait until all of them are available
            # by just looking into all the orderbooks and counting them
            #
            # we just print them here to keep this example simple
            #
            handle_all_orderbooks(orderbooks)
        except Exception as e:
            print(str(e))
            # raise e  # uncomment to break all loops in case of an error in any one of them
            break  # you can break just this one loop if it fails
        
def write_data(difference_dict):
    with open('data.json', "w") as file:
        json.dump(difference_dict, file)
        
import random
async def exchange_loop(exchange_id, symbols):
    exchange = getattr(ccxt.pro, exchange_id)()
    loops = [symbol_loop(exchange, symbol, random.randint(0, 100)) for symbol in symbols]
    await asyncio.gather(*loops)
    await exchange.close()


async def main():
    loops = [exchange_loop(exchange_id, symbols) for exchange_id, symbols in exchanges.items()]
    await asyncio.gather(*loops)

asyncio.run(main())
# write_data(difference_dict)
