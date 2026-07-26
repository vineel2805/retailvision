"""Parse Ultralytics track results into simple person records (FR-004)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

logger = logging.getLogger("retailvision.ai.tracker")


@dataclass(frozen=True)
class TrackedPerson:
    """One detected person with a temporary tracking id."""

    track_id: int
    bbox: Tuple[int, int, int, int]  # x1, y1, x2, y2
    centroid: Tuple[float, float]
    confidence: float


def parse_tracks(results) -> List[TrackedPerson]:
    """Extract tracked persons from the first YOLO Results object."""
    if not results:
        return []

    result = results[0]
    if result.boxes is None or len(result.boxes) == 0:
        return []

    boxes = result.boxes
    ids = boxes.id
    if ids is None:
        logger.warning(
            f"Detections found ({len(boxes)} boxes), but ByteTrack assigned no track IDs (boxes.id is None)."
        )
        return []

    tracked: List[TrackedPerson] = []
    xyxy = boxes.xyxy.cpu().numpy()
    confidences = boxes.conf.cpu().numpy()
    track_ids = ids.int().cpu().numpy()

    for i, track_id in enumerate(track_ids):
        x1, y1, x2, y2 = xyxy[i]
        cx = (x1 + x2) / 2.0
        cy = (y1 + y2) / 2.0
        tracked.append(
            TrackedPerson(
                track_id=int(track_id),
                bbox=(int(x1), int(y1), int(x2), int(y2)),
                centroid=(cx, cy),
                confidence=float(confidences[i]),
            )
        )

    logger.debug(f"Parsed {len(tracked)} active person tracks.")
    return tracked
