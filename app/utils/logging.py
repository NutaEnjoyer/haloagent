"""
Logging configuration for the application.
"""
import logging
import sys
from pathlib import Path
from typing import Optional

from app.config import settings


def setup_logging(log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        log_file: Optional path to log file. If None, logs only to stdout.

    Returns:
        Configured logger instance.
    """
    # Create logger
    logger = logging.getLogger("callerapi")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def log_call_event(logger: logging.Logger, event: str, call_id: str, **kwargs) -> None:
    """
    Log a structured call event.

    Args:
        logger: Logger instance
        event: Event name (e.g., "call_created", "call_answered")
        call_id: Call session ID
        **kwargs: Additional event data
    """
    extra_data = " | ".join([f"{k}={v}" for k, v in kwargs.items()])
    log_message = f"[{event}] call_id={call_id}"
    if extra_data:
        log_message += f" | {extra_data}"

    logger.info(log_message)


# Create default logger instance
logger = setup_logging()
