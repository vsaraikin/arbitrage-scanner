import asyncio
import logging
import signal

import ccxt.pro

from calculator import Engine

logger = logging.getLogger(__name__)


class Scanner:
    def __init__(self, loop):
        self.symbols = []
        self.exchanges = []
        self.orderbooks = {}
        self.engine = Engine()
        self.is_running = True
        self.loop = loop
        self.subscriptions = 0

    async def symbol_loop(self, exchange, symbol):
        while self.is_running:
            try:
                orderbook = await exchange.watch_order_book(symbol)
                self.orderbooks[exchange.id] = self.orderbooks.get(exchange.id, {})
                self.orderbooks[exchange.id][symbol] = orderbook
                print('===========================================================')

                self.engine.calculate(self.orderbooks)
                print(f"Currently there are: {self.subscriptions} subscriptions")
            except asyncio.CancelledError:
                # Gracefully handle cancellation
                logger.info(f"Task cancelled for {symbol} on {exchange.id}")
                task = asyncio.current_task()
                logger.info(task.cancel())
                self.subscriptions -= 1
                break
            except ccxt.RequestTimeout as e:
                # recoverable error, do nothing and retry later
                logger.critical(f"{type(e).__name__} {str(e)} on {exchange}")
            except ccxt.DDoSProtection as e:
                # recoverable error, you sleep a bit and retry later
                logger.critical(f"{type(e).__name__} {str(e)} on {exchange}")
                await asyncio.sleep(0.001)
            except ccxt.ExchangeNotAvailable as e:
                # recoverable error, do nothing and retry later
                logger.critical(f"{type(e).__name__} {str(e)} on {exchange}")
            except ccxt.NetworkError as e:
                # do nothing and retry later...
                logger.critical(f"{type(e).__name__} {str(e)} on {exchange}")
            except Exception as e:
                # panic and halt the execution in case of any other error
                logger.critical(f"{type(e).__name__} {str(e)} on {exchange}")
                self.subscriptions -= 1
                break

    async def exchange_init(self, exchange_id, symbols):
        exchange = getattr(ccxt.pro, exchange_id)()
        self.exchanges.append(exchange)
        self.subscriptions += len(symbols)
        loops = [self.symbol_loop(exchange, symbol) for symbol in symbols]
        await asyncio.gather(*loops)
        await exchange.close()

    async def stop(self):
        tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        for exchange in self.exchanges:
            logger.info("Closed exchange %s", exchange)
            await exchange.close()
        # self.loop.close()
        # self.loop.stop()

    async def _run(self, exchanges_symbols: dict[str, list[str]]):
        loops = [self.exchange_init(exchange_id, symbols) for exchange_id, symbols in exchanges_symbols.items()]
        await asyncio.gather(*loops)

    async def run(self, exchanges_symbols: dict[str, list[str]]):
        # TODO: RUN IN LOOP, add signals
        # signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
        # for sig in signals:
        #     self.loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self.shutdown(s, self.loop)))
        await self._run(exchanges_symbols)
