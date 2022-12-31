from ticker_engineering.tools import read_data

data = read_data('ticker_engineering/tickers_exchanges.json')

exchanges_selected = {
    'bequant', # dead
    # 'binance',
    # 'binancecoinm',
    # 'binanceus',
    # 'binanceusdm',
    # 'bitfinex2',
    # 'bitmex',
    'bitcoincom', # dead
    # 'bitstamp',
    # 'bittrex',
    # 'bybit',
    'coinbaseprime',
    'coinbasepro', # drops...
    # 'coinex',
    'cryptocom', # drops...
    # 'currencycom',
    # 'deribit',
    # 'gate', # too slow response
    'hitbtc', # drops
    # 'hollaex',
    'huobi', # drops...
    # 'huobijp',
    # 'huobipro',
    # 'kraken',
    # 'kucoin', # dead, slow responses
    # 'okcoin',
    'okex',
    'okx',
    'phemex',
    'upbit', # drops
    # 'whitebit',
}


data = {k:data[k] for k in data if k in exchanges_selected}
# for ex in data:
#     if ex not in exchanges_selected:
#         data.pop(ex)
        

def ticker_ex_configs(tickers_set: set) -> dict:
    all_connections = 0
    avaliable_tickers = set()
    matched_tickers_exs = {ticker:[] for ticker in tickers_set}
    matched_exs_tickers = {}

    for ex in data:
        for ticker in data[ex]:
            avaliable_tickers.add(ticker)
            
    for ticker in tickers_set:
        if ticker not in avaliable_tickers:
            print('Tickers not found on exchanges')
            exit()
        
    # Find exchanges where this tickers avaliable
    for ex in data:
        for ticker in tickers_set:
            if ticker in data[ex]:
                matched_tickers_exs[ticker].append(ex)

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
