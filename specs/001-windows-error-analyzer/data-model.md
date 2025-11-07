# Data Model: Windows Error Analyzer

**Date**: 2025-11-07
**Feature**: Windows Error Analyzer
**Purpose**: Define core data structures and their relationships

## Overview

This document defines the data models used throughout the Windows Error Analyzer application. All models are implemented as Python dataclasses with type hints for clarity and IDE support.

---

## Core Data Models

### 1. DumpFileAnalysis

Represents extracted information from a Windows memory dump file (.dmp).

**Purpose**: Store structured crash information parsed from dump files

**Fields**:

| Field | Type | Description | Required | Validation |
|-------|------|-------------|----------|------------|
| `file_path` | `str` | Original path to the .dmp file | Yes | Must be valid file path |
| `file_size_bytes` | `int` | Size of dump file in bytes | Yes | Must be > 0 |
| `crash_timestamp` | `datetime` | When the crash occurred (from dump) | Yes | Must be valid datetime |
| `crash_type` | `str` | Type of crash (e.g., "EXCEPTION", "ASSERTION") | Yes | Non-empty string |
| `error_code` | `str` | Hex error code (e.g., "0xC0000005") | No | Format: 0xHHHHHHHH |
| `faulting_module` | `str` | Name of module that caused crash | No | Non-empty string |
| `faulting_address` | `str` | Memory address where fault occurred | No | Format: 0xHHHHHHHH |
| `process_name` | `str` | Name of crashed process | Yes | Non-empty string |
| `process_id` | `int` | Process ID | No | Must be > 0 |
| `thread_id` | `int` | Faulting thread ID | No | Must be > 0 |
| `os_version` | `str` | Windows version (e.g., "Windows 10 Build 19045") | Yes | Non-empty string |
| `architecture` | `str` | System architecture (e.g., "x64", "x86") | Yes | "x64" or "x86" |
| `stack_trace` | `list[str]` | Stack trace frames (top 20) | No | List of strings |
| `loaded_modules` | `list[str]` | List of loaded module names | No | List of strings |
| `system_uptime_seconds` | `int` | System uptime at crash | No | Must be >= 0 |
| `parsing_errors` | `list[str]` | Errors encountered during parsing | No | List of error messages |

**Example**:
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class DumpFileAnalysis:
    file_path: str
    file_size_bytes: int
    crash_timestamp: datetime
    crash_type: str
    process_name: str
    os_version: str
    architecture: str
    error_code: str | None = None
    faulting_module: str | None = None
    faulting_address: str | None = None
    process_id: int | None = None
    thread_id: int | None = None
    stack_trace: list[str] = None
    loaded_modules: list[str] = None
    system_uptime_seconds: int | None = None
    parsing_errors: list[str] = None

    def __post_init__(self):
        if self.stack_trace is None:
            self.stack_trace = []
        if self.loaded_modules is None:
            self.loaded_modules = []
        if self.parsing_errors is None:
            self.parsing_errors = []
```

**Relationships**:
- One DumpFileAnalysis per AnalysisSession
- Referenced by AnalysisReport for crash context

---

### 2. EventLogEntry

Represents a single Windows event log entry from a .evtx file.

**Purpose**: Store structured event information with filtering support

**Fields**:

| Field | Type | Description | Required | Validation |
|-------|------|-------------|----------|------------|
| `record_number` | `int` | Unique event record number | Yes | Must be > 0 |
| `timestamp` | `datetime` | When event occurred (UTC) | Yes | Valid datetime |
| `event_id` | `int` | Windows Event ID | Yes | Must be > 0 |
| `source` | `str` | Event source/provider name | Yes | Non-empty string |
| `level` | `str` | Severity level | Yes | One of: "Critical", "Error", "Warning", "Information", "Verbose" |
| `category` | `str` | Event category | No | Non-empty string |
| `message` | `str` | Event message text | Yes | Non-empty string |
| `computer_name` | `str` | Name of computer that generated event | No | Non-empty string |
| `user_sid` | `str` | Security identifier of user | No | Valid SID format |
| `file_path` | `str` | Original .evtx file path | Yes | Valid file path |

**Example**:
```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class EventLevel(Enum):
    CRITICAL = "Critical"
    ERROR = "Error"
    WARNING = "Warning"
    INFORMATION = "Information"
    VERBOSE = "Verbose"

@dataclass
class EventLogEntry:
    record_number: int
    timestamp: datetime
    event_id: int
    source: str
    level: EventLevel
    message: str
    file_path: str
    category: str | None = None
    computer_name: str | None = None
    user_sid: str | None = None

    def is_error_or_critical(self) -> bool:
        return self.level in (EventLevel.CRITICAL, EventLevel.ERROR)

    def within_time_range(self, start: datetime, end: datetime) -> bool:
        return start <= self.timestamp <= end
```

**Relationships**:
- Multiple EventLogEntry objects per AnalysisSession
- Filtered and correlated with DumpFileAnalysis timestamp
- Referenced by AnalysisReport for timeline

---

### 3. AnalysisReport

Represents the LLM-generated analysis report.

**Purpose**: Store structured analysis results for output and export

**Fields**:

| Field | Type | Description | Required | Validation |
|-------|------|-------------|----------|------------|
| `session_id` | `str` | UUID of analysis session | Yes | Valid UUID format |
| `generated_at` | `datetime` | When report was generated | Yes | Valid datetime |
| `model_used` | `str` | OpenAI model name | Yes | e.g., "gpt-4", "gpt-3.5-turbo" |
| `root_cause_summary` | `str` | High-level explanation of crash cause | Yes | Non-empty string |
| `detailed_analysis` | `str` | Detailed technical analysis | Yes | Non-empty string |
| `event_timeline` | `list[str]` | Chronological timeline of relevant events | Yes | List of timeline items |
| `remediation_steps` | `list[str]` | Recommended actions to fix issue | Yes | List of action items |
| `confidence_level` | `str` | LLM confidence in analysis | No | "High", "Medium", "Low" |
| `limitations` | `list[str]` | Known limitations of analysis | No | List of limitation notes |
| `token_usage` | `int` | OpenAI API tokens consumed | No | Must be >= 0 |
| `processing_time_seconds` | `float` | Time taken to generate report | Yes | Must be > 0 |

**Example**:
```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

class ConfidenceLevel(Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"

@dataclass
class AnalysisReport:
    session_id: str
    generated_at: datetime
    model_used: str
    root_cause_summary: str
    detailed_analysis: str
    event_timeline: list[str]
    remediation_steps: list[str]
    processing_time_seconds: float
    confidence_level: ConfidenceLevel | None = None
    limitations: list[str] = None
    token_usage: int | None = None

    def __post_init__(self):
        if self.limitations is None:
            self.limitations = []

    def to_markdown(self) -> str:
        """Generate markdown representation of report"""
        # Implementation in markdown_reporter.py
        pass
```

**Relationships**:
- One AnalysisReport per AnalysisSession
- References DumpFileAnalysis and EventLogEntry data

---

### 4. AnalysisSession

Represents a complete diagnostic session.

**Purpose**: Aggregate all analysis artifacts for a single invocation

**Fields**:

| Field | Type | Description | Required | Validation |
|-------|------|-------------|----------|------------|
| `session_id` | `str` | Unique session identifier (UUID) | Yes | Valid UUID format |
| `created_at` | `datetime` | When session was created | Yes | Valid datetime |
| `dump_analysis` | `DumpFileAnalysis` | Parsed dump file data | No | Valid DumpFileAnalysis |
| `event_entries` | `list[EventLogEntry]` | Parsed event log entries | Yes | List of EventLogEntry |
| `analysis_report` | `AnalysisReport` | Generated analysis report | No | Valid AnalysisReport |
| `output_file_path` | `str` | Path to generated markdown report | No | Valid file path |
| `status` | `str` | Session status | Yes | One of: "parsing", "analyzing", "completed", "failed" |
| `error_message` | `str` | Error message if failed | No | Non-empty string |

**Example**:
```python
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import uuid

class SessionStatus(Enum):
    PARSING = "parsing"
    ANALYZING = "analyzing"
    COMPLETED = "completed"
    FAILED = "failed"

@dataclass
class AnalysisSession:
    session_id: str
    created_at: datetime
    event_entries: list[EventLogEntry]
    status: SessionStatus
    dump_analysis: DumpFileAnalysis | None = None
    analysis_report: AnalysisReport | None = None
    output_file_path: str | None = None
    error_message: str | None = None

    @classmethod
    def create_new(cls) -> "AnalysisSession":
        return cls(
            session_id=str(uuid.uuid4()),
            created_at=datetime.utcnow(),
            event_entries=[],
            status=SessionStatus.PARSING
        )

    def has_dump_file(self) -> bool:
        return self.dump_analysis is not None

    def has_analysis_report(self) -> bool:
        return self.analysis_report is not None

    def total_events(self) -> int:
        return len(self.event_entries)

    def error_events_count(self) -> int:
        return sum(1 for e in self.event_entries if e.is_error_or_critical())
```

**Relationships**:
- Contains one DumpFileAnalysis (optional)
- Contains multiple EventLogEntry objects
- Contains one AnalysisReport (optional)
- Root object for entire analysis workflow

---

## Data Flow

```text
Input Files
    ↓
┌─────────────────────────────────────────┐
│  Parsing Layer                          │
│  - dump_parser.py → DumpFileAnalysis    │
│  - evtx_parser.py → EventLogEntry[]     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  AnalysisSession                        │
│  - Aggregates all data                  │
│  - Manages workflow state               │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Analysis Layer                         │
│  - correlator.py (timestamp correlation)│
│  - llm_analyzer.py → AnalysisReport     │
└─────────────────────────────────────────┘
    ↓
┌─────────────────────────────────────────┐
│  Reporting Layer                        │
│  - markdown_reporter.py (file export)   │
│  - console_reporter.py (terminal output)│
└─────────────────────────────────────────┘
    ↓
Output Files (Markdown)
```

---

## Validation Rules

### Cross-Entity Validation

1. **Timestamp Correlation**:
   - Event log timestamps should be within reasonable range of dump crash timestamp (±24 hours warning if outside)
   - UTC consistency required across all timestamps

2. **File References**:
   - All file_path fields must point to existing files during parsing
   - Validate file exists before creating model instances

3. **Status Transitions**:
   - AnalysisSession.status must follow valid state machine:
     - `parsing → analyzing → completed`
     - `parsing → failed`
     - `analyzing → failed`

4. **Required Data for Analysis**:
   - AnalysisReport requires either DumpFileAnalysis OR at least one error/critical EventLogEntry
   - If only events (no dump), warn user about limited context

---

## Implementation Notes

### Type Safety

All models use Python type hints for IDE support and runtime validation. Consider using `pydantic` for enhanced validation if complexity increases.

### Serialization

Models should support:
- JSON serialization for debugging and session persistence
- Dataclass `asdict()` for conversion to dictionaries
- Custom `__str__` methods for human-readable representation

### Memory Management

For large event logs (millions of entries):
- Use generators where possible (don't materialize full list)
- Filter events early (only keep relevant events in memory)
- Consider streaming directly to report without full materialization

### Future Extensions

Designed to accommodate:
- Additional dump file formats (kernel dumps, full dumps)
- Custom event log filters
- Multiple analysis report formats
- Session persistence (save/load sessions)
