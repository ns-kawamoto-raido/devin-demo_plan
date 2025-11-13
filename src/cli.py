
"""Command-line interface for Windows Error Analyzer."""

import json
import sys
from dataclasses import asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any

import click

from src.parsers.dump_parser import DumpParserError
from src.parsers.windbg_parser import WinDbgParserError
from src.parsers import get_parser_for
from src.parsers.evtx_parser import EvtxParser, EvtxParserError
from src.models.dump_analysis import DumpFileAnalysis
from src.models.analysis_report import AnalysisReport, ConfidenceLevel
from src.models.event_log import EventLogEntry, EventLevel
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
@click.option(
    "--output",
    "output_path",
    type=click.Path(dir_okay=False, writable=True),
    help="Path to save analysis results (Markdown by default)",
)
@click.option(
    "--json",
    "output_json",
    is_flag=True,
    help="Export results as JSON (requires --output)",
)
@click.option(
    "--load",
    "load_path",
    type=click.Path(exists=True, dir_okay=False, readable=True),
    help="Load a previously saved JSON session (created via --json)",
)
def analyze(
    dmp,
    evtx,
    filter_level,
    start,
    end,
    time_window,
    analyze,
    model,
    sources,
    verbose,
    output_path,
    output_json,
    load_path,
):
    """Analyze Windows dump and/or event logs and display results."""
    reporter = ConsoleReporter()

    if load_path and (dmp or evtx):
        reporter.print_error("--load オプションと --dmp/--evtx は同時に指定できません")
        sys.exit(1)

    if not load_path and not dmp and not evtx:
        reporter.print_error("At least one input (--dmp or --evtx) is required")
        sys.exit(1)

    if output_json and not output_path:
        reporter.print_error("--json を使用する場合は --output で保存先ファイルを指定してください")
        sys.exit(1)

    try:
        dump_analysis: DumpFileAnalysis | None = None
        entries: list[EventLogEntry] = []
        analysis_report: AnalysisReport | None = None

        if load_path:
            dump_analysis, entries, analysis_report = _load_session(Path(load_path), reporter)
            if dump_analysis:
                reporter.display_dump_analysis(dump_analysis)
            reporter.display_events(entries)
            if analysis_report:
                reporter.display_ai_analysis(analysis_report)
            analyze = False
        else:
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

                # --start/--end 指定時は絶対時間。未指定なら --dmp + --time-window を利用。
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

                entries = list(filtered)
                entries.sort(key=lambda e: e.timestamp)

                if verbose:
                    reporter.print_info(f"Events after filtering: {len(entries)}")
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
            if not get_openai_api_key():
                reporter.print_error(
                    "OPENAI_API_KEY が未設定です。.env または環境変数へ設定してください。\n"
                    "ヒント: --no-analyze で抽出のみを実行できます"
                )
                analyze = False
            else:
                try:
                    correlated = correlate_events(
                        dump_analysis,
                        entries,
                        _parse_iso8601(start) if start else None,
                        _parse_iso8601(end) if end else None,
                        time_window,
                    )

                    analyzer = LLMAnalyzer(model=model)
                    summary = analyzer.summarize_inputs(dump_analysis, correlated)
                    report, meta = analyzer.analyze(summary)
                    analysis_report = report
                    reporter.display_ai_analysis(report)
                except Exception as exc:  # noqa: BLE001
                    reporter.print_warning(
                        "AI出力に失敗しました。リトライするか --no-analyze で抽出のみ保存してください。"
                    )
                    reporter.print_error(str(exc))

        if output_path:
            _save_outputs(
                Path(output_path),
                output_json,
                dump_analysis,
                entries,
                analysis_report,
                reporter,
            )

        reporter.print_success("Analysis complete!")
        sys.exit(0)

    except FileNotFoundError as e:
        reporter.print_error(str(e))
        sys.exit(2)
    except (DumpParserError, WinDbgParserError, EvtxParserError) as e:
        reporter.print_error(str(e))
        sys.exit(3)
    except Exception as e:  # noqa: BLE001
        reporter.print_error(f"予期しないエラーが発生しました: {e}")
        if verbose:
            reporter.console.print_exception()
        sys.exit(10)


def main():
    """Main entry point for the CLI."""
    cli()


def _save_outputs(
    output_path: Path,
    output_json: bool,
    dump_analysis: DumpFileAnalysis | None,
    entries: list[EventLogEntry],
    analysis_report: AnalysisReport | None,
    reporter: ConsoleReporter,
) -> None:
    """Persist analysis results to disk."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_json:
        payload = _build_json_payload(dump_analysis, entries, analysis_report)
        output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        reporter.print_info(f"JSONレポートを保存しました: {output_path}")
        return

    if analysis_report is None:
        reporter.print_warning("AIレポートが未生成のため、Markdown出力はサマリーのみになります")
        markdown = _fallback_markdown(dump_analysis, entries)
    else:
        markdown = analysis_report.to_markdown()

    output_path.write_text(markdown, encoding="utf-8")
    reporter.print_info(f"Markdownレポートを保存しました: {output_path}")


def _build_json_payload(
    dump_analysis: DumpFileAnalysis | None,
    entries: list[EventLogEntry],
    analysis_report: AnalysisReport | None,
) -> dict:
    return {
        "version": 1,
        "dump_analysis": _serialize_dataclass(dump_analysis),
        "events": [_serialize_dataclass(e) for e in entries],
        "analysis_report": _serialize_dataclass(analysis_report),
    }


def _serialize_dataclass(obj):
    if obj is None:
        return None
    data = asdict(obj)
    return {key: _serialize_value(value) for key, value in data.items()}


def _serialize_value(value: Any):
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    return value


def _fallback_markdown(dump_analysis: DumpFileAnalysis | None, entries: list[EventLogEntry]) -> str:
    lines: list[str] = []
    lines.append("# Windows Error Analysis (Summary)")
    lines.append("")
    if dump_analysis:
        lines.append("## Dump Summary")
        lines.append(f"File: {dump_analysis.file_path}")
        lines.append(f"Crash Type: {dump_analysis.crash_type}")
        lines.append(f"Process: {dump_analysis.process_name}")
        lines.append("")
    if entries:
        lines.append("## Event Log Highlights")
        for entry in entries[:10]:
            dt = entry.timestamp
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            ts = dt.astimezone(timezone.utc).isoformat()
            message = (entry.message or "").splitlines()[0]
            lines.append(f"- {ts} [{entry.level.value}] {entry.source}: {message}")
    if not dump_analysis and not entries:
        lines.append("(No data available)")
    return "\n".join(lines)


def _load_session(
    session_path: Path, reporter: ConsoleReporter
) -> tuple[DumpFileAnalysis | None, list[EventLogEntry], AnalysisReport | None]:
    try:
        text = session_path.read_text(encoding="utf-8")
    except OSError as exc:  # noqa: PERF203
        raise ValueError(f"セッションファイルにアクセスできません: {session_path}") from exc
    try:
        raw = json.loads(text)
    except json.JSONDecodeError as exc:  # noqa: PERF203
        raise ValueError(f"JSONセッションを読み込めませんでした: {session_path}") from exc

    if not isinstance(raw, dict):
        raise ValueError("保存されたセッションの形式が不正です")

    dump = _deserialize_dump_analysis(raw.get("dump_analysis"))
    events = [_deserialize_event_log_entry(item) for item in raw.get("events", [])]
    report = _deserialize_analysis_report(raw.get("analysis_report"))

    reporter.print_info(f"セッションを読み込みました: {session_path}")
    return dump, events, report


def _deserialize_dump_analysis(payload: dict | None) -> DumpFileAnalysis | None:
    if not payload:
        return None
    data = payload.copy()
    if (ts := data.get("crash_timestamp")):
        data["crash_timestamp"] = datetime.fromisoformat(ts)
    return DumpFileAnalysis(**data)


def _deserialize_event_log_entry(payload: dict) -> EventLogEntry:
    data = payload.copy()
    level_value = data.get("level")
    if level_value is None:
        raise ValueError("Event entry missing level")
    data["level"] = EventLevel(level_value)
    if (ts := data.get("timestamp")):
        data["timestamp"] = datetime.fromisoformat(ts)
    else:
        raise ValueError("Event entry missing timestamp")
    return EventLogEntry(**data)


def _deserialize_analysis_report(payload: dict | None) -> AnalysisReport | None:
    if not payload:
        return None
    data = payload.copy()
    if (ts := data.get("generated_at")):
        data["generated_at"] = datetime.fromisoformat(ts)
    if (confidence := data.get("confidence_level")):
        data["confidence_level"] = ConfidenceLevel(confidence)
    return AnalysisReport(**data)


if __name__ == "__main__":
    main()
