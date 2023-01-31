from tools import read_data

data = read_data('ticker_engineering/all_tickers_exchanges.json')

exchanges_selected = read_data('ticker_engineering/configs.json')['exchanges_selected']

data = {k:data[k] for k in data if k in exchanges_selected}
        

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
    
    for ticker in list(matched_tickers_exs):
        if len(matched_tickers_exs[ticker]) < 2: # impossible to arbitrage it
            matched_tickers_exs.pop(ticker)
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
