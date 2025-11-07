"""Data model for event log entries."""

from dataclasses import dataclass
from datetime import datetime

from src.models import EventLevel


@dataclass
class EventLogEntry:
    """Represents a single Windows event log entry from a .evtx file."""

    record_number: int
    timestamp: datetime
    event_id: int
    source: str
    level: EventLevel
    message: str
    file_path: str
    category: str | None = None
    computer_name: str | None = None
    user_sid: str | None = None

    def __post_init__(self) -> None:
        """Validate data after initialization."""
        if self.record_number <= 0:
            raise ValueError("record_number must be greater than 0")
        if self.event_id <= 0:
            raise ValueError("event_id must be greater than 0")
        if not self.source:
            raise ValueError("source cannot be empty")
        if not self.message:
            raise ValueError("message cannot be empty")
        if not self.file_path:
            raise ValueError("file_path cannot be empty")

    def is_error_or_critical(self) -> bool:
        """Check if event is error or critical level.

        Returns:
            True if event is critical or error level
        """
        return self.level in (EventLevel.CRITICAL, EventLevel.ERROR)

    def within_time_range(self, start: datetime, end: datetime) -> bool:
        """Check if event timestamp is within time range.

        Args:
            start: Start of time range
            end: End of time range

        Returns:
            True if event timestamp is within range
        """
        return start <= self.timestamp <= end
