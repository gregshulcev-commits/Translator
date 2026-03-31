"""GUI-friendly helpers for installed dictionary pack management."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from ..config import AppConfig
from ..models import DictionaryPackInfo
from ..plugins.dictionary_sqlite import SQLiteDictionaryPlugin


class DictionaryManagerError(RuntimeError):
    """Raised when an installed dictionary pack cannot be managed safely."""


@dataclass(frozen=True)
class InstalledDictionaryRecord:
    pack_info: DictionaryPackInfo
    db_path: Path
    bundled: bool
    removable: bool

    @property
    def pack_id(self) -> str:
        return self.pack_info.pack_id

    @property
    def title(self) -> str:
        return self.pack_info.title

    @property
    def direction(self) -> str:
        return self.pack_info.direction

    @property
    def category(self) -> str:
        return self.pack_info.category

    @property
    def description(self) -> str:
        return self.pack_info.description

    @property
    def source(self) -> str:
        return self.pack_info.source


def list_installed_dictionary_records(config: AppConfig) -> list[InstalledDictionaryRecord]:
    records: list[InstalledDictionaryRecord] = []
    seen_paths: set[Path] = set()

    for db_path, bundled in _candidate_dictionary_paths(config):
        resolved = _safe_resolve(db_path)
        if resolved in seen_paths or not resolved.exists() or not resolved.is_file():
            continue
        seen_paths.add(resolved)
        try:
            plugin = SQLiteDictionaryPlugin(resolved)
        except Exception:
            continue
        try:
            info = plugin.pack_info()
        finally:
            plugin.close()
        records.append(
            InstalledDictionaryRecord(
                pack_info=info,
                db_path=resolved,
                bundled=bundled,
                removable=(not bundled and _is_within(resolved, config.runtime_dictionary_dir)),
            )
        )

    return sorted(records, key=lambda item: (item.bundled, item.direction, item.title.lower(), item.db_path.name.lower()))


def remove_installed_dictionary(record: InstalledDictionaryRecord, config: AppConfig) -> Path:
    path = _safe_resolve(record.db_path)
    runtime_dir = _safe_resolve(config.runtime_dictionary_dir)

    if record.bundled:
        raise DictionaryManagerError("Встроенные словари нельзя удалить из GUI. Можно удалить только пользовательские пакеты.")
    if not _is_within(path, runtime_dir):
        raise DictionaryManagerError("Удалять можно только словари из пользовательской runtime-папки приложения.")
    if path.is_symlink() or not path.exists() or not path.is_file():
        raise DictionaryManagerError(f"Словарь не найден или путь небезопасен: {path}")

    try:
        os.unlink(path)
    except OSError as exc:
        raise DictionaryManagerError(f"Не удалось удалить словарь {path.name}: {exc}") from exc
    return path


def _candidate_dictionary_paths(config: AppConfig) -> list[tuple[Path, bool]]:
    paths = [
        (config.starter_dictionary_db, True),
        (config.starter_dictionary_ru_en_db, True),
    ]
    runtime_paths = sorted(Path(config.runtime_dictionary_dir).glob("*.sqlite"))
    paths.extend((path, False) for path in runtime_paths)
    return paths


def _safe_resolve(path: Path) -> Path:
    return Path(path).expanduser().resolve()


def _is_within(path: Path, parent: Path) -> bool:
    path = _safe_resolve(path)
    parent = _safe_resolve(parent)
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True
