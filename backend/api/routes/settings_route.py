"""Adaptive performance settings REST API router (FR-014)."""

from pydantic import BaseModel
from fastapi import APIRouter

from backend.api.deps import engine

router = APIRouter(prefix="/api/settings", tags=["Settings"])


class SettingsOverrideRequest(BaseModel):
    model_name: str = "yolov8n.pt"
    frame_skip: int = 1
    inference_size: int = 640
    roi_enabled: bool = True
    use_onnx: bool = False


@router.get("")
def get_settings():
    """Return active hardware benchmark and adaptive performance configuration."""
    return engine.adaptive_config.to_dict()


@router.post("")
def update_settings(req: SettingsOverrideRequest):
    """Override adaptive performance settings (FR-014)."""
    cfg = engine.adaptive_config
    cfg.model_name = req.model_name
    cfg.frame_skip = max(1, req.frame_skip)
    cfg.inference_size = req.inference_size
    cfg.roi_enabled = req.roi_enabled
    cfg.use_onnx = req.use_onnx

    # Re-apply updated settings to detector
    engine.detector.frame_skip = cfg.frame_skip
    engine.detector.inference_size = cfg.inference_size
    engine.detector.use_onnx = cfg.use_onnx

    return {"status": "success", "config": cfg.to_dict()}
