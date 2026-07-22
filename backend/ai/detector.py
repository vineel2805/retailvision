"""YOLOv8n person detection wrapper (FR-003)."""

from __future__ import annotations

from pathlib import Path

from ultralytics import YOLO


class PersonDetector:
    """Loads YOLOv8-nano and runs ByteTrack-backed tracking on frames."""

    def __init__(
        self,
        model_path: str | Path,
        confidence: float = 0.4,
        inference_size: int = 640,
        device: str = "cpu",
        tracker_config: str = "bytetrack.yaml",
        person_class_id: int = 0,
    ):
        self.confidence = confidence
        self.inference_size = inference_size
        self.device = device
        self.tracker_config = tracker_config
        self.person_class_id = person_class_id

        path = Path(model_path)
        if not path.is_absolute():
            path = Path.cwd() / path
        self.model = YOLO(str(path))

    def track(self, frame):
        """
        Detect and track persons in a single frame.

        Uses model.track() with persist=True so ByteTrack IDs remain stable
        across consecutive frames (FR-004).
        """
        return self.model.track(
            frame,
            persist=True,
            classes=[self.person_class_id],
            conf=self.confidence,
            imgsz=self.inference_size,
            device=self.device,
            tracker=self.tracker_config,
            verbose=False,
        )
