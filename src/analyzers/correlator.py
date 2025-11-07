"""Timestamp correlation between dumps and events."""

from datetime import datetime, timedelta

from src.models.dump_analysis import DumpFileAnalysis
from src.models.event_log import EventLogEntry


class Correlator:
    """Correlates timestamps between dump files and event logs."""

    def get_crash_time(self, dump_analysis: DumpFileAnalysis) -> datetime:
        """Get crash timestamp from dump analysis.

        Args:
            dump_analysis: DumpFileAnalysis object

        Returns:
            Crash timestamp
        """
        return dump_analysis.crash_timestamp

    def filter_relevant_events(
        self, events: list[EventLogEntry], crash_time: datetime, time_window_seconds: int = 3600
    ) -> list[EventLogEntry]:
        """Filter events within time window of crash.

        Args:
            events: List of EventLogEntry objects
            crash_time: Crash timestamp
            time_window_seconds: Time window in seconds (default: 1 hour)

        Returns:
            Filtered list of events within time window
        """
        start_time = crash_time - timedelta(seconds=time_window_seconds)
        end_time = crash_time + timedelta(seconds=time_window_seconds)
        return [event for event in events if event.within_time_range(start_time, end_time)]

    def generate_timeline(
        self, events: list[EventLogEntry], crash_time: datetime | None = None
    ) -> list[str]:
        """Generate chronological timeline of events.

        Args:
            events: List of EventLogEntry objects
            crash_time: Optional crash timestamp to mark in timeline

        Returns:
            List of timeline strings
        """
        timeline = []
        sorted_events = sorted(events, key=lambda e: e.timestamp)

        for event in sorted_events:
            time_str = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            level_str = event.level.value
            timeline_entry = f"{time_str} | {level_str} | {event.source} | Event {event.event_id}: {event.message[:100]}"
            timeline.append(timeline_entry)

        if crash_time:
            crash_str = crash_time.strftime("%Y-%m-%d %H:%M:%S")
            timeline.append(f"{crash_str} | CRASH | System | Application crash occurred")

        return timeline
