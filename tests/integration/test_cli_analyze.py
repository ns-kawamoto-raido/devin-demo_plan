from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CLI = [sys.executable, "-m", "src.cli", "analyze"]


def _run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, check=True)


def test_analyze_dump_only(tmp_path):
    dmp = PROJECT_ROOT / "sample" / "sample.dmp"
    result = _run(CLI + ["--dmp", str(dmp)])
    assert "Windows Dump File Analysis" in result.stdout
    assert "Analysis complete" in result.stdout


def test_analyze_events_only_with_filters(tmp_path):
    evtx = PROJECT_ROOT / "sample" / "sample.evtx"
    result = _run(
        CLI
        + [
            "--evtx",
            str(evtx),
            "--filter-level",
            "error",
            "--start",
            "2025-10-23T00:00:00Z",
            "--end",
            "2025-10-24T00:00:00Z",
        ]
    )
    assert "Event Logs" in result.stdout
    assert "Analysis complete" in result.stdout


def test_analyze_dump_and_events_time_window(tmp_path):
    dmp = PROJECT_ROOT / "sample" / "sample.dmp"
    evtx = PROJECT_ROOT / "sample" / "sample.evtx"
    result = _run(CLI + ["--dmp", str(dmp), "--evtx", str(evtx), "--time-window", "3600"])
    assert "Windows Dump File Analysis" in result.stdout
    assert "Event Logs" in result.stdout
    assert "Analysis complete" in result.stdout


def test_analyze_dump_with_markdown_output(tmp_path):
    dmp = PROJECT_ROOT / "sample" / "sample.dmp"
    out_file = tmp_path / "report.md"
    result = _run(
        CLI + ["--dmp", str(dmp), "--output", str(out_file), "--no-analyze"]
    )
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "# Windows Error Analysis" in content
    assert "Analysis complete" in result.stdout


def test_analyze_json_export_and_reload(tmp_path):
    dmp = PROJECT_ROOT / "sample" / "sample.dmp"
    evtx = PROJECT_ROOT / "sample" / "sample.evtx"
    session_file = tmp_path / "session.json"
    _run(
        CLI
        + [
            "--dmp",
            str(dmp),
            "--evtx",
            str(evtx),
            "--output",
            str(session_file),
            "--json",
            "--no-analyze",
        ]
    )
    assert session_file.exists()
    data = json.loads(session_file.read_text(encoding="utf-8"))
    assert data["dump_analysis"]["file_path"].endswith("sample.dmp")
    assert len(data["events"]) > 0

    result = _run(CLI + ["--load", str(session_file)])
    assert "Windows Dump File Analysis" in result.stdout
    assert "Event Logs" in result.stdout
