"""ROI (Region of Interest) cropping helper for line-crossing inference efficiency (Fixes Bug 2)."""

from __future__ import annotations

from typing import Tuple
import numpy as np


class ROICropper:
    """
    Crops video frame around the counting line before running inference.
    Preserves full human vertical height so standing/walking persons are not truncated.
    Translates bounding box coordinates back to full frame space.
    """

    def __init__(self, padding: int = 150):
        self.padding = padding

    def get_roi_bounds(
        self,
        frame_shape: Tuple[int, int, ...],
        point1: Tuple[int, int],
        point2: Tuple[int, int],
    ) -> Tuple[int, int, int, int]:
        """
        Calculate bounding box (x1, y1, x2, y2) around line segment with padding.
        Preserves full frame height to ensure standing/walking human bodies are never cut off.
        """
        height, width = frame_shape[:2]

        x1 = min(point1[0], point2[0]) - self.padding
        x2 = max(point1[0], point2[0]) + self.padding

        # Preserve full vertical height so human heads and legs are not truncated
        y1 = 0
        y2 = height

        x1 = max(0, int(x1))
        x2 = min(width, int(x2))

        # Fallback if x crop is too narrow
        if (x2 - x1) < 200:
            x1 = max(0, min(point1[0], point2[0]) - 200)
            x2 = min(width, max(point1[0], point2[0]) + 200)

        return x1, y1, x2, y2

    def crop(
        self,
        frame: np.ndarray,
        point1: Tuple[int, int],
        point2: Tuple[int, int],
    ) -> Tuple[np.ndarray, Tuple[int, int, int, int]]:
        """Crop frame to ROI around the given points."""
        x1, y1, x2, y2 = self.get_roi_bounds(frame.shape, point1, point2)
        roi_frame = frame[y1:y2, x1:x2]
        return roi_frame, (x1, y1, x2, y2)
