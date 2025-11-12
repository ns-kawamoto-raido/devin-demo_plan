from __future__ import annotations

import heapq
import os
from collections.abc import Iterable, Iterator
from datetime import datetime, timezone
from typing import Optional
import xml.etree.ElementTree as ET

from Evtx.Evtx import Evtx  # python-evtx

from src.models.event_log import EventLogEntry, EventLevel
from src.utils.progress import spinner


class EvtxParserError(Exception):
    pass


class EvtxParser:
    def __init__(self, max_warning_samples: int = 5) -> None:
        self.warning_count: int = 0
        self._warning_samples: list[str] = []
        self._max_warning_samples = max_warning_samples

    LEVEL_MAP = {
        "1": EventLevel.CRITICAL,
        "2": EventLevel.ERROR,
        "3": EventLevel.WARNING,
        "4": EventLevel.INFORMATION,
        "5": EventLevel.VERBOSE,
    }

    def parse(self, paths: str | list[str]) -> Iterator[EventLogEntry]:
        files = [paths] if isinstance(paths, str) else list(paths)
        if not files:
            return iter(())

        for p in files:
            self._validate_file(p)

        iterators = [self._iter_file(p) for p in files]
        if len(iterators) == 1:
            yield from iterators[0]
        else:
            yield from self.merge_events(iterators)

    def _iter_file(self, path: str) -> Iterator[EventLogEntry]:
        with spinner(f"Parsing event log: {os.path.basename(path)}"):
            with Evtx(path) as evtx:
                for record in evtx.records():
                    try:
                        xml = record.xml()
                        entry = self._from_xml(xml, path, record.record_num())
                        if entry:
                            yield entry
                    except Exception as e:
                        # 壊れたレコードはスキップし継続（警告を集計）
                        self.warning_count += 1
                        if len(self._warning_samples) < self._max_warning_samples:
                            self._warning_samples.append(f"{type(e).__name__}: {e}")
                        continue

    @staticmethod
    def merge_events(iterables: Iterable[Iterator[EventLogEntry]]) -> Iterator[EventLogEntry]:
        def keyer(it: Iterator[EventLogEntry]):
            for item in it:
                yield (item.timestamp, item)

        heap: list[tuple[datetime, EventLogEntry]] = []
        iter_wrapped = [keyer(it) for it in iterables]
        for idx, it in enumerate(iter_wrapped):
            try:
                ts, item = next(it)
                heap.append((ts, idx, item, it))
            except StopIteration:
                pass
        heapq.heapify(heap)

        while heap:
            ts, idx, item, it = heapq.heappop(heap)
            yield item
            try:
                nts, nitem = next(it)
                heapq.heappush(heap, (nts, idx, nitem, it))
            except StopIteration:
                pass

    def _from_xml(self, xml: str, file_path: str, fallback_record_id: int) -> Optional[EventLogEntry]:
        root = ET.fromstring(xml)
        ns = "{http://schemas.microsoft.com/win/2004/08/events/event}"
        sys = root.find(f"{ns}System")
        if sys is None:
            return None

        provider = sys.find(f"{ns}Provider")
        source = provider.get("Name") if provider is not None else "Unknown"

        event_id_el = sys.find(f"{ns}EventID")
        event_id = int(event_id_el.text) if event_id_el is not None and event_id_el.text else 0

        level_el = sys.find(f"{ns}Level")
        level_text = level_el.text if level_el is not None and level_el.text else "4"
        level = self.LEVEL_MAP.get(level_text, EventLevel.INFORMATION)

        time_el = sys.find(f"{ns}TimeCreated")
        ts_str = time_el.get("SystemTime") if time_el is not None else None
        if ts_str:
            # 例: 2025-11-07 08:22:31.123456Z or 2025-11-07T08:22:31.123456Z
            ts_norm = ts_str.replace(" ", "T").replace("Z", "+00:00")
            timestamp = datetime.fromisoformat(ts_norm)
        else:
            timestamp = datetime.now(timezone.utc)
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=timezone.utc)
        else:
            timestamp = timestamp.astimezone(timezone.utc)

        comp_el = sys.find(f"{ns}Computer")
        computer = comp_el.text if comp_el is not None else None

        user_el = sys.find(f"{ns}Security")
        user_sid = user_el.get("UserID") if user_el is not None else None

        rec_id_el = sys.find(f"{ns}EventRecordID")
        record_number = (
            int(rec_id_el.text) if rec_id_el is not None and rec_id_el.text else int(fallback_record_id)
        )

        # メッセージは RenderingInfo が無い場合が多いので EventData の Data を結合
        msg = self._extract_message(root, ns)

        return EventLogEntry(
            record_number=record_number,
            timestamp=timestamp,
            event_id=event_id,
            source=source or "Unknown",
            level=level,
            message=msg or "",
            file_path=file_path,
            computer_name=computer,
            user_sid=user_sid,
        )

    @staticmethod
    def _extract_message(root: ET.Element, ns: str) -> str:
        # RenderingInfo/Message があれば最優先
        rend = root.find(f"{ns}RenderingInfo")
        if rend is not None:
            msg_el = rend.find(f"{ns}Message")
            if msg_el is not None and msg_el.text:
                return msg_el.text.strip()

        # EventData の Data を結合
        event_data = root.find(f"{ns}EventData")
        if event_data is not None:
            parts: list[str] = []
            for d in event_data.findall(f"{ns}Data"):
                if d.text:
                    parts.append(d.text.strip())
            if parts:
                return ", ".join(parts)

        return ""

    # --- warnings API ---
    def warnings_summary(self) -> tuple[int, list[str]]:
        """Return (count, samples) of per-record parsing warnings."""
        return self.warning_count, list(self._warning_samples)

    @staticmethod
    def _validate_file(path: str) -> None:
        if not os.path.exists(path):
            raise EvtxParserError(f"File not found: {path}")
        if not os.path.isfile(path):
            raise EvtxParserError(f"Not a file: {path}")
        if not path.lower().endswith(".evtx"):
            raise EvtxParserError(f"Not an .evtx file: {path}")
