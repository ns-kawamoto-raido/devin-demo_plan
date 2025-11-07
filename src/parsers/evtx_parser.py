"""Parser for Windows event log files (.evtx)."""

import os
from datetime import datetime
from typing import Iterator

from src.models import EventLevel
from src.models.event_log import EventLogEntry


class EvtxParser:
    """Parser for Windows Event Log files."""

    def parse(self, file_path: str, quiet: bool = False) -> list[EventLogEntry]:
        """Parse a Windows event log file.

        Args:
            file_path: Path to the .evtx file to parse
            quiet: If True, suppress progress output

        Returns:
            List of EventLogEntry objects

        Raises:
            FileNotFoundError: If file does not exist
            ValueError: If file cannot be parsed
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Event log file not found: {file_path}")

        file_size = os.path.getsize(file_path)
        if file_size == 0:
            raise ValueError(f"Event log file is empty: {file_path}")

        entries = []
        try:
            for entry in self._parse_stream(file_path):
                entries.append(entry)
        except Exception as e:
            if not entries:
                raise ValueError(f"Failed to parse event log file: {str(e)}")

        return entries

    def _parse_stream(self, file_path: str) -> Iterator[EventLogEntry]:
        """Parse event log file as a stream.

        Args:
            file_path: Path to the .evtx file

        Yields:
            EventLogEntry objects
        """
        try:
            import Evtx.Evtx as evtx
            import Evtx.Views as views
        except ImportError:
            raise ValueError("python-evtx library not installed. Install with: pip install python-evtx")

        try:
            with evtx.Evtx(file_path) as log:
                for record in log.records():
                    try:
                        entry = self._parse_record(record, file_path)
                        if entry:
                            yield entry
                    except Exception:
                        continue
        except Exception as e:
            raise ValueError(f"Failed to open event log file: {str(e)}")

    def _parse_record(self, record: any, file_path: str) -> EventLogEntry | None:
        """Parse a single event record.

        Args:
            record: Event record from python-evtx
            file_path: Path to the source .evtx file

        Returns:
            EventLogEntry object or None if parsing fails
        """
        try:
            import xml.etree.ElementTree as ET

            xml_str = record.xml()
            root = ET.fromstring(xml_str)

            ns = {"ns": "http://schemas.microsoft.com/win/2004/08/events/event"}

            system = root.find("ns:System", ns)
            if system is None:
                return None

            record_number = int(system.find("ns:EventRecordID", ns).text)
            event_id = int(system.find("ns:EventID", ns).text)

            time_created = system.find("ns:TimeCreated", ns)
            timestamp_str = time_created.get("SystemTime")
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

            provider = system.find("ns:Provider", ns)
            source = provider.get("Name", "Unknown")

            level_elem = system.find("ns:Level", ns)
            level_code = int(level_elem.text) if level_elem is not None else 4
            level = self._map_level(level_code)

            computer_elem = system.find("ns:Computer", ns)
            computer_name = computer_elem.text if computer_elem is not None else None

            event_data = root.find("ns:EventData", ns)
            message = ""
            if event_data is not None:
                data_items = event_data.findall("ns:Data", ns)
                message = " ".join([d.text or "" for d in data_items])

            if not message:
                message = f"Event ID {event_id}"

            return EventLogEntry(
                record_number=record_number,
                timestamp=timestamp,
                event_id=event_id,
                source=source,
                level=level,
                message=message,
                file_path=file_path,
                computer_name=computer_name,
            )

        except Exception:
            return None

    def _map_level(self, level_code: int) -> EventLevel:
        """Map Windows event level code to EventLevel enum.

        Args:
            level_code: Windows event level code

        Returns:
            EventLevel enum value
        """
        level_map = {
            1: EventLevel.CRITICAL,
            2: EventLevel.ERROR,
            3: EventLevel.WARNING,
            4: EventLevel.INFORMATION,
            5: EventLevel.VERBOSE,
        }
        return level_map.get(level_code, EventLevel.INFORMATION)

    def merge_events(self, event_lists: list[list[EventLogEntry]]) -> list[EventLogEntry]:
        """Merge multiple event lists chronologically.

        Args:
            event_lists: List of event log entry lists

        Returns:
            Merged and sorted list of events
        """
        all_events = []
        for events in event_lists:
            all_events.extend(events)
        return sorted(all_events, key=lambda e: e.timestamp)
