import asyncio
import ccxt.pro
from termcolor import cprint
import random
from ticker_engineering.tools import timeit, generate_proxies, read_data
from ticker_engineering.create_configs import ticker_ex_configs
import logging
import time
import sys

logging.basicConfig(filename=f'messages_{time.time()}.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logger=logging.getLogger() 
logger.setLevel(logging.INFO) 

orderbooks = {}

@timeit
def handle_all_orderbooks(orderbooks):
    """
    Calculate arbitrage opportunity as: `exchange[ticker] with the lowest ask -- exchange[ticker] with the highest bid`
    """
    market_data_tmp_ask = {symbol:{ex:float('inf') for ex in tickers_ex[symbol]} for symbol in tickers_ex}
    market_data_tmp_bid = {symbol:{ex:float('-inf') for ex in tickers_ex[symbol]} for symbol in tickers_ex}
        
    for exchange_id, orderbooks_by_symbol in orderbooks.items():
        for symbol in orderbooks_by_symbol.keys():
            orderbook = orderbooks_by_symbol[symbol]
            if orderbook['bids'] and orderbook['asks']:
                market_data_tmp_bid[symbol][exchange_id] = orderbook['bids'][0][0]
                market_data_tmp_ask[symbol][exchange_id] = orderbook['asks'][0][0]
                # tickers_ex.pop(symbol)
            # print(ccxt.pro.Exchange.iso8601(orderbook['timestamp']), exchange_id, symbol, orderbook['bids'][0][0], orderbook['asks'][0][0],)
    
    for symbol in tickers_ex.keys():
        min_key = min(market_data_tmp_ask[symbol], key=market_data_tmp_ask[symbol].get)
        max_key = max(market_data_tmp_bid[symbol], key=market_data_tmp_bid[symbol].get)

        difference = market_data_tmp_bid[symbol][max_key] - market_data_tmp_ask[symbol][min_key]
        differrence_pct = difference/market_data_tmp_ask[symbol][min_key]
        
        if differrence_pct > threshold:
            # Liquidity check          
            logger.info(f"{symbol}: BID {market_data_tmp_bid[symbol][max_key]} on {max_key} | ASK {market_data_tmp_ask[symbol][min_key]} on {min_key} // DIFF on {symbol}: {round(difference, 5)} or {round(differrence_pct * 100, 3)}%")


async def symbol_loop(exchange: ccxt.pro.Exchange, symbol: str, id: int):
    """
    Checking whether a desired `exchange[ticker]` is liquid and listening to ordebook
    """
    while True:
        # logger.info([exchange, symbol, id])
        try:
            ticker_data = await exchange.watch_ticker(symbol)
            if ticker_data.get('baseVolume'): # and ticker.get('quoteVolume'): # ticker.get('bidVolume') and ticker.get('askVolume') and 
                orderbook = await exchange.watchOrderBook(symbol)
                orderbooks[exchange.id] = orderbooks.get(exchange.id, {})
                orderbooks[exchange.id][symbol] = orderbook
                handle_all_orderbooks(orderbooks)
                
                if (exchange, symbol) not in count_connection:
                    count_connection.add((exchange, symbol))
                    print(f"{round( 100 * (len(count_connection)/all_connections), 2)}%")
                else:
                    asyncio.sleep(0.000000000001)
            else:
                logger.warning(f"{symbol} on {exchange} is not liquid -> exit market")
                break    
            
        except ccxt.RequestTimeout as e:
            logger.critical(f"{type(e).__name__} {str(e)} on {exchange}") # recoverable error, do nothing and retry later
        except ccxt.DDoSProtection as e:
            logger.critical(f"{type(e).__name__} {str(e)} on {exchange}") # recoverable error, you might want to sleep a bit here and retry later
            await asyncio.sleep(0.1)
        except ccxt.ExchangeNotAvailable as e:
            logger.critical(f"{type(e).__name__} {str(e)} on {exchange}") # recoverable error, do nothing and retry later
        except ccxt.NetworkError as e:
            logger.critical(f"{type(e).__name__} {str(e)} on {exchange}") # do nothing and retry later...
        except Exception as e:
            logger.critical(f"{type(e).__name__} {str(e)} on {exchange}") # panic and halt the execution in case of any other error
            break
   

async def spot_check(exchange: ccxt.pro.Exchange, symbols: list) -> list:
    """
    A function that ensures whether we are looking exactly for 'SPOT' market
    """
    markets = await exchange.load_markets()
    new_symbols = []
    for symbol in symbols:
        res = markets.get(symbol)

        if not res:
            continue
        
        if not res.get('type'):
            continue
        
        res = res.get('type')
        
        if res.lower() != 'spot':
            print(symbol, exchange, 'is not spot but:', res)
        else:
            new_symbols.append(symbol)
            
    return new_symbols
   
async def exchange_loop(exchange_id: ccxt.pro.Exchange, symbols: list):
    
    exchange = getattr(ccxt.pro, exchange_id)(
        {
        # 'http': proxy_http,
        # 'https': proxy_https,
        # 'aiohttp_proxy': proxy_http,
        # 'enableRateLimit': True
        }
    )
    
    symbols = await spot_check(exchange, symbols)
    
    if len(symbols) > 0:
        loops = [symbol_loop(exchange, symbol, random.randint(0, 10000)) for symbol in symbols]
        await asyncio.gather(*loops)
        await exchange.close()
    else:
        print("No tickers on", exchange)
        await exchange.close()


async def exec_scanner(exchanges: dict):
    print("Total future connections:", len(exchanges.keys()))
    loops = [exchange_loop(exchange_id, symbols) for exchange_id, symbols in exchanges.items()]
    await asyncio.gather(*loops)


# proxy_http, proxy_https = generate_proxies()
# print('Got proxy:', proxy_http, proxy_https)

threshold = 1/100
ticker_set = set(read_data('ticker_engineering/tickers_exchanges.json')['huobi'][:200])

count_connection = set()
ex_tickers, tickers_ex, all_connections = ticker_ex_configs(ticker_set)
asyncio.run(exec_scanner(ex_tickers))
