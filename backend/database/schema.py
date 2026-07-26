"""SQLite schema per PRD Section 14.1."""

import sqlite3
from pathlib import Path


SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cameras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_url TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'offline'
);

CREATE TABLE IF NOT EXISTS visitor_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL DEFAULT (datetime('now', 'localtime')),
    direction TEXT NOT NULL CHECK (direction IN ('entry', 'exit')),
    confidence REAL NOT NULL,
    tracking_id INTEGER NOT NULL,
    camera_id INTEGER NOT NULL,
    FOREIGN KEY (camera_id) REFERENCES cameras(id)
);

CREATE TABLE IF NOT EXISTS daily_summary (
    date DATE PRIMARY KEY,
    entries INTEGER NOT NULL DEFAULT 0,
    exits INTEGER NOT NULL DEFAULT 0,
    occupancy INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS sync_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payload TEXT NOT NULL,
    synced INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_visitor_events_timestamp
    ON visitor_events(timestamp);
CREATE INDEX IF NOT EXISTS idx_visitor_events_camera
    ON visitor_events(camera_id);
CREATE INDEX IF NOT EXISTS idx_sync_queue_synced
    ON sync_queue(synced);
"""


def init_database(db_path: Path) -> sqlite3.Connection:
    """Create tables if missing and return an open connection."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn
