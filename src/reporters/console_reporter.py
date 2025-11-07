"""Console reporter using Rich library for formatted output."""

from rich.console import Console
from rich.table import Table

from src.models.analysis_report import AnalysisReport
from src.models.dump_analysis import DumpFileAnalysis
from src.models.event_log import EventLogEntry


class ConsoleReporter:
    """Reporter for Rich-formatted console output."""

    def __init__(self) -> None:
        """Initialize console reporter."""
        self.console = Console()

    def display_dump_info(self, dump_analysis: DumpFileAnalysis) -> None:
        """Display dump file information.

        Args:
            dump_analysis: DumpFileAnalysis object
        """
        self.console.print("\n[bold cyan]Crash Information[/bold cyan]")
        self.console.print(f"File: {dump_analysis.file_path}")
        self.console.print(f"Timestamp: {dump_analysis.crash_timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        if dump_analysis.error_code:
            self.console.print(f"Error Code: [red]{dump_analysis.error_code}[/red]")
        if dump_analysis.faulting_module:
            self.console.print(f"Faulting Module: [yellow]{dump_analysis.faulting_module}[/yellow]")
        self.console.print(f"Process: {dump_analysis.process_name}")
        if dump_analysis.process_id:
            self.console.print(f"PID: {dump_analysis.process_id}")
        self.console.print(f"OS: {dump_analysis.os_version}")
        self.console.print(f"Architecture: {dump_analysis.architecture}")

        if dump_analysis.stack_trace:
            self.console.print("\n[bold cyan]Stack Trace (Top Frames)[/bold cyan]")
            for i, frame in enumerate(dump_analysis.stack_trace[:10], 1):
                self.console.print(f"  {i}. {frame}")

        if dump_analysis.parsing_errors:
            self.console.print("\n[yellow]Parsing Warnings:[/yellow]")
            for error in dump_analysis.parsing_errors:
                self.console.print(f"  - {error}")

    def display_events(self, events: list[EventLogEntry], max_display: int = 50) -> None:
        """Display event log entries.

        Args:
            events: List of EventLogEntry objects
            max_display: Maximum number of events to display
        """
        if not events:
            self.console.print("\n[yellow]No events to display[/yellow]")
            return

        self.console.print(f"\n[bold cyan]Event Log Timeline ({len(events)} events)[/bold cyan]")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Time", style="dim")
        table.add_column("Level", style="bold")
        table.add_column("Source")
        table.add_column("Event ID")
        table.add_column("Message", max_width=60)

        for event in events[:max_display]:
            time_str = event.timestamp.strftime("%H:%M:%S")
            level_str = event.level.value

            level_color = "white"
            if event.level.value in ["Critical", "Error"]:
                level_color = "red"
            elif event.level.value == "Warning":
                level_color = "yellow"
            elif event.level.value == "Information":
                level_color = "blue"

            table.add_row(
                time_str,
                f"[{level_color}]{level_str}[/{level_color}]",
                event.source,
                str(event.event_id),
                event.message[:60],
            )

        self.console.print(table)

        if len(events) > max_display:
            self.console.print(f"\n[dim]... and {len(events) - max_display} more events[/dim]")

    def display_analysis_report(self, report: AnalysisReport) -> None:
        """Display analysis report.

        Args:
            report: AnalysisReport object
        """
        self.console.print("\n[bold cyan]AI Analysis[/bold cyan]")

        self.console.print("\n[bold]Root Cause:[/bold]")
        self.console.print(report.root_cause_summary)

        self.console.print("\n[bold]Detailed Analysis:[/bold]")
        self.console.print(report.detailed_analysis)

        if report.remediation_steps:
            self.console.print("\n[bold]Recommended Actions:[/bold]")
            for i, step in enumerate(report.remediation_steps, 1):
                self.console.print(f"  {i}. {step}")

        self.console.print("\n[bold]Analysis Metadata:[/bold]")
        self.console.print(f"  Model: {report.model_used}")
        if report.confidence_level:
            self.console.print(f"  Confidence: {report.confidence_level.value}")
        self.console.print(f"  Processing Time: {report.processing_time_seconds:.2f}s")
        if report.token_usage:
            self.console.print(f"  Tokens Used: {report.token_usage:,}")

    def display_success(self, message: str) -> None:
        """Display success message.

        Args:
            message: Success message
        """
        self.console.print(f"\n[green]✓[/green] {message}")

    def display_error(self, message: str) -> None:
        """Display error message.

        Args:
            message: Error message
        """
        self.console.print(f"\n[red]Error:[/red] {message}", style="bold red")

    def display_warning(self, message: str) -> None:
        """Display warning message.

        Args:
            message: Warning message
        """
        self.console.print(f"\n[yellow]Warning:[/yellow] {message}")
