"""Data access for cameras, visitor events, and daily summaries."""

from __future__ import annotations

import sqlite3
from datetime import date, datetime
from typing import Optional


class CountingRepository:
    """SQLite repository for Phase 1 counting events."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def ensure_camera(
        self,
        name: str,
        source_type: str,
        source_url: str,
    ) -> int:
        """Return existing camera id or insert a new row."""
        row = self._conn.execute(
            "SELECT id FROM cameras WHERE source_url = ?",
            (source_url,),
        ).fetchone()
        if row:
            camera_id = row["id"]
            self._conn.execute(
                "UPDATE cameras SET name = ?, source_type = ?, status = 'online' WHERE id = ?",
                (name, source_type, camera_id),
            )
        else:
            cursor = self._conn.execute(
                """
                INSERT INTO cameras (name, source_type, source_url, status)
                VALUES (?, ?, ?, 'online')
                """,
                (name, source_type, source_url),
            )
            camera_id = cursor.lastrowid
        self._conn.commit()
        return camera_id

    def set_camera_status(self, camera_id: int, status: str) -> None:
        self._conn.execute(
            "UPDATE cameras SET status = ? WHERE id = ?",
            (status, camera_id),
        )
        self._conn.commit()

    def log_visitor_event(
        self,
        direction: str,
        confidence: float,
        tracking_id: int,
        camera_id: int,
        timestamp: Optional[datetime] = None,
    ) -> int:
        """Insert a crossing event and refresh today's daily summary."""
        ts = timestamp or datetime.now()
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        cursor = self._conn.execute(
            """
            INSERT INTO visitor_events (timestamp, direction, confidence, tracking_id, camera_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (ts_str, direction, confidence, tracking_id, camera_id),
        )
        event_id = cursor.lastrowid

        today = ts.date()
        entries, exits = self.get_today_event_totals(today)
        occupancy = max(0, entries - exits)
        self._upsert_daily_summary(today, entries, exits, occupancy)
        self._conn.commit()
        return event_id

    def get_today_event_totals(self, day: Optional[date] = None) -> tuple[int, int]:
        """Count entry/exit events for the given calendar day."""
        day = day or date.today()
        day_str = day.isoformat()
        row = self._conn.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN direction = 'entry' THEN 1 ELSE 0 END), 0) AS entries,
                COALESCE(SUM(CASE WHEN direction = 'exit' THEN 1 ELSE 0 END), 0) AS exits
            FROM visitor_events
            WHERE date(timestamp) = ?
            """,
            (day_str,),
        ).fetchone()
        return int(row["entries"]), int(row["exits"])

    def get_daily_summary(self, day: Optional[date] = None) -> dict:
        day = day or date.today()
        entries, exits = self.get_today_event_totals(day)
        occupancy = max(0, entries - exits)
        return {"date": day.isoformat(), "entries": entries, "exits": exits, "occupancy": occupancy}

    def _upsert_daily_summary(
        self,
        day: date,
        entries: int,
        exits: int,
        occupancy: int,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO daily_summary (date, entries, exits, occupancy)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(date) DO UPDATE SET
                entries = excluded.entries,
                exits = excluded.exits,
                occupancy = excluded.occupancy
            """,
            (day.isoformat(), entries, exits, occupancy),
        )
