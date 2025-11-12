from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import uuid

from src.models.event_log import EventLogEntry
from src.models.dump_analysis import DumpFileAnalysis


class SessionStatus(Enum):
    PARSING = "parsing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AnalysisSession:
    session_id: str
    created_at: datetime
    event_entries: list[EventLogEntry]
    status: SessionStatus
    dump_analysis: DumpFileAnalysis | None = None
    analysis_report: object | None = None
    output_file_path: str | None = None
    error_message: str | None = None

    @classmethod
    def create_new(cls) -> "AnalysisSession":
        return cls(
            session_id=str(uuid.uuid4()),
            created_at=datetime.now(timezone.utc),
            event_entries=[],
            status=SessionStatus.PARSING,
        )

    def has_dump_file(self) -> bool:
        return self.dump_analysis is not None

    def has_analysis_report(self) -> bool:
        return self.analysis_report is not None

    def total_events(self) -> int:
        return len(self.event_entries)

    def error_events_count(self) -> int:
        return sum(1 for e in self.event_entries if hasattr(e, "is_error_or_critical") and e.is_error_or_critical())

