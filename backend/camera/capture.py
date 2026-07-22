"""USB webcam capture via OpenCV."""

from __future__ import annotations

import cv2


class WebcamCapture:
    """Wraps cv2.VideoCapture for a USB camera device."""

    def __init__(
        self,
        device_index: int = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
    ):
        self.device_index = device_index
        self._cap = cv2.VideoCapture(device_index)
        if not self._cap.isOpened():
            raise RuntimeError(f"Could not open webcam at index {device_index}")

        self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        self._cap.set(cv2.CAP_PROP_FPS, fps)

    @property
    def is_open(self) -> bool:
        return self._cap.isOpened()

    def read(self):
        """Return (success, frame)."""
        return self._cap.read()

    def release(self) -> None:
        self._cap.release()
