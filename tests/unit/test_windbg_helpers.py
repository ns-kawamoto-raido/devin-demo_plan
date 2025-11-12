"""Unit tests for WinDbg parser helper functions."""

from datetime import timezone


from src.parsers.windbg_parser import WinDbgParser


class TestWinDbgHelpers:
    """Test cases for WinDbg parser helper functions."""

    def test_parse_debug_time_with_positive_offset(self):
        """Test parsing debug time with positive UTC offset."""
        parser = WinDbgParser()
        sample_output = """
Debug session time: Tue Nov 11 07:01:02 2025 (UTC + 9:00)
System Uptime: 1 days 02:03:04.567
"""
        result = parser._parse_debug_time(sample_output)
        
        assert result is not None
        assert result.tzinfo == timezone.utc
        assert result.hour == 22
        assert result.minute == 1
        assert result.second == 2

    def test_parse_debug_time_with_negative_offset(self):
        """Test parsing debug time with negative UTC offset."""
        parser = WinDbgParser()
        sample_output = """
Debug session time: Mon Nov 10 22:12:33.123 2025 (UTC - 8:00)
System Uptime: 0 days 05:30:15.000
"""
        result = parser._parse_debug_time(sample_output)
        
        assert result is not None
        assert result.tzinfo == timezone.utc
        assert result.hour == 6
        assert result.minute == 12
        assert result.second == 33

    def test_parse_debug_time_with_milliseconds(self):
        """Test parsing debug time with milliseconds."""
        parser = WinDbgParser()
        sample_output = """
Debug session time: Wed Nov 12 15:30:45.789 2025 (UTC + 0:00)
"""
        result = parser._parse_debug_time(sample_output)
        
        assert result is not None
        assert result.tzinfo == timezone.utc
        assert result.hour == 15
        assert result.minute == 30
        assert result.second == 45
        assert result.microsecond == 789000

    def test_parse_debug_time_no_match(self):
        """Test parsing debug time when pattern doesn't match."""
        parser = WinDbgParser()
        sample_output = """
Some other output without debug time
"""
        result = parser._parse_debug_time(sample_output)
        
        assert result is None

    def test_parse_system_uptime_days_and_time(self):
        """Test parsing system uptime with days."""
        parser = WinDbgParser()
        sample_output = """
System Uptime: 2 days 03:04:05.123
"""
        result = parser._parse_system_uptime(sample_output)
        
        assert result is not None
        expected = 2 * 86400 + 3 * 3600 + 4 * 60 + 5
        assert result == expected

    def test_parse_system_uptime_time_only(self):
        """Test parsing system uptime without days."""
        parser = WinDbgParser()
        sample_output = """
System Uptime: 12:34:56.789
"""
        result = parser._parse_system_uptime(sample_output)
        
        assert result is not None
        expected = 12 * 3600 + 34 * 60 + 56
        assert result == expected

    def test_parse_system_uptime_not_available(self):
        """Test parsing system uptime when not available."""
        parser = WinDbgParser()
        sample_output = """
System Uptime: not available
"""
        result = parser._parse_system_uptime(sample_output)
        
        assert result is None

    def test_parse_system_uptime_no_match(self):
        """Test parsing system uptime when pattern doesn't match."""
        parser = WinDbgParser()
        sample_output = """
Some other output without uptime
"""
        result = parser._parse_system_uptime(sample_output)
        
        assert result is None

    def test_find_first_with_match(self):
        """Test _find_first helper with matching pattern."""
        parser = WinDbgParser()
        text = """
PROCESS_NAME:  test.exe
EXCEPTION_CODE: (NTSTATUS) 0xc0000005
"""
        result = parser._find_first(text, r"^PROCESS_NAME:\s*(?P<v>.+)$", default=None)
        
        assert result == "test.exe"

    def test_find_first_with_no_match(self):
        """Test _find_first helper with no matching pattern."""
        parser = WinDbgParser()
        text = """
Some output without the pattern
"""
        result = parser._find_first(text, r"^PROCESS_NAME:\s*(?P<v>.+)$", default="default_value")
        
        assert result == "default_value"
