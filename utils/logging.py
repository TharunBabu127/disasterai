"""
Logging configuration for DisasterAI.
Provides structured logging with different log levels.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from config import api_config


def setup_logger(
    name: str = "disasterai",
    log_file: Optional[str] = "disasterai.log",
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG
) -> logging.Logger:
    """
    Configure and return a logger instance.

    Args:
        name: Logger name
        log_file: Path to log file (None for no file logging)
        console_level: Logging level for console output
        file_level: Logging level for file output

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Prevent adding handlers multiple times
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (if requested)
    if log_file:
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_dir / log_file)
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# Create default logger
logger = setup_logger()


def log_disaster_event(
    disaster_id: int,
    event_type: str,
    message: str,
    level: int = logging.INFO,
    **kwargs
):
    """
    Convenience function for logging disaster-related events.

    Args:
        disaster_id: ID of the disaster
        event_type: Type of event (created, updated, etc.)
        message: Log message
        level: Logging level
        **kwargs: Additional context to log
    """
    log_msg = f"[Disaster #{disaster_id}] {event_type}: {message}"
    if kwargs:
        context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        log_msg += f" | {context}"

    logger.log(level, log_msg)


def log_api_call(api_name: str, success: bool, duration: float, **kwargs):
    """
    Log external API calls.

    Args:
        api_name: Name of the API (USGS, GDACS, etc.)
        success: Whether the call succeeded
        duration: Duration in seconds
        **kwargs: Additional context
    """
    status = "SUCCESS" if success else "FAILED"
    msg = f"API Call: {api_name} - {status} - Duration: {duration:.2f}s"
    if kwargs:
        context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg += f" | {context}"

    level = logging.INFO if success else logging.WARNING
    logger.log(level, msg)


def log_database_operation(operation: str, table: str, record_id: int = None, **kwargs):
    """
    Log database operations.

    Args:
        operation: Type of operation (CREATE, UPDATE, DELETE, SELECT)
        table: Table name
        record_id: ID of affected record
        **kwargs: Additional context
    """
    msg = f"DB [{operation}] on {table}"
    if record_id:
        msg += f" (ID: {record_id})"
    if kwargs:
        context = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg += f" | {context}"

    logger.debug(msg)