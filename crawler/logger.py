from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from config import LOG_FOLDER


def get_logger(name: str = "udc") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    for filename in ("crawler.log", "download.log", "errors.log"):
        handler = RotatingFileHandler(LOG_FOLDER / filename, maxBytes=5_000_000, backupCount=3, encoding="utf-8")
        handler.setFormatter(formatter)
        handler.setLevel(logging.ERROR if filename == "errors.log" else logging.INFO)
        logger.addHandler(handler)
    logger.addHandler(logging.StreamHandler())
    return logger
