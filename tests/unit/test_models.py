"""Tests for data models."""

from datetime import datetime

import pytest

from src.models import EventLevel, SessionStatus
from src.models.analysis_session import AnalysisSession
from src.models.dump_analysis import DumpFileAnalysis
from src.models.event_log import EventLogEntry


def test_dump_file_analysis_creation() -> None:
    """Test DumpFileAnalysis creation."""
    dump = DumpFileAnalysis(
        file_path="/test/crash.dmp",
        file_size_bytes=1024,
        crash_timestamp=datetime.utcnow(),
        crash_type="EXCEPTION",
        process_name="test.exe",
        os_version="Windows 10",
        architecture="x64",
    )
    assert dump.file_path == "/test/crash.dmp"
    assert dump.file_size_bytes == 1024
    assert dump.architecture == "x64"


def test_dump_file_analysis_validation() -> None:
    """Test DumpFileAnalysis validation."""
    with pytest.raises(ValueError):
        DumpFileAnalysis(
            file_path="",
            file_size_bytes=1024,
            crash_timestamp=datetime.utcnow(),
            crash_type="EXCEPTION",
            process_name="test.exe",
            os_version="Windows 10",
            architecture="x64",
        )


def test_event_log_entry_creation() -> None:
    """Test EventLogEntry creation."""
    entry = EventLogEntry(
        record_number=1,
        timestamp=datetime.utcnow(),
        event_id=1000,
        source="Application",
        level=EventLevel.ERROR,
        message="Test error",
        file_path="/test/System.evtx",
    )
    assert entry.record_number == 1
    assert entry.event_id == 1000
    assert entry.is_error_or_critical()


def test_event_log_entry_time_range() -> None:
    """Test EventLogEntry time range check."""
    now = datetime.utcnow()
    entry = EventLogEntry(
        record_number=1,
        timestamp=now,
        event_id=1000,
        source="Application",
        level=EventLevel.ERROR,
        message="Test error",
        file_path="/test/System.evtx",
    )
    from datetime import timedelta
    start = now - timedelta(hours=1)
    end = now + timedelta(hours=1)
    assert entry.within_time_range(start, end)


def test_analysis_session_creation() -> None:
    """Test AnalysisSession creation."""
    session = AnalysisSession.create_new()
    assert session.session_id is not None
    assert session.status == SessionStatus.PARSING
    assert session.total_events() == 0
    assert not session.has_dump_file()
    assert not session.has_analysis_report()
