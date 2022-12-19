from ticker_engineering.tools import read_data
from scanner import exec_scanner
import asyncio

tickers_exchanges = read_data('ticker_engineering\exchanges_tickers.json')

tickers = ['LTC/BTC']
ex_list = tickers_exchanges['LTC/BTC']

asyncio.run(exec_scanner(tickers, ex_list))