from datetime import datetime, timezone
from pathlib import Path

from src.models.event_log import EventLogEntry, EventLevel
from src.parsers.evtx_parser import EvtxParser


SAMPLE_EVTX = Path(__file__).resolve().parents[2] / "sample" / "sample.evtx"


def test_parse_sample_evtx_produces_events():
    parser = EvtxParser()
    events = list(parser.parse(str(SAMPLE_EVTX)))

    assert events, "Expected sample EVTX to yield events"
    assert all(e.file_path.endswith("sample.evtx") for e in events)
    assert any(e.level in (EventLevel.ERROR, EventLevel.CRITICAL) for e in events)


def test_merge_events_orders_by_timestamp():
    parser = EvtxParser()
    early = EventLogEntry(
        record_number=1,
        timestamp=datetime(2025, 1, 1, tzinfo=timezone.utc),
        event_id=1,
        source="SourceA",
        level=EventLevel.ERROR,
        message="early",
        file_path="fileA",
    )
    late = EventLogEntry(
        record_number=2,
        timestamp=datetime(2025, 1, 2, tzinfo=timezone.utc),
        event_id=2,
        source="SourceB",
        level=EventLevel.WARNING,
        message="late",
        file_path="fileB",
    )

    merged = list(parser.merge_events([iter([late]), iter([early])]))
    assert [e.timestamp for e in merged] == [early.timestamp, late.timestamp]
