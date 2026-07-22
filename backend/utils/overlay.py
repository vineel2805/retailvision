"""OpenCV overlay drawing for Phase 1 live preview."""

from __future__ import annotations

from typing import List, Tuple

import cv2

from backend.counting.line import CountingLine
from backend.tracking.tracker import TrackedPerson

Point = Tuple[int, int]


def draw_overlay(
    frame,
    counting_line: CountingLine,
    tracks: List[TrackedPerson],
    entries: int,
    exits: int,
    occupancy: int,
    fps: float,
) -> None:
    """Draw counting line, detections, and stats on the frame in-place."""
    _draw_counting_line(frame, counting_line)
    _draw_tracks(frame, tracks)
    _draw_hud(frame, entries, exits, occupancy, fps)


def _draw_counting_line(frame, counting_line: CountingLine) -> None:
    p1 = (int(counting_line.point_a[0]), int(counting_line.point_a[1]))
    p2 = (int(counting_line.point_b[0]), int(counting_line.point_b[1]))
    cv2.line(frame, p1, p2, (0, 255, 255), 2)
    cv2.circle(frame, p1, 6, (0, 200, 255), -1)
    cv2.circle(frame, p2, 6, (0, 200, 255), -1)
    cv2.putText(
        frame,
        "COUNTING LINE",
        (p1[0], p1[1] - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0, 255, 255),
        1,
        cv2.LINE_AA,
    )


def _draw_tracks(frame, tracks: List[TrackedPerson]) -> None:
    for person in tracks:
        x1, y1, x2, y2 = person.bbox
        cx, cy = int(person.centroid[0]), int(person.centroid[1])
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.circle(frame, (cx, cy), 4, (0, 0, 255), -1)
        label = f"ID {person.track_id} {person.confidence:.2f}"
        cv2.putText(
            frame,
            label,
            (x1, max(y1 - 8, 12)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.45,
            (0, 255, 0),
            1,
            cv2.LINE_AA,
        )


def _draw_hud(frame, entries: int, exits: int, occupancy: int, fps: float) -> None:
    h, w = frame.shape[:2]
    panel_h = 90
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, panel_h), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.55, frame, 0.45, 0, frame)

    lines = [
        f"Entries: {entries}   Exits: {exits}   Occupancy: {occupancy}",
        f"FPS: {fps:.1f}   Press Q to quit",
    ]
    for i, text in enumerate(lines):
        cv2.putText(
            frame,
            text,
            (12, 28 + i * 28),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
