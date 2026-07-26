"""YOLOv8n person detection wrapper (FR-003, FR-014, Section 13, Bug 2 Fix)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional, Tuple

import torch
from ultralytics import YOLO

from backend.ai.onnx_exporter import export_to_onnx
from backend.ai.roi import ROICropper

logger = logging.getLogger("retailvision.ai.detector")


class PersonDetector:
    """
    Loads YOLOv8 model (PyTorch or ONNX) and runs ByteTrack-backed tracking on frames.
    Supports ROI cropping, frame-skipping, and ONNX Runtime.
    """

    def __init__(
        self,
        model_path: str | Path,
        confidence: float = 0.4,
        inference_size: int = 640,
        device: str = "cpu",
        tracker_config: str = "bytetrack.yaml",
        person_class_id: int = 0,
        frame_skip: int = 1,
        roi_padding: Optional[int] = None,
        use_onnx: bool = False,
    ):
        self.confidence = confidence
        self.inference_size = inference_size
        self.device = device
        self.tracker_config = tracker_config
        self.person_class_id = person_class_id
        self.frame_skip = max(1, frame_skip)
        self.roi_cropper = ROICropper(padding=roi_padding) if roi_padding else None
        self.use_onnx = use_onnx

        self.frame_counter = 0
        self._last_results = None

        path = Path(model_path)
        if not path.is_absolute():
            path = Path.cwd() / path

        # Try ONNX format if requested
        if use_onnx:
            onnx_path = path.with_suffix(".onnx")
            if not onnx_path.exists():
                exported = export_to_onnx(path, imgsz=inference_size)
                if exported and exported.exists():
                    path = exported
            elif onnx_path.exists():
                path = onnx_path

        logger.info(f"Initializing PersonDetector with model: {path}")
        self.model_path = path
        # Explicitly define task='detect' to avoid ONNX task guessing warnings
        self.model = YOLO(str(path), task="detect")

    def track(
        self,
        frame,
        line_points: Optional[Tuple[Tuple[int, int], Tuple[int, int]]] = None,
    ):
        """
        Detect and track persons in a single frame.

        Uses model.track() with persist=True so ByteTrack IDs remain stable
        across consecutive frames (FR-004).
        Supports frame skipping and ROI cropping.
        """
        self.frame_counter += 1

        # Frame skipping logic
        if self.frame_skip > 1 and (self.frame_counter % self.frame_skip != 0):
            if self._last_results is not None:
                return self._last_results

        input_frame = frame
        roi_offset = (0, 0)

        # ROI cropping logic
        if self.roi_cropper and line_points:
            p1, p2 = line_points
            input_frame, (rx1, ry1, rx2, ry2) = self.roi_cropper.crop(frame, p1, p2)
            roi_offset = (rx1, ry1)

        results = self.model.track(
            input_frame,
            persist=True,
            classes=[self.person_class_id],
            conf=self.confidence,
            imgsz=self.inference_size,
            device=self.device,
            tracker=self.tracker_config,
            verbose=False,
        )

        # Re-adjust detection bounding boxes back to full frame coordinates if ROI cropped
        if roi_offset != (0, 0) and results and len(results) > 0:
            result = results[0]
            if result.boxes is not None and len(result.boxes) > 0:
                rx, ry = roi_offset
                if hasattr(result.boxes, "xyxy") and result.boxes.xyxy is not None:
                    offset = torch.tensor([rx, ry, rx, ry], device=result.boxes.xyxy.device)
                    result.boxes.xyxy += offset
                    if hasattr(result.boxes, "data") and result.boxes.data is not None:
                        result.boxes.data[:, 0:4] += offset

        self._last_results = results
        return results
