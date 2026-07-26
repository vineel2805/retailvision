"""Phase 1 unit tests for ZoneOccupancyTracker and VisitorCounter."""

from __future__ import annotations

import tempfile
from pathlib import Path
import pytest

from backend.counting.counter import VisitorCounter
from backend.counting.zone import ZoneConfig, ZoneOccupancyTracker
from backend.database.repository import CountingRepository
from backend.database.schema import init_database
from backend.tracking.tracker import TrackedPerson


@pytest.fixture
def temp_db():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = Path(f.name)
    conn = init_database(db_path)
    yield conn
    conn.close()
    if db_path.exists():
        db_path.unlink()


def test_foot_point_and_polygon_test():
    # Polygon box: x from 0 to 100, y from 0 to 100
    poly = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    config = ZoneConfig(camera_id=1, polygon=poly, confirmation_frames=3)
    tracker = ZoneOccupancyTracker(config)

    # Person 1: foot at (50, 50) -> inside polygon
    p1 = TrackedPerson(track_id=1, bbox=(40, 20, 60, 50), centroid=(50.0, 35.0), confidence=0.9)
    assert tracker.is_foot_inside(p1.bbox) is True

    # Person 2: foot at (150, 150) -> outside polygon
    p2 = TrackedPerson(track_id=2, bbox=(140, 120, 160, 150), centroid=(150.0, 135.0), confidence=0.85)
    assert tracker.is_foot_inside(p2.bbox) is False


def test_hysteresis_and_live_occupancy():
    poly = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    config = ZoneConfig(camera_id=1, polygon=poly, confirmation_frames=3)
    tracker = ZoneOccupancyTracker(config)

    # Track 1 starts outside
    t_outside = TrackedPerson(track_id=10, bbox=(140, 120, 160, 150), centroid=(150.0, 135.0), confidence=0.9)

    res1 = tracker.update([t_outside])
    assert res1.occupancy == 0
    assert len(res1.events) == 0

    # Track 1 moves inside -> frame 1
    t_inside = TrackedPerson(track_id=10, bbox=(40, 20, 60, 50), centroid=(50.0, 35.0), confidence=0.9)
    res2 = tracker.update([t_inside])
    assert res2.occupancy == 0  # Hysteresis frame 1/3 (not confirmed yet)
    assert len(res2.events) == 0

    # Frame 2
    res3 = tracker.update([t_inside])
    assert res3.occupancy == 0  # Hysteresis frame 2/3

    # Frame 3 -> Hysteresis threshold reached! Confirmed inside!
    res4 = tracker.update([t_inside])
    assert res4.occupancy == 1  # Live occupancy = 1
    assert len(res4.events) == 1
    assert res4.events[0].direction == "entry"
    assert res4.events[0].track_id == 10


def test_stale_track_pruning():
    poly = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    config = ZoneConfig(camera_id=1, polygon=poly, confirmation_frames=1)
    tracker = ZoneOccupancyTracker(config)

    t_in = TrackedPerson(track_id=5, bbox=(10, 10, 30, 30), centroid=(20.0, 20.0), confidence=0.9)
    res1 = tracker.update([t_in])
    assert res1.occupancy == 1

    # Next frame, track 5 disappears
    res2 = tracker.update([])
    assert res2.occupancy == 0
    assert 5 not in tracker._confirmed_state


def test_visitor_counter_integration(temp_db):
    repo = CountingRepository(temp_db)
    poly = [(0.0, 0.0), (100.0, 0.0), (100.0, 100.0), (0.0, 100.0)]
    config = ZoneConfig(camera_id=1, polygon=poly, confirmation_frames=1)
    tracker = ZoneOccupancyTracker(config)

    counter = VisitorCounter(repository=repo, camera_id=1, zone_tracker=tracker)

    t1 = TrackedPerson(track_id=1, bbox=(10, 10, 30, 30), centroid=(20.0, 20.0), confidence=0.9)
    counter.process_tracks([t1])

    assert counter.occupancy == 1
    assert counter.entries == 1
    assert counter.exits == 0
