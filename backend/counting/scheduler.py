"""Scheduled background jobs (FR-011 automatic midnight reset)."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from apscheduler.schedulers.background import BackgroundScheduler

if TYPE_CHECKING:
    from backend.counting.counter import VisitorCounter
    from backend.counting.reconciliation import OccupancyReconciler

logger = logging.getLogger("retailvision.system.scheduler")


class CounterScheduler:
    """Manages periodic tasks: automatic midnight reset and drift reconciliation."""

    def __init__(
        self,
        counter: VisitorCounter,
        reconciler: Optional[OccupancyReconciler] = None,
        reset_hour: int = 0,
        reset_minute: int = 0,
    ):
        self.counter = counter
        self.reconciler = reconciler
        self.reset_hour = reset_hour
        self.reset_minute = reset_minute
        self.scheduler = BackgroundScheduler(daemon=True)

    def start(self) -> None:
        """Schedule midnight reset and periodic drift reconciliation."""
        # Daily midnight reset job (FR-011)
        self.scheduler.add_job(
            self.perform_daily_reset,
            "cron",
            hour=self.reset_hour,
            minute=self.reset_minute,
            id="midnight_reset",
            replace_existing=True,
        )

        # Periodic drift correction check every 15 minutes (FR-016)
        if self.reconciler:
            self.scheduler.add_job(
                self.perform_drift_check,
                "interval",
                minutes=15,
                id="drift_reconciliation",
                replace_existing=True,
            )

        self.scheduler.start()
        logger.info(
            f"Scheduler started. Daily reset scheduled for {self.reset_hour:02d}:{self.reset_minute:02d}"
        )

    def perform_daily_reset(self) -> None:
        """Reset in-memory counters for new calendar day (retaining DB events)."""
        logger.info("[SCHEDULER] Performing daily counter reset at midnight...")
        if self.reconciler:
            self.reconciler.check_and_reconcile(self.counter, force=True)

        self.counter.entries = 0
        self.counter.exits = 0
        logger.info("[SCHEDULER] Daily counter reset complete. Entries=0, Exits=0, Occupancy=0")

    def perform_drift_check(self) -> None:
        """Trigger idle drift reconciliation check."""
        if self.reconciler:
            self.reconciler.check_and_reconcile(self.counter, force=False)

    def stop(self) -> None:
        """Shutdown background scheduler."""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("Scheduler stopped.")
