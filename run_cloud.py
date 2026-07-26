"""
RetailVision Cloud Server Entrypoint (FR-012, FR-015).

Run from project root with virtual environment active:

    python run_cloud.py

Starts Cloud API & Remote Read-Only Web Dashboard on http://localhost:8001.
"""

import sys
import uvicorn
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from cloud.api.main import app

if __name__ == "__main__":
    print("=" * 60)
    print("Starting RetailVision Cloud Server & Remote Web Dashboard")
    print("Access Remote Dashboard at: http://localhost:8001")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
