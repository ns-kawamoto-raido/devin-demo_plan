"""Command-line interface for Windows Error Analyzer."""

import sys
from datetime import datetime, timedelta, timezone

import click

from src.parsers.dump_parser import DumpParserError
from src.parsers.windbg_parser import WinDbgParserError
from src.parsers import get_parser_for
from src.parsers.evtx_parser import EvtxParser, EvtxParserError
from src.models.event_log import EventLogEntry
from src.utils.filters import filter_by_level, filter_by_time_range, filter_by_source
from src.reporters.console_reporter import ConsoleReporter
from src.utils.config import get_openai_api_key
from src.analyzers.correlator import correlate_events
from src.analyzers.llm_analyzer import LLMAnalyzer


def _parse_iso8601(value: str) -> datetime:
    v = value.strip().replace(" ", "T").replace("Z", "+00:00")
    dt = datetime.fromisoformat(v)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Windows Error Analyzer - Extract and analyze Windows crash dumps and event logs."""
    pass


@cli.command()
@click.option(
    "--dmp",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to Windows dump file (.dmp)",
)
@click.option(
    "--evtx",
    multiple=True,
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Path to Windows event log file(s) (.evtx). Can be specified multiple times.",
)
@click.option(
    "--filter-level",
    type=click.Choice(["all", "critical", "error", "warning", "info", "verbose"], case_sensitive=False),
    default="all",
    help="Event level filter (default: all)",
)
@click.option(
    "--start",
    type=str,
    help="Start time (ISO8601, e.g., 2025-11-12T00:00:00+09:00). Overrides --time-window if provided.",
)
@click.option(
    "--end",
    type=str,
    help="End time (ISO8601). Overrides --time-window if provided.",
)
@click.option(
    "--time-window",
    type=int,
    default=3600,
    show_default=True,
    help="Time window in seconds around crash timestamp when --dmp is provided.",
)
@click.option(
    "--analyze/--no-analyze",
    default=True,
    help="Enable/disable LLM-powered analysis (default: enabled)",
)
@click.option(
    "--model",
    type=click.Choice(["gpt-4", "gpt-3.5-turbo"], case_sensitive=False),
    default="gpt-4",
    help="OpenAI model for analysis",
)
@click.option(
    "--source",
    "sources",
    multiple=True,
    help="Filter events by source/provider name (repeatable)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose output",
)
def analyze(dmp, evtx, filter_level, start, end, time_window, analyze, model, sources, verbose):
    """Analyze Windows dump and/or event logs and display results."""
    reporter = ConsoleReporter()

    if not dmp and not evtx:
        reporter.print_error("At least one input (--dmp or --evtx) is required")
        sys.exit(1)

    try:
        dump_analysis = None
        if dmp:
            if verbose:
                reporter.print_info(f"Parsing dump file: {dmp}")
            parser = get_parser_for(dmp)
            dump_analysis = parser.parse(dmp)
            if verbose:
                reporter.print_success("Dump file parsed successfully")
            reporter.display_dump_analysis(dump_analysis)

        if evtx:
            if verbose:
                reporter.print_info(f"Parsing event logs: {', '.join(evtx)}")
            eparser = EvtxParser()
            entries_iter = eparser.parse(list(evtx))

            # --start/--end があれば最優先。無ければ --dmp + --time-window を採用。
            start_dt = end_dt = None
            if start and end:
                start_dt = _parse_iso8601(start)
                end_dt = _parse_iso8601(end)
            elif dump_analysis is not None and time_window and time_window > 0:
                ct = dump_analysis.crash_timestamp
                if ct.tzinfo is None:
                    ct = ct.replace(tzinfo=timezone.utc)
                start_dt = ct - timedelta(seconds=time_window)
                end_dt = ct + timedelta(seconds=time_window)

            # ストリーミングでフィルタ
            filtered = entries_iter
            filtered = filter_by_level(filtered, filter_level)
            if sources:
                filtered = filter_by_source(filtered, set(sources))
            if start_dt and end_dt:
                filtered = filter_by_time_range(filtered, start_dt, end_dt)

            entries: list[EventLogEntry] = list(filtered)
            entries.sort(key=lambda e: e.timestamp)

            if verbose:
                reporter.print_info(f"Events after filtering: {len(entries)}")
            # per-record 警告要約（T034）
            warn_count, warn_samples = eparser.warnings_summary()
            if warn_count:
                reporter.print_warning(
                    f"Event log parsing encountered {warn_count} record error(s); continued parsing."
                )
                if verbose and warn_samples:
                    for s in warn_samples:
                        reporter.print_warning(f"  - {s}")

            reporter.display_events(entries)

        # US3: LLM-powered analysis
        if analyze:
            # Validate API key availability
            if not get_openai_api_key():
                reporter.print_error("OPENAI_API_KEY が未設定です。.env または環境変数を設定してください。\nヒント: --no-analyze を付けると抽出のみ実行できます。")
                # フォールバック: 抽出結果の表示は継続済み
                analyze = False
            else:
                try:
                    # Correlate events around crash timestamp or given range
                    correlated = correlate_events(
                        dump_analysis, entries if evtx else [],
                        _parse_iso8601(start) if start else None,
                        _parse_iso8601(end) if end else None,
                        time_window,
                    )

                    analyzer = LLMAnalyzer(model=model)
                    summary = analyzer.summarize_inputs(dump_analysis, correlated)
                    report, meta = analyzer.analyze(summary)
                    reporter.display_ai_analysis(report)
                except Exception as e:
                    # US3-4: LLM不通時のフォールバック
                    reporter.print_warning(
                        "AI解析に失敗しました。後で再試行するか、--no-analyze で抽出のみを保存してください。"
                    )
                    reporter.print_error(str(e))

        reporter.print_success("Analysis complete!")
        sys.exit(0)

    except FileNotFoundError as e:
        reporter.print_error(str(e))
        sys.exit(2)
    except (DumpParserError, WinDbgParserError, EvtxParserError) as e:
        reporter.print_error(str(e))
        sys.exit(3)
    except Exception as e:
        reporter.print_error(f"予期しないエラーが発生しました: {e}")
        if verbose:
            reporter.console.print_exception()
        sys.exit(10)


def main():
    """Main entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
