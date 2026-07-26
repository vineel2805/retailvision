"""Logging system setup for RetailVision (PRD Section 17)."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

import config.settings as settings


def setup_logging() -> None:
    """Configure system, AI, camera, app, and sync loggers."""
    log_dir = settings.PROJECT_ROOT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_format = logging.Formatter(
        "%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
    )

    loggers_config = {
        "retailvision": log_dir / "app.log",
        "retailvision.system": log_dir / "system.log",
        "retailvision.ai": log_dir / "ai.log",
        "retailvision.camera": log_dir / "camera.log",
        "retailvision.sync": log_dir / "sync.log",
    }

    for name, file_path in loggers_config.items():
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        # Avoid duplicate handlers if setup is called multiple times
        if not logger.handlers:
            file_handler = RotatingFileHandler(
                file_path, maxBytes=5 * 1024 * 1024, backupCount=3
            )
            file_handler.setFormatter(log_format)
            logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(log_format)
            logger.addHandler(console_handler)


def get_logger(module_name: str) -> logging.Logger:
    """Retrieve logger instance for a given module name."""
    return logging.getLogger(f"retailvision.{module_name}")
