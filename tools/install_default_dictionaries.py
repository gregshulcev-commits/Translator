#!/usr/bin/env python3
"""Install bundled starter packs and try to fetch larger default packs.

The script is safe to run repeatedly. It always prepares the small built-in
technical glossaries for both directions and then attempts to install bundled
technical/literary packs plus the larger FreeDict packs when internet access is
available.
"""
from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pdf_word_translator.config import AppConfig
from pdf_word_translator.models import EN_RU, RU_EN
from pdf_word_translator.utils.dictionary_builder import DictionaryMetadata, ensure_dictionary_database
from pdf_word_translator.utils.dictionary_installer import install_catalog_entry_by_id, install_default_pack


def main() -> int:
    config = AppConfig()
    config.ensure_runtime_directories()

    ensure_dictionary_database(
        config.starter_dictionary_csv,
        config.starter_dictionary_db,
        metadata=DictionaryMetadata(
            pack_name="Встроенный технический EN→RU",
            direction=EN_RU,
            pack_kind="technical",
            description="Компактный технический словарь, входящий в дистрибутив.",
            source=str(config.starter_dictionary_csv),
        ),
    )
    print(f"[OK] Starter EN→RU glossary ready: {config.starter_dictionary_db}")

    ensure_dictionary_database(
        config.starter_dictionary_ru_en_csv,
        config.starter_dictionary_ru_en_db,
        metadata=DictionaryMetadata(
            pack_name="Встроенный технический RU→EN",
            direction=RU_EN,
            pack_kind="technical",
            description="Компактный технический словарь, входящий в дистрибутив.",
            source=str(config.starter_dictionary_ru_en_csv),
        ),
    )
    print(f"[OK] Starter RU→EN glossary ready: {config.starter_dictionary_ru_en_db}")

    bundled_pack_ids = [
        "technical_en_ru",
        "technical_ru_en",
        "literary_en_ru",
        "literary_ru_en",
    ]
    for pack_id in bundled_pack_ids:
        try:
            db_path = install_catalog_entry_by_id(config, pack_id)
            print(f"[OK] Installed bundled pack {pack_id}: {db_path}")
        except Exception as exc:
            print(f"[WARN] Failed to install bundled pack {pack_id}: {exc}")

    for direction, label in ((EN_RU, "EN→RU"), (RU_EN, "RU→EN")):
        try:
            db_path = install_default_pack(config.runtime_dictionary_dir, config.runtime_download_dir, direction=direction)
            print(f"[OK] FreeDict {label} pack installed: {db_path}")
        except Exception as exc:
            print(f"[WARN] FreeDict {label} pack was not installed automatically: {exc}")
            print("[WARN] The application will still run with the bundled dictionaries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
