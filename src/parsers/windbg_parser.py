"""WinDbg-backed parser for full and kernel dumps.

This module shells out to cdb/kd to analyze non-minidump .dmp files and
extract key fields into DumpFileAnalysis.
"""

from __future__ import annotations

import os
import shlex
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import re

from src.models.dump_analysis import DumpFileAnalysis
from src.utils.config import find_debugger, get_symbol_path


class WinDbgParserError(Exception):
    pass


@dataclass
class _DbgTools:
    cdb: str | None
    kd: str | None


class WinDbgParser:
    """Parser that leverages WinDbg (cdb/kd) for non-minidump files."""

    def __init__(self) -> None:
        dbg = find_debugger()
        self.tools = _DbgTools(cdb=dbg.get("cdb"), kd=dbg.get("kd"))
        self.symbol_path = get_symbol_path()

    def parse(self, file_path: str) -> DumpFileAnalysis:
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Dump file not found: {file_path}")

        size = Path(file_path).stat().st_size
        if size == 0:
            raise WinDbgParserError("Dump file is empty")

        # Choose debugger: try cdb first (user/full dumps), then kd (kernel)
        out = None
        errors: list[str] = []
        cmd_base = (
            ".symfix; .symopt+ 0x40; .reload; !analyze -v; .ecxr; kv; lm; .time; q"
        )

        if self.tools.cdb and Path(self.tools.cdb).exists():
            out, rc = self._run(self.tools.cdb, file_path, cmd_base)
            # If open failed or not a user dump, fall back to kd
            if rc != 0 and self.tools.kd and Path(self.tools.kd).exists():
                out2, rc2 = self._run(self.tools.kd, file_path, cmd_base)
                if rc2 == 0:
                    out, rc = out2, rc2
        elif self.tools.kd and Path(self.tools.kd).exists():
            out, rc = self._run(self.tools.kd, file_path, cmd_base)
        else:
            raise WinDbgParserError(
                "WinDbg (cdb/kd) が見つかりません。Windows SDK の Debugging Tools をインストールし、CDB_PATH/KD_PATH を設定してください。"
            )

        if out is None:
            raise WinDbgParserError("WinDbg 実行に失敗しました")

        # Parse minimal fields from output
        process_name = self._find_first(
            out, r"^PROCESS_NAME:\s*(?P<v>.+)$", default="System"
        )
        error_code = self._find_first(
            out, r"^EXCEPTION_CODE:\s*\(.*\)\s*(?P<v>0x[0-9a-fA-F]+)", default=None
        )
        if not error_code:
            # Kernel bugcheck
            bug = self._find_first(
                out, r"^BUGCHECK_STR:\s*(?P<v>.+)$", default=None
            )
            if bug:
                error_code = bug.strip()

        faulting_module = self._find_first(
            out, r"^Probably caused by :\s*(?P<v>\S+)", default=None
        )
        if not faulting_module:
            faulting_module = self._find_first(
                out, r"^MODULE_NAME\s*:\s*(?P<v>\S+)", default=None
            )

        faulting_address = self._find_first(
            out, r"^FAULTING_IP:\s*\S+\s+(?P<v>0x[0-9A-Fa-f]+)", default=None
        )

        thread_id = None
        tid = self._find_first(out, r"^FAULTING_THREAD:\s*(?P<v>0x[0-9a-fA-F]+)", None)
        if tid:
            try:
                thread_id = int(tid, 16)
            except Exception:
                pass

        # Loaded modules: parse a few names from `lm` section
        modules = self._parse_modules(out)

        # Basic arch/os placeholders (can be improved with vertarget parsing)
        arch = "x64"
        os_version = "Windows (WinDbg)"

        # Stack preview: take first several frames from `kv` output
        stack = self._parse_stack(out)

        analysis = DumpFileAnalysis(
            file_path=file_path,
            file_size_bytes=size,
            crash_timestamp=datetime.utcnow(),
            crash_type="EXCEPTION" if error_code else "BUGCHECK",
            process_name=process_name or "System",
            os_version=os_version,
            architecture=arch,
            error_code=error_code,
            faulting_module=faulting_module,
            faulting_address=faulting_address,
            process_id=None,
            thread_id=thread_id,
            stack_trace=stack,
            loaded_modules=modules,
            system_uptime_seconds=None,
            parsing_errors=errors,
        )
        return analysis

    def _run(self, tool: str, dump: str, command: str) -> tuple[str, int]:
        args = [tool, "-z", dump, "-y", self.symbol_path, "-c", command]
        try:
            proc = subprocess.run(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=300,
            )
            return proc.stdout, proc.returncode
        except subprocess.TimeoutExpired as e:
            return (f"[timeout] {e}", 1)

    def _find_first(self, text: str, pattern: str, default: str | None) -> str | None:
        m = re.search(pattern, text, flags=re.MULTILINE)
        return m.group("v").strip() if m else default

    def _parse_modules(self, text: str) -> list[str]:
        mods: list[str] = []
        # Heuristic: lines of `lm` that look like: 'module start end  name'
        for line in text.splitlines():
            # Typical: 'fffff803`2b5a0000 fffff803`2b666000   nt       (pdb symbols)'
            parts = line.strip().split()
            if len(parts) >= 3 and re.match(r"^[0-9a-fA-F`]+$", parts[0]) and re.match(
                r"^[0-9a-fA-F`]+$", parts[1]
            ):
                name = parts[2]
                if name not in mods and len(name) <= 64:
                    mods.append(name)
            if len(mods) >= 50:
                break
        return mods

    def _parse_stack(self, text: str) -> list[str]:
        stack: list[str] = []
        capture = False
        for line in text.splitlines():
            if re.search(r"^Child-SP|^#\s+\w+", line):
                capture = True
            if capture:
                if line.strip() == "" and stack:
                    break
                if len(line.strip()) > 0:
                    stack.append(line.strip())
            if len(stack) >= 20:
                break
        if not stack:
            # fallback: take a few lines around '!analyze -v' output for context
            for line in text.splitlines():
                if "!analyze -v" in line:
                    stack.append("WinDbg analysis available in raw output")
                    break
        return stack

