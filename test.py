from configs import exchanges_list
import ccxt 
from tools import write_data

tickers_exchanges = {}

try:

    for id in exchanges_list:
        # check if the exchange is supported by ccxt
        exchange_found = id in ccxt.exchanges

        if exchange_found:

            print('Instantiating', id)

            tickers_exchanges[id] = []
            
            # instantiate the exchange by id
            exchange = getattr(ccxt, id)()

            if exchange.has['fetchTickers'] != True:
                raise ccxt.NotSupported ('Exchange ' + exchange.id + ' does not have the endpoint to fetch all tickers from the API.')

            # load all markets from the exchange
            markets = exchange.load_markets()

            try:

                tickers = exchange.fetch_tickers()
                for symbol, ticker in tickers.items():
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


write_data(tickers_exchanges, 'tickers_exchanges.json')

