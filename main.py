import asyncio

from src.scanner.scanner import Scanner
from src.utils.decorators import read_configs

from src.utils.logger.logger import setup_logging
from src.markets.exchange_configs_generator import GenerateExchangeConfig

setup_logging()


async def main():
    loop = asyncio.get_event_loop()
    cfg = GenerateExchangeConfig.get_mutual_markets(read_configs(),
                                                    max_limit=2,
                                                    min_limit=3,
                                                    )
    s = Scanner(loop)
    try:
        await s.run(cfg)
    except KeyboardInterrupt:
        print("Interrupt received, stopping...")
    finally:
        await s.stop()
        print("Shutdown complete.")

if __name__ == "__main__":
    asyncio.run(main())
