# utils/logger.py
import logging
from logging.handlers import TimedRotatingFileHandler

def setup_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            TimedRotatingFileHandler(log_file, when="midnight", backupCount=7, encoding="utf-8"),
            logging.StreamHandler()
        ]
    )
    logging.getLogger("aiogram").setLevel(logging.WARNING)
