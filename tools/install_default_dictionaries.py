#!/usr/bin/env python3
"""Install the default bundled and downloadable dictionary packs."""
from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pdf_word_translator.config import AppConfig
from pdf_word_translator.utils.dictionary_builder import ensure_dictionary_database
from pdf_word_translator.utils.freedict_importer import install_default_freedict_dictionary


def main() -> int:
    config = AppConfig()
    config.ensure_runtime_directories()
    ensure_dictionary_database(config.starter_dictionary_csv, config.starter_dictionary_db)
    print(f"[OK] Bundled technical glossary ready: {config.starter_dictionary_db}")

    try:
        db_path = install_default_freedict_dictionary(config.runtime_dictionary_dir, config.runtime_download_dir)
        print(f"[OK] FreeDict EN-RU pack installed: {db_path}")
    except Exception as exc:
        print(f"[WARN] FreeDict EN-RU pack was not installed automatically: {exc}")
        print("[WARN] The application will still run with the bundled technical glossary.")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
