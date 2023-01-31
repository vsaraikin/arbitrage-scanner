import asyncio
import ccxt.pro
from tools import timeit, read_data, write_data
from create_configs import ticker_ex_configs
import logging
import tqdm.asyncio
import random
import time


FILTERED_CONFIGS = 'ticker_engineering/filtered_tickers_exchanges.json'


async def spot_check(exchange: ccxt.pro.Exchange, symbol: str, markets: dict) -> str:
    """ Check whether a market is liquid """
    res = markets.get(symbol)

    if not res:
        return
    if not res.get('type'):
        return
    
    res = res.get('type')
    
    if res.lower() != 'spot':
        print(symbol, exchange, 'is not spot but:', res)
    else:
        # print(symbol, exchange)
        ticker_data = await exchange.watch_ticker(symbol)
        if ticker_data.get('baseVolume'): # and ticker.get('quoteVolume'): # ticker.get('bidVolume') and ticker.get('askVolume') and 
            return symbol   
        
        
async def prepare_symbols(exchange: ccxt.pro.Exchange, symbols: list) -> list:
    markets = await exchange.load_markets()
    coroutines =  [spot_check(exchange, symbol, markets) for symbol in symbols]
    new_symbols = await asyncio.gather(*coroutines)
    new_symbols = [x for x in new_symbols if x is not None]
    return new_symbols


async def exchange_loop(exchange_id: ccxt.pro.Exchange, symbols: list):
    exchange = getattr(ccxt.pro, exchange_id)()
    new_symbols = await prepare_symbols(exchange, symbols)
    await exchange.close()
    return {exchange_id: new_symbols}


async def run_filtering(exchanges: dict):
    # print("Total future exchanges:", len(exchanges.keys()))
    # print("Total future subscribtions:", all_connections)
    loops = [exchange_loop(exchange_id, symbols) for exchange_id, symbols in exchanges.items()]
    new_pairs = await tqdm.asyncio.tqdm.gather(*loops)
    merged_pairs = {key:val for d in new_pairs for key,val in d.items()}
    return merged_pairs


async def write_filtered_symbols(ex_tickers):
    """ Save symbols which are filtered """
    
    merged_pairs = await run_filtering(ex_tickers)
    filtered_configs = read_data(FILTERED_CONFIGS)
    if not filtered_configs:
        write_data(merged_pairs, FILTERED_CONFIGS)
    else:
        for ex in merged_pairs.keys():
            if not filtered_configs.get(ex):
               filtered_configs[ex] = merged_pairs[ex]
            else:
                [filtered_configs[ex].append(symbol) for symbol in merged_pairs[ex]]
        write_data(filtered_configs, FILTERED_CONFIGS)


top_tickers = read_data('ticker_engineering/all_tickers_exchanges.json')['binance']


import multiprocessing

if __name__ == '__main__':
    for _ in tqdm.tqdm(top_tickers):
        ticker = random.choice(top_tickers)
        ex_tickers, tickers_ex, all_connections = ticker_ex_configs({ticker})
            
        p = multiprocessing.Process(target=asyncio.run(write_filtered_symbols(ex_tickers)))
        p.start()
        p.join(10)
        
        if p.is_alive():
            print("running... let's kill it...")

            # Terminate - may not work if process is stuck for good
            p.terminate()
            # OR Kill - will work for sure, no chance for process to finish nicely however
            # p.kill()

            p.join()
        top_tickers.remove(ticker)