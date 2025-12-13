"""Debug logging shim that delegates to the project's standardized logger.

This module preserves the simple `init_debug_log()`, `log()`, and
`close_debug_log()` API used by the codebase but delegates to
`utils.logger` so all output goes through the same logging configuration.
"""
import logging
from pathlib import Path
from typing import Optional

try:
    # Prefer the project's configured logger
    from utils.logger import setup_logger
    _logger = setup_logger(log_file="promptbuilder_debug.log", level=logging.DEBUG)
except Exception:
    from utils import logger
    logger.exception('Auto-captured exception')
    # Fallback: basic logger to stdout
    _logger = logging.getLogger("promptbuilder_debug_fallback")
    if not _logger.handlers:
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
        _logger.addHandler(ch)
    _logger.setLevel(logging.DEBUG)

_file_handler: Optional[logging.Handler] = None

def init_debug_log():
    """Initialize debug logging (attach a file handler at DEBUG level).

    This will create/overwrite `promptbuilder_debug.log` in the current
    working directory and ensure detailed debug messages are recorded.
    """
    global _file_handler
    try:
        log_path = Path("promptbuilder_debug.log")
        # Remove existing file so we start fresh
        try:
            if log_path.exists():
                log_path.unlink()
        except Exception:
            from utils import logger
            logger.exception('Auto-captured exception')
            # Non-fatal; proceed to attach handler which will overwrite
            pass

        # Attach file handler if not already attached
        if not _file_handler:
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fh.setLevel(logging.DEBUG)
            fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
            _logger.addHandler(fh)
            _file_handler = fh

        _logger.debug("=== Debug Log Started ===")
    except Exception as e:
        from utils import logger
        logger.exception('Auto-captured exception')
        # Last-resort fallback: write a simple warning to the configured logger
        try:
            _logger.warning(f"Could not initialize debug log: {e}")
        except Exception:
            from utils import logger
            logger.exception('Auto-captured exception')
            pass

def log(message: str, level: int = logging.INFO):
    """Log a message via the shared logger.

    Args:
        message: The message to log.
        level: Logging level (defaults to INFO).
    """
    try:
        _logger.log(level, message)
    except Exception:
        from utils import logger
        logger.exception('Auto-captured exception')
        # Ignore logging failures
        pass

def close_debug_log():
    """Close debug log file handler if attached."""
    global _file_handler
    try:
        if _file_handler:
            _logger.debug("=== Debug Log Ended ===")
            _logger.removeHandler(_file_handler)
            try:
                _file_handler.close()
            except Exception:
                from utils import logger
                logger.exception('Auto-captured exception')
                pass
            _file_handler = None
    except Exception:
        from utils import logger
        logger.exception('Auto-captured exception')
        pass
