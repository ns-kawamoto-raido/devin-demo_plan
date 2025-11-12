"""Data model for Windows dump file analysis."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DumpFileAnalysis:
    """Represents extracted information from a Windows memory dump file (.dmp).
    
    This class stores structured crash information parsed from dump files,
    including crash details, system information, and stack traces.
    """
    
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
    stack_trace: list[str] = field(default_factory=list)
    loaded_modules: list[str] = field(default_factory=list)
    system_uptime_seconds: int | None = None
    parsing_errors: list[str] = field(default_factory=list)
    # Extended fields extracted primarily from WinDbg
    bugcheck_args: list[str] = field(default_factory=list)
    irql: int | None = None
    image_name: str | None = None
    symbol_name: str | None = None
    failure_bucket_id: str | None = None
    default_bucket_id: str | None = None
    os_build: str | None = None
    module_version: str | None = None
    module_timestamp: str | None = None
    bugcheck_code: str | None = None
    faulting_thread_address: str | None = None
    os_name: str | None = None

    def __post_init__(self):
        """Validate fields after initialization."""
        if self.file_size_bytes <= 0:
            raise ValueError("file_size_bytes must be greater than 0")
        
        if not self.crash_type:
            raise ValueError("crash_type must be non-empty")
        
        if not self.process_name:
            raise ValueError("process_name must be non-empty")
        
        if not self.os_version:
            raise ValueError("os_version must be non-empty")
        
        if self.architecture not in ("x64", "x86", "ARM64", "ARM"):
            raise ValueError(f"architecture must be x64, x86, ARM64, or ARM, got: {self.architecture}")
        
        if self.process_id is not None and self.process_id <= 0:
            raise ValueError("process_id must be greater than 0")
        
        if self.thread_id is not None and self.thread_id <= 0:
            raise ValueError("thread_id must be greater than 0")
        
        if self.system_uptime_seconds is not None and self.system_uptime_seconds < 0:
            raise ValueError("system_uptime_seconds must be >= 0")

    def has_error_code(self) -> bool:
        """Check if error code is available."""
        return self.error_code is not None and self.error_code != ""

    def has_stack_trace(self) -> bool:
        """Check if stack trace is available."""
        return len(self.stack_trace) > 0

    def has_parsing_errors(self) -> bool:
        """Check if there were any parsing errors."""
        return len(self.parsing_errors) > 0
