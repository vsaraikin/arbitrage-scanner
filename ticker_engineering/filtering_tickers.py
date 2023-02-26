import asyncio
import logging
import random
import time
from typing import Union
import logging
import logging.config

logging.config.fileConfig('logging.conf')
logger = logging.getLogger('default')


from tools import timeit, read_data, write_data, NoResponseFromExchange, timeout
from ticker_configurator import CreateConfigs

import tqdm, tqdm.asyncio
import ccxt.pro


FILTERED_CONFIGS_PATH = 'ticker_engineering/filtered_tickers_exchanges.json'


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


@timeout(1)
async def exchange_loop(exchange_id: ccxt.pro.Exchange, symbols: list) -> Union[dict, None]:
    exchange = getattr(ccxt.pro, exchange_id)()
    try:
        new_symbols = await prepare_symbols(exchange, symbols)
        await exchange.close()
        return {exchange_id: new_symbols}
    except (NoResponseFromExchange, ccxt.base.errors.RequestTimeout, asyncio.exceptions.TimeoutError, asyncio.exceptions.CancelledError):
        await exchange.close()
        logger.critical(f'Conncetion with {exchange_id} dropped')
        return


async def run_filtering(exchanges: dict) -> dict:
    print("Total future exchanges:", len(exchanges.keys()))
    loops = [exchange_loop(exchange_id, symbols) for exchange_id, symbols in exchanges.items()]
    new_pairs = await tqdm.asyncio.tqdm.gather(*loops)
    new_pairs = [x for x in new_pairs if x != None]
    
    if new_pairs:
        merged_pairs = {key:val for d in new_pairs for key,val in d.items()}
        return merged_pairs
    else:
        return


async def write_filtered_symbols(ex_tickers: dict) -> None:
    """ Save symbols which are filtered """
    
    merged_pairs = await run_filtering(ex_tickers)
    
    if merged_pairs:
    
        filtered_configs = read_data(FILTERED_CONFIGS_PATH)
        
        if not filtered_configs:
            write_data(merged_pairs, FILTERED_CONFIGS_PATH)
        else:
            for ex in merged_pairs.keys():
                if not filtered_configs.get(ex):
                    filtered_configs[ex] = merged_pairs[ex]
                else:
                    [filtered_configs[ex].append(symbol) for symbol in merged_pairs[ex]]
            write_data(filtered_configs, FILTERED_CONFIGS_PATH)

    else:
        logger.info(f'No pairs for {ex_tickers}')


top_tickers = {
    "STRM/USDT",
    "SUN/USDT",
    "SUPER/USDT",
    "SUSHI/BTC",
    "SUSHI/UAH",
    "SUSHI/USDT",
    "SXP/USDT",
    "TABOO/USDT",
    "TCG2/USDT",
}

def symbol_filter(symbols: set):

    for ticker in symbols:
        logger.info(f'Preparing for {ticker}')
        ex_tickers, tickers_ex, _ = CreateConfigs({ticker}).manage_configs()
        asyncio.run(write_filtered_symbols(ex_tickers))
