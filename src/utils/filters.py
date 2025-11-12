from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
from typing import Iterator

from src.models.event_log import EventLogEntry, EventLevel


def filter_by_level(entries: Iterable[EventLogEntry], level: str | None) -> Iterator[EventLogEntry]:
    if not level or level.lower() == "all":
        yield from entries
        return

    level_map = {
        "critical": EventLevel.CRITICAL,
        "error": EventLevel.ERROR,
        "warning": EventLevel.WARNING,
        "info": EventLevel.INFORMATION,
        "information": EventLevel.INFORMATION,
        "verbose": EventLevel.VERBOSE,
    }
    target = level_map.get(level.lower())
    if target is None:
        yield from entries
        return

    for e in entries:
        if e.level == target:
            yield e


def filter_by_time_range(entries: Iterable[EventLogEntry], start: datetime, end: datetime) -> Iterator[EventLogEntry]:
    for e in entries:
        if e.within_time_range(start, end):
            yield e


def filter_by_source(entries: Iterable[EventLogEntry], sources: set[str] | None) -> Iterator[EventLogEntry]:
    if not sources:
        yield from entries
        return
    src_lower = {s.lower() for s in sources}
    for e in entries:
        if e.source.lower() in src_lower:
            yield e

