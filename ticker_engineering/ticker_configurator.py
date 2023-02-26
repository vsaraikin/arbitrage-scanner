from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Tuple

import ccxt.pro

from ticker_engineering.tools import write_data, read_data


tickers_exchanges = {}

PATH_EXCHANGES_CONFIGS = 'ticker_engineering/configs.json'
PATH_TICKERS_EXCHANGES_STORAGE = 'ticker_engineering/all_tickers_exchanges.json'


@dataclass
class CreateStorage:
    """Class for creating storage for all selected exchanges and symbols related to them"""
    exchanges_selected: list[str] = field(default_factory = lambda: read_data(PATH_EXCHANGES_CONFIGS)['exchanges_selected'])
    
    
    @staticmethod
    def fetch_tickers(id):
        try:
            # check if the exchange is supported by ccxt
            exchange_found = id in ccxt.exchanges

            if exchange_found:

                print('Instantiating', id)

                tickers_exchanges[id] = []
                
                # instantiate the exchange by id
                exchange = getattr(ccxt, id)()

                if exchange.has['fetchTickers'] != True:
                    raise ccxt.NotSupported('Exchange ' + exchange.id + ' does not have the endpoint to fetch all tickers from the API.')

                # load all markets from the exchange
                # markets = await exchange.load_markets()

                try:

                    tickers = exchange.fetch_tickers()
                    for symbol, _ in tickers.items():
                        tickers_exchanges[id].append(symbol)

                except ccxt.DDoSProtection as e:
                    print(type(e).__name__, e.args, 'DDoS Protection (ignoring)')
                except ccxt.RequestTimeout as e:
                    print(type(e).__name__, e.args, 'Request Timeout (ignoring)')
                except ccxt.ExchangeNotAvailable as e:
                    print(type(e).__name__, e.args, 'Exchange Not Available due to downtime or maintenance (ignoring)')
                except ccxt.AuthenticationError as e:
                    print(type(e).__name__, e.args, 'Authentication Error (missing API keys, ignoring)')
            else:
                    print('Exchange', id, 'not found')

        except Exception as e:
            print(type(e).__name__, e.args, str(e))
            
            
    def _exec_fetching(self):
        n_threads = len(self.exchanges_selected)
        
        with ThreadPoolExecutor(n_threads) as executor:
            executor.map(self.fetch_tickers, self.exchanges_selected)
            
    
    def _write_configs(self):
        write_data(tickers_exchanges, PATH_TICKERS_EXCHANGES_STORAGE)
        
    
    def manage_configs(self):
        self._exec_fetching()
        self._write_configs()



class CreateConfigs(CreateStorage):
    """Create configuration for the scanner 'on-the-fly'"""
    def __init__(self, ticker_set: set[str]):    
        CreateStorage.__init__(self)
        self.storage = read_data(PATH_TICKERS_EXCHANGES_STORAGE)
        self.data = {k:self.storage[k] for k in self.storage if k in self.exchanges_selected}
        self.ticker_set = ticker_set
            
            
    @staticmethod
    def _ticker_ex_configs(data: dict, tickers_set: set) -> Tuple[dict, dict, set]:
        all_connections: int = 0
        avaliable_tickers: set = set()
        matched_exs_tickers: dict = {}
        matched_tickers_exs = {ticker:[] for ticker in tickers_set}

        for ex in data:
            for ticker in data[ex]:
                avaliable_tickers.add(ticker)
                
        for ticker in tickers_set:
            if ticker not in avaliable_tickers:
                print(f'Tickers {ticker} not found on exchanges -> skip that')
                
            
        # Find exchanges where this tickers avaliable
        for ex in data:
            for ticker in tickers_set:
                if ticker in data[ex]:
                    matched_tickers_exs[ticker].append(ex)
        
        for ticker in list(matched_tickers_exs):
            if len(matched_tickers_exs[ticker]) < 2: # impossible to arbitrage it
                matched_tickers_exs.pop(ticker)      # because we need at least 2 exchanges to trade
                tickers_set.remove(ticker)

        # Switch ex to ticker
        for ticker in tickers_set:
            for ex in matched_tickers_exs[ticker]:
                if not matched_exs_tickers.get(ex):
                    matched_exs_tickers[ex] = [ticker]
                    all_connections += 1
                else:
                    matched_exs_tickers[ex].append(ticker)
                    all_connections += 1
                    
        return matched_exs_tickers, matched_tickers_exs, all_connections
    
    
    def manage_configs(self):
        return self._ticker_ex_configs(self.data, self.ticker_set)


if __name__ == '__main__':
    cs = CreateStorage()
    cs.manage_configs()
    
