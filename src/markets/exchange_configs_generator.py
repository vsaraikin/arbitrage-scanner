import logging
from dataclasses import dataclass, field
import random

import asyncio

import ccxt.pro as ws_ccxt
import tqdm

from src.utils.logger.logger import setup_logging
from src.utils.decorators import write_data

logger = logging.getLogger(__name__)
setup_logging()

# Exchange configuration
EXCHANGES: list[str] = [
    # 'binance',
    # # 'binancecoinm' # futures,
    # 'binanceusdm',
    # 'bingx',
    # # 'bitcoincom', # broken gateway
    # 'bitfinex',
    # 'bitfinex2',
    # 'bitget',
    # # 'bithumb', # too long to wait
    # 'bitmart',
    # 'bitmex',
    # 'bitopro',
    # # 'bitrue', # websockets are not avaliable
    # # 'bitstamp', # websockets are not avaliable
    # 'bitvavo',
    # 'blockchaincom',
    # 'bybit',
    # 'cex', # apiKey
    # 'coinbase', # rate limit but it is working
    # 'coinbaseinternational', # apiKey
    'coinbasepro',
    # 'coinex',
    # 'coinone',
    # 'cryptocom',
    # 'currencycom',
    # # 'deribit', # derivatives only
    # 'exmo',
    # 'gate',
    # 'gateio', # just stopped
    # 'gemini', # websockets are not avaliable
    # 'htx',
    # 'huobi',
    # 'huobijp',
    # 'kraken',
    # 'krakenfutures', # only futures
    # 'kucoin',
    # 'kucoinfutures', # only futures
    # 'lbank',
    # 'mexc',  # giant lag for market data
    # 'ndax',
    # 'okcoin', # giant lag for market data
    # 'okx',
    # 'p2b',
    # 'phemex',
    # 'poloniex',
    # 'poloniexfutures', # only futures
    # 'probit',
    # 'upbit',
    # 'whitebit',
]

# TODO:
# some exchanges may have tokens been delisted,
# so we need to map all exchanges to BTC, because it is the most common
# BTC_MAP = {
#     k: 'BTC/USDT' for k in EXCHANGES
# }


# Custom errors
class DelistedCoin(Exception):
    """Some coins might be delisted from the exchange."""
    pass


# Configuration model
@dataclass
class ExchangeConfig:
    symbols: list[str] = field(default_factory=list)
    exchange: str = field(default_factory=str)

    def to_dict(self) -> dict[str, list[str]]:
        return {self.exchange: self.symbols}

    def add_symbols(self, symbols: list[str]) -> None:
        if self._is_empty():
            self.symbols = symbols
        else:
            self.symbols.extend(symbols)

    def _is_empty(self) -> bool:
        return self.symbols == []


class CCXTWSExchangeController:
    """Extend basic CCXT Exchange WS functionality"""

    def __init__(self, exchange_id: str):
        self.exchange: ws_ccxt.Exchange = getattr(ws_ccxt, exchange_id)()

    async def check_ws_connection(self, symbols: list[str]):
        """
        Check whether exchange supports websocket connection.
        Exchange may have coins delisted or any other issue may occur.
        :param symbols: list of symbols to check
        """
        symbol = random.choice(symbols)
        try:
            resp = await self.exchange.watch_ticker(symbol=symbol)
            logger.debug(f"For {self.exchange.id} successfully checked ws connection: {resp.keys()}")
            return True
        except DelistedCoin as e:
            logger.debug(f"For {self.exchange.id} coin {symbol} is delinted: {str(e)}")
            await self.check_ws_connection(symbols=symbols)
        except Exception as e:
            logger.debug(f"For {self.exchange.id} websocket is not supported, {str(e)}")
            return False

    async def check_market_liquidity(self, orderbook: dict) -> str | None:
        """Check whether market has liquidity"""
        async with semaphore:
            symbol = orderbook.get('symbol')

            if not symbol:
                logger.debug("No symbol found!")
                return

            if orderbook.get('type') == 'spot' and orderbook.get('spot') and \
                    (self.exchange.id in ('exmo', 'coinex', 'coinone') or orderbook.get('active')):
                ticker_data = await self.exchange.watch_ticker(symbol=symbol)
                if ticker_data.get('baseVolume') > 0:
                    return symbol
                else:
                    logger.debug(f'Market {symbol} is not liquid')
            else:
                logger.debug(f'Market {symbol} is not a spot')

    async def recreate_connection(self):
        """Recreate connection for the exchange."""
        await self.exchange.close()
        self.exchange = getattr(ws_ccxt, self.exchange.id)()
        logger.debug(f"Recreated connection for {self.exchange.id}")

    def get_exchange(self):
        return self.exchange


ALLOWED_SUBSCRIPTIONS_AT_ONCE = 20
semaphore = asyncio.Semaphore(ALLOWED_SUBSCRIPTIONS_AT_ONCE)
CHUNK_SIZE = 50


class GenerateExchangeConfig:
    def __init__(self, exchange: str):
        self.exchange_configs = ExchangeConfig(exchange=exchange)
        self.progress_bar = False
        self.retries = 0
        self.max_retries = 3
        self.controller = CCXTWSExchangeController(exchange)
        self.exchange = self.controller.get_exchange()

    @staticmethod
    def _save_config(data: ExchangeConfig, filename: str):
        write_data(data.to_dict(), f'{filename}.json')

    @staticmethod
    def get_mutual_markets(markets: dict, min_limit: int = 0, max_limit: int = 0) -> dict[str]:
        """
        Get mutual markets for exchanges to listen to.
        :param markets: dict of markets
        :param min_limit: minimum number of exchanges that symbol should have to listen to
        :param max_limit: maximum number of exchanges that symbol should have to listen to
        :return: dict of suitable markets
        """
        symbols = {}
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

    async def generate_config(self):
        """
        Generate exchange configs file e.g. {'exchange': ['BTC/USDT', 'ETH/USDT', ...]}
        """
        try:
            if self.exchange.id not in ws_ccxt.exchanges:
                logger.debug(f"{self.exchange} is not supported.")
                return

            # load available markets
            markets = await self.exchange.load_markets()
            if not markets:
                logger.debug(f"Empty markets for {self.exchange}")
                return

            if not await self.controller.check_ws_connection(symbols=list(markets.keys())):
                return

            for i in tqdm.trange(0, len(markets.keys()), CHUNK_SIZE):
                logger.debug(f"Batch {i} out of {len(markets.keys())} – {self.exchange.id}")
                markets_slice = list(markets.keys())[i:i + CHUNK_SIZE]
                liquid_markets = [
                    result for result in await asyncio.gather(*[
                        self.controller.check_market_liquidity(markets[market]) for market in markets_slice
                    ]) if result is not None]
                self.exchange_configs.add_symbols(liquid_markets)
                await self.controller.recreate_connection()

        except Exception as e:
            logger.critical(type(e).__name__, e.args, str(e))
        finally:
            await self.exchange.close()
            self._save_config(self.exchange_configs, self.exchange.id)


async def run():
    await asyncio.gather(*[
        GenerateExchangeConfig(exchange).generate_config() for exchange in EXCHANGES
    ])


if __name__ == '__main__':
    asyncio.run(run())
    # suitable_markets = mutual_markets(read_data("markets.json"), min_limit=4, max_limit=3)  # for testing purposes
