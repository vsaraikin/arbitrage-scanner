import logging
import time

from src.const import PATH_TO_LOGS


def setup_logging():
    logging.basicConfig(filename=f'{PATH_TO_LOGS}/messages_{int(time.time())}.log',
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.INFO)
