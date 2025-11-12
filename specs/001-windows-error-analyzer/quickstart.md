# Quickstart Guide: Windows Error Analyzer

**Version**: 1.0.0
**Date**: 2025-11-07
**Audience**: Developers and contributors

## Overview

This guide helps developers set up the Windows Error Analyzer development environment and understand the basic workflow for contributing to the project.

---

## Prerequisites

- Python 3.11 or higher
- Git
- OpenAI API key (for testing analysis features)
- Sample .dmp and .evtx files for testing (can be created or use fixtures)

### Recommended Tools

- VS Code with Python extension
- Windows PC (for native testing) or WSL/Linux (for development)
- WinDbg (optional, for understanding dump file structures)

---

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd windows-error-analyzer
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/macOS
source venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Or using requirements
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### 4. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-...
```

### 5. Verify Installation

```bash
# Run tests to verify setup
pytest

# Try the CLI
python -m src.cli --help
```

---

## Project Structure

```
windows-error-analyzer/
├── src/                      # Application source code
│   ├── cli.py               # CLI entry point (Click)
│   ├── parsers/             # File parsing logic
│   │   ├── dump_parser.py   # .dmp file parser
│   │   └── evtx_parser.py   # .evtx file parser
│   ├── models/              # Data models (dataclasses)
│   ├── analyzers/           # Analysis logic
│   │   ├── llm_analyzer.py  # OpenAI integration
│   │   └── correlator.py    # Timestamp correlation
│   ├── reporters/           # Output generation
│   │   ├── markdown_reporter.py
│   │   └── console_reporter.py
│   └── utils/               # Utilities (config, progress, filters)
│
├── tests/                   # Test suite
│   ├── fixtures/            # Sample files for testing
│   ├── unit/               # Unit tests
│   └── integration/        # Integration tests
│
├── specs/                   # Design specifications
│   └── 001-windows-error-analyzer/
│       ├── spec.md          # Feature specification
│       ├── plan.md          # Implementation plan
│       ├── data-model.md    # Data model documentation
│       └── contracts/       # Interface contracts
│
├── pyproject.toml          # Project configuration
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
├── README.md              # User documentation
└── .env.example           # Example environment variables
```

---

## Development Workflow

### Running the CLI (Development Mode)

```bash
# Basic analysis
python -m src.cli analyze \
  --dmp tests/fixtures/sample.dmp \
  --evtx tests/fixtures/sample.evtx \
  --output test_report.md

# Without LLM analysis (faster for testing)
python -m src.cli analyze \
  --dmp tests/fixtures/sample.dmp \
  --evtx tests/fixtures/sample.evtx \
  --no-analyze \
  --output test_extraction.md

# Verbose output for debugging
python -m src.cli analyze \
  --dmp tests/fixtures/sample.dmp \
  --evtx tests/fixtures/sample.evtx \
  --output test_report.md \
  --verbose

# Event logs only with filters
python -m src.cli analyze \
  --evtx tests/fixtures/sample.evtx \
  --filter-level warning \
  --source "Service Control Manager" \
  --start 2025-10-23T00:00:00Z \
  --end   2025-10-24T00:00:00Z

# Dump + events using a relative time window
python -m src.cli analyze \
  --dmp tests/fixtures/sample.dmp \
  --evtx tests/fixtures/sample.evtx \
  --time-window 3600
```

**Filtering tips**

- `--filter-level` accepts `all`, `critical`, `error`, `warning`, `info`, `verbose` (default: `all`).
- `--source` can be specified multiple times to keep only certain providers (case-insensitive).
- Absolute ranges: use `--start` / `--end` with ISO-8601 timestamps (UTC recommended).
- Relative ranges: when `--dmp` is provided, `--time-window` restricts events to ±N seconds around the crash time.

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_dump_parser.py

# Run with verbose output
pytest -v

# Run integration tests only
pytest tests/integration/
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint code
ruff check src/ tests/

# Type checking
mypy src/

# Run all quality checks
black src/ tests/ && ruff check src/ tests/ && mypy src/
```

---

## Common Development Tasks

### Adding a New Parser

1. Create new parser module in `src/parsers/`
2. Implement parser class following existing pattern
3. Add corresponding data model in `src/models/`
4. Write unit tests in `tests/unit/`
5. Add integration test in `tests/integration/`
6. Update CLI to support new file type

**Example**:
```python
# src/parsers/custom_parser.py
from src.models.custom_data import CustomData

class CustomParser:
    def parse(self, file_path: str) -> CustomData:
        # Implementation
        pass
```

### Adding a New CLI Command

1. Add command function in `src/cli.py`
2. Use Click decorators for arguments/options
3. Add tests in `tests/integration/test_cli.py`
4. Update CLI contract documentation

**Example**:
```python
@cli.command()
@click.option('--input', required=True)
def new_command(input: str):
    """New command description"""
    pass
```

### Adding a New Report Format

1. Create reporter in `src/reporters/`
2. Implement `Reporter` interface
3. Add output format option to CLI
4. Write tests for new format

### Testing with Real Files

```bash
# Create test fixtures directory
mkdir -p tests/fixtures/real

# Copy real crash files (anonymize first!)
# Add to .gitignore if sensitive

# Run analysis
python -m src.cli analyze \
  --dmp tests/fixtures/real/crash.dmp \
  --evtx tests/fixtures/real/System.evtx \
  --output debug_report.md \
  --verbose
```

---

## Debugging Tips

### Enable Debug Logging

```python
# In your test or development script
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Inspect Parsed Data

```python
from src.parsers.dump_parser import DumpParser

parser = DumpParser()
dump_analysis = parser.parse("tests/fixtures/sample.dmp")

# Pretty print the data
import pprint
pprint.pprint(dump_analysis.__dict__)
```

### Test LLM Prompts

```python
from src.analyzers.llm_analyzer import LLMAnalyzer

analyzer = LLMAnalyzer(api_key="your-key")

# Test with minimal data
result = analyzer.analyze(
    dump_summary="Test crash",
    events=["Test event"]
)
print(result)
```

---

## Coding Standards

### Python Style

- Follow PEP 8 style guide
- Use type hints for all function signatures
- Use dataclasses for data models
- Maximum line length: 100 characters
- Use f-strings for string formatting

### Documentation

- Every module should have a docstring
- Every public function/class should have docstrings
- Use Google-style docstrings

**Example**:
```python
def parse_dump_file(file_path: str) -> DumpFileAnalysis:
    """Parse a Windows memory dump file.

    Args:
        file_path: Path to the .dmp file to parse

    Returns:
        DumpFileAnalysis object containing extracted information

    Raises:
        FileNotFoundError: If file does not exist
        ParseError: If file cannot be parsed
    """
    pass
```

### Testing

- Aim for 80%+ code coverage
- Write unit tests for business logic
- Write integration tests for workflows
- Use fixtures for test data
- Mock external APIs (OpenAI)

---

## Creating Sample Test Files

### Generate Sample Dump File

You can use Windows Task Manager to create a dump file:

1. Open Task Manager
2. Right-click a process → "Create dump file"
3. Copy to `tests/fixtures/sample.dmp`

**Or create minimal test dump:**
```python
# Use minidump library to create test file
# (Simplified example - actual implementation more complex)
from minidump.minidumpfile import MinidumpFile

# Create minimal valid dump for testing
# See minidump documentation for details
```

### Generate Sample Event Log

Export from Windows Event Viewer:

1. Open Event Viewer
2. Select log (System, Application)
3. Right-click → Save All Events As
4. Save as .evtx format
5. Copy to `tests/fixtures/sample.evtx`

---

## Troubleshooting

### Issue: Import errors after installation

**Solution**: Make sure you're in the virtual environment and installed in editable mode:
```bash
pip install -e .
```

### Issue: OpenAI API errors in tests

**Solution**: Mock the OpenAI client in tests:
```python
from unittest.mock import Mock, patch

@patch('src.analyzers.llm_analyzer.OpenAI')
def test_analysis(mock_openai):
    mock_openai.return_value.chat.completions.create.return_value = Mock(...)
```

### Issue: Can't parse dump files on Linux/macOS

**Solution**: This is expected - minidump library has limited cross-platform support. Use Windows for full testing or use pre-parsed test fixtures.

---

## Contributing

### Before Submitting a PR

1. ✅ Run all tests: `pytest`
2. ✅ Run code quality checks: `black . && ruff check . && mypy src/`
3. ✅ Update documentation if needed
4. ✅ Add tests for new features
5. ✅ Update CHANGELOG.md

### Pull Request Process

1. Create feature branch: `git checkout -b feature/description`
2. Make changes with clear commit messages
3. Push and create PR with description
4. Address review feedback
5. Squash commits if requested

---

## Resources

### Documentation

- [Feature Specification](./spec.md)
- [Implementation Plan](./plan.md)
- [Data Model](./data-model.md)
- [CLI Contract](./contracts/cli-interface.md)

### External Resources

- [minidump library docs](https://github.com/skelsec/minidump)
- [python-evtx docs](https://github.com/williballenthin/python-evtx)
- [OpenAI Python SDK](https://github.com/openai/openai-python)
- [Click documentation](https://click.palletsprojects.com/)
- [Rich documentation](https://rich.readthedocs.io/)

### Windows Debugging

- [WinDbg documentation](https://docs.microsoft.com/en-us/windows-hardware/drivers/debugger/)
- [Understanding Windows crash dumps](https://docs.microsoft.com/en-us/windows/win32/debug/crash-dump-analysis)
- [Windows Event Log format](https://docs.microsoft.com/en-us/windows/win32/wes/windows-event-log)

---

## Next Steps

After completing this quickstart:

1. Read the [Feature Specification](./spec.md) to understand requirements
2. Review the [Data Model](./data-model.md) to understand data structures
3. Check open issues for good first contributions
4. Join development discussions

## Questions?

- File an issue for bugs or questions
- Check existing documentation in `specs/` directory
- Review test cases for usage examples
