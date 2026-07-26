"""Camera management, line calibration, and polygon zone configuration router (FR-001, FR-005, Phase 3)."""

import json
from typing import List, Tuple
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

import config.settings as settings
from backend.api.deps import engine
from backend.camera.capture import create_capture_source

router = APIRouter(prefix="/api/camera", tags=["Camera"])


class ZoneConfigRequest(BaseModel):
    polygon: List[Tuple[float, float]]
    confirmation_frames: int = 5


class CameraConfigRequest(BaseModel):
    name: str = "Store Camera"
    source_type: str = "usb"  # "usb", "rtsp", "onvif"
    source_url: str = "0"
    width: int = 1280
    height: int = 720
    fps: int = 30


@router.get("")
def get_camera_info():
    """Return camera configuration, active zone polygon, confirmation frames, and frame dimensions."""
    camera = engine.repository.get_camera_by_id(engine.camera_id)
    frame_width = engine.frame_width or settings.CAMERA_WIDTH
    frame_height = engine.frame_height or settings.CAMERA_HEIGHT
    return {
        "camera": camera,
        "zone": {
            "polygon": engine.counter.zone_tracker.config.polygon,
            "confirmation_frames": engine.counter.zone_tracker.config.confirmation_frames,
            "frame_width": frame_width,
            "frame_height": frame_height,
        },
    }


@router.get("/zone")
def get_zone_config():
    """Return current polygon zone coordinates, confirmation frames, and frame dimensions."""
    frame_width = engine.frame_width or settings.CAMERA_WIDTH
    frame_height = engine.frame_height or settings.CAMERA_HEIGHT
    return {
        "polygon": engine.counter.zone_tracker.config.polygon,
        "confirmation_frames": engine.counter.zone_tracker.config.confirmation_frames,
        "frame_width": frame_width,
        "frame_height": frame_height,
    }


@router.post("/zone")
def update_zone_config(config: ZoneConfigRequest):
    """Update active polygon zone coordinates and hysteresis confirmation frames (Phase 3)."""
    if len(config.polygon) < 3:
        raise HTTPException(status_code=400, detail="Polygon must contain at least 3 points.")

    engine.counter.zone_tracker.set_polygon(config.polygon)
    engine.counter.zone_tracker.config.confirmation_frames = max(1, config.confirmation_frames)

    # Persist in SQLite system_settings
    engine.repository.set_setting("zone_polygon", json.dumps(config.polygon))
    engine.repository.set_setting("zone_confirmation_frames", str(config.confirmation_frames))

    return {"status": "success", "zone": config}


@router.post("/config")
def update_camera_config(config: CameraConfigRequest):
    """Switch camera source (USB, RTSP, ONVIF)."""
    try:
        new_capture = create_capture_source(
            source_url=config.source_url,
            source_type=config.source_type,
            width=config.width,
            height=config.height,
            fps=config.fps,
        )
        if engine.capture:
            engine.capture.release()
        engine.capture = new_capture

        engine.camera_id = engine.repository.ensure_camera(
            name=config.name,
            source_type=config.source_type,
            source_url=config.source_url,
        )
        engine.counter.camera_id = engine.camera_id
        return {"status": "success", "camera_id": engine.camera_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to switch camera: {e}")
