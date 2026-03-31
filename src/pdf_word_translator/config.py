"""Application configuration and path helpers.

The MVP keeps runtime state in XDG-style directories under the user's home
folder, while packaged resources stay inside the project tree.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


PACKAGE_ROOT = Path(__file__).resolve().parent
# ``src/pdf_word_translator`` -> project root.
PROJECT_ROOT = PACKAGE_ROOT.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
DEFAULT_STARTER_CSV = DATA_ROOT / "starter_dictionary.csv"
DEFAULT_STARTER_DB = DATA_ROOT / "starter_dictionary.sqlite"


def _xdg_path(env_name: str, fallback: Path) -> Path:
    raw = os.environ.get(env_name)
    return Path(raw).expanduser() if raw else fallback


RUNTIME_DATA_DIR = _xdg_path("XDG_DATA_HOME", Path.home() / ".local" / "share") / "pdf_word_translator_mvp"
RUNTIME_CACHE_DIR = _xdg_path("XDG_CACHE_HOME", Path.home() / ".cache") / "pdf_word_translator_mvp"
RUNTIME_LOG_DIR = RUNTIME_CACHE_DIR / "logs"
RUNTIME_DICTIONARY_DIR = RUNTIME_DATA_DIR / "dictionaries"
RUNTIME_DOWNLOAD_DIR = RUNTIME_CACHE_DIR / "downloads"
EXTERNAL_PLUGIN_DIR = RUNTIME_DATA_DIR / "plugins"
SETTINGS_FILE = RUNTIME_DATA_DIR / "settings.json"


@dataclass(frozen=True)
class AppConfig:
    """Resolved configuration for the running application."""

    starter_dictionary_csv: Path = DEFAULT_STARTER_CSV
    starter_dictionary_db: Path = DEFAULT_STARTER_DB
    runtime_data_dir: Path = RUNTIME_DATA_DIR
    runtime_cache_dir: Path = RUNTIME_CACHE_DIR
    runtime_log_dir: Path = RUNTIME_LOG_DIR
    runtime_dictionary_dir: Path = RUNTIME_DICTIONARY_DIR
    runtime_download_dir: Path = RUNTIME_DOWNLOAD_DIR
    external_plugin_dir: Path = EXTERNAL_PLUGIN_DIR
    settings_file: Path = SETTINGS_FILE

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
