"""FastAPI main application entrypoint for RetailVision Local Server."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import config.settings as settings
from backend.api.deps import engine
from backend.api.routes import camera, reports, settings_route, stats, video

logger = logging.getLogger("retailvision.api.app")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start system engine background tasks on startup and clean up on shutdown."""
    logger.info("Starting RetailVision Local API server...")
    engine.start()
    yield
    logger.info("Shutting down RetailVision Local API server...")
    engine.stop()


app = FastAPI(
    title="RetailVision Local API",
    version="2.0",
    description="AI-powered people counting & local telemetry API",
    lifespan=lifespan,
)

# Enable CORS for local desktop & web dashboards
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(stats.router)
app.include_router(video.router)
app.include_router(camera.router)
app.include_router(reports.router)
app.include_router(settings_route.router)


@app.get("/health")
def health_check():
    return {"status": "ok", "app": "RetailVision Local", "version": "2.0"}


@app.websocket("/ws/live")
async def websocket_live_stats(websocket: WebSocket):
    """Real-time WebSocket endpoint pushing live telemetry updates every 1 sec."""
    await websocket.accept()
    logger.info("WebSocket client connected to /ws/live")
    try:
        while True:
            telemetry = engine.get_system_telemetry()
            await websocket.send_json(telemetry)
            await asyncio.sleep(1.0)
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected from /ws/live")
    except Exception as e:
        logger.warning(f"WebSocket error: {e}")


# Mount built React frontend static files if dist folder exists
dist_dir = settings.PROJECT_ROOT / "frontend" / "dist"
if dist_dir.exists():
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="frontend")
