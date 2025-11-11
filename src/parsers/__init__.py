"""Parsers package utilities."""

from __future__ import annotations

import os
from typing import Protocol

from .dump_parser import DumpParser


class ParserProtocol(Protocol):
    def parse(self, file_path: str):  # pragma: no cover - protocol signature only
        ...


def _read_magic(path: str) -> bytes:
    try:
        with open(path, "rb") as f:
            return f.read(4)
    except Exception:
        return b""


def get_parser_for(file_path: str) -> ParserProtocol:
    """Return appropriate parser based on dump signature.

    - MDMP -> use pure-Python Minidump parser
    - otherwise -> fall back to WinDbg-based parser for full/kernel dumps
    """
    magic = _read_magic(file_path)
    if magic == b"MDMP":
        return DumpParser()

    # Late import to avoid hard dependency when not used
    from .windbg_parser import WinDbgParser  # type: ignore

    return WinDbgParser()
