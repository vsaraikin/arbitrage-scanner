import asyncio

from src.scanner import Scanner
from src.tools import read_data


async def main():
    cfg = read_data("config/routes.json")
    s = Scanner()
    try:
        await s.run(cfg)
    except KeyboardInterrupt:
        await s.stop()
    finally:
        print("Shutdown complete.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Program terminated by user")
