#!/usr/bin/env python3
"""Install an Argos Translate language model package for one direction."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Install Argos Translate language packages")
    parser.add_argument("--from-lang", required=True, help="Source language code, e.g. en")
    parser.add_argument("--to-lang", required=True, help="Target language code, e.g. ru")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        import argostranslate.package  # type: ignore
    except Exception as exc:
        print("[ERROR] Optional dependency 'argos-translate' is not installed.")
        print("[ERROR] Install it first, for example:")
        print("        python -m pip install argostranslate")
        print(f"[DETAILS] {exc}")
        return 1

    print("[INFO] Updating Argos package index...")
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    package = next(
        (item for item in available_packages if item.from_code == args.from_lang and item.to_code == args.to_lang),
        None,
    )
    if package is None:
        print(f"[ERROR] Package {args.from_lang}->{args.to_lang} was not found in the Argos index.")
        return 2

    print(f"[INFO] Downloading {package.from_code}->{package.to_code} package...")
    archive_path = package.download()
    print(f"[INFO] Installing from {archive_path}...")
    argostranslate.package.install_from_path(archive_path)
    print(f"[OK] Argos package installed: {args.from_lang}->{args.to_lang}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
