from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional


class ConfidenceLevel(Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class AnalysisReport:
    session_id: str
    generated_at: datetime
    model_used: str
    root_cause_summary: str
    detailed_analysis: str
    event_timeline: List[str]
    remediation_steps: List[str]
    processing_time_seconds: float
    confidence_level: Optional[ConfidenceLevel] = None
    limitations: List[str] | None = None
    token_usage: Optional[int] = None

    def __post_init__(self) -> None:
        if self.limitations is None:
            self.limitations = []

