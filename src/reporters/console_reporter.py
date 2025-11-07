"""Console reporter for displaying dump file analysis results."""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.models.dump_analysis import DumpFileAnalysis


class ConsoleReporter:
    """Reporter for displaying analysis results in the console using Rich formatting."""

    def __init__(self):
        """Initialize the console reporter."""
        self.console = Console()

    def display_dump_analysis(self, analysis: DumpFileAnalysis) -> None:
        """Display dump file analysis results in a formatted console output.
        
        Args:
            analysis: DumpFileAnalysis object to display
        """
        self.console.print()
        self.console.print(Panel.fit(
            "[bold cyan]Windows Dump File Analysis[/bold cyan]",
            border_style="cyan"
        ))
        self.console.print()

        self._display_crash_summary(analysis)
        self.console.print()

        self._display_system_info(analysis)
        self.console.print()

        if analysis.has_stack_trace():
            self._display_stack_trace(analysis)
            self.console.print()

        if analysis.loaded_modules:
            self._display_loaded_modules(analysis)
            self.console.print()

        if analysis.has_parsing_errors():
            self._display_parsing_errors(analysis)
            self.console.print()

    def _display_crash_summary(self, analysis: DumpFileAnalysis) -> None:
        """Display crash summary information."""
        table = Table(title="Crash Summary", show_header=False, box=None)
        table.add_column("Field", style="bold yellow", width=25)
        table.add_column("Value", style="white")

        table.add_row("File Path", analysis.file_path)
        table.add_row("File Size", f"{analysis.file_size_bytes:,} bytes")
        table.add_row("Crash Timestamp", analysis.crash_timestamp.strftime("%Y-%m-%d %H:%M:%S UTC"))
        table.add_row("Crash Type", analysis.crash_type)
        
        if analysis.has_error_code():
            table.add_row("Error Code", f"[bold red]{analysis.error_code}[/bold red]")
        
        table.add_row("Process Name", analysis.process_name)
        
        if analysis.process_id:
            table.add_row("Process ID", str(analysis.process_id))
        
        if analysis.thread_id:
            table.add_row("Thread ID", str(analysis.thread_id))
        
        if analysis.faulting_module:
            table.add_row("Faulting Module", f"[bold red]{analysis.faulting_module}[/bold red]")
        
        if analysis.faulting_address:
            table.add_row("Faulting Address", analysis.faulting_address)

        self.console.print(table)

    def _display_system_info(self, analysis: DumpFileAnalysis) -> None:
        """Display system information."""
        table = Table(title="System Information", show_header=False, box=None)
        table.add_column("Field", style="bold cyan", width=25)
        table.add_column("Value", style="white")

        table.add_row("OS Version", analysis.os_version)
        table.add_row("Architecture", analysis.architecture)
        
        if analysis.system_uptime_seconds is not None:
            uptime_hours = analysis.system_uptime_seconds / 3600
            table.add_row("System Uptime", f"{uptime_hours:.2f} hours")

        self.console.print(table)

    def _display_stack_trace(self, analysis: DumpFileAnalysis) -> None:
        """Display stack trace information."""
        self.console.print("[bold green]Stack Trace:[/bold green]")
        
        for i, frame in enumerate(analysis.stack_trace, 1):
            self.console.print(f"  {i:2d}. {frame}")

    def _display_loaded_modules(self, analysis: DumpFileAnalysis) -> None:
        """Display loaded modules."""
        self.console.print(f"[bold green]Loaded Modules ({len(analysis.loaded_modules)}):[/bold green]")
        
        display_count = min(20, len(analysis.loaded_modules))
        for i, module in enumerate(analysis.loaded_modules[:display_count], 1):
            self.console.print(f"  {i:2d}. {module}")
        
        if len(analysis.loaded_modules) > display_count:
            remaining = len(analysis.loaded_modules) - display_count
            self.console.print(f"  ... and {remaining} more modules")

    def _display_parsing_errors(self, analysis: DumpFileAnalysis) -> None:
        """Display parsing errors."""
        self.console.print("[bold yellow]Parsing Warnings:[/bold yellow]")
        
        for error in analysis.parsing_errors:
            self.console.print(f"  [yellow]⚠[/yellow] {error}")

    def print_error(self, message: str) -> None:
        """Print an error message.
        
        Args:
            message: Error message to display
        """
        self.console.print(f"[bold red]Error:[/bold red] {message}")

    def print_success(self, message: str) -> None:
        """Print a success message.
        
        Args:
            message: Success message to display
        """
        self.console.print(f"[bold green]✓[/bold green] {message}")

    def print_info(self, message: str) -> None:
        """Print an info message.
        
        Args:
            message: Info message to display
        """
        self.console.print(f"[bold blue]ℹ[/bold blue] {message}")
