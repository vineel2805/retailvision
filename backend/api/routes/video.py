"""MJPEG Live Feed REST API router (FR-002, Fixes Bug 1 & Bug 2)."""

from __future__ import annotations

import time
import cv2
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from backend.api.deps import engine

router = APIRouter(prefix="/api/video_feed", tags=["Video"])


def generate_frames(hide_zone: bool = False):
    """Yields MJPEG video stream frames from the lock-protected latest frame buffer."""
    while True:
        frame = engine.get_latest_annotated_frame(hide_zone=hide_zone)
        if frame is None:
            time.sleep(0.03)
            continue

        ok, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ok:
            time.sleep(0.01)
            continue

        frame_bytes = buffer.tobytes()
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n" + frame_bytes + b"\r\n"
        )
        time.sleep(0.03)  # ~30 FPS stream rate


@router.get("")
def stream_video_feed(hide_zone: bool = False):
    """Returns multipart MJPEG live video stream."""
    return StreamingResponse(
        generate_frames(hide_zone=hide_zone),
        media_type="multipart/x-mixed-replace; boundary=frame",
    )
