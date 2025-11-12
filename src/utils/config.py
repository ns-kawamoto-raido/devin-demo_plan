"""Configuration helpers for debugger integration and API keys."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def get_windbg_timeout() -> int:
    """Get WinDbg timeout in seconds from environment variable.
    
    Returns:
        Timeout in seconds (default: 300)
    """
    try:
        timeout = int(os.getenv("WINDBG_TIMEOUT_SECONDS", "300"))
        return max(1, min(timeout, 3600))  # Clamp between 1 and 3600 seconds
    except ValueError:
        return 300


def get_symbol_path() -> str:
    """Resolve the symbol path for debuggers.

    Priority:
    1. ENV `SYMBOL_PATH` or `SYM_PATH`
    2. Default to public MS symbol server with local cache at C:\\Symbols
    """
    sym = os.getenv("SYMBOL_PATH") or os.getenv("SYM_PATH")
    if sym:
        return sym
    cache = Path(os.getenv("SYMBOL_CACHE", r"C:\\Symbols"))
    return f"srv*{cache}*https://msdl.microsoft.com/download/symbols"


def find_debugger() -> dict[str, str | None]:
    """Find paths for cdb/kd/windbg if available.

    Search order:
    - Explicit env vars: CDB_PATH, KD_PATH, WINDBG_PATH
    - Common install locations under Windows Kits 10 Debuggers
    """
    env_cdb = os.getenv("CDB_PATH")
    env_kd = os.getenv("KD_PATH")
    env_windbg = os.getenv("WINDBG_PATH")

    candidates = []
    program_files_x86 = os.getenv("ProgramFiles(x86)", r"C:\\Program Files (x86)")
    common = Path(program_files_x86) / "Windows Kits" / "10" / "Debuggers"
    for arch in ("x64", "x86"):
        base = common / arch
        candidates.append((str(base / "cdb.exe"), str(base / "kd.exe"), str(base / "windbg.exe")))

    def _exists(p: str | None) -> str | None:
        return p if p and Path(p).exists() else None

    found_cdb = _exists(env_cdb)
    found_kd = _exists(env_kd)
    found_wb = _exists(env_windbg)

    if not (found_cdb and found_kd and found_wb):
        for cdb, kd, wb in candidates:
            found_cdb = found_cdb or _exists(cdb)
            found_kd = found_kd or _exists(kd)
            found_wb = found_wb or _exists(wb)

    return {"cdb": found_cdb, "kd": found_kd, "windbg": found_wb}


def get_windbg_timeout() -> int:
    """Return WinDbg execution timeout seconds from env or default (300)."""
    try:
        return int(os.getenv("WINDBG_TIMEOUT", "300"))
    except Exception:
        return 300


def get_openai_api_key() -> Optional[str]:
    """Return OpenAI API key from environment or .env file.

    Order:
    1) ENV OPENAI_API_KEY
    2) .env file in project root (simple KEY=VALUE parser)
    """
    key = os.getenv("OPENAI_API_KEY")
    if key:
        return key

    # Try to read .env one level above this file (project root)
    try:
        root = Path(__file__).resolve().parents[2]
        env_path = root / ".env"
        if env_path.exists():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k == "OPENAI_API_KEY" and v:
                    # cache into env for subsequent uses
                    os.environ["OPENAI_API_KEY"] = v
                    return v
    except Exception:
        pass

    return None

