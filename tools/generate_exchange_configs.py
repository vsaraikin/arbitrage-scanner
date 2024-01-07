import asyncio
import logging
import ccxt
import ccxt.pro as ccxt_ws
import tqdm.asyncio

from common.utils import write_data


exchanges_symbols = {}

logger = logging.getLogger(__name__)


ALLOWED_SUBSCRIPTIONS_AT_ONCE = 20
semaphore = asyncio.Semaphore(ALLOWED_SUBSCRIPTIONS_AT_ONCE)


def save_markets(data):
    write_data(data, "bitmart_4.json")  # todo: config/....


async def check_market_eligibility(market, exchange) -> str | None:
    # Market should be spot and have enough liquidity there
    async with semaphore:  # Acquire a token from the semaphore
        symbol = market.get('symbol')

        if not symbol:
            print("No symbol found!")
            return

        if market.get('type') == 'spot' and market.get('spot') and market.get('active'):
            ticker_data = await exchange.watch_ticker(symbol=symbol)
            if ticker_data.get('baseVolume') > 0:
                return symbol
            else:
                print(f'Market {symbol} is not liquid')
        else:
            print(f'Market {symbol} is not a spot')


async def get_info(exchange):
    try:
        present = exchange in ccxt.exchanges
        if present:
            print('Instantiating', exchange)
            exchange_ws = getattr(ccxt_ws, exchange)()

            markets = await exchange_ws.load_markets()
            tasks = []
            for market in list(markets.keys())[260:350]:
                task = check_market_eligibility(markets[market], exchange_ws)
                tasks.append(task)

            # Exclude some symbols
            eligible_markets = [result for result in await tqdm.asyncio.tqdm.gather(*tasks) if result is not None]
            exchanges_symbols[exchange] = eligible_markets
            await exchange_ws.close()
        else:
            print('Exchange', exchange, 'not found')

    except Exception as e:
        print(type(e).__name__, e.args, str(e))


async def main():
    """
    Fetches exchange symbols and checks liquidity, instrument type for particular symbol.
    Creates markets.json file `exchange: symbols[str]` with suitable markets.
    :return:
    """
    exchanges = ["bitmart"]
    loops = [get_info(exchange) for exchange in exchanges]
    await tqdm.asyncio.tqdm.gather(*loops)


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
    save_markets(exchanges_symbols)
