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

    def to_markdown(self) -> str:
        """Return a simple markdown representation (stub; can be extended)."""
        lines: list[str] = []
        lines.append("# Windows Error Analysis Report")
        lines.append("")
        lines.append(f"**Session ID**: {self.session_id}")
        lines.append(f"**Model Used**: {self.model_used}")
        lines.append(f"**Processing Time**: {self.processing_time_seconds:.1f} seconds")
        if self.confidence_level:
            lines.append(f"**Confidence**: {self.confidence_level.value}")
        if self.token_usage is not None:
            lines.append(f"**Tokens Used**: {self.token_usage}")
        lines.append("")
        lines.append("## Root Cause")
        lines.append(self.root_cause_summary or "(no summary)")
        lines.append("")
        lines.append("## Detailed Analysis")
        lines.append(self.detailed_analysis or "(no details)")
        lines.append("")
        if self.event_timeline:
            lines.append("## Event Timeline")
            for item in self.event_timeline:
                lines.append(f"- {item}")
            lines.append("")
        if self.remediation_steps:
            lines.append("## Recommended Actions")
            for i, step in enumerate(self.remediation_steps, 1):
                lines.append(f"{i}. {step}")
            lines.append("")
        return "\n".join(lines)
