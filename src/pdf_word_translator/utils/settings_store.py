"""Persistent UI and provider settings."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json
import os

from ..models import EN_RU, SUPPORTED_DIRECTIONS, TranslationDirection, direction_source_lang, direction_target_lang


SUPPORTED_UI_THEMES = {"light", "dark"}


@dataclass
class UiSettings:
    """User-facing settings stored on disk."""

    ui_font_size: int = 11
    ui_scale_percent: int = 100
    ui_theme: str = "dark"
    direction: TranslationDirection = EN_RU
    context_provider_id: str = "disabled"
    libretranslate_url: str = "http://127.0.0.1:5000"
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

    @classmethod
    def from_mapping(cls, payload: object) -> "UiSettings":
        if not isinstance(payload, dict):
            return cls().normalized()
        allowed_keys = cls.__dataclass_fields__.keys()
        filtered = {key: payload[key] for key in allowed_keys if key in payload}
        try:
            return cls(**filtered).normalized()
        except (TypeError, ValueError):
            return cls().normalized()

    def normalized(self) -> "UiSettings":
        """Clamp values into a safe range before they reach the GUI."""
        direction = self.direction if self.direction in SUPPORTED_DIRECTIONS else EN_RU

        provider_raw = self.context_provider_id if isinstance(self.context_provider_id, str) else str(self.context_provider_id or "disabled")
        provider = provider_raw.strip().lower() or "disabled"
        if provider not in {"disabled", "argos", "libretranslate", "yandex"}:
            provider = "disabled"

        try:
            ui_font_size = int(self.ui_font_size)
        except (TypeError, ValueError):
            ui_font_size = UiSettings.ui_font_size

        try:
            ui_scale_percent = int(self.ui_scale_percent)
        except (TypeError, ValueError):
            ui_scale_percent = UiSettings.ui_scale_percent

        theme_raw = self.ui_theme if isinstance(self.ui_theme, str) else str(self.ui_theme or "dark")
        ui_theme = theme_raw.strip().lower() or "dark"
        if ui_theme not in SUPPORTED_UI_THEMES:
            ui_theme = "dark"

        def _clean_text(value: object, default: str = "") -> str:
            if value is None:
                return default
            if isinstance(value, str):
                return value.strip() or default
            return str(value).strip() or default

        return UiSettings(
            ui_font_size=max(9, min(24, ui_font_size)),
            ui_scale_percent=max(80, min(180, ui_scale_percent)),
            ui_theme=ui_theme,
            direction=direction,
            context_provider_id=provider,
            libretranslate_url=_clean_text(self.libretranslate_url, "http://127.0.0.1:5000"),
            libretranslate_api_key=_clean_text(self.libretranslate_api_key),
            yandex_folder_id=_clean_text(self.yandex_folder_id),
            yandex_api_key=_clean_text(self.yandex_api_key),
            yandex_iam_token=_clean_text(self.yandex_iam_token),
        )


def _restrict_file_permissions(path: Path) -> None:
    if os.name != "posix":
        return
    try:
        os.chmod(path, 0o600)
    except OSError:
        return


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
        return UiSettings.from_mapping(payload)

    def save(self, settings: UiSettings) -> None:
        self._settings_file.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(settings.normalized())
        temp_path = self._settings_file.with_name(self._settings_file.name + ".tmp")
        temp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        _restrict_file_permissions(temp_path)
        os.replace(temp_path, self._settings_file)
        _restrict_file_permissions(self._settings_file)
