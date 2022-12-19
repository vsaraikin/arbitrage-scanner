import pandas as pd
from tools import write_data
import json

tickers_exchanges = json.load(open('ticker_engineering\\tickers_exchanges.json'))

all_tickers = set()
for unique_tickers in tickers_exchanges.values():
    for unique in set(unique_tickers):
        all_tickers.add(unique)
    
print("There are", len(all_tickers), "unique tickers")

tickers = {t:[] for t in all_tickers}

for unique in all_tickers:
    for ex in tickers_exchanges:
        if unique in tickers_exchanges[ex]:
            tickers[unique].append(ex)

# write_data(tickers, 'exchanges_tickers.json')

write_data({k:tickers[k] for k in tickers if len(tickers[k]) > 10}, 'ticker_engineering\\exchanges_tickers.json')



