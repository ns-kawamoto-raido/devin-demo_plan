"""Unit tests for DumpFileAnalysis model."""

from datetime import datetime

import pytest

from src.models.dump_analysis import DumpFileAnalysis


class TestDumpFileAnalysis:
    """Test cases for DumpFileAnalysis data model."""

    def test_create_minimal_analysis(self):
        """Test creating a minimal DumpFileAnalysis object."""
        analysis = DumpFileAnalysis(
            file_path="/path/to/crash.dmp",
            file_size_bytes=1024,
            crash_timestamp=datetime.utcnow(),
            crash_type="EXCEPTION",
            process_name="test.exe",
            os_version="Windows 10 Build 19045",
            architecture="x64"
        )
        assert analysis.file_path == "/path/to/crash.dmp"
        assert analysis.file_size_bytes == 1024
        assert analysis.crash_type == "EXCEPTION"
        assert analysis.process_name == "test.exe"
        assert analysis.architecture == "x64"

    def test_invalid_file_size(self):
        """Test that invalid file size raises error."""
        with pytest.raises(ValueError, match="file_size_bytes"):
            DumpFileAnalysis(
                file_path="/path/to/crash.dmp",
                file_size_bytes=0,
                crash_timestamp=datetime.utcnow(),
                crash_type="EXCEPTION",
                process_name="test.exe",
                os_version="Windows 10",
                architecture="x64"
            )

    def test_invalid_architecture(self):
        """Test that invalid architecture raises error."""
        with pytest.raises(ValueError, match="architecture"):
            DumpFileAnalysis(
                file_path="/path/to/crash.dmp",
                file_size_bytes=1024,
                crash_timestamp=datetime.utcnow(),
                crash_type="EXCEPTION",
                process_name="test.exe",
                os_version="Windows 10",
                architecture="invalid"
            )

    def test_has_error_code(self):
        """Test has_error_code method."""
        analysis = DumpFileAnalysis(
            file_path="/path/to/crash.dmp",
            file_size_bytes=1024,
            crash_timestamp=datetime.utcnow(),
            crash_type="EXCEPTION",
            process_name="test.exe",
            os_version="Windows 10",
            architecture="x64",
            error_code="0xC0000005"
        )
        assert analysis.has_error_code() is True

    def test_has_stack_trace(self):
        """Test has_stack_trace method."""
        analysis = DumpFileAnalysis(
            file_path="/path/to/crash.dmp",
            file_size_bytes=1024,
            crash_timestamp=datetime.utcnow(),
            crash_type="EXCEPTION",
            process_name="test.exe",
            os_version="Windows 10",
            architecture="x64",
            stack_trace=["frame1", "frame2"]
        )
        assert analysis.has_stack_trace() is True

    def test_default_lists(self):
        """Test that default lists are initialized properly."""
        analysis = DumpFileAnalysis(
            file_path="/path/to/crash.dmp",
            file_size_bytes=1024,
            crash_timestamp=datetime.utcnow(),
            crash_type="EXCEPTION",
            process_name="test.exe",
            os_version="Windows 10",
            architecture="x64"
        )
        assert isinstance(analysis.stack_trace, list)
        assert isinstance(analysis.loaded_modules, list)
        assert isinstance(analysis.parsing_errors, list)
        assert len(analysis.stack_trace) == 0
        assert len(analysis.loaded_modules) == 0
        assert len(analysis.parsing_errors) == 0
