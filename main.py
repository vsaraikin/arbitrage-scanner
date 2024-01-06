import asyncio

from src.scanner import Scanner
from src.utils import read_data, read_configs

from src.logging_config import setup_logging

setup_logging()


async def main():
    loop = asyncio.get_event_loop()
    cfg = read_configs()
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
