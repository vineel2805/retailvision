"""Entry/exit counters and live zone occupancy orchestration (FR-006, FR-007, Phase 1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from backend.counting.line import CountingLine, CrossingEvent
from backend.counting.zone import ZoneOccupancyTracker
from backend.database.repository import CountingRepository
from backend.tracking.tracker import TrackedPerson


@dataclass
class VisitorCounter:
    """
    Orchestrates zone-based occupancy tracking and entry/exit analytics events.

    Occupancy is a live, self-correcting measurement every frame from ZoneOccupancyTracker,
    never an accumulator or `entries - exits`.
    """

    repository: CountingRepository
    camera_id: int
    counting_line: Optional[CountingLine] = None
    zone_tracker: ZoneOccupancyTracker = field(default_factory=ZoneOccupancyTracker)
    entries: int = 0
    exits: int = 0
    _current_occupancy: int = 0
    _recent_events: List[CrossingEvent] = field(default_factory=list)

    @property
    def occupancy(self) -> int:
        """Live, self-correcting current zone occupancy count."""
        return self._current_occupancy

    def sync_from_database(self) -> None:
        """Load today's cumulative entry/exit totals from persisted events on startup."""
        summary = self.repository.get_daily_summary()
        self.entries = summary["entries"]
        self.exits = summary["exits"]

    def process_tracks(self, tracks: List[TrackedPerson]) -> List[CrossingEvent]:
        """
        Process active tracks through ZoneOccupancyTracker.
        Updates live occupancy and logs any boundary transition events.
        """
        result = self.zone_tracker.update(tracks)
        self._current_occupancy = result.occupancy

        for event in result.events:
            self._record_event(event)

        self._recent_events = result.events
        return result.events

    def _record_event(self, event: CrossingEvent) -> None:
        """Increment cumulative daily analytics counter, log to SQLite, print to console."""
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
            f"entries={self.entries} exits={self.exits} live_occupancy={self.occupancy}"
        )
