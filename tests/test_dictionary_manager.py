from __future__ import annotations

from pathlib import Path

import pytest

from pdf_word_translator.config import AppConfig, DATA_ROOT
from pdf_word_translator.utils.dictionary_installer import import_csv_pack
from pdf_word_translator.utils.dictionary_manager import (
    DictionaryManagerError,
    InstalledDictionaryRecord,
    list_installed_dictionary_records,
    remove_installed_dictionary,
)


def test_list_installed_dictionary_records_marks_bundled_and_runtime(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime_dictionaries"
    runtime_dir.mkdir()
    runtime_db = import_csv_pack(DATA_ROOT / "packs" / "technical_en_ru.csv", runtime_dir)
    config = AppConfig(runtime_dictionary_dir=runtime_dir)

    records = list_installed_dictionary_records(config)

    bundled = [record for record in records if record.bundled]
    runtime = [record for record in records if record.db_path == runtime_db]
    assert bundled
    assert runtime
    assert runtime[0].removable is True


def test_remove_installed_dictionary_refuses_bundled_pack(tmp_path: Path) -> None:
    config = AppConfig(runtime_dictionary_dir=tmp_path / "runtime")
    record = list_installed_dictionary_records(config)[0]

    with pytest.raises(DictionaryManagerError):
        remove_installed_dictionary(record, config)


def test_remove_installed_dictionary_deletes_runtime_pack(tmp_path: Path) -> None:
    runtime_dir = tmp_path / "runtime_dictionaries"
    runtime_dir.mkdir()
    runtime_db = import_csv_pack(DATA_ROOT / "packs" / "technical_en_ru.csv", runtime_dir)
    config = AppConfig(runtime_dictionary_dir=runtime_dir)
    records = list_installed_dictionary_records(config)
    record = next(item for item in records if item.db_path == runtime_db)

    removed_path = remove_installed_dictionary(record, config)

    assert removed_path == runtime_db.resolve()
    assert not runtime_db.exists()


def test_remove_installed_dictionary_rejects_outside_runtime_path(tmp_path: Path) -> None:
    outside_db = tmp_path / "outside.sqlite"
    outside_db.write_text("stub", encoding="utf-8")
    record = InstalledDictionaryRecord(
        pack_info=type("Pack", (), {
            "pack_id": "outside",
            "title": "Outside",
            "direction": "en-ru",
            "category": "test",
            "description": "",
            "source": "",
        })(),
        db_path=outside_db,
        bundled=False,
        removable=True,
    )
    config = AppConfig(runtime_dictionary_dir=tmp_path / "runtime")

    with pytest.raises(DictionaryManagerError):
        remove_installed_dictionary(record, config)
