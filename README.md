# Windows Error Analyzer

A Python-based CLI tool that extracts and analyzes crash information from Windows dump files (.dmp) and event logs (.evtx). The tool parses these files to extract structured information, displays it in a human-readable format with filtering capabilities, and leverages OpenAI's API to generate automated analysis reports with root cause identification and remediation recommendations.

## Features

- **Dump File Analysis**: Parse Windows memory dump files (.dmp) and extract crash information
- **Event Log Analysis**: Parse Windows Event Log files (.evtx) and extract events with filtering
- **LLM-Powered Analysis**: Generate automated analysis reports using OpenAI's GPT-4 or GPT-3.5-turbo
- **Rich Terminal Output**: Beautiful formatted output with progress bars and color coding
- **Markdown Export**: Export analysis reports to Markdown format for documentation

## Prerequisites

- Python 3.11 or higher
- OpenAI API key (for analysis features)
- Sample .dmp and .evtx files for testing

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

## Usage

### Basic Analysis

```bash
python -m src.cli analyze \
  --dmp crash.dmp \
  --evtx System.evtx \
  --output report.md
```

### Extract Only (No LLM Analysis)

```bash
python -m src.cli analyze \
  --dmp crash.dmp \
  --evtx System.evtx \
  --no-analyze \
  --output extraction.md
```

### Use GPT-3.5 for Faster Analysis

```bash
python -m src.cli analyze \
  --dmp crash.dmp \
  --evtx System.evtx \
  --model gpt-3.5-turbo \
  --output report.md
```

### Filter Only Critical/Error Events

```bash
python -m src.cli analyze \
  --evtx System.evtx \
  --filter-level error \
  --output events.md
```

### Verbose Output for Debugging

```bash
python -m src.cli analyze \
  --dmp crash.dmp \
  --evtx System.evtx \
  --output report.md \
  --verbose
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_dump_parser.py
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

## Project Structure

```
src/
├── cli.py                    # CLI entry point
├── parsers/                  # File parsing logic
├── models/                   # Data models
├── analyzers/                # Analysis logic
├── reporters/                # Output generation
└── utils/                    # Utilities

tests/
├── fixtures/                 # Sample files
├── unit/                     # Unit tests
└── integration/              # Integration tests
```

## Documentation

- [Feature Specification](specs/001-windows-error-analyzer/spec.md)
- [Implementation Plan](specs/001-windows-error-analyzer/plan.md)
- [Data Model](specs/001-windows-error-analyzer/data-model.md)
- [CLI Contract](specs/001-windows-error-analyzer/contracts/cli-interface.md)
- [Quickstart Guide](specs/001-windows-error-analyzer/quickstart.md)

## License

MIT License
