"""Camera management and virtual line calibration router (FR-001, FR-005)."""

from typing import Tuple
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException

from backend.api.deps import engine
from backend.camera.capture import create_capture_source
from backend.counting.line import CountingLine

router = APIRouter(prefix="/api/camera", tags=["Camera"])


class LineConfigRequest(BaseModel):
    point_a: Tuple[int, int]
    point_b: Tuple[int, int]
    entry_direction: str = "negative_to_positive"


class CameraConfigRequest(BaseModel):
    name: str = "Store Camera"
    source_type: str = "usb"  # "usb", "rtsp", "onvif"
    source_url: str = "0"
    width: int = 1280
    height: int = 720
    fps: int = 30


@router.get("")
def get_camera_info():
    """Return camera configuration and active line coordinates."""
    camera = engine.repository.get_camera_by_id(engine.camera_id)
    return {
        "camera": camera,
        "line": {
            "point_a": engine.counting_line.point_a,
            "point_b": engine.counting_line.point_b,
            "entry_direction": engine.counting_line.entry_direction,
        },
    }


@router.post("/line")
def update_line_config(config: LineConfigRequest):
    """Update virtual counting line coordinates and direction."""
    engine.counting_line = CountingLine(
        point_a=config.point_a,
        point_b=config.point_b,
        entry_direction=config.entry_direction,
    )
    engine.counter.counting_line = engine.counting_line
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
