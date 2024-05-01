import json
import logging
import os
import sys
import time


class JsonFormatter(logging.Formatter):
    def format(self, record):
        record.message = record.getMessage()
        if self.usesTime():
            record.asctime = self.formatTime(record, self.datefmt)

        log_record = {
            "time": record.asctime,
            "name": record.name,
            "level": record.levelname,
            "message": record.message
        }

        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)

        return json.dumps(log_record)


def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    json_formatter = JsonFormatter(datefmt='%Y-%m-%d %H:%M:%S')

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(json_formatter)

    # log_file_name = f'messages_{int(time.time())}.log'
    log_file_name = 'app.log'
    log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), log_file_name)
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(json_formatter)

    # Add the handlers to the logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
