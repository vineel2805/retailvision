"""Cloud API server for RetailVision Remote Monitoring (FR-012, FR-015)."""

from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from cloud.auth.jwt import DEMO_USERS, create_access_token, verify_token
from cloud.database import CloudRepository, init_cloud_db

conn = init_cloud_db()
cloud_repo = CloudRepository(conn)

app = FastAPI(
    title="RetailVision Cloud Remote API",
    version="2.0",
    description="Anonymized store summary cloud sync and remote viewer API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


class SyncPayload(BaseModel):
    store_id: str = "store-001"
    date: str
    hour: int
    entries: int
    exits: int
    occupancy: int


@app.post("/api/auth/login")
def login_remote_user(req: LoginRequest):
    """Issue JWT token for remote store owner access (FR-015)."""
    expected_pass = DEMO_USERS.get(req.username)
    if not expected_pass or expected_pass != req.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    token = create_access_token({"sub": req.username, "role": "viewer"})
    return {"access_token": token, "token_type": "bearer"}


@app.post("/api/sync/store-summary")
def receive_store_summary(payload: SyncPayload):
    """Receive anonymized aggregate hourly numeric counts from local store engine."""
    cloud_repo.upsert_store_summary(
        store_id=payload.store_id,
        date_str=payload.date,
        hour=payload.hour,
        entries=payload.entries,
        exits=payload.exits,
        occupancy=payload.occupancy,
    )
    return {"status": "synced", "store_id": payload.store_id}


@app.get("/api/remote/summary")
def get_remote_store_summary(user: dict = Depends(verify_token)):
    """Read-only aggregate metrics for store owner remote view (FR-012)."""
    return cloud_repo.get_latest_store_summary(store_id="store-001")


# Serve remote dashboard static files if compiled
remote_dist = Path(__file__).resolve().parent.parent / "web-dashboard" / "dist"
if remote_dist.exists():
    app.mount("/", StaticFiles(directory=str(remote_dist), html=True), name="remote_dashboard")
