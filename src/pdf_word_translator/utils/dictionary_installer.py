"""Helpers for installing dictionary packs from the GUI and CLI."""
from __future__ import annotations

from pathlib import Path
import re
import shutil

from ..config import AppConfig
from ..models import EN_RU, RU_EN, SUPPORTED_DIRECTIONS, TranslationDirection
from .dictionary_builder import (
    DictionaryMetadata,
    DictionaryPackOptions,
    build_dictionary_from_csv,
    build_reverse_dictionary_from_csv,
)
from .dictionary_catalog import DictionaryPackSpec, available_pack_specs, pack_spec_by_id
from .freedict_importer import build_dictionary_from_freedict_tei, install_default_freedict_dictionary


def install_sqlite_pack(source_path: Path, runtime_dictionary_dir: Path) -> Path:
    source_path = Path(source_path)
    runtime_dictionary_dir = Path(runtime_dictionary_dir)
    runtime_dictionary_dir.mkdir(parents=True, exist_ok=True)
    destination = _unique_destination(runtime_dictionary_dir, source_path.stem, ".sqlite")
    shutil.copy2(source_path, destination)
    return destination


def import_csv_pack(
    source_path: Path,
    runtime_dictionary_dir: Path,
    *,
    direction: TranslationDirection = EN_RU,
    pack_options: DictionaryPackOptions | None = None,
) -> Path:
    source_path = Path(source_path)
    runtime_dictionary_dir = Path(runtime_dictionary_dir)
    runtime_dictionary_dir.mkdir(parents=True, exist_ok=True)
    destination = _unique_destination(runtime_dictionary_dir, source_path.stem, ".sqlite")
    metadata = pack_options or DictionaryMetadata(pack_name=source_path.stem, direction=direction, pack_kind="csv")
    if direction == RU_EN and source_path.name.endswith("_en_ru.csv"):
        return build_reverse_dictionary_from_csv(source_path, destination, metadata=metadata)
    return build_dictionary_from_csv(source_path, destination, metadata=metadata)


def import_reverse_csv_pack(source_path: Path, runtime_dictionary_dir: Path) -> Path:
    source_path = Path(source_path)
    runtime_dictionary_dir = Path(runtime_dictionary_dir)
    runtime_dictionary_dir.mkdir(parents=True, exist_ok=True)
    destination = _unique_destination(runtime_dictionary_dir, source_path.stem + "_reverse", ".sqlite")
    metadata = DictionaryMetadata(pack_name=source_path.stem + " RU→EN", direction=RU_EN, pack_kind="csv-reverse")
    return build_reverse_dictionary_from_csv(source_path, destination, metadata=metadata)


def import_freedict_pack(
    source_path: Path,
    runtime_dictionary_dir: Path,
    *,
    direction: TranslationDirection = EN_RU,
    pack_options: DictionaryPackOptions | None = None,
) -> Path:
    source_path = Path(source_path)
    runtime_dictionary_dir = Path(runtime_dictionary_dir)
    runtime_dictionary_dir.mkdir(parents=True, exist_ok=True)
    destination = _unique_destination(runtime_dictionary_dir, source_path.stem, ".sqlite")
    metadata = pack_options or DictionaryMetadata(pack_name=source_path.stem, direction=direction, pack_kind="freedict")
    return build_dictionary_from_freedict_tei(source_path, destination, direction=direction, metadata=metadata)


def install_default_pack(runtime_dictionary_dir: Path, download_dir: Path, *, direction: TranslationDirection = EN_RU) -> Path:
    metadata = DictionaryMetadata(
        pack_name="FreeDict EN→RU" if direction == EN_RU else "FreeDict RU→EN",
        direction=direction,
        pack_kind="general",
        description="FreeDict TEI import",
        source="FreeDict",
    )
    return install_default_freedict_dictionary(runtime_dictionary_dir, download_dir, direction=direction, metadata=metadata)


def catalog_entries(config: AppConfig) -> list[DictionaryPackSpec]:
    return available_pack_specs(config)


def available_catalog_items(config: AppConfig | None = None) -> list[DictionaryPackSpec]:
    return catalog_entries(config or AppConfig())


def install_catalog_entry(entry: DictionaryPackSpec, config: AppConfig) -> Path:
    if entry.install_mode == "bundled_csv":
        if entry.csv_path is None:
            raise RuntimeError(f"Пакет {entry.pack_id} не содержит CSV-источник")
        direction = RU_EN if entry.direction == RU_EN else EN_RU
        return import_csv_pack(entry.csv_path, config.runtime_dictionary_dir, direction=direction)
    if entry.install_mode == "freedict_remote":
        direction = RU_EN if entry.direction == RU_EN else EN_RU
        return install_default_pack(config.runtime_dictionary_dir, config.runtime_download_dir, direction=direction)
    raise RuntimeError(f"Неизвестный install_mode для пакета {entry.pack_id}: {entry.install_mode}")


def install_catalog_entry_by_id(config: AppConfig, pack_id: str) -> Path:
    return install_catalog_entry(pack_spec_by_id(config, pack_id), config)


def install_catalog_pack(entry: DictionaryPackSpec, runtime_dictionary_dir: Path, download_dir: Path) -> Path:
    temp_config = AppConfig(runtime_dictionary_dir=Path(runtime_dictionary_dir), runtime_download_dir=Path(download_dir))
    return install_catalog_entry(entry, temp_config)


def install_catalog(runtime_dictionary_dir: Path, download_dir: Path, pack_ids: list[str], config: AppConfig | None = None) -> list[Path]:
    resolved = config or AppConfig(runtime_dictionary_dir=Path(runtime_dictionary_dir), runtime_download_dir=Path(download_dir))
    return [install_catalog_entry_by_id(resolved, pack_id) for pack_id in pack_ids]


def _unique_destination(directory: Path, raw_name: str, suffix: str) -> Path:
    """Return the canonical destination for a pack.

    v4 intentionally overwrites an existing pack with the same sanitized name
    instead of creating *_1, *_2 duplicates. This keeps the in-app catalog and
    composite dictionary stable when the user reinstalls or refreshes a pack.
    """
    base_name = _sanitize_name(raw_name)
    return directory / f"{base_name}{suffix}"


def _sanitize_name(value: str) -> str:
    sanitized = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return sanitized.strip("._") or "dictionary_pack"
