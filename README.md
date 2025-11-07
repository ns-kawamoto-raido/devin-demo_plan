# Windows Error Analyzer

A Python-based CLI tool that extracts and analyzes crash information from Windows dump files (.dmp) and event logs (.evtx).

## Features

### User Story 1: Extract and Display Dump File Contents ✅

Extract and display information from Windows memory dump files (.dmp), including:
- Crash information (error codes, crash type, timestamp)
- Faulting module and address
- Process information
- System information (OS version, architecture)
- Stack traces
- Loaded modules

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ns-kawamoto-raido/devin-demo_plan.git
cd devin-demo_plan
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Analyze a Dump File

Extract and display information from a Windows dump file:

```bash
python -m src.cli analyze --dmp /path/to/crash.dmp
```

With verbose output:

```bash
python -m src.cli analyze --dmp /path/to/crash.dmp --verbose
```

### Example Output

```
╭─────────────────────────────────────╮
│ Windows Dump File Analysis          │
╰─────────────────────────────────────╯

Crash Summary
─────────────────────────────────────
File Path              /path/to/crash.dmp
File Size              1,234,567 bytes
Crash Timestamp        2025-11-07 08:30:15 UTC
Crash Type             EXCEPTION
Error Code             0xC0000005
Process Name           myapp.exe
Thread ID              1234
Faulting Module        kernel32.dll
Faulting Address       0x00007FF812345678

System Information
─────────────────────────────────────
OS Version             Windows 10 Build 19045
Architecture           x64

Stack Trace:
  1. Stack memory region: 0x000000000012F000
  2. Stack size: 4096 bytes

Loaded Modules (15):
  1. myapp.exe
  2. ntdll.dll
  3. kernel32.dll
  ...

✓ Analysis complete!
```

## Testing

Run the test suite:

```bash
pytest tests/
```

Run tests with coverage:

```bash
pytest --cov=src tests/
```

## Development

### Project Structure

```
devin-demo_plan/
├── src/
│   ├── models/           # Data models
│   │   └── dump_analysis.py
│   ├── parsers/          # File parsers
│   │   └── dump_parser.py
│   ├── reporters/        # Output formatters
│   │   └── console_reporter.py
│   └── cli.py           # CLI interface
├── tests/
│   ├── unit/            # Unit tests
│   └── fixtures/        # Test data
├── requirements.txt     # Python dependencies
└── README.md
```

### Running Lint Checks

```bash
ruff check .
```

## Requirements

- Python 3.11+
- minidump >= 0.0.21
- click >= 8.0.0
- rich >= 13.0.0
- pytest >= 8.0.0 (for testing)

## Roadmap

- [x] User Story 1: Extract and display dump file contents
- [ ] User Story 2: Extract and display event log contents
- [ ] User Story 3: Generate LLM-powered analysis reports
- [ ] User Story 4: Save and export analysis results

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
