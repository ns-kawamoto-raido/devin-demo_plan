"""LLM analyzer using OpenAI API."""

import time
from datetime import datetime

from src.models import ConfidenceLevel
from src.models.analysis_report import AnalysisReport
from src.models.dump_analysis import DumpFileAnalysis
from src.models.event_log import EventLogEntry


class LLMAnalyzer:
    """Analyzer using OpenAI's LLM for crash analysis."""

    def __init__(self, api_key: str, model: str = "gpt-4") -> None:
        """Initialize LLM analyzer.

        Args:
            api_key: OpenAI API key
            model: Model name (gpt-4 or gpt-3.5-turbo)
        """
        self.api_key = api_key
        self.model = model
        self.client = None

    def _init_client(self) -> None:
        """Initialize OpenAI client."""
        if self.client is None:
            try:
                from openai import OpenAI

                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ValueError("openai library not installed. Install with: pip install openai")

    def analyze(
        self,
        session_id: str,
        dump_analysis: DumpFileAnalysis | None,
        events: list[EventLogEntry],
        event_timeline: list[str],
    ) -> AnalysisReport:
        """Analyze crash data using LLM.

        Args:
            session_id: Session ID
            dump_analysis: Optional DumpFileAnalysis object
            events: List of EventLogEntry objects
            event_timeline: Timeline of events

        Returns:
            AnalysisReport object

        Raises:
            ValueError: If API call fails
        """
        self._init_client()

        start_time = time.time()

        prompt = self._build_prompt(dump_analysis, events, event_timeline)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Windows diagnostic expert. Analyze crash dumps and event logs to identify root causes and provide remediation steps.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=2000,
            )

            content = response.choices[0].message.content
            token_usage = response.usage.total_tokens if hasattr(response, "usage") else None

            root_cause, detailed_analysis, remediation_steps = self._parse_response(content)

            processing_time = time.time() - start_time

            return AnalysisReport(
                session_id=session_id,
                generated_at=datetime.utcnow(),
                model_used=self.model,
                root_cause_summary=root_cause,
                detailed_analysis=detailed_analysis,
                event_timeline=event_timeline,
                remediation_steps=remediation_steps,
                processing_time_seconds=processing_time,
                confidence_level=ConfidenceLevel.MEDIUM,
                token_usage=token_usage,
            )

        except Exception as e:
            raise ValueError(f"OpenAI API error: {str(e)}")

    def _build_prompt(
        self,
        dump_analysis: DumpFileAnalysis | None,
        events: list[EventLogEntry],
        event_timeline: list[str],
    ) -> str:
        """Build prompt for LLM.

        Args:
            dump_analysis: Optional DumpFileAnalysis object
            events: List of EventLogEntry objects
            event_timeline: Timeline of events

        Returns:
            Prompt string
        """
        prompt_parts = []

        prompt_parts.append("Analyze the following Windows error information:\n")

        if dump_analysis:
            prompt_parts.append("## Crash Information")
            prompt_parts.append(f"Process: {dump_analysis.process_name}")
            if dump_analysis.error_code:
                prompt_parts.append(f"Error Code: {dump_analysis.error_code}")
            if dump_analysis.faulting_module:
                prompt_parts.append(f"Faulting Module: {dump_analysis.faulting_module}")
            prompt_parts.append(f"OS: {dump_analysis.os_version}")
            prompt_parts.append(f"Architecture: {dump_analysis.architecture}")
            prompt_parts.append("")

        if events:
            prompt_parts.append("## Recent Events")
            error_events = [e for e in events if e.is_error_or_critical()]
            for event in error_events[:10]:
                prompt_parts.append(
                    f"- {event.timestamp.strftime('%H:%M:%S')} | {event.level.value} | {event.source} | Event {event.event_id}"
                )
            prompt_parts.append("")

        prompt_parts.append(
            "Please provide:\n1. Root cause summary (2-3 sentences)\n2. Detailed technical analysis\n3. Recommended remediation steps (numbered list)"
        )

        return "\n".join(prompt_parts)

    def _parse_response(self, content: str) -> tuple[str, str, list[str]]:
        """Parse LLM response.

        Args:
            content: LLM response content

        Returns:
            Tuple of (root_cause, detailed_analysis, remediation_steps)
        """
        lines = content.split("\n")

        root_cause = "Unable to determine root cause from available data."
        detailed_analysis = content
        remediation_steps = ["Review system logs for additional information"]

        sections = {"root": [], "detailed": [], "remediation": []}
        current_section = "detailed"

        for line in lines:
            line_lower = line.lower()
            if "root cause" in line_lower:
                current_section = "root"
                continue
            elif "detailed" in line_lower or "technical" in line_lower:
                current_section = "detailed"
                continue
            elif "remediation" in line_lower or "recommended" in line_lower or "steps" in line_lower:
                current_section = "remediation"
                continue

            if line.strip():
                sections[current_section].append(line.strip())

        if sections["root"]:
            root_cause = " ".join(sections["root"])

        if sections["detailed"]:
            detailed_analysis = "\n".join(sections["detailed"])

        if sections["remediation"]:
            remediation_steps = [
                line.lstrip("0123456789.-) ") for line in sections["remediation"] if line.strip()
            ]

        return root_cause, detailed_analysis, remediation_steps
