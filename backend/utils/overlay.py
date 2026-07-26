"""OpenCV overlay drawing for zone occupancy and live telemetry."""

from __future__ import annotations

from typing import List, Optional, Set, Tuple

import cv2
import numpy as np

from backend.counting.zone import ZoneOccupancyTracker
from backend.tracking.tracker import TrackedPerson

Point = Tuple[float, float]


def draw_overlay(
    frame: np.ndarray,
    tracks: List[TrackedPerson],
    entries: int,
    exits: int,
    occupancy: int,
    fps: float,
    zone_tracker: Optional[ZoneOccupancyTracker] = None,
    inside_track_ids: Optional[Set[int]] = None,
) -> None:
    """Draw polygon occupancy zone, track bounding boxes, foot-points, and HUD stats."""
    if zone_tracker and zone_tracker.config.polygon:
        _draw_zone_polygon(frame, zone_tracker.config.polygon)

    _draw_tracks(frame, tracks, inside_track_ids, zone_tracker)
    _draw_hud(frame, entries, exits, occupancy, fps)


def _draw_zone_polygon(frame: np.ndarray, polygon: List[Point]) -> None:
    """Draw semi-transparent filled polygon zone with bright outline."""
    if len(polygon) < 3:
        return

    pts = np.array(polygon, dtype=np.int32)
    overlay = frame.copy()
    cv2.fillPoly(overlay, [pts], (255, 180, 0))  # Warm cyan/amber tint
    cv2.addWeighted(overlay, 0.15, frame, 0.85, 0, frame)

    cv2.polylines(frame, [pts], isClosed=True, color=(255, 220, 0), thickness=2, lineType=cv2.LINE_AA)


def _draw_tracks(
    frame: np.ndarray,
    tracks: List[TrackedPerson],
    inside_track_ids: Optional[Set[int]] = None,
    zone_tracker: Optional[ZoneOccupancyTracker] = None,
) -> None:
    """Draw track bounding boxes, foot-point markers, and IN/OUT status labels."""
    for person in tracks:
        x1, y1, x2, y2 = person.bbox
        foot_x = int((x1 + x2) / 2.0)
        foot_y = int(y2)

        is_inside = False
        if inside_track_ids is not None:
            is_inside = person.track_id in inside_track_ids
        elif zone_tracker:
            is_inside = zone_tracker.is_foot_inside(person.bbox)

        box_color = (0, 220, 0) if is_inside else (255, 180, 0)
        status_tag = "[IN]" if is_inside else "[OUT]"

        # Draw bounding box
        cv2.rectangle(frame, (x1, y1), (x2, y2), box_color, 2)

        # Draw foot-point dot at bottom-center of bounding box
        cv2.circle(frame, (foot_x, foot_y), 6, box_color, -1, lineType=cv2.LINE_AA)

        label = f"ID {person.track_id} {person.confidence:.2f} {status_tag}"
        cv2.putText(
            frame,
            label,
            (x1, max(y1 - 8, 14)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            box_color,
            1,
            cv2.LINE_AA,
        )


def _draw_hud(frame: np.ndarray, entries: int, exits: int, occupancy: int, fps: float) -> None:
    h, w = frame.shape[:2]
    panel_h = 70
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, panel_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.65, frame, 0.35, 0, frame)

    text_occupancy = f"LIVE OCCUPANCY: {occupancy}"
    text_stats = f"Entries: {entries}   Exits: {exits}   FPS: {fps:.1f}"

    cv2.putText(
        frame,
        text_occupancy,
        (16, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )

    cv2.putText(
        frame,
        text_stats,
        (16, 56),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (220, 220, 220),
        1,
        cv2.LINE_AA,
    )
