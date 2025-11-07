"""Data model for dump file analysis."""

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DumpFileAnalysis:
    """Represents extracted information from a Windows memory dump file (.dmp)."""

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

    def __post_init__(self) -> None:
        """Validate data after initialization."""
        if self.file_size_bytes <= 0:
            raise ValueError("file_size_bytes must be greater than 0")
        if not self.file_path:
            raise ValueError("file_path cannot be empty")
        if not self.process_name:
            raise ValueError("process_name cannot be empty")
        if not self.os_version:
            raise ValueError("os_version cannot be empty")
        if self.architecture not in ["x64", "x86", "ARM64", "ARM"]:
            raise ValueError(f"Invalid architecture: {self.architecture}")
