from common.utils import read_data

data = read_data("markets.json")


def mutual_markets(markets: dict, min_limit: int = 0, max_limit: int = 0):
    symbols = {}  # symbol: [exchanges]
    for ex in markets.keys():
        for symbol in markets[ex]:
            if not symbols.get(symbol):
                symbols[symbol] = [ex]
            else:
                symbols[symbol].append(ex)

    if min_limit or max_limit:
        for symbol, exchanges in symbols.copy().items():
            if not max_limit < len(exchanges) <= min_limit:
                del symbols[symbol]

    markets = {}
    for symbol, exchanges in symbols.items():
        for ex in exchanges:
            if not markets.get(ex):
                markets[ex] = [symbol]
            else:
                markets[ex].append(symbol)

    return markets


if __name__ == "__main__":
    suitable_markets = mutual_markets(data, min_limit=4, max_limit=3)  # for testing purposes
