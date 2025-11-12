from datetime import datetime, timezone

from src.models.event_log import EventLogEntry, EventLevel
from src.utils.filters import filter_by_level, filter_by_time_range, filter_by_source


def _entry(level: EventLevel, source: str, ts: datetime) -> EventLogEntry:
    return EventLogEntry(
        record_number=1,
        timestamp=ts,
        event_id=100,
        source=source,
        level=level,
        message="msg",
        file_path="sample.evtx",
    )


def test_filter_by_level_respects_case_insensitive():
    entries = [
        _entry(EventLevel.ERROR, "SrcA", datetime.now(timezone.utc)),
        _entry(EventLevel.INFORMATION, "SrcB", datetime.now(timezone.utc)),
    ]
    filtered = list(filter_by_level(entries, "ERROR"))
    assert len(filtered) == 1
    assert filtered[0].level is EventLevel.ERROR


def test_filter_by_time_range_inclusive_bounds():
    start = datetime(2025, 1, 1, tzinfo=timezone.utc)
    end = datetime(2025, 1, 1, 1, tzinfo=timezone.utc)
    entries = [
        _entry(EventLevel.ERROR, "SrcA", start),
        _entry(EventLevel.ERROR, "SrcA", end),
    ]
    filtered = list(filter_by_time_range(entries, start, end))
    assert len(filtered) == 2


def test_filter_by_source_accepts_multiple_sources():
    entries = [
        _entry(EventLevel.ERROR, "SourceA", datetime.now(timezone.utc)),
        _entry(EventLevel.ERROR, "SourceB", datetime.now(timezone.utc)),
    ]
    filtered = list(filter_by_source(entries, {"sourcea"}))
    assert len(filtered) == 1
    assert filtered[0].source == "SourceA"
