#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

choose_python() {
    local candidate
    for candidate in python3.13 python3 python; do
        if command -v "$candidate" >/dev/null 2>&1; then
            printf '%s\n' "$candidate"
            return 0
        fi
    done
    return 1
}

PYTHON_BIN="$(choose_python || true)"
if [[ -z "$PYTHON_BIN" ]]; then
    echo "[ERROR] python3 not found" >&2
    exit 1
fi

exec "$PYTHON_BIN" "$PROJECT_ROOT/tools/desktop_manager.py" uninstall "$@"
