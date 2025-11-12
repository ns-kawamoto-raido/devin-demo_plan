"""Unit tests for dump parser."""

import os
import tempfile

import pytest

from src.parsers.dump_parser import DumpParser, DumpParserError


class TestDumpParser:
    """Test cases for DumpParser class."""

    def test_parser_initialization(self):
        """Test that parser can be initialized."""
        parser = DumpParser()
        assert parser is not None

    def test_parse_nonexistent_file(self):
        """Test parsing a file that doesn't exist."""
        parser = DumpParser()
        with pytest.raises(FileNotFoundError):
            parser.parse("/nonexistent/file.dmp")

    def test_parse_empty_file(self):
        """Test parsing an empty file."""
        parser = DumpParser()
        with tempfile.NamedTemporaryFile(suffix=".dmp", delete=False) as f:
            temp_path = f.name
        
        try:
            with pytest.raises(DumpParserError, match="empty"):
                parser.parse(temp_path)
        finally:
            os.unlink(temp_path)

    def test_parse_invalid_file(self):
        """Test parsing an invalid dump file."""
        parser = DumpParser()
        with tempfile.NamedTemporaryFile(suffix=".dmp", delete=False, mode='wb') as f:
            f.write(b"This is not a valid dump file")
            temp_path = f.name
        
        try:
            with pytest.raises(DumpParserError):
                parser.parse(temp_path)
        finally:
            os.unlink(temp_path)
