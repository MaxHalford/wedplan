"""Logging configuration for the application."""

import logging
import sys
from typing import TextIO

from wedplan.core.config import get_settings


def configure_logging(stream: TextIO = sys.stdout) -> None:
    """Configure application logging.

    Args:
        stream: Output stream for log messages.
    """
    settings = get_settings()

    logging.basicConfig(
        level=getattr(logging, settings.log_level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=stream,
    )


def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name.

    Args:
        name: Logger name (typically __name__).

    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)
