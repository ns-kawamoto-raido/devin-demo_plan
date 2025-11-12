"""WinDbg-backed parser for full and kernel dumps.

This module shells out to cdb/kd to analyze non-minidump .dmp files and
extract key fields into DumpFileAnalysis.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
import re

from src.models.dump_analysis import DumpFileAnalysis
from src.utils.config import find_debugger, get_symbol_path, get_windbg_timeout


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
        # Simpler approach: run key commands in separate passes to avoid quoting issues
        cmd_analyze = '!analyze -v; q'
        cmd_kn = 'kn; q'
        cmd_lm = 'lm t n; q'
        cmd_vertarget = 'vertarget; q'
        cmd_time = '.time; q'

        if self.tools.cdb and Path(self.tools.cdb).exists():
            out, rc = self._run(self.tools.cdb, file_path, cmd_analyze)
            out_kn, _ = self._run(self.tools.cdb, file_path, cmd_kn)
            out_lm, _ = self._run(self.tools.cdb, file_path, cmd_lm)
            out_vt, _ = self._run(self.tools.cdb, file_path, cmd_vertarget)
            out_time, _ = self._run(self.tools.cdb, file_path, cmd_time)
            # Fallback to kd if analyze failed
            if rc != 0 and self.tools.kd and Path(self.tools.kd).exists():
                out, rc = self._run(self.tools.kd, file_path, cmd_analyze)
                out_kn, _ = self._run(self.tools.kd, file_path, cmd_kn)
                out_lm, _ = self._run(self.tools.kd, file_path, cmd_lm)
                out_vt, _ = self._run(self.tools.kd, file_path, cmd_vertarget)
                out_time, _ = self._run(self.tools.kd, file_path, cmd_time)
        elif self.tools.kd and Path(self.tools.kd).exists():
            out, rc = self._run(self.tools.kd, file_path, cmd_analyze)
            out_kn, _ = self._run(self.tools.kd, file_path, cmd_kn)
            out_lm, _ = self._run(self.tools.kd, file_path, cmd_lm)
            out_vt, _ = self._run(self.tools.kd, file_path, cmd_vertarget)
            out_time, _ = self._run(self.tools.kd, file_path, cmd_time)
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
            bug = self._find_first(out, r"^BUGCHECK_STR:\s*(?P<v>.+)$", None)
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
        # In kernel dumps, FAULTING_THREAD is typically ETHREAD address, not TID
        faulting_thread_address = self._find_first(
            out, r"^FAULTING_THREAD:\s*(?P<v>0x[0-9a-fA-F]+)", None
        )

        # Loaded modules: parse a few names from `lm` section
        modules = self._parse_modules(out_lm or "")

        # Basic arch/os placeholders (can be improved with vertarget parsing)
        arch = "x64"
        os_version = self._parse_os_version(out_vt or "") or "Windows (WinDbg)"
        os_name = self._find_first(out, r"^OSNAME:\s*(?P<v>.+)$", None)

        # Stack preview: take first several frames from `kv` output
        stack = self._parse_stack(out)  # from !analyze -v
        if not stack:
            stack = self._parse_stack_kn(out_kn or "")

        # Timestamp/Uptime from `.time` output (dump-internal time)
        debug_ts = self._parse_debug_time(out_time or "") or datetime.now(timezone.utc)
        uptime_seconds = self._parse_system_uptime(out_time or "")

        # Extended fields from !analyze/vertarget output
        bugcheck_args = self._parse_bugcheck_args(out)
        bugcheck_code = self._find_first(out, r"^BUGCHECK_CODE:\s*(?P<v>\S+)$", None)
        irql = self._parse_irql(out)
        image_name = self._find_first(out, r"^IMAGE_NAME:\s*(?P<v>\S+)$", None)
        symbol_name = self._find_first(out, r"^SYMBOL_NAME:\s*(?P<v>.+)$", None)
        failure_bucket_id = self._find_first(out, r"^FAILURE_BUCKET_ID:\s*(?P<v>.+)$", None)
        default_bucket_id = self._find_first(out, r"^DEFAULT_BUCKET_ID:\s*(?P<v>.+)$", None)
        os_build = self._parse_vertarget(out)

        # If we have a faulting module, get detailed metadata via a second pass
        module_version = None
        module_timestamp = None
        if faulting_module:
            out2, rc2 = self._run_any(
                [self.tools.cdb, self.tools.kd],
                file_path,
                f".symfix; .reload; .printf \"##BEGIN_LMVM##\\n\"; lmv m {faulting_module}; .printf \"\\n##END_LMVM##\\n\"; q",
            )
            if rc2 == 0 and out2:
                module_version, module_timestamp = self._parse_lmvm(out2)
        if image_name:
            faulting_module = image_name

        analysis = DumpFileAnalysis(
            file_path=file_path,
            file_size_bytes=size,
            crash_timestamp=debug_ts,
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
            system_uptime_seconds=uptime_seconds,
            parsing_errors=errors,
            bugcheck_args=bugcheck_args,
            bugcheck_code=bugcheck_code,
            irql=irql,
            image_name=image_name,
            symbol_name=symbol_name,
            failure_bucket_id=failure_bucket_id,
            default_bucket_id=default_bucket_id,
            os_build=os_build,
            os_name=os_name,
            module_version=module_version,
            module_timestamp=module_timestamp,
            faulting_thread_address=faulting_thread_address,
        )
        return analysis

    def _run(self, tool: str, dump: str, command: str) -> tuple[str, int]:
        args = [tool, "-z", dump, "-y", self.symbol_path, "-c", command]
        timeout = get_windbg_timeout()
        try:
            proc = subprocess.run(
                args,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout,
            )
            return proc.stdout, proc.returncode
        except subprocess.TimeoutExpired as e:
            return (f"[timeout after {timeout}s] {e}", 1)

    def _find_first(self, text: str, pattern: str, default: str | None) -> str | None:
        m = re.search(pattern, text, flags=re.MULTILINE)
        return m.group("v").strip() if m else default

    def _run_any(self, tools: list[str | None], dump: str, command: str) -> tuple[str | None, int]:
        for t in tools:
            if t and Path(t).exists():
                out, rc = self._run(t, dump, command)
                if rc == 0:
                    return out, rc
        return None, 1

    def _parse_modules(self, text: str) -> list[str]:
        mods: list[str] = []
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("kd>"):
                continue
            parts = line.split()
            # Expect e.g.: 'fffff806`ec2b0000 fffff806`ec3a0000 modulename'
            if len(parts) >= 3 and re.match(r"^[0-9a-fA-F`]+$", parts[0]) and re.match(r"^[0-9a-fA-F`]+$", parts[1]):
                name = parts[2]
            else:
                name = parts[-1] if parts else ""
            if not name or name in ('"', "'") or re.match(r"^[0-9a-fA-F`:+]+$", name):
                continue
            if name not in mods:
                mods.append(name)
            if len(mods) >= 50:
                break
        return mods

    def _parse_stack(self, text: str) -> list[str]:
        stack: list[str] = []
        m = re.search(r"^STACK_TEXT:.*$([\s\S]*?)(?:^\s*$|^SYMBOL_NAME:)", text, flags=re.MULTILINE)
        if m:
            block = m.group(1)
            for line in block.splitlines():
                s = line.strip()
                if s:
                    stack.append(s)
        if not stack:
            stack.append("Stack trace requires symbol files for detailed analysis")
        return stack[:20]

    def _parse_os_version(self, text: str) -> str | None:
        vt = self._slice(text, "##BEGIN_VERTARGET##", "##END_VERTARGET##")
        if not vt:
            return None
        # Example: 'Windows 10 Kernel Version 26100 MP (32 procs) Free x64'
        m = re.search(r"^(Windows\s+\d+\s+Kernel\s+Version\s+\d+).*$", vt, flags=re.MULTILINE)
        return m.group(1) if m else None

    def _slice(self, text: str, begin: str, end: str) -> str | None:
        s = text.find(begin)
        e = text.find(end)
        if s == -1 or e == -1 or e <= s:
            return None
        return text[s + len(begin) : e].strip()

    def _parse_bugcheck_args(self, text: str) -> list[str]:
        args: list[str] = []
        for n in range(1, 5):
            m = re.search(rf"^Arg{n}:\s*(?P<v>.+)$", text, flags=re.MULTILINE)
            if m:
                args.append(m.group("v").strip())
        return args

    def _parse_irql(self, text: str) -> int | None:
        m = re.search(r"^(?:IRQL|CURRENT_IRQL):\s*(?P<v>\d+)$", text, flags=re.MULTILINE)
        if m:
            try:
                return int(m.group("v"))
            except Exception:
                return None
        return None

    def _parse_vertarget(self, text: str) -> str | None:
        # Example: 'Windows 10 Kernel Version 19041 MP (16 procs) Free x64'
        m = re.search(r"^Windows .* Version\s+(?P<v>\d+).*$", text, flags=re.MULTILINE)
        return m.group("v") if m else None

    def _parse_lmvm(self, text: str) -> tuple[str | None, str | None]:
        ver = None
        ts = None
        m = re.search(r"^\s*File version\s*:\s*(?P<v>.+)$", text, flags=re.MULTILINE|re.IGNORECASE)
        if m:
            ver = m.group("v").strip()
        m2 = re.search(r"^\s*Timestamp\s*:\s*(?P<v>.+)$", text, flags=re.MULTILINE|re.IGNORECASE)
        if m2:
            ts = m2.group("v").strip()
        return ver, ts

    def _parse_debug_time(self, text: str) -> datetime | None:
        """Parse WinDbg `.time` 'Debug session time' and return timezone-aware UTC datetime.

        Example lines:
          Debug session time: Mon Nov 10 22:12:33.123 2025 (UTC - 8:00)
          Debug session time: Tue Nov 11 07:01:02 2025 (UTC + 9:00)
        """
        m = re.search(
            r"^Debug session time:\s*(?P<dt>[A-Za-z]{3}\s+[A-Za-z]{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?\s+\d{4})\s*\((?P<tz>UTC\s*[+\-]\s*\d{1,2}:\d{2})\)",
            text,
            flags=re.MULTILINE,
        )
        if not m:
            return None
        dt_str = m.group("dt")
        tz_str = m.group("tz").replace(" ", "")  # e.g., UTC-8:00 or UTC+9:00
        # Parse datetime (assumed local in given tz)
        for fmt in ("%a %b %d %H:%M:%S.%f %Y", "%a %b %d %H:%M:%S %Y"):
            try:
                local_dt = datetime.strptime(dt_str, fmt)
                break
            except ValueError:
                local_dt = None
        if local_dt is None:
            return None

        # Convert to UTC by subtracting the offset sign from the local time
        # tz_str like 'UTC-8:00' means local = UTC-8, hence UTC = local + 8
        m2 = re.match(r"UTC([+\-])(\d{1,2}):(\d{2})", tz_str)
        if not m2:
            return local_dt.replace(tzinfo=timezone.utc)
        sign, hh, mm = m2.groups()
        hours = int(hh)
        minutes = int(mm)
        delta_minutes = hours * 60 + minutes
        if sign == "+":
            # local = UTC + offset -> UTC = local - offset
            offset_minutes = delta_minutes
            utc_dt = local_dt.replace(microsecond=local_dt.microsecond) - timedelta(
                minutes=offset_minutes
            )
        else:
            # local = UTC - offset -> UTC = local + offset
            offset_minutes = delta_minutes
            utc_dt = local_dt + timedelta(minutes=offset_minutes)
        
        return utc_dt.replace(tzinfo=timezone.utc)

    def _parse_system_uptime(self, text: str) -> int | None:
        """Parse 'System Uptime' from `.time` output into seconds."""
        m = re.search(r"^System Uptime:\s*(?P<v>.+)$", text, flags=re.MULTILINE)
        if not m:
            return None
        v = m.group("v").strip()
        if v.lower().startswith("not available"):
            return None
        # Formats like: '2 days 03:04:05.123' or '03:04:05.123'
        days = 0
        rest = v
        md = re.match(r"(\d+)\s+days?\s+(.*)", rest)
        if md:
            days = int(md.group(1))
            rest = md.group(2)
        # strip milliseconds
        rest = rest.split()[0]
        hms = rest.split(":")
        if len(hms) < 3:
            return None
        try:
            h, m, s = int(hms[0]), int(hms[1]), int(float(hms[2]))
            return days * 86400 + h * 3600 + m * 60 + s
        except Exception:
            return None
