"""Persistent UI settings.

The project only exposes one end-user setting for now: interface font size.
The implementation is intentionally tiny so it can later grow into a more
complete preferences subsystem without affecting the rest of the application.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json


@dataclass
class UiSettings:
    """User-facing settings stored on disk."""

    ui_font_size: int = 11

    def normalized(self) -> "UiSettings":
        """Clamp values into a safe range before they reach the GUI."""
        return UiSettings(ui_font_size=max(9, min(18, int(self.ui_font_size))))


class SettingsStore:
    """Load and save ``UiSettings`` as JSON."""

    def __init__(self, settings_file: Path):
        self._settings_file = Path(settings_file)

    def load(self) -> UiSettings:
        if not self._settings_file.exists():
            return UiSettings()
        try:
            payload = json.loads(self._settings_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, ValueError):
            return UiSettings()
        return UiSettings(**payload).normalized()

    def save(self, settings: UiSettings) -> None:
        self._settings_file.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(settings.normalized())
        self._settings_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
