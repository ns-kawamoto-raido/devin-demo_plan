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

### User Story 2: Extract and Display Event Log Contents (in progress)

Stream .evtx files and render human-readable tables with:
- Chronological ordering, JST timestamps, and Rich formatting
- Filtering by severity (--filter-level), source (--source), and time window/absolute range
- Support for multiple files merged on timestamp
- Graceful handling of corrupted records (skip & warn)

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

### Analyze Event Logs

Parse one or more `.evtx` files without a dump input:

```bash
python -m src.cli analyze \
  --evtx sample/Application.evtx \
  --evtx sample/System.evtx \
  --filter-level error \
  --source "Service Control Manager" \
  --start 2025-10-23T00:00:00Z \
  --end   2025-10-24T00:00:00Z
```

Key options:

- `--filter-level`: `all`, `critical`, `error`, `warning`, `info`, `verbose` (default: `all`)
- `--source`: repeatable option to keep only specific providers (case-insensitive)
- `--start` / `--end`: absolute UTC window (ISO-8601) for event timestamps

### Combine Dump & Event Logs

When a dump file is provided, you can set a relative window around the crash timestamp:

```bash
python -m src.cli analyze \
  --dmp sample/sample.dmp \
  --evtx sample/sample.evtx \
  --time-window 1800  # ±30 minutes around crash time
```

### Full/Kernel Dumps (WinDbg integration)

- 本ツールは `MDMP` 署名のミニダンプは純粋Pythonで解析し、その他（`PAGE` 先頭の完全/カーネルダンプなど）は WinDbg（cdb/kd）を自動起動して解析します。
- 事前に Windows SDK の Debugging Tools をインストールしてください。
- 環境変数が設定されていれば検出をスキップします。

環境変数の例:

```powershell
# デバッガのパス（任意。未指定時は既定パスを探索）
$env:CDB_PATH = "C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\cdb.exe"
$env:KD_PATH  = "C:\Program Files (x86)\Windows Kits\10\Debuggers\x64\kd.exe"

# シンボルパス（任意。未指定時はMSシンボルサーバーを使用）
$env:SYMBOL_PATH = "srv*C:\Symbols*https://msdl.microsoft.com/download/symbols"
$env:SYMBOL_CACHE = "C:\Symbols"  # シンボルキャッシュの場所

# WinDbgタイムアウト設定（秒単位、デフォルト: 300秒）
$env:WINDBG_TIMEOUT_SECONDS = "600"
```

### タイムスタンプ表示

- すべてのタイムスタンプは **JST（日本標準時、UTC+9）** で表示されます
- 内部的にはUTCで保存され、表示時にJSTに変換されます

### Example Output

```
╭─────────────────────────────────────╮
│ Windows Dump File Analysis          │
╰─────────────────────────────────────╯

Crash Summary
─────────────────────────────────────
File Path              /path/to/crash.dmp
File Size              1,234,567 bytes
Crash Timestamp        2025-11-07 17:30:15 JST
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
- [ ] User Story 2: Extract and display event log contents (in progress)
- [ ] User Story 3: Generate LLM-powered analysis reports
- [ ] User Story 4: Save and export analysis results

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
