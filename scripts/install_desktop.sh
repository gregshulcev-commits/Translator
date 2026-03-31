#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

if command -v python3.13 >/dev/null 2>&1; then
    PYTHON_BIN="python3.13"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "[ERROR] python3 not found"
    exit 1
fi

if [ ! -d .venv ]; then
    "$PYTHON_BIN" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

if ! python - <<'PY' >/dev/null 2>&1
import tkinter
PY
then
    echo "[WARN] tkinter is not available in the current Python environment."
    echo "[WARN] On Fedora install it with: sudo dnf install python3-tkinter"
fi

export PYTHONPATH="$PROJECT_ROOT/src"
python tools/install_default_dictionaries.py

echo
echo "[OK] Installation complete."
echo "Run the application with:"
echo "  source .venv/bin/activate && PYTHONPATH=src python -m pdf_word_translator.app"
