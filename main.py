import asyncio
import ccxt.pro
from termcolor import cprint
import random
from ticker_engineering.tools import timeit, generate_proxies
from ticker_engineering.create_configs import ticker_ex_configs

orderbooks = {}

@timeit
def handle_all_orderbooks(orderbooks):
    
    # print('We have the following orderbooks:')
    market_data_tmp_ask = {symbol:{ex:float('inf') for ex in tickers_ex[symbol]} for symbol in tickers_ex}
    market_data_tmp_bid = {symbol:{ex:float('-inf') for ex in tickers_ex[symbol]} for symbol in tickers_ex}

    # print("Current connections:", len(orderbooks), "Expercted number:", len(exchanges))
        
    for exchange_id, orderbooks_by_symbol in orderbooks.items():
        for symbol in orderbooks_by_symbol.keys():
            orderbook = orderbooks_by_symbol[symbol]
            market_data_tmp_bid[symbol][exchange_id] = orderbook['bids'][0][0]
            market_data_tmp_ask[symbol][exchange_id] = orderbook['asks'][0][0]
            # print(ccxt.pro.Exchange.iso8601(orderbook['timestamp']), exchange_id, symbol, orderbook['bids'][0][0], orderbook['asks'][0][0],)
    
    for symbol in tickers_ex:
        min_key = min(market_data_tmp_ask[symbol], key=market_data_tmp_ask[symbol].get)
        max_key = max(market_data_tmp_bid[symbol], key=market_data_tmp_bid[symbol].get)
        
        difference = market_data_tmp_bid[symbol][max_key] - market_data_tmp_ask[symbol][min_key]
        differrence_pct = difference/market_data_tmp_ask[symbol][min_key]
        
        if differrence_pct > threshold:
            
            cprint(f"{symbol}: BID {market_data_tmp_bid[symbol][max_key]} on {max_key} | ASK {market_data_tmp_ask[symbol][min_key]} on {min_key}", 'blue')
            cprint(f"DIFF on {symbol}: {round(difference, 5)} or {round(differrence_pct * 100, 3)}%", "green")


async def symbol_loop(exchange, symbol):
    while True:
        try:
            orderbook = await exchange.watchOrderBook(symbol)
            orderbooks[exchange.id] = orderbooks.get(exchange.id, {})
            orderbooks[exchange.id][symbol] = orderbook
            # print('===========================================================', id_func)
            
            handle_all_orderbooks(orderbooks)
        except Exception as e:
            print(str(e))
            exit()
            # raise e
   
proxy_http, proxy_https = generate_proxies()
print('Got proxy:', proxy_http, proxy_https)

async def spot_check(exchange, symbols):
    markets = await exchange.load_markets()
    print(markets['BTC/USDT']['type'])
    # for symbol in symbols:
    #     if res != 'spot':
    #         print(symbol, exchange, 'is not spot but:', res)
            # symbols.remove(symbol)
    return symbols
   
async def exchange_loop(exchange_id, symbols):
    
    exchange = getattr(ccxt.pro, exchange_id)(
        # {
        # 'http': proxy_http,
        # 'https': proxy_https,
        # 'aiohttp_proxy': proxy_http,
        # 'enableRateLimit': True
        # }
    )
    symbols = await spot_check(exchange, symbols)
    
    loops = [symbol_loop(exchange, symbol) for symbol in symbols]
    await asyncio.gather(*loops)
    await exchange.close()


async def exec_scanner(exchanges: dict):
    print("Total future connections:", len(exchanges.keys()))
    loops = [exchange_loop(exchange_id, symbols) for exchange_id, symbols in exchanges.items()]
    await asyncio.gather(*loops)


threshold = 1/1000
ex_tickers, tickers_ex = ticker_ex_configs({"BTC/AED", "BTC/AUD", "BTC/BIDR", "BTC/BKRW", "BTC/BRL", "BTC/BRL20", "BTC/BUSD", "BTC/BYN", 
                                            "BTC/BYN:BYN", "BTC/CAD", "BTC/CHF", "BTC/CNHT", "BTC/DAI", "BTC/EOSDT", "BTC/EUR", "BTC/EUR:EUR", 
                                            "BTC/EURB", "BTC/EUROC", "BTC/EURS", "BTC/EURST", "BTC/EURT", "BTC/EURT:EURT", "BTC/GBP", "BTC/GBPB", 
                                            "BTC/GUSD", "BTC/IDRT", "BTC/INR", "BTC/JPY", "BTC/KRW", "BTC/KZT", "BTC/MIM", "BTC/MXNT", "BTC/NGN", 
                                            "BTC/PAX", "BTC/PLN", "BTC/RUB", "BTC/RUB20", "BTC/SGD", "BTC/TRY", "BTC/TRY20", "BTC/TRYB", "BTC/TUSD",
                                            "BTC/TWD", "BTC/UAH", "BTC/USD", "BTC/USD:USD", "BTC/USD:USD-221230", "BTC/USD:USD-230127", "BTC/USD:USD-230224", 
                                            "BTC/USD:USD-230331", "BTC/USDB", "BTC/USDC", "BTC/USDD", "BTC/USDP", "BTC/USDS", "BTC/USDT", "BTC/USDT:USDT", 
                                            "BTC/USDX", "BTC/USDZ", "BTC/UST", "BTC/VAI", "BTC/XAUT", "BTC/ZAR"})
asyncio.run(exec_scanner(ex_tickers))
