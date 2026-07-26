"""Camera management, line calibration, and polygon zone configuration router (FR-001, FR-005, Phase 3)."""

import json
from typing import List, Tuple
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from backend.api.deps import engine
from backend.camera.capture import create_capture_source
from backend.counting.line import CountingLine
from backend.counting.zone import ZoneConfig

router = APIRouter(prefix="/api/camera", tags=["Camera"])


class LineConfigRequest(BaseModel):
    point_a: Tuple[int, int]
    point_b: Tuple[int, int]
    entry_direction: str = "negative_to_positive"


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
    """Return camera configuration, active zone polygon, and confirmation frames."""
    camera = engine.repository.get_camera_by_id(engine.camera_id)
    return {
        "camera": camera,
        "zone": {
            "polygon": engine.counter.zone_tracker.config.polygon,
            "confirmation_frames": engine.counter.zone_tracker.config.confirmation_frames,
        },
        "line": {
            "point_a": engine.counting_line.point_a if engine.counting_line else (40, 240),
            "point_b": engine.counting_line.point_b if engine.counting_line else (250, 240),
            "entry_direction": engine.counting_line.entry_direction if engine.counting_line else "negative_to_positive",
        },
    }


@router.get("/zone")
def get_zone_config():
    """Return current polygon zone coordinates and confirmation frames."""
    return {
        "polygon": engine.counter.zone_tracker.config.polygon,
        "confirmation_frames": engine.counter.zone_tracker.config.confirmation_frames,
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


@router.post("/line")
def update_line_config(config: LineConfigRequest):
    """Update virtual counting line coordinates and direction (Legacy)."""
    engine.counting_line = CountingLine(
        point_a=config.point_a,
        point_b=config.point_b,
        entry_direction=config.entry_direction,
    )
    return {"status": "success", "line": config}


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
