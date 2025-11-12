from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class EventLevel(Enum):
    CRITICAL = "Critical"
    ERROR = "Error"
    WARNING = "Warning"
    INFORMATION = "Information"
    VERBOSE = "Verbose"


@dataclass
class EventLogEntry:
    record_number: int
    timestamp: datetime  # UTC
    event_id: int
    source: str
    level: EventLevel
    message: str
    file_path: str
    category: str | None = None
    computer_name: str | None = None
    user_sid: str | None = None

    def is_error_or_critical(self) -> bool:
        return self.level in (EventLevel.CRITICAL, EventLevel.ERROR)

    def within_time_range(self, start: datetime, end: datetime) -> bool:
        return start <= self.timestamp <= end

