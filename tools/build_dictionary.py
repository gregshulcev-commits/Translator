"""CLI wrapper to rebuild the starter SQLite dictionary."""
from __future__ import annotations

from pathlib import Path
import argparse

from pdf_word_translator.utils.dictionary_builder import build_dictionary_from_csv


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SQLite dictionary from a CSV source")
    parser.add_argument("csv", type=Path)
    parser.add_argument("sqlite", type=Path)
    args = parser.parse_args()
    build_dictionary_from_csv(args.csv, args.sqlite)
    print(f"Built dictionary: {args.sqlite}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
