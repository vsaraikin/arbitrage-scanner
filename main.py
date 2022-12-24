from ticker_engineering.tools import read_data
from scanner import exec_scanner
import asyncio
# from multiprocessing import Pool
import concurrent.futures
import time
import random

tickers_exchanges = read_data('ticker_engineering/exchanges_tickers.json')

tickers = list(tickers_exchanges.keys())[20:30]
ex_list = [tickers_exchanges[t] for t in tickers]

threshold = 1/1000

def run_search(pair):
    ticker, exchanges, threshold = pair
    # time.sleep(random.randint(1, 10))
    asyncio.run(exec_scanner(ticker, exchanges, threshold))

pairs = [([ti], ex, threshold) for ti, ex in zip(tickers, ex_list)]

if __name__ == '__main__':
    # with Pool(processes=len(tickers)) as pool:
    #     pool.starmap(run_search, pairs)
    
    with concurrent.futures.ThreadPoolExecutor(len(tickers)) as pool:
        futures = [pool.submit(run_search, pair) for pair in pairs]
        for f in futures:
            f.result()