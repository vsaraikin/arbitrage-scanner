import asyncio
import logging
import time

import ccxt.pro

from src.calculator import Engine

logging.basicConfig(filename=f'messages_{time.time()}.log',
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Scanner:
    def __init__(self):
        self.symbols = []
        self.exchanges = []
        self.orderbooks = {}
        self.engine = Engine()
        self.is_running = True

    async def symbol_loop(self, exchange, symbol):
        while self.is_running:
            try:
                orderbook = await exchange.watch_order_book(symbol)
                self.orderbooks[exchange.id] = self.orderbooks.get(exchange.id, {})
                self.orderbooks[exchange.id][symbol] = orderbook
                print('===========================================================')

                self.engine.calculate(self.orderbooks)
            except asyncio.CancelledError:
                # Gracefully handle cancellation
                print(f"Task cancelled for {symbol} on {exchange.id}")
                break
            except ccxt.RequestTimeout as e:
                # recoverable error, do nothing and retry later
                logger.critical(f"{type(e).__name__} {str(e)} on {exchange}")
            except ccxt.DDoSProtection as e:
                # recoverable error, you sleep a bit and retry later
                logger.critical(f"{type(e).__name__} {str(e)} on {exchange}")
                await asyncio.sleep(0.000001)
            except ccxt.ExchangeNotAvailable as e:
                # recoverable error, do nothing and retry later
                logger.critical(f"{type(e).__name__} {str(e)} on {exchange}")
            except ccxt.NetworkError as e:
                # do nothing and retry later...
                logger.critical(f"{type(e).__name__} {str(e)} on {exchange}")
            except Exception as e:
                # panic and halt the execution in case of any other error
                logger.critical(f"{type(e).__name__} {str(e)} on {exchange}")
                break

    async def exchange_init(self, exchange_id, symbols):
        exchange = getattr(ccxt.pro, exchange_id)()
        loops = [self.symbol_loop(exchange, symbol) for symbol in symbols]
        await asyncio.gather(*loops)
        await exchange.close()

    async def run(self, exchanges_symbols: dict[str, list[str]]):
        loops = [self.exchange_init(exchange_id, symbols) for exchange_id, symbols in exchanges_symbols.items()]
        await asyncio.gather(*loops)

    async def stop(self):
        self.is_running = False
        # Close each exchange instance
        for exchange in self.exchanges:
            await exchange.close()
        # Optionally, you can wait for all tasks to complete
        pending = asyncio.all_tasks()
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
