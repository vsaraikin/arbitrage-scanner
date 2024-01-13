import asyncio
import json
import logging
import os
import time

import ccxt
import ccxt.pro as ccxt_ws
import tqdm.asyncio

from common.utils import write_data, read_data

exchanges_symbols: dict = {}

logger = logging.getLogger(__name__)

ALLOWED_SUBSCRIPTIONS_AT_ONCE = 20
semaphore = asyncio.Semaphore(ALLOWED_SUBSCRIPTIONS_AT_ONCE)
CHUNK_SIZE = 50


def save_markets(data: dict):
    write_data(data, "data.json")  # todo: config/....


async def check_market_eligibility(market: dict, exchange: ccxt.pro.Exchange) -> str | None:
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


async def get_info(exchange: str):
    try:
        present = exchange in ccxt.exchanges
        if present:
            print('Instantiating', exchange)
            exchange_ws = getattr(ccxt_ws, exchange)()

            markets = await exchange_ws.load_markets()
            await exchange_ws.close()
            del exchange_ws

            for i in range(0, len(markets.keys()), CHUNK_SIZE):

                await asyncio.sleep(3)
                markets_slice = list(markets.keys())[i:i + CHUNK_SIZE]
                exchange_ws = getattr(ccxt_ws, exchange)()

                tasks = [check_market_eligibility(markets[market], exchange_ws) for market in markets_slice]

                # Exclude some symbols
                eligible_markets = [result for result in await tqdm.asyncio.tqdm.gather(*tasks) if result is not None]
                if not exchanges_symbols.get(exchange):
                    exchanges_symbols[exchange] = eligible_markets
                else:
                    exchanges_symbols[exchange].extend(eligible_markets)
                await exchange_ws.close()
                del exchange_ws

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
    exchanges = [
    'ascendex',
    'bitfinex',
    'bitfinex2',
    'bitget',
    'bitmex',
    'bitpanda',
    # 'bitrue',
    # 'bitstamp',
    # 'bitvavo',
    # 'blockchaincom',
    # 'bybit',
    # 'cex',
    # 'coinbase',
    # 'coinbasepro',
    # 'coinex',
    # 'cryptocom',
    # 'currencycom',
    # 'deribit',
    # 'exmo',
    # 'gate',
    # 'gateio',
    # 'gemini',
    # 'hitbtc',
    # 'hollaex',
    # 'htx',
    # 'huobi',
    # 'huobijp',
    # 'idex',
    # 'independentreserve',
    # 'kraken',
    # 'krakenfutures',
    # 'kucoin',
    # 'kucoinfutures',
    # 'luno',
    # 'mexc',
    # 'ndax',
    # 'okcoin',
    # 'okx',
    # 'phemex',
    # 'poloniex',
    # 'poloniexfutures',
    # 'probit',
    # 'upbit',
    # 'wazirx',
    # 'whitebit',
    # 'woo',
]

    loops = [get_info(exchange) for exchange in exchanges]
    await tqdm.asyncio.tqdm.gather(*loops)


if __name__ == '__main__':
    asyncio.run(main(), debug=True)
    save_markets(exchanges_symbols)
