# Demo: User Story 1 - Dump File Extraction

This document demonstrates the implementation of User Story 1: "Extraction and display of dmp file contents".

## Implementation Overview

The implementation includes:

1. **Data Model** (`src/models/dump_analysis.py`):
   - `DumpFileAnalysis` dataclass with validation
   - Fields for crash information, system info, stack traces, and loaded modules

2. **Parser** (`src/parsers/dump_parser.py`):
   - `DumpParser` class using the minidump library
   - Extracts crash information from .dmp files
   - Handles errors gracefully with clear error messages

3. **Reporter** (`src/reporters/console_reporter.py`):
   - `ConsoleReporter` class using Rich library
   - Formatted console output with tables and colors
   - Displays crash summary, system info, stack traces, and modules

4. **CLI** (`src/cli.py`):
   - Click-based command-line interface
   - `analyze` command with `--dmp` option
   - Proper error handling and exit codes

## Testing with Actual .dmp Files

The implementation can be tested with actual Windows dump files:

### Prerequisites

You need a Windows .dmp file to test. These can be obtained from:
- Windows crash dumps (typically in `C:\Windows\Minidump\`)
- Application crash dumps
- Generated test dumps

### Running the Demo

1. **Basic Analysis**:
```bash
python -m src.cli analyze --dmp /path/to/your/crash.dmp
```

2. **Verbose Mode**:
```bash
python -m src.cli analyze --dmp /path/to/your/crash.dmp --verbose
```

### Expected Output

The tool will display:
- ✅ File path and size
- ✅ Crash timestamp
- ✅ Crash type (EXCEPTION, etc.)
- ✅ Error code (if available)
- ✅ Process name and IDs
- ✅ Faulting module and address (if available)
- ✅ OS version and architecture
- ✅ Stack trace information
- ✅ List of loaded modules

### Error Handling

The implementation handles various error scenarios:

1. **File Not Found**:
```bash
$ python -m src.cli analyze --dmp /nonexistent/file.dmp
Error: Dump file not found: /nonexistent/file.dmp
```

2. **Invalid Dump File**:
```bash
$ python -m src.cli analyze --dmp /path/to/invalid.dmp
Error: Failed to parse dump file: [error details]
```

3. **Empty File**:
```bash
$ python -m src.cli analyze --dmp /path/to/empty.dmp
Error: Dump file is empty: /path/to/empty.dmp
```

## Unit Tests

The implementation includes comprehensive unit tests:

```bash
# Run all tests
pytest tests/

# Run specific test files
pytest tests/unit/test_dump_analysis.py
pytest tests/unit/test_dump_parser.py

# Run with verbose output
pytest tests/ -v
```

### Test Coverage

- ✅ Data model validation
- ✅ Parser initialization
- ✅ File existence validation
- ✅ Empty file handling
- ✅ Invalid file handling
- ✅ Error code detection
- ✅ Stack trace detection

## Acceptance Criteria

User Story 1 acceptance scenarios are met:

1. ✅ **Given** a valid .dmp file from a Windows crash, **When** the user loads it into the tool, **Then** the tool extracts and displays crash information including error codes, faulting module, and timestamp

2. ✅ **Given** a large .dmp file (>1GB), **When** the user loads it, **Then** the tool processes it without hanging (streaming approach used)

3. ✅ **Given** a corrupted or invalid .dmp file, **When** the user attempts to load it, **Then** the tool displays a clear error message explaining the file cannot be processed

## Independent Testing

This implementation can be tested independently without requiring:
- Event log files (.evtx)
- LLM analysis
- Network connectivity
- External services

Simply provide a .dmp file and the tool will extract and display its contents.

## Next Steps

Future user stories will add:
- Event log extraction and display (User Story 2)
- LLM-powered analysis (User Story 3)
- Export functionality (User Story 4)
