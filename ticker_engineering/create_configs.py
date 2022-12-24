from ticker_engineering.tools import read_data

data = read_data('ticker_engineering/tickers_exchanges.json')


def ticker_ex_configs(tickers_set: set) -> dict:
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
            else:
                matched_exs_tickers[ex].append(ticker)
                
    return matched_exs_tickers, matched_tickers_exs
