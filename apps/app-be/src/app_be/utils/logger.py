"""Shared logging configuration."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

LOG_DIR = Path(__file__).resolve().parent.parent / "logs"


def setup_logging(level: int = logging.INFO) -> None:
    """Configure root logging with a rotating file handler and console output."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[
            RotatingFileHandler(
                LOG_DIR / "app.log", maxBytes=5 * 1024 * 1024, backupCount=3
            ),
            logging.StreamHandler(),
        ],
    )


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
