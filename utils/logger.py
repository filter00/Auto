import logging
import os

def get_logger(name=__name__):
    level = os.getenv("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        level=getattr(logging, level, logging.INFO),
    )
    return logging.getLogger(name)
