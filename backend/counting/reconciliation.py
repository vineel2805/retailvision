"""Occupancy drift correction reconciliation engine (FR-016, Zone-based)."""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from backend.counting.counter import VisitorCounter

logger = logging.getLogger("retailvision.system.reconciliation")


class OccupancyReconciler:
    """
    Monitors motion/idle state and performs drift reconciliation on occupancy counts
    to prevent accumulation of drift errors over multi-day continuous operation.
    """

    def __init__(
        self,
        idle_threshold_seconds: float = 300.0,  # 5 minutes idle
    ):
        self.idle_threshold_seconds = idle_threshold_seconds
        self.last_track_timestamp = time.time()

    def update_activity(self, active_track_count: int) -> None:
        """Call on every frame update with count of active tracks."""
        if active_track_count > 0:
            self.last_track_timestamp = time.time()

    def check_and_reconcile(
        self, counter: VisitorCounter, force: bool = False
    ) -> Optional[int]:
        """
        Check if store is idle (or force is True) and reconcile occupancy drift.
        Returns corrected occupancy value if adjustment occurred, or None.
        """
        now = time.time()
        idle_duration = now - self.last_track_timestamp

        if force or (idle_duration >= self.idle_threshold_seconds and counter.occupancy > 0):
            old_occ = counter.occupancy
            # Reconcile live occupancy against current active tracks in zone tracker
            counter.process_tracks([])
            new_occ = counter.occupancy

            logger.info(
                f"[RECONCILIATION] Drift corrected! Idle duration: {idle_duration:.1f}s. "
                f"Occupancy adjusted: {old_occ} -> {new_occ}"
            )
            return new_occ

        return None
