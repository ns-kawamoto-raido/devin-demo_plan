# CLI Interface Contract: Windows Error Analyzer

**Date**: 2025-11-07
**Tool**: windows-error-analyzer
**Purpose**: Define command-line interface contract for all interactions

## Overview

Windows Error Analyzer is a CLI tool built with Click framework. This document defines the complete CLI interface, including commands, arguments, options, output formats, and exit codes.

---

## Installation and Setup

### Installation
```bash
pip install windows-error-analyzer
```

### Configuration
```bash
# Set OpenAI API key (required for analysis)
export OPENAI_API_KEY="sk-..."

# Or create config file
windows-error-analyzer config --set-api-key
```

---

## Commands

### 1. Main Command: `analyze`

Analyze Windows dump and event log files to generate diagnostic report.

#### Synopsis
```bash
windows-error-analyzer analyze [OPTIONS] --output REPORT.md
```

#### Arguments

None (all inputs via options)

#### Options

| Option | Short | Type | Required | Default | Description |
|--------|-------|------|----------|---------|-------------|
| `--dmp` | `-d` | PATH | No* | None | Path to Windows dump file (.dmp) |
| `--evtx` | `-e` | PATH | No* | None | Path to event log file(s) (.evtx), can be specified multiple times |
| `--output` | `-o` | PATH | Yes | None | Path for output markdown report |
| `--analyze/--no-analyze` | | FLAG | No | `--analyze` | Enable/disable LLM analysis |
| `--model` | `-m` | TEXT | No | `gpt-4` | OpenAI model to use (gpt-4, gpt-3.5-turbo) |
| `--filter-level` | `-f` | CHOICE | No | `error` | Event log filter level (all, critical, error, warning, info) |
| `--time-window` | `-t` | INT | No | 3600 | Time window in seconds around crash (for event filtering) |
| `--verbose` | `-v` | FLAG | No | False | Enable verbose output |
| `--quiet` | `-q` | FLAG | No | False | Suppress progress output (JSON only) |
| `--json` | | FLAG | No | False | Output results as JSON instead of markdown |

\* At least one of `--dmp` or `--evtx` is required

#### Examples

**Basic analysis with dump and event logs:**
```bash
windows-error-analyzer analyze \
  --dmp crash.dmp \
  --evtx System.evtx \
  --evtx Application.evtx \
  --output report.md
```

**Extract only (no LLM analysis):**
```bash
windows-error-analyzer analyze \
  --dmp crash.dmp \
  --evtx System.evtx \
  --no-analyze \
  --output extraction.md
```

**Use GPT-3.5 for faster/cheaper analysis:**
```bash
windows-error-analyzer analyze \
  --dmp crash.dmp \
  --evtx System.evtx \
  --model gpt-3.5-turbo \
  --output report.md
```

**Filter only critical/error events:**
```bash
windows-error-analyzer analyze \
  --evtx System.evtx \
  --filter-level error \
  --output events.md
```

**JSON output for scripting:**
```bash
windows-error-analyzer analyze \
  --dmp crash.dmp \
  --evtx System.evtx \
  --output report.json \
  --json \
  --quiet
```

#### Output (Markdown Format)

```markdown
# Windows Error Analysis Report

**Analysis Date**: 2025-11-07 14:30:00 UTC
**Session ID**: 12345678-1234-1234-1234-123456789012

## Summary

[High-level summary of crash]

## Crash Information

**File**: C:\crashes\crash.dmp
**Timestamp**: 2025-11-06 23:15:42 UTC
**Error Code**: 0xC0000005 (Access Violation)
**Faulting Module**: ntdll.dll
**Process**: MyApp.exe (PID: 4532)

### Stack Trace

```
ntdll.dll!RtlUserThreadStart+0x21
kernel32.dll!BaseThreadInitThunk+0x14
MyApp.exe!main+0x123
...
```

## Event Log Timeline

| Time | Level | Source | Event ID | Message |
|------|-------|--------|----------|---------|
| 23:15:40 | Warning | Application | 1000 | Application error detected |
| 23:15:42 | Critical | System | 1001 | System crash detected |

## AI Analysis

### Root Cause

[LLM-generated root cause analysis]

### Detailed Analysis

[LLM-generated detailed technical analysis]

### Recommended Actions

1. [Action item 1]
2. [Action item 2]
3. [Action item 3]

## Analysis Metadata

- **Model Used**: gpt-4
- **Confidence**: High
- **Processing Time**: 45.2 seconds
- **Tokens Used**: 3,245
```

#### Output (JSON Format)

```json
{
  "session_id": "12345678-1234-1234-1234-123456789012",
  "analysis_date": "2025-11-07T14:30:00Z",
  "dump_analysis": {
    "file_path": "C:\\crashes\\crash.dmp",
    "crash_timestamp": "2025-11-06T23:15:42Z",
    "error_code": "0xC0000005",
    "faulting_module": "ntdll.dll",
    "process_name": "MyApp.exe",
    "process_id": 4532,
    "stack_trace": ["ntdll.dll!RtlUserThreadStart+0x21", "..."]
  },
  "event_entries": [
    {
      "timestamp": "2025-11-06T23:15:40Z",
      "level": "Warning",
      "source": "Application",
      "event_id": 1000,
      "message": "Application error detected"
    }
  ],
  "analysis_report": {
    "root_cause_summary": "...",
    "detailed_analysis": "...",
    "remediation_steps": ["...", "...", "..."],
    "confidence_level": "High",
    "model_used": "gpt-4",
    "token_usage": 3245,
    "processing_time_seconds": 45.2
  }
}
```

#### Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 0 | Success | Analysis completed successfully |
| 1 | Invalid arguments | Missing required arguments or invalid file paths |
| 2 | File not found | Input file(s) do not exist |
| 3 | Parsing error | Failed to parse dump or event log file |
| 4 | API error | OpenAI API authentication or quota error |
| 5 | Network error | Unable to connect to OpenAI API |
| 10 | Internal error | Unexpected error occurred |

---

### 2. Configuration Command: `config`

Manage tool configuration and API keys.

#### Synopsis
```bash
windows-error-analyzer config [OPTIONS]
```

#### Options

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `--set-api-key` | FLAG | No | Prompt for OpenAI API key and save to config |
| `--show-config` | FLAG | No | Display current configuration |
| `--reset` | FLAG | No | Reset configuration to defaults |

#### Examples

```bash
# Set API key interactively
windows-error-analyzer config --set-api-key

# Show current configuration
windows-error-analyzer config --show-config

# Reset to defaults
windows-error-analyzer config --reset
```

---

### 3. Version Command: `version`

Display tool version information.

#### Synopsis
```bash
windows-error-analyzer version
```

#### Output
```
Windows Error Analyzer v1.0.0
Python: 3.11.5
Dependencies:
  - minidump: 0.0.21
  - python-evtx: 0.7.4
  - openai: 1.3.5
  - click: 8.1.7
  - rich: 13.7.0
```

---

### 4. Help Command

Display help information.

#### Synopsis
```bash
windows-error-analyzer --help
windows-error-analyzer analyze --help
windows-error-analyzer config --help
```

---

## Progress Output (stderr)

When not in quiet mode, progress is displayed using Rich library:

```
Parsing dump file... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:15
Parsing event logs... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 100% 0:00:08
Filtering events... ⠋ Found 15 relevant events
Analyzing with AI... ⠙ Waiting for OpenAI response...
✓ Analysis complete! Report saved to: report.md
```

---

## Error Messages

Error messages are printed to stderr with clear actionable guidance:

**Missing API key:**
```
Error: OpenAI API key not found.
Please set OPENAI_API_KEY environment variable or run:
  windows-error-analyzer config --set-api-key
```

**Invalid file:**
```
Error: Cannot read dump file: C:\crashes\crash.dmp
File does not exist or is not accessible.
```

**Corrupted file:**
```
Warning: Dump file parsing encountered 3 errors.
Partial information extracted. Analysis may be limited.
See report for details.
```

**API quota exceeded:**
```
Error: OpenAI API quota exceeded.
Please check your API usage at https://platform.openai.com/usage
```

---

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OPENAI_API_KEY` | Yes (for analysis) | None | OpenAI API key for LLM analysis |
| `WINDOWS_ERROR_ANALYZER_CONFIG` | No | `~/.windows-error-analyzer/config.json` | Path to configuration file |
| `WINDOWS_ERROR_ANALYZER_CACHE` | No | `~/.windows-error-analyzer/cache/` | Cache directory for temp files |

---

## Configuration File

Location: `~/.windows-error-analyzer/config.json`

Format:
```json
{
  "api_key": "sk-...",
  "default_model": "gpt-4",
  "default_filter_level": "error",
  "default_time_window": 3600
}
```

---

## Contract Testing

### Required Test Scenarios

1. **Valid invocation**: All required arguments provided, files exist
2. **Missing required args**: Should exit with code 1 and helpful message
3. **File not found**: Should exit with code 2 and clear error
4. **Invalid file format**: Should exit with code 3 and partial results if possible
5. **API key missing**: Should exit with code 4 and setup instructions
6. **Network failure**: Should exit with code 5 and retry guidance
7. **Progress output**: Verify rich progress bars appear (not in quiet mode)
8. **JSON output**: Verify parseable JSON structure
9. **Multiple evtx files**: Verify chronological merging
10. **No-analyze mode**: Verify extraction works without API calls

### Example Integration Test

```python
def test_cli_analyze_basic():
    result = subprocess.run([
        "windows-error-analyzer", "analyze",
        "--dmp", "tests/fixtures/sample.dmp",
        "--evtx", "tests/fixtures/sample.evtx",
        "--output", "test_report.md",
        "--no-analyze"  # Skip API for testing
    ], capture_output=True)

    assert result.returncode == 0
    assert os.path.exists("test_report.md")
    assert "Crash Information" in open("test_report.md").read()
```

---

## Backward Compatibility

**Versioning**: Follow semantic versioning (MAJOR.MINOR.PATCH)

**Breaking Changes**:
- CLI option removals or renames → MAJOR version bump
- Exit code changes → MAJOR version bump
- Output format changes → MINOR version bump (keep old format optional)

**Deprecation Process**:
1. Mark feature as deprecated in help text
2. Print warning when used
3. Maintain for at least 2 MINOR versions
4. Remove in next MAJOR version
