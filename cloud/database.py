"""Cloud Database layer storing Store Summaries (PRD Section 14.2)."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List

CLOUD_DB_PATH = Path(__file__).resolve().parent / "cloud_store.db"


def init_cloud_db() -> sqlite3.Connection:
    conn = sqlite3.connect(CLOUD_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS store_summary (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id TEXT NOT NULL,
            date DATE NOT NULL,
            hour INTEGER NOT NULL,
            entries INTEGER NOT NULL,
            exits INTEGER NOT NULL,
            occupancy INTEGER NOT NULL,
            synced_at DATETIME DEFAULT (datetime('now', 'localtime')),
            UNIQUE(store_id, date, hour)
        )
        """
    )
    conn.commit()
    return conn


class CloudRepository:

    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def upsert_store_summary(
        self,
        store_id: str,
        date_str: str,
        hour: int,
        entries: int,
        exits: int,
        occupancy: int,
    ) -> None:
        self.conn.execute(
            """
            INSERT INTO store_summary (store_id, date, hour, entries, exits, occupancy)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(store_id, date, hour) DO UPDATE SET
                entries = excluded.entries,
                exits = excluded.exits,
                occupancy = excluded.occupancy,
                synced_at = datetime('now', 'localtime')
            """,
            (store_id, date_str, hour, entries, exits, occupancy),
        )
        self.conn.commit()

    def get_latest_store_summary(self, store_id: str = "store-001") -> Dict[str, Any]:
        rows = self.conn.execute(
            """
            SELECT date, hour, entries, exits, occupancy, synced_at
            FROM store_summary
            WHERE store_id = ?
            ORDER BY date DESC, hour DESC
            """,
            (store_id,),
        ).fetchall()

        results = [dict(r) for r in rows]
        total_entries = sum(r["entries"] for r in results)
        total_exits = sum(r["exits"] for r in results)
        latest_occ = results[0]["occupancy"] if results else 0
        peak_hour_row = max(results, key=lambda x: x["entries"]) if results else None
        peak_hour_str = f"{peak_hour_row['hour']}:00" if peak_hour_row and peak_hour_row["entries"] > 0 else "N/A"

        return {
            "store_id": store_id,
            "total_entries": total_entries,
            "total_exits": total_exits,
            "current_occupancy": latest_occ,
            "peak_hour": peak_hour_str,
            "hourly_data": results,
        }
