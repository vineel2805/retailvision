"""Live stats REST API router (FR-008)."""

from fastapi import APIRouter
from backend.api.deps import engine

router = APIRouter(prefix="/api/stats", tags=["Stats"])


@router.get("")
def get_live_stats():
    """Returns today's entries, exits, occupancy, FPS, CPU, RAM, camera and AI status."""
    return engine.get_system_telemetry()
