"""ONNX export and quantization helper for YOLOv8 models."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from ultralytics import YOLO

logger = logging.getLogger("retailvision.ai.onnx")


def export_to_onnx(
    model_path: Path | str,
    output_dir: Optional[Path | str] = None,
    int8: bool = False,
    imgsz: int = 640,
) -> Optional[Path]:
    """
    Export PyTorch YOLO model (.pt) to ONNX format.
    Returns path to exported ONNX model if successful, or None on failure.
    """
    model_path = Path(model_path)
    if not model_path.exists():
        logger.error(f"Model file not found: {model_path}")
        return None

    try:
        logger.info(f"Exporting {model_path} to ONNX (INT8={int8}, imgsz={imgsz})...")
        model = YOLO(str(model_path))
        onnx_file_str = model.export(
            format="onnx",
            imgsz=imgsz,
            int8=int8,
            simplify=True,
            verbose=False,
        )
        if onnx_file_str:
            onnx_path = Path(onnx_file_str)
            logger.info(f"Successfully exported ONNX model to {onnx_path}")
            return onnx_path
    except Exception as e:
        logger.warning(f"Failed to export model to ONNX: {e}")

    return None
