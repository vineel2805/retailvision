"""Entry/exit counters and occupancy (FR-006, FR-007)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from backend.counting.line import CountingLine, CrossingEvent
from backend.database.repository import CountingRepository
from backend.tracking.tracker import TrackedPerson


@dataclass
class VisitorCounter:
    """
    Orchestrates line crossing checks and maintains running totals.

    Occupancy = entries - exits, clamped to zero (FR-007).
    """

    counting_line: CountingLine
    repository: CountingRepository
    camera_id: int
    entries: int = 0
    exits: int = 0
    _recent_events: List[CrossingEvent] = field(default_factory=list)

    @property
    def occupancy(self) -> int:
        """Current occupancy; never negative (FR-007)."""
        return max(0, self.entries - self.exits)

    def sync_from_database(self) -> None:
        """Load today's totals from persisted events (e.g. on startup)."""
        summary = self.repository.get_daily_summary()
        self.entries = summary["entries"]
        self.exits = summary["exits"]

    def process_tracks(self, tracks: List[TrackedPerson]) -> List[CrossingEvent]:
        """Check all active tracks for crossings and persist new events."""
        active_ids = {t.track_id for t in tracks}
        new_events: List[CrossingEvent] = []

        for person in tracks:
            event = self.counting_line.update_track(
                track_id=person.track_id,
                centroid=person.centroid,
                confidence=person.confidence,
            )
            if event is None:
                continue

            self._record_event(event)
            new_events.append(event)

        self.counting_line.prune_stale_tracks(active_ids)
        self._recent_events = new_events
        return new_events

    def _record_event(self, event: CrossingEvent) -> None:
        """Update in-memory counters, log to SQLite, print to console."""
        if event.direction == "entry":
            self.entries += 1
        else:
            self.exits += 1

        self.repository.log_visitor_event(
            direction=event.direction,
            confidence=event.confidence,
            tracking_id=event.track_id,
            camera_id=self.camera_id,
        )

        print(
            f"[{event.direction.upper()}] track={event.track_id} "
            f"conf={event.confidence:.2f} | "
            f"entries={self.entries} exits={self.exits} occupancy={self.occupancy}"
        )
