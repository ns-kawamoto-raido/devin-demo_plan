"""Event log filtering utilities."""

from datetime import datetime, timedelta
from typing import Any

from src.models import EventLevel


def filter_by_level(events: list[Any], level: str) -> list[Any]:
    """Filter events by severity level.

    Args:
        events: List of EventLogEntry objects
        level: Filter level (all, critical, error, warning, info)

    Returns:
        Filtered list of events
    """
    if level == "all":
        return events

    level_map = {
        "critical": [EventLevel.CRITICAL],
        "error": [EventLevel.CRITICAL, EventLevel.ERROR],
        "warning": [EventLevel.CRITICAL, EventLevel.ERROR, EventLevel.WARNING],
        "info": [EventLevel.CRITICAL, EventLevel.ERROR, EventLevel.WARNING, EventLevel.INFORMATION],
    }

    allowed_levels = level_map.get(level.lower(), [EventLevel.CRITICAL, EventLevel.ERROR])
    return [event for event in events if event.level in allowed_levels]


def filter_by_time_range(
    events: list[Any], center_time: datetime, window_seconds: int
) -> list[Any]:
    """Filter events by time range around a center time.

    Args:
        events: List of EventLogEntry objects
        center_time: Center timestamp (e.g., crash time)
        window_seconds: Time window in seconds (±window_seconds from center)

    Returns:
        Filtered list of events within time range
    """
    start_time = center_time - timedelta(seconds=window_seconds)
    end_time = center_time + timedelta(seconds=window_seconds)
    return [event for event in events if event.within_time_range(start_time, end_time)]


def filter_by_source(events: list[Any], source: str) -> list[Any]:
    """Filter events by source name.

    Args:
        events: List of EventLogEntry objects
        source: Source name to filter by (case-insensitive)

    Returns:
        Filtered list of events from specified source
    """
    source_lower = source.lower()
    return [event for event in events if source_lower in event.source.lower()]


def sort_events_chronologically(events: list[Any]) -> list[Any]:
    """Sort events by timestamp in chronological order.

    Args:
        events: List of EventLogEntry objects

    Returns:
        Sorted list of events
    """
    return sorted(events, key=lambda event: event.timestamp)
