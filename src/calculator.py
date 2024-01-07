class ArbitrageStorage:
    ...


class Engine:

    def __init__(self):
        self.significance_level = 0.001

    def calculate(self, orderbooks: dict):
        prices_by_symbol = {}

        for exchange_id, orderbooks_by_symbol in orderbooks.items():
            for symbol, orderbook in orderbooks_by_symbol.items():
                if symbol not in prices_by_symbol:
                    prices_by_symbol[symbol] = {
                        'lowest_ask': float('inf'),
                        'lowest_ask_exchange': None,
                        'highest_bid': 0,
                        'highest_bid_exchange': None
                    }

                if orderbook['asks']:
                    lowest_ask = orderbook['asks'][0][0]
                    if lowest_ask < prices_by_symbol[symbol]['lowest_ask']:
                        prices_by_symbol[symbol]['lowest_ask'] = lowest_ask
                        prices_by_symbol[symbol]['lowest_ask_exchange'] = exchange_id

                if orderbook['bids']:
                    highest_bid = orderbook['bids'][0][0]
                    if highest_bid > prices_by_symbol[symbol]['highest_bid']:
                        prices_by_symbol[symbol]['highest_bid'] = highest_bid
                        prices_by_symbol[symbol]['highest_bid_exchange'] = exchange_id

        for symbol, prices in prices_by_symbol.items():
            value = round(prices['highest_bid'] / prices['lowest_ask'], 3)
            print(value - 1, self.significance_level)
            if value - 1 > self.significance_level:
                print(f"{symbol} - Spread {value * 100} | Lowest Ask: {prices['lowest_ask']} (Exchange: {prices['lowest_ask_exchange']}), Highest Bid: {prices['highest_bid']} (Exchange: {prices['highest_bid_exchange']})")

