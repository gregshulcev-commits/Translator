"""Logging helpers for the application."""
from __future__ import annotations

from logging.handlers import RotatingFileHandler
from pathlib import Path
import logging


def setup_logging(log_dir: Path) -> Path:
    """Configure console and rotating file logging.

    Returns the resolved log file path so the UI can surface it if needed.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / "app.log"

    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Avoid duplicating handlers when tests or smoke scripts initialize logging
    # more than once.
    if root.handlers:
        return log_path

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = RotatingFileHandler(log_path, maxBytes=1_000_000, backupCount=3, encoding="utf-8")
    file_handler.setFormatter(formatter)

    root.addHandler(console_handler)
    root.addHandler(file_handler)
    return log_path
