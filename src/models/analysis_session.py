"""Data model for analysis session."""

import uuid
from dataclasses import dataclass
from datetime import datetime

from src.models import SessionStatus
from src.models.analysis_report import AnalysisReport
from src.models.dump_analysis import DumpFileAnalysis
from src.models.event_log import EventLogEntry


@dataclass
class AnalysisSession:
    """Represents a complete diagnostic session."""

    session_id: str
    created_at: datetime
    event_entries: list[EventLogEntry]
    status: SessionStatus
    dump_analysis: DumpFileAnalysis | None = None
    analysis_report: AnalysisReport | None = None
    output_file_path: str | None = None
    error_message: str | None = None

    @classmethod
    def create_new(cls) -> "AnalysisSession":
        """Create a new analysis session.

        Returns:
            New AnalysisSession instance
        """
        return cls(
            session_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            event_entries=[],
            status=SessionStatus.PARSING,
        )

    def has_dump_file(self) -> bool:
        """Check if session has dump file analysis.

        Returns:
            True if dump analysis is present
        """
        return self.dump_analysis is not None

    def has_analysis_report(self) -> bool:
        """Check if session has analysis report.

        Returns:
            True if analysis report is present
        """
        return self.analysis_report is not None

    def total_events(self) -> int:
        """Get total number of events.

        Returns:
            Number of event entries
        """
        return len(self.event_entries)

    def error_events_count(self) -> int:
        """Get count of error and critical events.

        Returns:
            Number of error/critical events
        """
        return sum(1 for e in self.event_entries if e.is_error_or_critical())
