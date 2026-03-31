#!/usr/bin/env python3
"""Inspect and install Argos Translate language model packages."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from pdf_word_translator.models import EN_RU, RU_EN
from pdf_word_translator.utils.argos_manager import (  # noqa: E402
    ArgosManagerError,
    direction_display,
    import_argos_model_from_path,
    install_argos_model_for_direction,
    list_argos_models,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Inspect and install Argos Translate language packages")
    parser.add_argument("--from-lang", help="Source language code, e.g. en")
    parser.add_argument("--to-lang", help="Target language code, e.g. ru")
    parser.add_argument("--file", help="Install a local .argosmodel archive")
    parser.add_argument("--list", action="store_true", help="Show EN↔RU status and available package versions")
    return parser


def _direction_from_codes(from_lang: str, to_lang: str) -> str:
    pair = (from_lang.strip().lower(), to_lang.strip().lower())
    if pair == ("en", "ru"):
        return EN_RU
    if pair == ("ru", "en"):
        return RU_EN
    raise ArgosManagerError("Поддерживаются только направления en->ru и ru->en.")


def main() -> int:
    args = build_parser().parse_args()

    if args.list:
        state = list_argos_models(update_index=True)
        if not state.dependency_ready:
            print(f"[ERROR] {state.dependency_error}")
            return 1
        for model in state.models:
            status = "installed" if model.installed else "not installed"
            available = "yes" if model.available_for_download else "no"
            version = model.package_version or "—"
            print(
                f"[MODEL] {model.display_name}: installed={status}; available={available}; "
                f"version={version}; notes={model.notes}"
            )
        return 0

    if args.file:
        try:
            result = import_argos_model_from_path(Path(args.file))
        except ArgosManagerError as exc:
            print(f"[ERROR] {exc}")
            return 2
        print(f"[OK] {result.message}")
        return 0

    if not args.from_lang or not args.to_lang:
        print("[ERROR] Укажите --from-lang/--to-lang или используйте --file / --list.")
        return 2

    try:
        direction = _direction_from_codes(args.from_lang, args.to_lang)
        result = install_argos_model_for_direction(direction)
    except ArgosManagerError as exc:
        print(f"[ERROR] {exc}")
        return 3

    print(f"[OK] {result.message}")
    if result.package_name or result.package_version:
        print(f"[INFO] Package: {result.package_name or direction_display(direction)} {result.package_version}".rstrip())
    if result.archive_path:
        print(f"[INFO] Archive: {result.archive_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
