"""Offline queue & cloud sync worker (FR-012, FR-013, Section 14.2)."""

from __future__ import annotations

import logging
import time
from datetime import datetime
from typing import Optional
import requests

from backend.database.repository import CountingRepository

logger = logging.getLogger("retailvision.sync")


class SyncWorker:
    """
    Periodically aggregates hourly store summaries, enqueues them locally,
    and pushes unsynced items to the cloud API when internet connectivity is available.
    Guarantees no data loss during internet outages.
    """

    def __init__(
        self,
        repository: CountingRepository,
        store_id: str = "store-001",
        cloud_api_url: str = "http://localhost:8001",
        sync_interval_seconds: float = 30.0,
    ):
        self.repository = repository
        self.store_id = store_id
        self.cloud_api_url = cloud_api_url
        self.sync_interval_seconds = sync_interval_seconds

    def enqueue_current_hourly_summary(self) -> None:
        """Aggregate current hour totals and add to sync queue."""
        now = datetime.now()
        hourly_rows = self.repository.get_hourly_breakdown(now.date(), now.date())
        current_hour_str = f"{now.hour:02d}"

        row_for_hour = next((r for r in hourly_rows if r["hour"] == current_hour_str), None)
        entries = row_for_hour["entries"] if row_for_hour else 0
        exits = row_for_hour["exits"] if row_for_hour else 0
        occupancy = max(0, entries - exits)

        payload = {
            "store_id": self.store_id,
            "date": now.date().isoformat(),
            "hour": now.hour,
            "entries": entries,
            "exits": exits,
            "occupancy": occupancy,
            "timestamp": now.isoformat(),
        }

        self.repository.enqueue_sync_item(payload)
        logger.info(f"Enqueued store summary payload for sync: {payload}")

    def push_queued_items(self) -> int:
        """Push unsynced local items to cloud API."""
        items = self.repository.get_unsynced_items(limit=20)
        if not items:
            return 0

        synced_ids = []
        for item in items:
            item_id = item["id"]
            payload = item["payload"]
            try:
                resp = requests.post(
                    f"{self.cloud_api_url}/api/sync/store-summary",
                    json=payload,
                    timeout=5.0,
                )
                if resp.status_code in (200, 201):
                    synced_ids.append(item_id)
                else:
                    logger.warning(
                        f"Cloud sync API returned status {resp.status_code}: {resp.text}"
                    )
                    break
            except Exception as e:
                logger.info(f"Cloud sync offline / unreachable: {e}")
                break  # Retry next sync interval

        if synced_ids:
            self.repository.mark_items_synced(synced_ids)
            logger.info(f"Successfully synced {len(synced_ids)} payload(s) to cloud API.")

        return len(synced_ids)
