"""Unit tests for parser selection logic."""

import tempfile
from pathlib import Path


from src.parsers import get_parser_for
from src.parsers.dump_parser import DumpParser
from src.parsers.windbg_parser import WinDbgParser


class TestParserSelection:
    """Test cases for automatic parser selection based on dump file signature."""

    def test_mdmp_signature_selects_dump_parser(self):
        """Test that MDMP signature selects DumpParser."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dmp") as f:
            f.write(b"MDMP")
            f.write(b"\x00" * 100)
            temp_path = f.name

        try:
            parser = get_parser_for(temp_path)
            assert isinstance(parser, DumpParser)
        finally:
            Path(temp_path).unlink()

    def test_page_signature_selects_windbg_parser(self):
        """Test that PAGE signature selects WinDbgParser."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dmp") as f:
            f.write(b"PAGE")
            f.write(b"\x00" * 100)
            temp_path = f.name

        try:
            parser = get_parser_for(temp_path)
            assert isinstance(parser, WinDbgParser)
        finally:
            Path(temp_path).unlink()

    def test_unknown_signature_selects_windbg_parser(self):
        """Test that unknown signature defaults to WinDbgParser."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dmp") as f:
            f.write(b"UNKN")
            f.write(b"\x00" * 100)
            temp_path = f.name

        try:
            parser = get_parser_for(temp_path)
            assert isinstance(parser, WinDbgParser)
        finally:
            Path(temp_path).unlink()

    def test_empty_file_selects_windbg_parser(self):
        """Test that empty file defaults to WinDbgParser."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".dmp") as f:
            temp_path = f.name

        try:
            parser = get_parser_for(temp_path)
            assert isinstance(parser, WinDbgParser)
        finally:
            Path(temp_path).unlink()
