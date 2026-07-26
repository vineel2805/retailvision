"""Comprehensive unit & integration test suite for RetailVision v2.0."""

from __future__ import annotations

import io
import sqlite3
import tempfile
import time
from datetime import date, datetime
from pathlib import Path

import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.ai.adaptive import AdaptivePerformanceManager
from backend.ai.detector import PersonDetector
from backend.ai.roi import ROICropper
from backend.camera.capture import DirectWebcamCapture, ThreadedCapture, create_capture_source
from backend.counting.counter import VisitorCounter
from backend.counting.line import CountingLine
from backend.counting.reconciliation import OccupancyReconciler
from backend.database.repository import CountingRepository
from backend.database.schema import init_database
from backend.sync.worker import SyncWorker
from backend.tracking.tracker import parse_tracks
from backend.utils.exporter import ReportExporter
from cloud.api.main import app as cloud_app
from cloud.auth.jwt import create_access_token


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    conn = init_database(db_path)
    yield conn
    conn.close()
    if db_path.exists():
        db_path.unlink()


def test_roi_cropper_full_height():
    cropper = ROICropper(padding=150)
    shape = (720, 1280, 3)
    p1 = (40, 240)
    p2 = (250, 240)

    x1, y1, x2, y2 = cropper.get_roi_bounds(shape, p1, p2)
    assert x1 == 0
    assert y1 == 0
    assert x2 == 400
    assert y2 == 720  # Preserves full vertical height so human bodies are not truncated


def test_adaptive_benchmarking():
    config = AdaptivePerformanceManager.benchmark_system()
    assert config.tier in ("low_power", "standard", "recommended")
    assert config.frame_skip >= 1
    assert config.inference_size in (320, 480, 640)


def test_repository_and_reports(temp_db):
    repo = CountingRepository(temp_db)
    cam_id = repo.ensure_camera("Test Cam", "usb", "0")
    assert cam_id > 0

    # Log visitor crossing events
    repo.log_visitor_event("entry", 0.95, 1, cam_id)
    repo.log_visitor_event("entry", 0.92, 2, cam_id)
    repo.log_visitor_event("exit", 0.88, 3, cam_id)

    today_summary = repo.get_daily_summary()
    assert today_summary["entries"] == 2
    assert today_summary["exits"] == 1
    assert today_summary["occupancy"] == 1

    # Hourly report query
    hourly = repo.get_hourly_breakdown(date.today(), date.today())
    assert len(hourly) > 0

    summary_data = repo.get_period_summary(date.today(), date.today())
    assert summary_data["total_entries"] == 2
    assert summary_data["total_exits"] == 1

    # Export formats
    csv_str = ReportExporter.to_csv(summary_data)
    assert "RetailVision Footfall Report" in csv_str

    xlsx_bytes = ReportExporter.to_xlsx(summary_data)
    assert len(xlsx_bytes) > 0

    pdf_bytes = ReportExporter.to_pdf(summary_data)
    assert len(pdf_bytes) > 0


def test_occupancy_reconciliation(temp_db):
    repo = CountingRepository(temp_db)
    line = CountingLine((0, 10), (100, 10), "negative_to_positive")
    counter = VisitorCounter(counting_line=line, repository=repo, camera_id=1, entries=5, exits=2)

    assert counter.occupancy == 3

    reconciler = OccupancyReconciler(idle_threshold_seconds=0.1)
    reconciler.last_track_timestamp -= 1.0  # simulate 1s idle

    corrected = reconciler.check_and_reconcile(counter, force=False)
    assert corrected == 0
    assert counter.occupancy == 0


def test_sync_queue(temp_db):
    repo = CountingRepository(temp_db)
    worker = SyncWorker(repository=repo, cloud_api_url="http://localhost:8001")

    item_id = repo.enqueue_sync_item({"test": "payload"})
    assert item_id > 0

    unsynced = repo.get_unsynced_items()
    assert len(unsynced) == 1
    assert unsynced[0]["payload"]["test"] == "payload"

    repo.mark_items_synced([item_id])
    assert len(repo.get_unsynced_items()) == 0


def test_cloud_auth_and_sync_api():
    client = TestClient(cloud_app)

    # Login
    login_resp = client.post("/api/auth/login", json={"username": "owner", "password": "retail2026"})
    assert login_resp.status_code == 200
    token = login_resp.json()["access_token"]

    # Sync payload
    sync_payload = {
        "store_id": "store-001",
        "date": "2026-07-26",
        "hour": 12,
        "entries": 10,
        "exits": 4,
        "occupancy": 6,
    }
    sync_resp = client.post("/api/sync/store-summary", json=sync_payload)
    assert sync_resp.status_code == 200

    # Get remote summary with auth header
    remote_resp = client.get(
        "/api/remote/summary",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert remote_resp.status_code == 200
    data = remote_resp.json()
    assert data["total_entries"] == 10
    assert data["current_occupancy"] == 6


def test_detector_and_tracking_flow():
    img = cv2.imread("retailvision-env/Lib/site-packages/ultralytics/assets/bus.jpg")

    det = PersonDetector("models/yolov8n.pt", roi_padding=None, use_onnx=False)
    results = det.track(img)
    tracks = parse_tracks(results)

    assert len(tracks) >= 3
    for t in tracks:
        assert t.track_id > 0
        assert t.confidence > 0.5
        assert len(t.bbox) == 4
