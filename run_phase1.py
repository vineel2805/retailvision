"""
RetailVision Phase 1 — local counting engine.

Run from project root with the virtual environment active:

    python run_phase1.py

Adjust the virtual line coordinates in config/settings.py to match your
camera view before testing crossings.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import cv2

# Ensure project root is on sys.path when run as a script
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config.settings as settings
from backend.utils.line_calibrator import select_line_interactive
from backend.ai.detector import PersonDetector
from backend.camera.capture import WebcamCapture
from backend.counting.counter import VisitorCounter
from backend.counting.line import CountingLine
from backend.database.repository import CountingRepository
from backend.database.schema import init_database
from backend.tracking.tracker import parse_tracks
from backend.utils.overlay import draw_overlay


def main() -> int:
    print("RetailVision Phase 1 — starting local counting engine")
    print(f"Database: {settings.DB_PATH}")
    print(f"Line: {settings.LINE_POINT_1} -> {settings.LINE_POINT_2}")
    print(f"Entry direction: {settings.ENTRY_DIRECTION}")
    print("Press Q in the preview window to stop.\n")

    settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
    settings.MODELS_DIR.mkdir(parents=True, exist_ok=True)

    conn = init_database(settings.DB_PATH)
    repository = CountingRepository(conn)

    source_url = str(settings.CAMERA_INDEX)
    camera_id = repository.ensure_camera(
        name=settings.CAMERA_NAME,
        source_type=settings.CAMERA_SOURCE_TYPE,
        source_url=source_url,
    )

    model_path = settings.MODELS_DIR / settings.MODEL_NAME
    detector = PersonDetector(
        model_path=model_path,
        confidence=settings.CONFIDENCE_THRESHOLD,
        inference_size=settings.INFERENCE_SIZE,
        device=settings.DEVICE,
        tracker_config=settings.TRACKER_CONFIG,
        person_class_id=settings.PERSON_CLASS_ID,
    )

    

    counter = VisitorCounter(
        counting_line=counting_line,
        repository=repository,
        camera_id=camera_id,
    )
    counter.sync_from_database()
    print(
        f"Loaded today: entries={counter.entries} "
        f"exits={counter.exits} occupancy={counter.occupancy}\n"
    )

    capture = WebcamCapture(
        device_index=settings.CAMERA_INDEX,
        width=settings.CAMERA_WIDTH,
        height=settings.CAMERA_HEIGHT,
        fps=settings.CAMERA_FPS,
    )
    # NEW: let the user click the line instead of hardcoding it
    calibrated = select_line_interactive(capture)
    line_point_1 = calibrated[0] if calibrated else settings.LINE_POINT_1
    line_point_2 = calibrated[1] if calibrated else settings.LINE_POINT_2

    counting_line = CountingLine(
        point_a=line_point_1,
        point_b=line_point_2,
        entry_direction=settings.ENTRY_DIRECTION,
    )

    window_name = "RetailVision Phase 1"
    fps = 0.0
    frame_count = 0
    fps_timer = time.perf_counter()

    try:
        while True:
            ok, frame = capture.read()
            if not ok:
                print("Failed to read frame from webcam — retrying...")
                repository.set_camera_status(camera_id, "offline")
                time.sleep(0.5)
                continue

            repository.set_camera_status(camera_id, "online")

            results = detector.track(frame)
            tracks = parse_tracks(results)
            counter.process_tracks(tracks)

            frame_count += 1
            elapsed = time.perf_counter() - fps_timer
            if elapsed >= 1.0:
                fps = frame_count / elapsed
                frame_count = 0
                fps_timer = time.perf_counter()

            draw_overlay(
                frame=frame,
                counting_line=counting_line,
                tracks=tracks,
                entries=counter.entries,
                exits=counter.exits,
                occupancy=counter.occupancy,
                fps=fps,
            )

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), ord("Q")):
                break

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    finally:
        repository.set_camera_status(camera_id, "offline")
        capture.release()
        cv2.destroyAllWindows()
        conn.close()
        print(
            f"\nFinal — entries={counter.entries} exits={counter.exits} "
            f"occupancy={counter.occupancy}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
