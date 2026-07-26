"""
RetailVision v2.0 — Local API Server & AI Counting Engine Entrypoint.

Run from project root with virtual environment active:

    python run_v2.py

Starts FastAPI backend on http://localhost:8000 with embedded React dashboard.
"""

import sys
import uvicorn
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.api.app import app

if __name__ == "__main__":
    print("=" * 60)
    print("Starting RetailVision v2.0 Local Engine & Web Dashboard")
    print("Access Local Dashboard at: http://localhost:8000")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
