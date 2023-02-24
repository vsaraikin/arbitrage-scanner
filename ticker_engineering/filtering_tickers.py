import asyncio
import logging
import random
import time
from typing import Union

from tools import timeit, read_data, write_data
from ticker_configurator import CreateConfigs

from tqdm import tqdm
import ccxt.pro


FILTERED_CONFIGS = 'ticker_engineering/filtered_tickers_exchanges.json'

class NoResponseFromExchange(Exception):
    """Raise exception if exchange did not respond"""
    def __init__(self, message="No response from exchange: ") -> None:
        super().__init__(message)


async def spot_check(exchange: ccxt.pro.Exchange, symbol: str, markets: dict) -> Union[str, None]:
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
    try:
        with timeout(5, exception=NoResponseFromExchange): # need to implement that
            new_symbols = await prepare_symbols(exchange, symbols)
            await exchange.close()
            return {exchange_id: new_symbols}
    except NoResponseFromExchange:
        await exchange.close()
        return

async def run_filtering(exchanges: dict):
    print("Total future exchanges:", len(exchanges.keys()))
    loops = [exchange_loop(exchange_id, symbols) for exchange_id, symbols in exchanges.items()]
    new_pairs = await tqdm.asyncio.tqdm.gather(*loops)
    
    # while new_pairs
    
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


top_tickers = {
    'SOL/USDT', 'CRO/USDT'
}


# from interruptingcow import timeout

for ticker in tqdm(top_tickers):
    ex_tickers, tickers_ex, _ = CreateConfigs({ticker}).manage_configs()
    
asyncio.run(write_filtered_symbols(ex_tickers))
