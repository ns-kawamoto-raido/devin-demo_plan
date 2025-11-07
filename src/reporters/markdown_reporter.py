"""Markdown reporter for generating markdown reports."""

from src.models.analysis_report import AnalysisReport
from src.models.analysis_session import AnalysisSession
from src.models.dump_analysis import DumpFileAnalysis
from src.models.event_log import EventLogEntry


class MarkdownReporter:
    """Reporter for generating Markdown reports."""

    def generate_report(self, session: AnalysisSession) -> str:
        """Generate complete markdown report.

        Args:
            session: AnalysisSession object

        Returns:
            Markdown formatted report
        """
        lines = []

        lines.append("# Windows Error Analysis Report")
        lines.append("")
        lines.append(f"**Analysis Date**: {session.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        lines.append(f"**Session ID**: {session.session_id}")
        lines.append("")

        if session.dump_analysis:
            lines.extend(self._format_dump_info(session.dump_analysis))
            lines.append("")

        if session.event_entries:
            lines.extend(self._format_events(session.event_entries))
            lines.append("")

        if session.analysis_report:
            lines.extend(self._format_analysis_report(session.analysis_report))
            lines.append("")

        return "\n".join(lines)

    def _format_dump_info(self, dump_analysis: DumpFileAnalysis) -> list[str]:
        """Format dump information as markdown.

        Args:
            dump_analysis: DumpFileAnalysis object

        Returns:
            List of markdown lines
        """
        lines = []
        lines.append("## Crash Information")
        lines.append("")
        lines.append(f"**File**: {dump_analysis.file_path}")
        lines.append(f"**Timestamp**: {dump_analysis.crash_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        if dump_analysis.error_code:
            lines.append(f"**Error Code**: {dump_analysis.error_code}")
        if dump_analysis.faulting_module:
            lines.append(f"**Faulting Module**: {dump_analysis.faulting_module}")
        lines.append(f"**Process**: {dump_analysis.process_name}")
        if dump_analysis.process_id:
            lines.append(f"**PID**: {dump_analysis.process_id}")
        lines.append(f"**OS**: {dump_analysis.os_version}")
        lines.append(f"**Architecture**: {dump_analysis.architecture}")
        lines.append("")

        if dump_analysis.stack_trace:
            lines.append("### Stack Trace")
            lines.append("")
            lines.append("```")
            for frame in dump_analysis.stack_trace[:20]:
                lines.append(frame)
            lines.append("```")
            lines.append("")

        if dump_analysis.loaded_modules:
            lines.append("### Loaded Modules")
            lines.append("")
            for module in dump_analysis.loaded_modules[:20]:
                lines.append(f"- {module}")
            lines.append("")

        return lines

    def _format_events(self, events: list[EventLogEntry]) -> list[str]:
        """Format events as markdown table.

        Args:
            events: List of EventLogEntry objects

        Returns:
            List of markdown lines
        """
        lines = []
        lines.append("## Event Log Timeline")
        lines.append("")
        lines.append(f"Total events: {len(events)}")
        lines.append("")
        lines.append("| Time | Level | Source | Event ID | Message |")
        lines.append("|------|-------|--------|----------|---------|")

        for event in events[:100]:
            time_str = event.timestamp.strftime("%H:%M:%S")
            message_short = event.message[:80].replace("|", "\\|")
            lines.append(
                f"| {time_str} | {event.level.value} | {event.source} | {event.event_id} | {message_short} |"
            )

        if len(events) > 100:
            lines.append("")
            lines.append(f"*... and {len(events) - 100} more events*")

        return lines

    def _format_analysis_report(self, report: AnalysisReport) -> list[str]:
        """Format analysis report as markdown.

        Args:
            report: AnalysisReport object

        Returns:
            List of markdown lines
        """
        return report.to_markdown().split("\n")

    def save_to_file(self, content: str, file_path: str) -> None:
        """Save markdown content to file.

        Args:
            content: Markdown content
            file_path: Output file path

        Raises:
            IOError: If file cannot be written
        """
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            raise IOError(f"Failed to write report to {file_path}: {str(e)}")
