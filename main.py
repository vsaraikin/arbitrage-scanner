import asyncio
import ccxt.pro
from termcolor import cprint
import random
from ticker_engineering.tools import timeit, generate_proxies, read_data
from ticker_engineering.create_configs import ticker_ex_configs

orderbooks = {}

# @timeit
def handle_all_orderbooks(orderbooks):
    
    # print('We have the following orderbooks:')
    market_data_tmp_ask = {symbol:{ex:float('inf') for ex in tickers_ex[symbol]} for symbol in tickers_ex}
    market_data_tmp_bid = {symbol:{ex:float('-inf') for ex in tickers_ex[symbol]} for symbol in tickers_ex}
    # liquidity
    # print("Current connections:", len(orderbooks), "Expercted number:", len(exchanges))
    
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
            
            
            cprint(f"{symbol}: BID {market_data_tmp_bid[symbol][max_key]} on {max_key} | ASK {market_data_tmp_ask[symbol][min_key]} on {min_key}", 'blue')
            cprint(f"DIFF on {symbol}: {round(difference, 5)} or {round(differrence_pct * 100, 3)}%", "green")


async def symbol_loop(exchange, symbol):
    while True:
        try:
            ticker = await exchange.watch_ticker(symbol)
            if ticker.get('baseVolume') and ticker.get('quoteVolume'): # ticker.get('bidVolume') and ticker.get('askVolume') and 
                orderbook = await exchange.watchOrderBook(symbol)
                orderbooks[exchange.id] = orderbooks.get(exchange.id, {})
                orderbooks[exchange.id][symbol] = orderbook
                handle_all_orderbooks(orderbooks)
            else:
                print(f"{symbol} on {exchange} is not liquid")    
            
        except ccxt.RequestTimeout as e:
            # recoverable error, do nothing and retry later
            print(type(e).__name__, str(e))
        except ccxt.DDoSProtection as e:
            # recoverable error, you might want to sleep a bit here and retry later
            print(type(e).__name__, str(e))
        except ccxt.ExchangeNotAvailable as e:
            # recoverable error, do nothing and retry later
            print(type(e).__name__, str(e))
        except ccxt.NetworkError as e:
            # do nothing and retry later...
            print(type(e).__name__, str(e))
        except Exception as e:
            # panic and halt the execution in case of any other error
            print(type(e).__name__, str(e))
            exit()
   
# proxy_http, proxy_https = generate_proxies()
# print('Got proxy:', proxy_http, proxy_https)

async def spot_check(exchange, symbols):
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
   
async def exchange_loop(exchange_id, symbols):
    
    exchange = getattr(ccxt.pro, exchange_id)(
        {
        # 'http': proxy_http,
        # 'https': proxy_https,
        # 'aiohttp_proxy': proxy_http,
        'enableRateLimit': True
        }
    )
    # exchange.verbose = True
    
    symbols = await spot_check(exchange, symbols)
    
    if len(symbols) > 0:
        loops = [symbol_loop(exchange, symbol) for symbol in symbols]
        await asyncio.gather(*loops)
        await exchange.close()
    else:
        # print("No tickers on", exchange)
        await exchange.close()


async def exec_scanner(exchanges: dict):
    print("Total future connections:", len(exchanges.keys()))
    loops = [exchange_loop(exchange_id, symbols) for exchange_id, symbols in exchanges.items()]
    await asyncio.gather(*loops)

threshold = 1/100
data = read_data('ticker_engineering/tickers_exchanges.json')
ticker_set = set(data['binance'])

ex_tickers, tickers_ex = ticker_ex_configs(ticker_set)
asyncio.run(exec_scanner(ex_tickers))
