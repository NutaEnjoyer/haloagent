"""
Time utilities for the application.
"""
from datetime import datetime, timezone


def utcnow() -> datetime:
    """
    Get current UTC time.

    Returns:
        Current datetime in UTC timezone.
    """
    return datetime.now(timezone.utc)


def format_timestamp(dt: datetime) -> str:
    """
    Format datetime to ISO 8601 string.

    Args:
        dt: Datetime object to format

    Returns:
        ISO 8601 formatted string
    """
    return dt.isoformat()


def calculate_duration_sec(start: datetime, end: datetime) -> int:
    """
    Calculate duration between two timestamps in seconds.

    Args:
        start: Start datetime
        end: End datetime

    Returns:
        Duration in seconds
    """
    delta = end - start
    return int(delta.total_seconds())
