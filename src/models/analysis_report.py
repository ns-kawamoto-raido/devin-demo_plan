"""Data model for analysis report."""

from dataclasses import dataclass, field
from datetime import datetime

from src.models import ConfidenceLevel


@dataclass
class AnalysisReport:
    """Represents the LLM-generated analysis report."""

    session_id: str
    generated_at: datetime
    model_used: str
    root_cause_summary: str
    detailed_analysis: str
    event_timeline: list[str]
    remediation_steps: list[str]
    processing_time_seconds: float
    confidence_level: ConfidenceLevel | None = None
    limitations: list[str] = field(default_factory=list)
    token_usage: int | None = None

    def __post_init__(self) -> None:
        """Validate data after initialization."""
        if not self.session_id:
            raise ValueError("session_id cannot be empty")
        if not self.model_used:
            raise ValueError("model_used cannot be empty")
        if not self.root_cause_summary:
            raise ValueError("root_cause_summary cannot be empty")
        if not self.detailed_analysis:
            raise ValueError("detailed_analysis cannot be empty")
        if self.processing_time_seconds <= 0:
            raise ValueError("processing_time_seconds must be greater than 0")

    def to_markdown(self) -> str:
        """Generate markdown representation of report.

        Returns:
            Markdown formatted report
        """
        lines = []
        lines.append("# Windows Error Analysis Report")
        lines.append("")
        lines.append(f"**Analysis Date**: {self.generated_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"**Session ID**: {self.session_id}")
        lines.append("")
        
        lines.append("## AI Analysis")
        lines.append("")
        lines.append("### Root Cause")
        lines.append("")
        lines.append(self.root_cause_summary)
        lines.append("")
        
        lines.append("### Detailed Analysis")
        lines.append("")
        lines.append(self.detailed_analysis)
        lines.append("")
        
        if self.event_timeline:
            lines.append("### Event Timeline")
            lines.append("")
            for event in self.event_timeline:
                lines.append(f"- {event}")
            lines.append("")
        
        lines.append("### Recommended Actions")
        lines.append("")
        for i, step in enumerate(self.remediation_steps, 1):
            lines.append(f"{i}. {step}")
        lines.append("")
        
        lines.append("## Analysis Metadata")
        lines.append("")
        lines.append(f"- **Model Used**: {self.model_used}")
        if self.confidence_level:
            lines.append(f"- **Confidence**: {self.confidence_level.value}")
        lines.append(f"- **Processing Time**: {self.processing_time_seconds:.2f} seconds")
        if self.token_usage:
            lines.append(f"- **Tokens Used**: {self.token_usage:,}")
        
        if self.limitations:
            lines.append("")
            lines.append("### Limitations")
            lines.append("")
            for limitation in self.limitations:
                lines.append(f"- {limitation}")
        
        return "\n".join(lines)
