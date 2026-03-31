#!/usr/bin/env python3
"""Backward-compatible helper for building the bundled glossary SQLite file."""
from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pdf_word_translator.utils.dictionary_builder import build_dictionary_from_csv


def main() -> int:
    data_dir = PROJECT_ROOT / "data"
    build_dictionary_from_csv(data_dir / "starter_dictionary.csv", data_dir / "starter_dictionary.sqlite")
    print("[OK] Rebuilt bundled glossary SQLite file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
