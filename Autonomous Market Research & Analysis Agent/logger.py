import logging
import os
from config import LOG_FILE

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

logger = logging.getLogger("market_research_agent")
logger.setLevel(logging.INFO)

if not logger.handlers:
    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
