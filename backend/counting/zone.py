"""Zone-based polygon occupancy counting and boundary transition engine (Phase 1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Set, Optional

import cv2
import numpy as np

from backend.counting.line import CrossingEvent
from backend.tracking.tracker import TrackedPerson

Point = Tuple[float, float]


@dataclass
class ZoneConfig:
    """Configuration for a polygon occupancy zone."""

    camera_id: int = 1
    polygon: List[Point] = field(default_factory=list)
    confirmation_frames: int = 5


@dataclass
class ZoneFrameResult:
    """Result of a single-frame zone occupancy evaluation."""

    occupancy: int
    events: List[CrossingEvent]
    inside_track_ids: Set[int]


class ZoneOccupancyTracker:
    """
    Evaluates live occupancy by testing person foot-points against a user-created polygon zone.
    Implements N-frame hysteresis to eliminate boundary jitter.
    Occupancy is a live self-correcting count of confirmed tracks inside the zone.
    """

    def __init__(self, config: Optional[ZoneConfig] = None):
        self.config = config or ZoneConfig()
        self._confirmed_state: Dict[int, bool] = {}
        self._pending_state: Dict[int, bool] = {}
        self._pending_count: Dict[int, int] = {}

    def set_polygon(self, polygon: List[Point]) -> None:
        """Update active polygon coordinates."""
        if len(polygon) >= 3:
            self.config.polygon = polygon

    @property
    def polygon_np(self) -> Optional[np.ndarray]:
        """Return polygon points as OpenCV-compatible int32 numpy array if valid."""
        if len(self.config.polygon) < 3:
            return None
        return np.array(self.config.polygon, dtype=np.int32)

    def is_foot_inside(self, bbox: Tuple[int, int, int, int]) -> bool:
        """
        Test if foot-point (bottom-center of bounding box) lies inside the active polygon zone.
        Foot-point = ((x1 + x2) / 2.0, float(y2)).
        """
        pts = self.polygon_np
        if pts is None:
            return False

        x1, y1, x2, y2 = bbox
        foot_x = (x1 + x2) / 2.0
        foot_y = float(y2)

        res = cv2.pointPolygonTest(pts, (foot_x, foot_y), False)
        return res >= 0

    def update(self, tracks: List[TrackedPerson]) -> ZoneFrameResult:
        """
        Process active tracks for the current frame.
        Returns live occupancy count, any boundary transition events, and set of inside IDs.
        """
        active_ids = {t.track_id for t in tracks}
        events: List[CrossingEvent] = []

        for person in tracks:
            track_id = person.track_id
            raw_inside = self.is_foot_inside(person.bbox)

            if track_id not in self._confirmed_state:
                # Initialize new track as confirmed outside (False) so entering zone produces an entry event
                self._confirmed_state[track_id] = False
                self._pending_state[track_id] = raw_inside
                self._pending_count[track_id] = 1 if raw_inside else 0

                if raw_inside and self.config.confirmation_frames <= 1:
                    # Immediately confirm entry if confirmation_frames <= 1
                    self._confirmed_state[track_id] = True
                    self._pending_count[track_id] = 0
                    events.append(
                        CrossingEvent(
                            track_id=track_id,
                            direction="entry",
                            confidence=person.confidence,
                            centroid=person.centroid,
                        )
                    )
            else:
                confirmed = self._confirmed_state[track_id]
                if raw_inside == confirmed:
                    # State agrees with confirmed; reset pending counter
                    self._pending_state[track_id] = raw_inside
                    self._pending_count[track_id] = 0
                else:
                    # State differs from confirmed; apply hysteresis
                    if self._pending_state.get(track_id) == raw_inside:
                        self._pending_count[track_id] += 1
                    else:
                        self._pending_state[track_id] = raw_inside
                        self._pending_count[track_id] = 1

                    if self._pending_count[track_id] >= self.config.confirmation_frames:
                        # Confirmed state flipped!
                        self._confirmed_state[track_id] = raw_inside
                        self._pending_count[track_id] = 0

                        direction = "entry" if raw_inside else "exit"
                        events.append(
                            CrossingEvent(
                                track_id=track_id,
                                direction=direction,
                                confidence=person.confidence,
                                centroid=person.centroid,
                            )
                        )

        # Prune stale tracks no longer visible
        self.prune_stale_tracks(active_ids)

        # Compute live occupancy fresh every frame call — count of active tracks confirmed inside
        inside_track_ids = {
            tid for tid in active_ids
            if self._confirmed_state.get(tid, False)
        }
        live_occupancy = len(inside_track_ids)

        return ZoneFrameResult(
            occupancy=live_occupancy,
            events=events,
            inside_track_ids=inside_track_ids,
        )

    def prune_stale_tracks(self, active_track_ids: Set[int]) -> None:
        """Remove state for tracks no longer visible."""
        stale = set(self._confirmed_state.keys()) - active_track_ids
        for tid in stale:
            self._confirmed_state.pop(tid, None)
            self._pending_state.pop(tid, None)
            self._pending_count.pop(tid, None)
