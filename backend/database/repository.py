"""Data access for cameras, visitor events, daily summaries, reports, settings, and offline sync queue."""

from __future__ import annotations

import json
import sqlite3
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple


class CountingRepository:
    """SQLite repository for visitor counting events, reporting, and settings."""

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

    def get_cameras(self) -> List[Dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM cameras ORDER BY id ASC").fetchall()
        return [dict(row) for row in rows]

    def get_camera_by_id(self, camera_id: int) -> Optional[Dict[str, Any]]:
        row = self._conn.execute("SELECT * FROM cameras WHERE id = ?", (camera_id,)).fetchone()
        return dict(row) if row else None

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

    # FR-009 Reports & Hourly Breakdown Queries
    def get_hourly_breakdown(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[Dict[str, Any]]:
        """Return hourly breakdown of entries, exits, and peak status for range."""
        start_date = start_date or date.today()
        end_date = end_date or date.today()

        rows = self._conn.execute(
            """
            SELECT
                date(timestamp) AS event_date,
                strftime('%H', timestamp) AS hour,
                COALESCE(SUM(CASE WHEN direction = 'entry' THEN 1 ELSE 0 END), 0) AS entries,
                COALESCE(SUM(CASE WHEN direction = 'exit' THEN 1 ELSE 0 END), 0) AS exits
            FROM visitor_events
            WHERE date(timestamp) BETWEEN ? AND ?
            GROUP BY date(timestamp), strftime('%H', timestamp)
            ORDER BY event_date ASC, hour ASC
            """,
            (start_date.isoformat(), end_date.isoformat()),
        ).fetchall()

        results = [dict(r) for r in rows]

        # Calculate peak hour
        max_entries = max((r["entries"] for r in results), default=0)
        for r in results:
            r["is_peak_hour"] = (r["entries"] == max_entries and max_entries > 0)

        return results

    def get_period_summary(
        self,
        start_date: date,
        end_date: date,
    ) -> Dict[str, Any]:
        """Aggregate total entries, exits, peak hour for date range."""
        hourly = self.get_hourly_breakdown(start_date, end_date)
        total_entries = sum(h["entries"] for h in hourly)
        total_exits = sum(h["exits"] for h in hourly)
        peak_hour_row = max(hourly, key=lambda x: x["entries"]) if hourly else None
        peak_hour_str = f"{peak_hour_row['hour']}:00" if peak_hour_row and peak_hour_row['entries'] > 0 else "N/A"

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "total_entries": total_entries,
            "total_exits": total_exits,
            "peak_hour": peak_hour_str,
            "hourly_breakdown": hourly,
        }

    # FR-013 Sync Queue Operations
    def enqueue_sync_item(self, payload: Dict[str, Any]) -> int:
        payload_json = json.dumps(payload)
        cursor = self._conn.execute(
            "INSERT INTO sync_queue (payload, synced) VALUES (?, 0)",
            (payload_json,),
        )
        self._conn.commit()
        return cursor.lastrowid

    def get_unsynced_items(self, limit: int = 50) -> List[Dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT id, payload, created_at FROM sync_queue WHERE synced = 0 ORDER BY id ASC LIMIT ?",
            (limit,),
        ).fetchall()
        items = []
        for r in rows:
            items.append({
                "id": r["id"],
                "payload": json.loads(r["payload"]),
                "created_at": r["created_at"],
            })
        return items

    def mark_items_synced(self, item_ids: List[int]) -> None:
        if not item_ids:
            return
        placeholders = ",".join("?" for _ in item_ids)
        self._conn.execute(
            f"UPDATE sync_queue SET synced = 1 WHERE id IN ({placeholders})",
            item_ids,
        )
        self._conn.commit()

    # System Settings Operations
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        row = self._conn.execute(
            "SELECT value FROM system_settings WHERE key = ?",
            (key,),
        ).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        self._conn.execute(
            """
            INSERT INTO system_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
        self._conn.commit()
