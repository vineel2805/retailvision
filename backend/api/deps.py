"""Dependency injection and global state manager for the local FastAPI app (Fixes Bug 1 & Bug 2)."""

from __future__ import annotations

import logging
import psutil
import sqlite3
import threading
import time
from typing import Optional, Tuple

import cv2
import numpy as np

import config.settings as settings
from backend.ai.adaptive import AdaptiveConfig, AdaptivePerformanceManager
from backend.ai.detector import PersonDetector
from backend.camera.capture import BaseCapture, create_capture_source
from backend.counting.counter import VisitorCounter
from backend.counting.line import CountingLine
from backend.counting.reconciliation import OccupancyReconciler
from backend.counting.scheduler import CounterScheduler
from backend.database.repository import CountingRepository
from backend.database.schema import init_database
from backend.tracking.tracker import parse_tracks
from backend.utils.logger import setup_logging
from backend.utils.overlay import draw_overlay

logger = logging.getLogger("retailvision.api")


class SystemEngine:
    """Manages local video capture, AI detector, visitor counter, and background scheduler."""

    def __init__(self):
        setup_logging()
        settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
        settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)

        self.conn: sqlite3.Connection = init_database(settings.DB_PATH)
        self.repository = CountingRepository(self.conn)

        # Benchmark hardware adaptive tier
        self.adaptive_config: AdaptiveConfig = AdaptivePerformanceManager.benchmark_system()

        # Camera source setup
        self.camera_id = self.repository.ensure_camera(
            name=settings.CAMERA_NAME,
            source_type=settings.CAMERA_SOURCE_TYPE,
            source_url=str(settings.CAMERA_INDEX),
        )

        self.capture: BaseCapture = create_capture_source(
            source_url=settings.CAMERA_INDEX,
            source_type=settings.CAMERA_SOURCE_TYPE,
            width=settings.CAMERA_WIDTH,
            height=settings.CAMERA_HEIGHT,
            fps=settings.CAMERA_FPS,
        )

        # Counting Line
        self.counting_line = CountingLine(
            point_a=settings.LINE_POINT_1,
            point_b=settings.LINE_POINT_2,
            entry_direction=settings.ENTRY_DIRECTION,
        )

        # Visitor Counter
        self.counter = VisitorCounter(
            counting_line=self.counting_line,
            repository=self.repository,
            camera_id=self.camera_id,
        )
        self.counter.sync_from_database()

        # Person Detector (default roi_padding=None so full human height is preserved)
        model_path = settings.MODELS_DIR / self.adaptive_config.model_name
        if not model_path.exists():
            model_path = settings.MODELS_DIR / "yolov8n.pt"

        self.detector = PersonDetector(
            model_path=model_path,
            confidence=settings.CONFIDENCE_THRESHOLD,
            inference_size=self.adaptive_config.inference_size,
            device=settings.DEVICE,
            tracker_config=settings.TRACKER_CONFIG,
            person_class_id=settings.PERSON_CLASS_ID,
            frame_skip=self.adaptive_config.frame_skip,
            roi_padding=None,  # Preserves full body height for reliable detections
            use_onnx=self.adaptive_config.use_onnx,
        )

        # Drift Reconciler and Scheduler
        self.reconciler = OccupancyReconciler(idle_threshold_seconds=300.0)
        self.scheduler = CounterScheduler(counter=self.counter, reconciler=self.reconciler)

        self.fps: float = 0.0
        self.ai_health_status: str = "healthy"  # "healthy", "degraded", "restarting"
        self._is_running: bool = False

        self._latest_annotated_frame: Optional[np.ndarray] = None
        self._frame_lock = threading.Lock()
        self._processing_thread: Optional[threading.Thread] = None

    def get_system_telemetry(self) -> dict:
        """Collect current system stats (entries, exits, occupancy, FPS, CPU, RAM, camera/AI health)."""
        camera_status = "online" if (self.capture and self.capture.is_open) else "offline"
        cpu_usage = psutil.cpu_percent(interval=None)
        ram_usage = psutil.virtual_memory().percent

        return {
            "entries": self.counter.entries,
            "exits": self.counter.exits,
            "occupancy": self.counter.occupancy,
            "fps": round(self.fps, 1),
            "cpu_usage": cpu_usage,
            "ram_usage": ram_usage,
            "camera_status": camera_status,
            "ai_health": self.ai_health_status,
            "tier": self.adaptive_config.tier,
            "line_p1": self.counting_line.point_a,
            "line_p2": self.counting_line.point_b,
        }

    def _processing_loop(self) -> None:
        """Dedicated background loop running detection, counting, and overlay rendering."""
        frame_count = 0
        fps_timer = time.perf_counter()

        while self._is_running:
            if not self.capture or not self.capture.is_open:
                time.sleep(0.05)
                continue

            ok, frame = self.capture.read()
            if not ok or frame is None:
                time.sleep(0.01)
                continue

            try:
                line_points = (self.counting_line.point_a, self.counting_line.point_b)
                results = self.detector.track(frame, line_points=line_points)
                tracks = parse_tracks(results)
                self.counter.process_tracks(tracks)
                self.reconciler.update_activity(len(tracks))
                self.ai_health_status = "healthy"
            except Exception as e:
                logger.error(f"AI Detection error in main engine loop: {e}")
                self.ai_health_status = "degraded"
                tracks = []

            frame_count += 1
            elapsed = time.perf_counter() - fps_timer
            if elapsed >= 1.0:
                self.fps = frame_count / elapsed
                frame_count = 0
                fps_timer = time.perf_counter()

            # Render overlay on frame
            draw_overlay(
                frame=frame,
                counting_line=self.counting_line,
                tracks=tracks,
                entries=self.counter.entries,
                exits=self.counter.exits,
                occupancy=self.counter.occupancy,
                fps=self.fps,
            )

            with self._frame_lock:
                self._latest_annotated_frame = frame.copy()

            time.sleep(0.005)

    def get_latest_annotated_frame(self) -> Optional[np.ndarray]:
        """Return latest annotated frame safely from shared buffer."""
        with self._frame_lock:
            if self._latest_annotated_frame is None:
                return None
            return self._latest_annotated_frame.copy()

    def start(self) -> None:
        if self._is_running:
            return
        self._is_running = True
        self.scheduler.start()
        self._processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self._processing_thread.start()
        logger.info("SystemEngine processing loop started.")

    def stop(self) -> None:
        self._is_running = False
        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=2.0)
        self.scheduler.stop()
        if self.capture:
            self.capture.release()
        if self.conn:
            self.conn.close()
        logger.info("SystemEngine cleanly stopped.")


engine = SystemEngine()
