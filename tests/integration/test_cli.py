"""Integration tests for CLI."""

import subprocess
import sys


def test_cli_help() -> None:
    """Test CLI help command."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Windows Error Analyzer" in result.stdout


def test_cli_version() -> None:
    """Test CLI version command."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "Windows Error Analyzer" in result.stdout


def test_cli_analyze_missing_args() -> None:
    """Test CLI analyze command with missing arguments."""
    result = subprocess.run(
        [sys.executable, "-m", "src.cli", "analyze"],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
