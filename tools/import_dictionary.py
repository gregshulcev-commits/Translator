#!/usr/bin/env python3
"""Import dictionary sources into the SQLite runtime schema."""
from __future__ import annotations

import argparse
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pdf_word_translator.utils.dictionary_builder import build_dictionary_from_csv
from pdf_word_translator.utils.freedict_importer import build_dictionary_from_freedict_tei


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Convert dictionary sources into the MVP SQLite format")
    parser.add_argument("source", help="Path to a CSV glossary or FreeDict TEI file")
    parser.add_argument("output", help="Destination SQLite file")
    parser.add_argument(
        "--format",
        dest="source_format",
        choices=["csv", "freedict-tei"],
        required=True,
        help="Source dictionary format",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    source = Path(args.source).expanduser().resolve()
    output = Path(args.output).expanduser().resolve()

    if args.source_format == "csv":
        build_dictionary_from_csv(source, output)
    else:
        build_dictionary_from_freedict_tei(source, output)

    print(f"[OK] Built dictionary pack: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
