"""CLI interface for Windows Error Analyzer."""

import sys
from pathlib import Path

import click

from src.analyzers.correlator import Correlator
from src.analyzers.llm_analyzer import LLMAnalyzer
from src.models import SessionStatus
from src.models.analysis_session import AnalysisSession
from src.parsers.dump_parser import DumpParser
from src.parsers.evtx_parser import EvtxParser
from src.reporters.console_reporter import ConsoleReporter
from src.reporters.markdown_reporter import MarkdownReporter
from src.utils.config import Config
from src.utils.filters import filter_by_level, filter_by_time_range
from src.utils.progress import ProgressTracker


@click.group()
def cli() -> None:
    """Windows Error Analyzer - Analyze Windows crash dumps and event logs."""
    pass


@cli.command()
@click.option("--dmp", "-d", "dmp_file", type=click.Path(exists=True), help="Path to dump file (.dmp)")
@click.option(
    "--evtx",
    "-e",
    "evtx_files",
    type=click.Path(exists=True),
    multiple=True,
    help="Path to event log file(s) (.evtx)",
)
@click.option("--output", "-o", "output_file", required=True, type=click.Path(), help="Output report path")
@click.option("--analyze/--no-analyze", default=True, help="Enable/disable LLM analysis")
@click.option(
    "--model", "-m", default="gpt-4", help="OpenAI model (gpt-4, gpt-3.5-turbo)"
)
@click.option(
    "--filter-level",
    "-f",
    default="error",
    type=click.Choice(["all", "critical", "error", "warning", "info"]),
    help="Event filter level",
)
@click.option(
    "--time-window", "-t", default=3600, type=int, help="Time window in seconds around crash"
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--quiet", "-q", is_flag=True, help="Suppress progress output")
def analyze(
    dmp_file: str | None,
    evtx_files: tuple[str, ...],
    output_file: str,
    analyze: bool,
    model: str,
    filter_level: str,
    time_window: int,
    verbose: bool,
    quiet: bool,
) -> None:
    """Analyze Windows dump and event log files."""
    console = ConsoleReporter()

    if not dmp_file and not evtx_files:
        console.display_error("At least one of --dmp or --evtx is required")
        sys.exit(1)

    try:
        session = AnalysisSession.create_new()

        if dmp_file:
            with ProgressTracker("Parsing dump file...", quiet=quiet) as progress:
                dump_parser = DumpParser()
                session.dump_analysis = dump_parser.parse(dmp_file, quiet=quiet)
                progress.update(1)

            if not quiet:
                console.display_dump_info(session.dump_analysis)

        if evtx_files:
            evtx_parser = EvtxParser()
            all_events = []

            for evtx_file in evtx_files:
                with ProgressTracker(f"Parsing {Path(evtx_file).name}...", quiet=quiet) as progress:
                    events = evtx_parser.parse(evtx_file, quiet=quiet)
                    all_events.extend(events)
                    progress.update(1)

            session.event_entries = sorted(all_events, key=lambda e: e.timestamp)

            if session.dump_analysis:
                correlator = Correlator()
                crash_time = correlator.get_crash_time(session.dump_analysis)
                session.event_entries = filter_by_time_range(
                    session.event_entries, crash_time, time_window
                )

            session.event_entries = filter_by_level(session.event_entries, filter_level)

            if not quiet:
                console.display_events(session.event_entries)

        if analyze:
            config = Config()
            api_key = config.get_api_key()

            if not api_key:
                console.display_error(
                    "OpenAI API key not found.\n"
                    "Please set OPENAI_API_KEY environment variable or run:\n"
                    "  windows-error-analyzer config --set-api-key"
                )
                sys.exit(4)

            session.status = SessionStatus.ANALYZING

            with ProgressTracker("Analyzing with AI...", quiet=quiet) as progress:
                llm_analyzer = LLMAnalyzer(api_key=api_key, model=model)

                correlator = Correlator()
                crash_time = session.dump_analysis.crash_timestamp if session.dump_analysis else None
                event_timeline = correlator.generate_timeline(session.event_entries, crash_time)

                session.analysis_report = llm_analyzer.analyze(
                    session_id=session.session_id,
                    dump_analysis=session.dump_analysis,
                    events=session.event_entries,
                    event_timeline=event_timeline,
                )
                progress.update(1)

            if not quiet:
                console.display_analysis_report(session.analysis_report)

        session.status = SessionStatus.COMPLETED
        session.output_file_path = output_file

        markdown_reporter = MarkdownReporter()
        report_content = markdown_reporter.generate_report(session)
        markdown_reporter.save_to_file(report_content, output_file)

        console.display_success(f"Analysis complete! Report saved to: {output_file}")
        sys.exit(0)

    except FileNotFoundError as e:
        console.display_error(str(e))
        sys.exit(2)
    except ValueError as e:
        console.display_error(str(e))
        sys.exit(3)
    except OSError as e:
        console.display_error(str(e))
        sys.exit(10)
    except Exception as e:
        console.display_error(f"Unexpected error: {str(e)}")
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(10)


@cli.command()
@click.option("--set-api-key", is_flag=True, help="Set OpenAI API key")
@click.option("--show-config", is_flag=True, help="Show current configuration")
@click.option("--reset", is_flag=True, help="Reset configuration to defaults")
def config(set_api_key: bool, show_config: bool, reset: bool) -> None:
    """Manage tool configuration."""
    console = ConsoleReporter()
    cfg = Config()

    if set_api_key:
        api_key = click.prompt("Enter your OpenAI API key", hide_input=True)
        cfg.set_api_key(api_key)
        console.display_success("API key saved successfully")

    elif show_config:
        config_data = cfg.get_all_config()
        console.console.print("\n[bold cyan]Current Configuration:[/bold cyan]")
        for key, value in config_data.items():
            if key == "api_key":
                value = "***" + value[-4:] if value else "Not set"
            console.console.print(f"  {key}: {value}")

    elif reset:
        cfg.reset_config()
        console.display_success("Configuration reset to defaults")

    else:
        console.display_error("Please specify an option (--set-api-key, --show-config, or --reset)")
        sys.exit(1)


@cli.command()
def version() -> None:
    """Display version information."""
    from src import __version__

    console = ConsoleReporter()
    console.console.print(f"\n[bold cyan]Windows Error Analyzer[/bold cyan] v{__version__}")
    console.console.print(f"Python: {sys.version.split()[0]}")
    console.console.print("\nDependencies:")

    try:
        import Evtx
        console.console.print(f"  - python-evtx: {Evtx.__version__ if hasattr(Evtx, '__version__') else 'installed'}")
    except ImportError:
        console.console.print("  - python-evtx: not installed")

    try:
        import minidump
        console.console.print(f"  - minidump: {minidump.__version__ if hasattr(minidump, '__version__') else 'installed'}")
    except ImportError:
        console.console.print("  - minidump: not installed")

    try:
        import openai
        console.console.print(f"  - openai: {openai.__version__ if hasattr(openai, '__version__') else 'installed'}")
    except ImportError:
        console.console.print("  - openai: not installed")

    try:
        import click as click_module
        console.console.print(f"  - click: {click_module.__version__}")
    except (ImportError, AttributeError):
        console.console.print("  - click: installed")

    try:
        import rich
        console.console.print(f"  - rich: {rich.__version__}")
    except (ImportError, AttributeError):
        console.console.print("  - rich: installed")


if __name__ == "__main__":
    cli()
