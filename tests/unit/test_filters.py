"""Tests for event filtering utilities."""

from datetime import datetime, timedelta

from src.models import EventLevel
from src.models.event_log import EventLogEntry
from src.utils.filters import filter_by_level, filter_by_time_range, sort_events_chronologically


def create_test_event(level: EventLevel, timestamp: datetime) -> EventLogEntry:
    """Create a test event."""
    return EventLogEntry(
        record_number=1,
        timestamp=timestamp,
        event_id=1000,
        source="Test",
        level=level,
        message="Test message",
        file_path="/test/test.evtx",
    )


def test_filter_by_level_all() -> None:
    """Test filtering by level 'all'."""
    events = [
        create_test_event(EventLevel.CRITICAL, datetime.utcnow()),
        create_test_event(EventLevel.ERROR, datetime.utcnow()),
        create_test_event(EventLevel.WARNING, datetime.utcnow()),
        create_test_event(EventLevel.INFORMATION, datetime.utcnow()),
    ]
    filtered = filter_by_level(events, "all")
    assert len(filtered) == 4


def test_filter_by_level_error() -> None:
    """Test filtering by level 'error'."""
    events = [
        create_test_event(EventLevel.CRITICAL, datetime.utcnow()),
        create_test_event(EventLevel.ERROR, datetime.utcnow()),
        create_test_event(EventLevel.WARNING, datetime.utcnow()),
        create_test_event(EventLevel.INFORMATION, datetime.utcnow()),
    ]
    filtered = filter_by_level(events, "error")
    assert len(filtered) == 2


def test_filter_by_time_range() -> None:
    """Test filtering by time range."""
    now = datetime.utcnow()
    events = [
        create_test_event(EventLevel.ERROR, now - timedelta(hours=2)),
        create_test_event(EventLevel.ERROR, now - timedelta(minutes=30)),
        create_test_event(EventLevel.ERROR, now),
        create_test_event(EventLevel.ERROR, now + timedelta(hours=2)),
    ]
    filtered = filter_by_time_range(events, now, 3600)
    assert len(filtered) == 2


def test_sort_events_chronologically() -> None:
    """Test sorting events chronologically."""
    now = datetime.utcnow()
    events = [
        create_test_event(EventLevel.ERROR, now + timedelta(hours=1)),
        create_test_event(EventLevel.ERROR, now - timedelta(hours=1)),
        create_test_event(EventLevel.ERROR, now),
    ]
    sorted_events = sort_events_chronologically(events)
    assert sorted_events[0].timestamp < sorted_events[1].timestamp < sorted_events[2].timestamp
