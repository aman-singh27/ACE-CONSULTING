"""
Structured logging helper.
"""

import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger with the application-wide format."""
    return logging.getLogger(name)
