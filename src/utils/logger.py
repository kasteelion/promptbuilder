# -*- coding: utf-8 -*-
"""Logging configuration for the application."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "promptbuilder", log_file: Optional[str] = None, level: int = logging.INFO
) -> logging.Logger:
    """Set up a logger with console and optional file output.

    Args:
        name: Logger name
        log_file: Optional log file path. If None, logs only to console
        level: Logging level (default: INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid adding duplicate handlers
    if logger.handlers:
        return logger

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_path, encoding="utf-8")
            file_handler.setLevel(logging.DEBUG)  # File gets more detail
            file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not set up file logging: {e}")

    return logger


# Create a default logger instance
logger = setup_logger()
