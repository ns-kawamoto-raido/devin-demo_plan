# Research: Windows Error Analyzer

**Date**: 2025-11-07
**Feature**: Windows Error Analyzer
**Purpose**: Resolve technical uncertainties and validate technology choices

## Research Items

### 1. Best Library for .dmp (Windows Dump) File Parsing

**Question**: Which Python library should we use for parsing Windows memory dump files?

**Options Evaluated**:

1. **minidump** (by Chromium project)
   - Pure Python implementation
   - Well-maintained, used in production by Google
   - Supports reading minidump format structures
   - Limited to basic minidump information extraction

2. **minidump-py**
   - Less active maintenance
   - Simpler API but fewer features
   - May not support all dump file variations

3. **WinDbg wrapper** (via subprocess)
   - Most powerful and complete solution
   - Requires WinDbg installation on Windows
   - Can extract comprehensive crash analysis
   - Cross-platform development challenge (WinDbg Windows-only)

**Decision**: Use **minidump** library with optional WinDbg integration

**Rationale**:
- **minidump** provides pure Python parsing for core functionality (P1 requirement)
- Cross-platform development support (developers can work on Linux/macOS)
- Meets FR-001 requirements for basic crash info extraction
- Can add WinDbg integration later as enhancement for deeper analysis
- Well-maintained with active community

**Implementation Strategy**:
```python
# Primary: minidump library
from minidump.minidumpfile import MinidumpFile

# Optional: WinDbg wrapper for enhanced analysis (future enhancement)
# Detect if WinDbg is available and use for deeper stack analysis
```

**Alternatives Considered**:
- Pure WinDbg approach: Rejected due to cross-platform development requirement and installation dependency
- minidump-py: Rejected due to limited maintenance and feature set

---

### 2. Batch Processing Support

**Question**: Should the tool support batch processing multiple dump/event log pairs in one invocation?

**Context**: From Technical Context - "Should tool support batch processing multiple dump/event log pairs in one invocation?"

**Decision**: Start with **single session mode**, design for future batch support

**Rationale**:
- User scenarios (spec) describe single-session analysis workflow
- Success criteria (SC-001, SC-002) measure single-file processing performance
- MVP should focus on core analysis quality over throughput
- Single session reduces initial complexity
- Can add batch mode in later iteration without breaking changes

**Implementation Strategy**:
```bash
# Phase 1: Single session
windows-error-analyzer analyze --dmp crash.dmp --evtx system.evtx --output report.md

# Future: Batch mode (not in MVP)
windows-error-analyzer batch --input-dir ./crashes/ --output-dir ./reports/
```

**Design Consideration**:
- Keep analysis logic session-independent (no shared state)
- Makes future batch implementation straightforward
- CLI can be extended with new `batch` subcommand

**Alternatives Considered**:
- Batch mode first: Rejected as unnecessary complexity for MVP
- Multiple files via multiple CLI args: Confusing UX, rejected

---

### 3. Event Log Parsing Best Practices

**Question**: Best approach for parsing .evtx files with python-evtx library?

**Research Findings**:

**Library**: `python-evtx` (by Willi Ballenthin)
- Pure Python implementation of Windows Event Log parser
- No external dependencies
- Handles binary .evtx format
- Supports event iteration and XML extraction

**Best Practices**:
1. **Streaming for large files**: Use iterator pattern to avoid loading entire file into memory
2. **Error handling**: Handle corrupted records gracefully (continue parsing valid records)
3. **Timezone handling**: Event timestamps are in UTC, may need local time conversion for correlation
4. **Event filtering**: Filter at parse time (not post-parse) for better performance

**Code Pattern**:
```python
import Evtx.Evtx as evtx

def parse_evtx(file_path):
    with evtx.Evtx(file_path) as log:
        for record in log.records():
            # Stream processing - low memory footprint
            try:
                yield parse_event_record(record)
            except Exception as e:
                # Continue on corrupted records (FR-009)
                logger.warning(f"Skipped corrupted record: {e}")
                continue
```

**Performance Optimization**:
- Use generators for memory efficiency (handle millions of events)
- Early filtering by event level (Error, Critical) before full parsing
- Lazy XML parsing only when event details needed

---

### 4. OpenAI API Integration Best Practices

**Question**: How should we structure OpenAI API calls for dump/log analysis?

**Research Findings**:

**Library**: `openai` (official Python client) v1.0+

**Best Practices**:

1. **Token Management**:
   - Dump files can be large; need intelligent summarization before sending to API
   - Extract key information: error codes, module names, stack traces (top 10-20 frames)
   - Event logs: Filter to errors/warnings within ±1 hour of crash timestamp
   - Estimated token usage: 2000-5000 tokens per analysis

2. **Prompt Engineering**:
   - System prompt: Define role as Windows error diagnostic expert
   - User prompt: Structured format with sections (dump summary, event timeline, question)
   - Request specific output format (markdown with sections)

3. **Error Handling**:
   - API rate limits: Implement exponential backoff
   - API timeout: 60 second timeout for analysis requests
   - Fallback: Save extracted data if API fails (user can retry)

4. **Model Selection**:
   - Default: GPT-4 (best reasoning for technical analysis)
   - Fallback: GPT-3.5-turbo (faster, cheaper, configurable)
   - Make model configurable via CLI option

**Code Pattern**:
```python
from openai import OpenAI

client = OpenAI(api_key=config.api_key)

def analyze_crash(dump_summary: str, events: list[str]) -> str:
    prompt = f"""
    Analyze this Windows crash:

    ## Dump File Summary
    {dump_summary}

    ## Related Event Log Entries
    {format_events(events)}

    Provide:
    1. Root cause analysis
    2. Timeline of events
    3. Recommended remediation steps
    """

    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a Windows error diagnostic expert..."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,  # Lower temperature for factual analysis
        max_tokens=2000
    )

    return response.choices[0].message.content
```

**Configuration**:
- API key from environment variable `OPENAI_API_KEY` or config file
- Model selection via CLI: `--model gpt-4` or `--model gpt-3.5-turbo`
- Token budget awareness (warn user if analysis will be expensive)

---

### 5. Progress Feedback with Rich Library

**Question**: How to implement progress bars and status updates for long operations?

**Research Findings**:

**Library**: `rich` (by Will McGugan)
- Modern terminal formatting library
- Built-in progress bars, spinners, status messages
- Supports concurrent progress tracking
- Cross-platform (Windows, Linux, macOS)

**Implementation Strategy**:

```python
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.console import Console

console = Console()

# For file parsing (deterministic progress)
with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    TimeRemainingColumn()
) as progress:
    task = progress.add_task("Parsing dump file...", total=file_size)
    # Update as parsing progresses
    progress.update(task, advance=chunk_size)

# For LLM analysis (indeterminate progress)
with console.status("[bold green]Analyzing crash with AI...", spinner="dots"):
    result = llm_analyzer.analyze(dump, events)
```

**Features to Implement**:
- File parsing: Progress bar with percentage and ETA
- LLM API calls: Spinner with status message
- Event filtering: Progress for large event log processing
- Final output: Success message with report location

---

## Summary

All technical uncertainties have been resolved:

1. ✅ **Dump parsing**: minidump library (pure Python, cross-platform)
2. ✅ **Batch processing**: Single session for MVP, designed for future expansion
3. ✅ **Event log parsing**: python-evtx with streaming pattern
4. ✅ **OpenAI integration**: Official client with GPT-4, structured prompts, configurable
5. ✅ **Progress feedback**: Rich library for professional CLI experience

**Next Phase**: Proceed to Phase 1 (data models and contracts)
