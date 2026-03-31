#!/usr/bin/env bash
set -euo pipefail
export PYTHONPATH="$(cd "$(dirname "$0")/.." && pwd)/src"
exec python3 -m pdf_word_translator.app "$@"
