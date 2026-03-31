"""Persistent UI and provider settings."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json

from ..models import EN_RU, SUPPORTED_DIRECTIONS, TranslationDirection, direction_source_lang, direction_target_lang


@dataclass
class UiSettings:
    """User-facing settings stored on disk."""

    ui_font_size: int = 11
    direction: TranslationDirection = EN_RU
    context_provider_id: str = "disabled"
    libretranslate_url: str = "https://libretranslate.com"
    libretranslate_api_key: str = ""
    yandex_folder_id: str = ""
    yandex_api_key: str = ""
    yandex_iam_token: str = ""

    @property
    def source_lang(self) -> str:
        return direction_source_lang(self.direction)

    @property
    def target_lang(self) -> str:
        return direction_target_lang(self.direction)

    @property
    def context_provider(self) -> str:
        return self.context_provider_id

    @context_provider.setter
    def context_provider(self, value: str) -> None:
        self.context_provider_id = value

    def normalized(self) -> "UiSettings":
        """Clamp values into a safe range before they reach the GUI."""
        direction = self.direction if self.direction in SUPPORTED_DIRECTIONS else EN_RU
        provider = (self.context_provider_id or "disabled").strip().lower()
        if provider not in {"disabled", "argos", "libretranslate", "yandex"}:
            provider = "disabled"
        return UiSettings(
            ui_font_size=max(9, min(24, int(self.ui_font_size))),
            direction=direction,
            context_provider_id=provider,
            libretranslate_url=(self.libretranslate_url or "https://libretranslate.com").strip() or "https://libretranslate.com",
            libretranslate_api_key=(self.libretranslate_api_key or "").strip(),
            yandex_folder_id=(self.yandex_folder_id or "").strip(),
            yandex_api_key=(self.yandex_api_key or "").strip(),
            yandex_iam_token=(self.yandex_iam_token or "").strip(),
        )


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
        if isinstance(payload, dict):
            return UiSettings(**payload).normalized()
        return UiSettings().normalized()

    def save(self, settings: UiSettings) -> None:
        self._settings_file.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(settings.normalized())
        self._settings_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
