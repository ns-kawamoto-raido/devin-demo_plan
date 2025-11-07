"""Data models for Windows Error Analyzer."""

from enum import Enum


class EventLevel(Enum):
    """Event log severity levels."""
    CRITICAL = "Critical"
    ERROR = "Error"
    WARNING = "Warning"
    INFORMATION = "Information"
    VERBOSE = "Verbose"


class SessionStatus(Enum):
    """Analysis session status."""
    PARSING = "parsing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"


class ConfidenceLevel(Enum):
    """LLM analysis confidence level."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"
