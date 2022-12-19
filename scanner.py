import asyncio
import ccxt.pro
from termcolor import cprint
# from configs import exchanges_list, symbols
import random
from ticker_engineering.tools import write_data, timeit, get_proxy

orderbooks = {}



# @timeit
def handle_all_orderbooks(orderbooks, symbols, exchanges):
    
    print('We have the following orderbooks:')
    market_data_tmp_bid = {ticker:{exchange:float('-inf') for exchange in exchanges.keys()} for ticker in symbols} # Store best bids from all exchanges 
    market_data_tmp_ask = {ticker:{exchange:float('inf') for exchange in exchanges.keys()} for ticker in symbols} # Store best asks from all exchanges 
    
    print("Current connections:", len(orderbooks))
    
    # if len(orderbooks) != len(exchanges_list):
    #     exit()
    
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


async def symbol_loop(exchange, symbol, symbols, exchanges, id_func):
    while True:
        try:
            orderbook = await exchange.watch_order_book(symbol)
            orderbooks[exchange.id] = orderbooks.get(exchange.id, {})
            orderbooks[exchange.id][symbol] = orderbook
            print('===========================================================', id_func)
            
            handle_all_orderbooks(orderbooks, symbols, exchanges)
            # await exchange.close()
        except Exception as e:
            # await exchange.close()
            print(str(e))
            break
            # raise e
   
# proxy_http = get_proxy(ssl=False)   
# proxy_https = get_proxy(ssl=True)
# print('Got proxy:', proxy_http, proxy_https)
        
async def exchange_loop(exchange_id, symbols, exchanges):
    
    exchange = getattr(ccxt.pro, exchange_id)(
        # {'http': proxy_http, 'https': proxy_https, 'aiohttp_proxy': proxy_http}
    )
    # exchange.headers = {'Connection': 'close'}

    loops = [symbol_loop(exchange, symbol, symbols, exchanges, random.randint(0, 100)) for symbol in symbols]
    await asyncio.gather(*loops)
    await exchange.close()


async def exec_scanner(symbols, exchanges_list):
    exchanges = {ex:symbols for ex in exchanges_list}
    print("Total future connections:", len(exchanges_list))
    
    loops = [exchange_loop(exchange_id, symbols, exchanges) for exchange_id, symbols in exchanges.items()]
    await asyncio.gather(*loops)

