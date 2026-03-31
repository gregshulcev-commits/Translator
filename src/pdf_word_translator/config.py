"""Application configuration and path helpers.

The MVP keeps runtime state in XDG-style directories under the user's home
folder, while packaged resources stay inside the project tree.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
BUNDLED_PACKS_DIR = DATA_ROOT / "packs"
DEFAULT_STARTER_CSV = DATA_ROOT / "starter_dictionary.csv"
DEFAULT_STARTER_DB = DATA_ROOT / "starter_dictionary.sqlite"
DEFAULT_STARTER_RU_EN_CSV = DATA_ROOT / "starter_dictionary_ru_en.csv"
DEFAULT_STARTER_RU_EN_DB = DATA_ROOT / "starter_dictionary_ru_en.sqlite"


def _xdg_path(env_name: str, fallback: Path) -> Path:
    raw = os.environ.get(env_name)
    return Path(raw).expanduser() if raw else fallback

def _env_flag(env_name: str, default: bool = False) -> bool:
    raw = str(os.environ.get(env_name, "")).strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


RUNTIME_DATA_DIR = _xdg_path("XDG_DATA_HOME", Path.home() / ".local" / "share") / "pdf_word_translator_mvp"
RUNTIME_CACHE_DIR = _xdg_path("XDG_CACHE_HOME", Path.home() / ".cache") / "pdf_word_translator_mvp"
RUNTIME_LOG_DIR = RUNTIME_CACHE_DIR / "logs"
RUNTIME_DICTIONARY_DIR = RUNTIME_DATA_DIR / "dictionaries"
RUNTIME_DOWNLOAD_DIR = RUNTIME_CACHE_DIR / "downloads"
EXTERNAL_PLUGIN_DIR = RUNTIME_DATA_DIR / "plugins"
SETTINGS_FILE = RUNTIME_DATA_DIR / "settings.json"
ENABLE_EXTERNAL_PLUGINS = _env_flag("PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS", False)


@dataclass(frozen=True)
class AppConfig:
    """Resolved configuration for the running application."""

    project_root: Path = PROJECT_ROOT
    data_root: Path = DATA_ROOT
    bundled_packs_dir: Path = BUNDLED_PACKS_DIR
    starter_dictionary_csv: Path = DEFAULT_STARTER_CSV
    starter_dictionary_db: Path = DEFAULT_STARTER_DB
    starter_dictionary_ru_en_csv: Path = DEFAULT_STARTER_RU_EN_CSV
    starter_dictionary_ru_en_db: Path = DEFAULT_STARTER_RU_EN_DB
    runtime_data_dir: Path = RUNTIME_DATA_DIR
    runtime_cache_dir: Path = RUNTIME_CACHE_DIR
    runtime_log_dir: Path = RUNTIME_LOG_DIR
    runtime_dictionary_dir: Path = RUNTIME_DICTIONARY_DIR
    runtime_download_dir: Path = RUNTIME_DOWNLOAD_DIR
    external_plugin_dir: Path = EXTERNAL_PLUGIN_DIR
    settings_file: Path = SETTINGS_FILE
    enable_external_plugins: bool = ENABLE_EXTERNAL_PLUGINS

    def ensure_runtime_directories(self) -> None:
        """Create runtime directories if they do not exist yet."""
        for path in (
            self.runtime_data_dir,
            self.runtime_cache_dir,
            self.runtime_log_dir,
            self.runtime_dictionary_dir,
            self.runtime_download_dir,
            self.external_plugin_dir,
        ):
            path.mkdir(parents=True, exist_ok=True)
