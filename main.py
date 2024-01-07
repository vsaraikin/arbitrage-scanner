import asyncio

from src.scanner import Scanner
from common.utils import read_configs

from src.logging_config import setup_logging
from tools.find_mutual_markets import mutual_markets

setup_logging()


async def main():
    loop = asyncio.get_event_loop()
    cfg = mutual_markets(read_configs(), min_limit=3, max_limit=2)
    cfg = {
        "okx": ["KCAL/USDT"],
        "huobi":  ["KCAL/USDT"]
    }
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
