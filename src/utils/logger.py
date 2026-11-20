# -*- coding: utf-8 -*-
"""Logging configuration for the application."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
    name: str = "promptbuilder", log_file: Optional[str] = None, level: int = logging.INFO
) -> logging.Logger:
    """Set up a logger with console and rotating file output.

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

    # Console handler - cleaner format for terminal
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    # Use a format that is readable but professional
    console_format = logging.Formatter("[%(asctime)s] %(levelname)-7s - %(name)s - %(message)s", datefmt="%H:%M:%S")
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler (optional) - more detailed format
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Use RotatingFileHandler: max 10MB per file, keep 5 backups
            file_handler = RotatingFileHandler(
                log_path, 
                maxBytes=10 * 1024 * 1024, 
                backupCount=5, 
                encoding="utf-8"
            )
            file_handler.setLevel(logging.DEBUG)  # File always gets full detail
            file_format = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s")
            file_handler.setFormatter(file_format)
            logger.addHandler(file_handler)
        except Exception as e:
            # Fallback to simple print if logging setup fails
            print(f"CRITICAL WARNING: Could not set up file logging: {e}")

    return logger


# Create a default logger instance
# We use a default file in the output/logs dir
DEFAULT_LOG_PATH = Path(__file__).parent.parent.parent / "output" / "logs" / "app.log"
logger = setup_logger(log_file=str(DEFAULT_LOG_PATH))
