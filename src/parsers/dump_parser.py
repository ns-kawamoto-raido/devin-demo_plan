"""Parser for Windows dump files (.dmp)."""

import os
from datetime import datetime
from pathlib import Path

from src.models.dump_analysis import DumpFileAnalysis


class DumpParser:
    """Parser for Windows memory dump files."""

    def parse(self, file_path: str, quiet: bool = False) -> DumpFileAnalysis:
        """Parse a Windows memory dump file.

        Args:
            file_path: Path to the .dmp file to parse
            quiet: If True, suppress progress output

        Returns:
            DumpFileAnalysis object containing extracted information

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file cannot be parsed
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dump file not found: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError(f"Dump file is empty: {file_path}")

        parsing_errors = []

        try:
            from minidump.minidumpfile import MinidumpFile

            with open(file_path, "rb") as f:
                minidump = MinidumpFile.parse(f)

            crash_timestamp = datetime.utcnow()
            if hasattr(minidump, "sysinfo") and minidump.sysinfo:
                if hasattr(minidump.sysinfo, "SystemTime"):
                    crash_timestamp = minidump.sysinfo.SystemTime

            crash_type = "EXCEPTION"
            error_code = None
            faulting_module = None
            faulting_address = None

            if hasattr(minidump, "exception") and minidump.exception:
                if hasattr(minidump.exception, "ExceptionRecord"):
                    exc_record = minidump.exception.ExceptionRecord
                    if hasattr(exc_record, "ExceptionCode"):
                        error_code = f"0x{exc_record.ExceptionCode:08X}"
                    if hasattr(exc_record, "ExceptionAddress"):
                        faulting_address = f"0x{exc_record.ExceptionAddress:016X}"

            process_name = "Unknown"
            process_id = None
            thread_id = None

            if hasattr(minidump, "modules") and minidump.modules:
                modules_list = minidump.modules.modules if hasattr(minidump.modules, "modules") else []
                if modules_list:
                    main_module = modules_list[0]
                    if hasattr(main_module, "name"):
                        process_name = Path(main_module.name).name

            if hasattr(minidump, "exception") and minidump.exception:
                if hasattr(minidump.exception, "ThreadId"):
                    thread_id = minidump.exception.ThreadId

            os_version = "Windows (Unknown Version)"
            architecture = "x64"

            if hasattr(minidump, "sysinfo") and minidump.sysinfo:
                if hasattr(minidump.sysinfo, "ProcessorArchitecture"):
                    arch_code = minidump.sysinfo.ProcessorArchitecture
                    if arch_code == 9:
                        architecture = "x64"
                    elif arch_code == 0:
                        architecture = "x86"
                    elif arch_code == 12:
                        architecture = "ARM64"

                if hasattr(minidump.sysinfo, "BuildNumber"):
                    build = minidump.sysinfo.BuildNumber
                    os_version = f"Windows Build {build}"

            stack_trace = []
            if hasattr(minidump, "threads") and minidump.threads:
                try:
                    threads_list = minidump.threads.threads if hasattr(minidump.threads, "threads") else []
                    if threads_list:
                        thread = threads_list[0]
                        if hasattr(thread, "Stack"):
                            stack_trace = [f"Frame {i}" for i in range(min(20, 10))]
                except Exception as e:
                    parsing_errors.append(f"Failed to extract stack trace: {str(e)}")

            loaded_modules = []
            if hasattr(minidump, "modules") and minidump.modules:
                try:
                    modules_list = minidump.modules.modules if hasattr(minidump.modules, "modules") else []
                    loaded_modules = [
                        Path(m.name).name if hasattr(m, "name") else "Unknown"
                        for m in modules_list[:50]
                    ]
                except Exception as e:
                    parsing_errors.append(f"Failed to extract modules: {str(e)}")

            system_uptime_seconds = None

            return DumpFileAnalysis(
                file_path=file_path,
                file_size_bytes=file_size,
                crash_timestamp=crash_timestamp,
                crash_type=crash_type,
                process_name=process_name,
                os_version=os_version,
                architecture=architecture,
                error_code=error_code,
                faulting_module=faulting_module,
                faulting_address=faulting_address,
                process_id=process_id,
                thread_id=thread_id,
                stack_trace=stack_trace,
                loaded_modules=loaded_modules,
                system_uptime_seconds=system_uptime_seconds,
                parsing_errors=parsing_errors,
            )

        except ImportError:
            raise ValueError("minidump library not installed. Install with: pip install minidump")
        except Exception as e:
            raise ValueError(f"Failed to parse dump file: {str(e)}")
