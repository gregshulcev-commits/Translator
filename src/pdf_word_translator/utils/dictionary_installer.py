"""Helpers for installing dictionary packs from the GUI.

The GUI calls the same import/build logic that is available via CLI tools, so
users can manage dictionaries without leaving the application.
"""
from __future__ import annotations

from pathlib import Path
import re
import shutil

from .dictionary_builder import build_dictionary_from_csv
from .freedict_importer import build_dictionary_from_freedict_tei, install_default_freedict_dictionary


def install_sqlite_pack(source_path: Path, runtime_dictionary_dir: Path) -> Path:
    """Copy an existing SQLite pack into the runtime dictionary directory."""
    source_path = Path(source_path)
    runtime_dictionary_dir = Path(runtime_dictionary_dir)
    runtime_dictionary_dir.mkdir(parents=True, exist_ok=True)
    destination = _unique_destination(runtime_dictionary_dir, source_path.stem, ".sqlite")
    shutil.copy2(source_path, destination)
    return destination


def import_csv_pack(source_path: Path, runtime_dictionary_dir: Path) -> Path:
    """Build a SQLite pack from a CSV glossary and install it."""
    source_path = Path(source_path)
    runtime_dictionary_dir = Path(runtime_dictionary_dir)
    runtime_dictionary_dir.mkdir(parents=True, exist_ok=True)
    destination = _unique_destination(runtime_dictionary_dir, source_path.stem, ".sqlite")
    return build_dictionary_from_csv(source_path, destination)


def import_freedict_pack(source_path: Path, runtime_dictionary_dir: Path) -> Path:
    """Convert a FreeDict TEI source into a runtime SQLite pack."""
    source_path = Path(source_path)
    runtime_dictionary_dir = Path(runtime_dictionary_dir)
    runtime_dictionary_dir.mkdir(parents=True, exist_ok=True)
    destination = _unique_destination(runtime_dictionary_dir, source_path.stem, ".sqlite")
    return build_dictionary_from_freedict_tei(source_path, destination)


def install_default_pack(runtime_dictionary_dir: Path, download_dir: Path) -> Path:
    """Download and build the default general EN→RU dictionary pack."""
    return install_default_freedict_dictionary(runtime_dictionary_dir, download_dir)


def _unique_destination(directory: Path, raw_name: str, suffix: str) -> Path:
    base_name = _sanitize_name(raw_name)
    candidate = directory / f"{base_name}{suffix}"
    counter = 1
    while candidate.exists():
        candidate = directory / f"{base_name}_{counter}{suffix}"
        counter += 1
    return candidate


def _sanitize_name(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return sanitized.strip("._") or "dictionary_pack"
