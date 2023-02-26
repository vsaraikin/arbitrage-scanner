import logging
import time

import asyncio
import ccxt.pro

from ticker_engineering.tools import timeit, generate_proxies, read_data, timeout
from ticker_engineering.ticker_configurator import CreateConfigs


logging.basicConfig(filename=f'messages_{time.time()}.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logger=logging.getLogger() 
logger.setLevel(logging.INFO) 


@timeit
def handle_all_orderbooks(orderbooks):
    """
    Calculate arbitrage opportunity as: `exchange[ticker] with the lowest ask -- exchange[ticker] with the highest bid`
    """
    
    for exchange_id, orderbooks_by_symbol in orderbooks.items():
        for symbol in orderbooks_by_symbol.keys():
            orderbook = orderbooks_by_symbol[symbol]
            if orderbook['bids'] and orderbook['asks']:
                market_data_tmp_bid[symbol][exchange_id] = orderbook['bids'][0][0]
                market_data_tmp_ask[symbol][exchange_id] = orderbook['asks'][0][0]
                
    
    for symbol in tickers_ex.keys():
        min_key = min(market_data_tmp_ask[symbol], key=market_data_tmp_ask[symbol].get)
        max_key = max(market_data_tmp_bid[symbol], key=market_data_tmp_bid[symbol].get)

        difference = market_data_tmp_bid[symbol][max_key] - market_data_tmp_ask[symbol][min_key]
        differrence_pct = difference/market_data_tmp_ask[symbol][min_key]
        
        if differrence_pct > thresh_diff:
            logger.info(f"{symbol}: BID {market_data_tmp_bid[symbol][max_key]} on {max_key} | ASK {market_data_tmp_ask[symbol][min_key]} on {min_key} // DIFF on {symbol}: {round(difference, 5)} or {round(differrence_pct * 100, 3)}%")


async def symbol_loop(exchange: ccxt.pro.Exchange, symbol: str):
    """ Checking whether a desired `exchange[ticker]` is liquid and listening to ordebook """
    while True:
        try:          
            orderbook = await exchange.watchOrderBook(symbol)
            orderbooks[exchange.id] = orderbooks.get(exchange.id, {})
            orderbooks[exchange.id][symbol] = orderbook
            # handle_all_orderbooks(orderbooks)
                
            if (exchange, symbol) not in count_connection:
                count_connection.add((exchange, symbol))
                logger.info(f"Pairs [symbols - exhcnages] loaded {round( 100 * (len(count_connection)/all_connections), 2)}%")
                await asyncio.sleep(0.1)
            
        except ccxt.RequestTimeout as e:
            logger.critical(f"{type(e).__name__} {str(e)} on {exchange}") # recoverable error, do nothing and retry later
        except ccxt.DDoSProtection as e:
            logger.critical(f"{type(e).__name__} {str(e)} on {exchange}") # recoverable error, you might want to sleep a bit here and retry later
            await asyncio.sleep(0.000001)
        except ccxt.ExchangeNotAvailable as e:
            logger.critical(f"{type(e).__name__} {str(e)} on {exchange}") # recoverable error, do nothing and retry later
        except ccxt.NetworkError as e:
            logger.critical(f"{type(e).__name__} {str(e)} on {exchange}") # do nothing and retry later...
        except Exception as e:
            logger.critical(f"{type(e).__name__} {str(e)} on {exchange}") # panic and halt the execution in case of any other error
            break
   
@timeout(5)
async def exchange_init(exchange_id: ccxt.pro.Exchange, symbols: list):
    
    exchange = getattr(ccxt.pro, exchange_id)(
        {
        # 'http': 'http://' + proxy_http,
        # 'https': 'https://' + proxy_https,
        # 'aiohttp_proxy': 'http://' + proxy_http,
        'enableRateLimit': True,
        # 'verify': False,
        }
    )
    # exchange.session.verify= False        # Do not reject on SSL certificate checks
    logger.info(f'Initialized exchange object – {exchange_id}')
    
    if symbols:
        loops = [symbol_loop(exchange, symbol) for symbol in symbols]
        await asyncio.gather(*loops)
        await exchange.close()
    else:
        logger.info(f"No tickers on: {exchange}")
        await exchange.close()


async def exec_scanner(exchanges: dict):
    logger.info(f"Total future exchanges: {len(exchanges.keys())}")
    logger.info(f"Total future subscribtions: {all_connections}")
    loops = [exchange_init(exchange_id, symbols) for exchange_id, symbols in exchanges.items()]
    await asyncio.gather(*loops)


orderbooks = {}
thresh_diff = 1/100 # if best_ask - best_bid > thresh_diff -> add to db

count_connection = set()
ex_tickers, tickers_ex, all_connections = CreateConfigs({'BTC/USDT'}).manage_configs()

market_data_tmp_ask = {symbol:{ex:float('inf') for ex in tickers_ex[symbol]} for symbol in tickers_ex}
market_data_tmp_bid = {symbol:{ex:float('-inf') for ex in tickers_ex[symbol]} for symbol in tickers_ex}
asyncio.run(exec_scanner(ex_tickers))
