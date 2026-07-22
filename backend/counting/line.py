"""
Virtual counting line and crossing detection (FR-005, FR-006).

Line-crossing math overview
---------------------------
The counting line is a directed segment from point A (p1) to point B (p2).

For any point P, we compute a *signed side* using the 2D cross product:

    side(P) = sign( (B - A) × (P - A) )

Geometric meaning (right-hand rule in image coordinates where y increases
downward):
  • side > 0  → P is to the LEFT of the directed line A→B
  • side < 0  → P is to the RIGHT of the directed line A→B
  • side = 0  → P lies exactly on the infinite line through A and B

Each tracked person stores their previous centroid and previous side. When
the side value changes sign between frames, the person's movement segment
(prev → curr) has crossed the counting line. The transition direction
(negative→positive or positive→negative) determines entry vs exit per config.

We also verify that the movement segment actually intersects the finite
line segment A→B (not just the infinite extension), using a standard
segment-intersection test.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Literal, Optional, Tuple

Point = Tuple[float, float]
EntryDirection = Literal["negative_to_positive", "positive_to_negative"]


@dataclass(frozen=True)
class CrossingEvent:
    """A validated line crossing for one track."""

    track_id: int
    direction: Literal["entry", "exit"]
    confidence: float
    centroid: Point


@dataclass
class CountingLine:
    """Configurable virtual line with entry/exit direction rules."""

    point_a: Point
    point_b: Point
    entry_direction: EntryDirection = "negative_to_positive"

    def __post_init__(self) -> None:
        self._prev_sides: Dict[int, int] = {}
        self._prev_centroids: Dict[int, Point] = {}

    @staticmethod
    def _cross(o: Point, a: Point, b: Point) -> float:
        """2D cross product of vectors OA and OB."""
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    def signed_side(self, point: Point) -> int:
        """
        Return -1, 0, or +1 indicating which side of directed line A→B
        the point lies on (see module docstring).
        """
        cross = self._cross(self.point_a, self.point_b, point)
        if cross > 0:
            return 1
        if cross < 0:
            return -1
        return 0

    @staticmethod
    def _on_segment(p: Point, q: Point, r: Point, eps: float = 1e-6) -> bool:
        """True if point q lies on segment pr."""
        return (
            min(p[0], r[0]) - eps <= q[0] <= max(p[0], r[0]) + eps
            and min(p[1], r[1]) - eps <= q[1] <= max(p[1], r[1]) + eps
        )

    def segments_intersect(self, p1: Point, p2: Point) -> bool:
        """
        True if movement segment p1→p2 crosses the counting line segment
        A→B. Uses orientation tests for proper segment intersection.
        """
        a, b = self.point_a, self.point_b
        o1 = self._cross(a, b, p1)
        o2 = self._cross(a, b, p2)
        o3 = self._cross(p1, p2, a)
        o4 = self._cross(p1, p2, b)

        if o1 * o2 < 0 and o3 * o4 < 0:
            return True

        eps = 1e-6
        if abs(o1) < eps and self._on_segment(a, p1, b):
            return True
        if abs(o2) < eps and self._on_segment(a, p2, b):
            return True
        if abs(o3) < eps and self._on_segment(p1, a, p2):
            return True
        if abs(o4) < eps and self._on_segment(p1, b, p2):
            return True
        return False

    def _direction_from_transition(self, prev_side: int, curr_side: int) -> Optional[Literal["entry", "exit"]]:
        """Map a side sign change to entry or exit based on configured direction."""
        if prev_side == 0 or curr_side == 0 or prev_side == curr_side:
            return None

        transition = "negative_to_positive" if prev_side < 0 and curr_side > 0 else "positive_to_negative"
        if transition == self.entry_direction:
            return "entry"
        return "exit"

    def update_track(
        self,
        track_id: int,
        centroid: Point,
        confidence: float,
    ) -> Optional[CrossingEvent]:
        """
        Update a track's position and return a CrossingEvent if the person
        crossed the line this frame (FR-006: each crossing counts once).
        """
        curr_side = self.signed_side(centroid)
        prev_centroid = self._prev_centroids.get(track_id)
        prev_side = self._prev_sides.get(track_id)

        self._prev_centroids[track_id] = centroid
        self._prev_sides[track_id] = curr_side

        if prev_centroid is None or prev_side is None:
            return None

        if prev_side == curr_side:
            return None

        if not self.segments_intersect(prev_centroid, centroid):
            return None

        direction = self._direction_from_transition(prev_side, curr_side)
        if direction is None:
            return None

        return CrossingEvent(
            track_id=track_id,
            direction=direction,
            confidence=confidence,
            centroid=centroid,
        )

    def prune_stale_tracks(self, active_track_ids: set[int]) -> None:
        """Remove state for tracks no longer visible (FR-004)."""
        stale = set(self._prev_sides.keys()) - active_track_ids
        for track_id in stale:
            self._prev_sides.pop(track_id, None)
            self._prev_centroids.pop(track_id, None)
