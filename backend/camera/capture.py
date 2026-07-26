"""Multi-camera stream capture supporting USB webcam, RTSP, and ONVIF with thread-safe capture (FR-001, Bug 1 Fix)."""

from __future__ import annotations

import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union

import cv2
import numpy as np

logger = logging.getLogger("retailvision.camera")


class BaseCapture(ABC):
    """Abstract interface for all video capture sources."""

    @property
    @abstractmethod
    def is_open(self) -> bool:
        """Check if video source is currently opened."""
        pass

    @abstractmethod
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Return (success, frame)."""
        pass

    @abstractmethod
    def release(self) -> None:
        """Release underlying camera or stream resource."""
        pass


class DirectWebcamCapture(BaseCapture):
    """Raw cv2.VideoCapture wrapper for USB camera."""

    def __init__(
        self,
        device_index: Union[int, str] = 0,
        width: int = 640,
        height: int = 480,
        fps: int = 30,
    ):
        if isinstance(device_index, str) and device_index.isdigit():
            device_index = int(device_index)

        self.device_index = device_index
        self._cap = cv2.VideoCapture(device_index)
        if not self._cap.isOpened():
            logger.warning(f"Could not open webcam at index/source {device_index}")

        if self._cap.isOpened():
            self._cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
            self._cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
            self._cap.set(cv2.CAP_PROP_FPS, fps)

    @property
    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.is_open:
            return False, None
        return self._cap.read()

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class DirectRTSPCapture(BaseCapture):
    """Raw cv2.VideoCapture wrapper for RTSP streams."""

    def __init__(
        self,
        rtsp_url: str,
        width: int = 1280,
        height: int = 720,
        fps: int = 30,
        reconnect_interval: float = 2.0,
    ):
        self.rtsp_url = rtsp_url
        self.width = width
        self.height = height
        self.fps = fps
        self.reconnect_interval = reconnect_interval
        self._cap: Optional[cv2.VideoCapture] = None
        self._last_reconnect = 0.0

        self._connect()

    def _connect(self) -> bool:
        logger.info(f"Connecting to RTSP stream: {self.rtsp_url}")
        self._cap = cv2.VideoCapture(self.rtsp_url, cv2.CAP_FFMPEG)
        if self._cap.isOpened():
            self._cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            logger.info("RTSP connection established successfully.")
            return True
        logger.warning(f"Failed to open RTSP stream: {self.rtsp_url}")
        return False

    @property
    def is_open(self) -> bool:
        return self._cap is not None and self._cap.isOpened()

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        if not self.is_open:
            now = time.time()
            if now - self._last_reconnect >= self.reconnect_interval:
                self._last_reconnect = now
                self._connect()
            if not self.is_open:
                return False, None

        ok, frame = self._cap.read()
        if not ok:
            logger.warning("RTSP read frame failed — triggering reconnection attempt")
            if self._cap:
                self._cap.release()
                self._cap = None
            return False, None
        return ok, frame

    def release(self) -> None:
        if self._cap is not None:
            self._cap.release()
            self._cap = None


class ThreadedCapture(BaseCapture):
    """
    Thread-safe capture wrapper (Fixes Bug 1).
    A single dedicated background capture thread owns the ONLY call to raw_capture.read().
    Consumers read from a lock-protected latest frame buffer.
    """

    def __init__(self, raw_capture: BaseCapture):
        self.raw_capture = raw_capture
        self._latest_frame: Optional[np.ndarray] = None
        self._latest_ok: bool = False
        self._lock = threading.Lock()
        self._running = True
        self._is_released = False

        self._thread = threading.Thread(target=self._capture_loop, daemon=True)
        self._thread.start()

    def _capture_loop(self) -> None:
        """Single background thread continuously pulling frames from cv2.VideoCapture."""
        while self._running:
            if not self.raw_capture.is_open:
                time.sleep(0.05)
                continue

            ok, frame = self.raw_capture.read()
            with self._lock:
                self._latest_ok = ok
                if ok and frame is not None:
                    self._latest_frame = frame.copy()
                else:
                    self._latest_frame = None

            time.sleep(0.005)

    @property
    def is_open(self) -> bool:
        with self._lock:
            return not self._is_released and self.raw_capture.is_open

    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Thread-safe frame access from shared buffer."""
        with self._lock:
            if self._is_released or not self._latest_ok or self._latest_frame is None:
                return False, None
            return True, self._latest_frame.copy()

    def release(self) -> None:
        """Safely stops thread first, then releases VideoCapture guarded by lock."""
        with self._lock:
            if self._is_released:
                return
            self._is_released = True
            self._running = False

        if self._thread.is_alive():
            self._thread.join(timeout=2.0)

        with self._lock:
            self.raw_capture.release()
            logger.info("ThreadedCapture cleanly released underlying camera resource.")


# Aliases for backward compatibility
class WebcamCapture(ThreadedCapture):
    def __init__(self, device_index: Union[int, str] = 0, width: int = 640, height: int = 480, fps: int = 30):
        super().__init__(DirectWebcamCapture(device_index, width, height, fps))


class RTSPCapture(ThreadedCapture):
    def __init__(self, rtsp_url: str, width: int = 1280, height: int = 720, fps: int = 30):
        super().__init__(DirectRTSPCapture(rtsp_url, width, height, fps))


class ONVIFCapture(ThreadedCapture):
    def __init__(self, source_url: str, width: int = 1280, height: int = 720, fps: int = 30):
        rtsp_endpoint = source_url if source_url.startswith("rtsp://") else f"rtsp://{source_url}"
        super().__init__(DirectRTSPCapture(rtsp_endpoint, width, height, fps))


def create_capture_source(
    source_url: Union[str, int],
    source_type: str = "usb",
    width: int = 640,
    height: int = 480,
    fps: int = 30,
) -> BaseCapture:
    """Factory method returning thread-safe capture wrapper."""
    stype = str(source_type).lower()
    if stype == "rtsp" or str(source_url).startswith("rtsp://"):
        raw = DirectRTSPCapture(str(source_url), width=width, height=height, fps=fps)
    elif stype == "onvif":
        endpoint = str(source_url) if str(source_url).startswith("rtsp://") else f"rtsp://{source_url}"
        raw = DirectRTSPCapture(endpoint, width=width, height=height, fps=fps)
    else:
        raw = DirectWebcamCapture(device_index=source_url, width=width, height=height, fps=fps)

    return ThreadedCapture(raw)
