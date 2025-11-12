from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from src.models.dump_analysis import DumpFileAnalysis
from src.models.event_log import EventLogEntry


def correlate_events(
    dump: Optional[DumpFileAnalysis],
    events: List[EventLogEntry],
    start: Optional[datetime] = None,
    end: Optional[datetime] = None,
    time_window_seconds: int = 3600,
) -> List[EventLogEntry]:
    """Return events within [start,end] or within ±window around dump crash time.

    If start/end are provided, they take precedence. Otherwise, when dump is
    given, compute a window centered at dump.crash_timestamp. If neither is
    available, return events sorted chronologically.
    """
    if start and end:
        s = _ensure_utc(start)
        e = _ensure_utc(end)
        selected = [ev for ev in events if s <= _ensure_utc(ev.timestamp) <= e]
    elif dump is not None and dump.crash_timestamp:
        ct = _ensure_utc(dump.crash_timestamp)
        s = ct - timedelta(seconds=time_window_seconds)
        e = ct + timedelta(seconds=time_window_seconds)
        selected = [ev for ev in events if s <= _ensure_utc(ev.timestamp) <= e]
    else:
        selected = list(events)

    selected.sort(key=lambda ev: ev.timestamp)
    return selected


def generate_timeline(events: List[EventLogEntry]) -> List[str]:
    """Format events into human-friendly timeline strings (JST)."""
    jst = timezone(timedelta(hours=9))
    lines: List[str] = []
    for ev in events:
        ts = _ensure_utc(ev.timestamp).astimezone(jst).strftime("%Y-%m-%d %H:%M:%S JST")
        msg = (ev.message or "").strip().replace("\n", " ")
        if len(msg) > 512:
            msg = msg[:512] + "…"
        line = f"{ts} | {ev.level.value} | {ev.source} | {ev.event_id} | {msg}"
        lines.append(line)
    return lines


def _ensure_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)

