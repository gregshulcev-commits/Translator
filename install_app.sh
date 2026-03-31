#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

INSTALL_OPTIONAL=1
for arg in "$@"; do
    case "$arg" in
        --skip-optional|--base-only)
            INSTALL_OPTIONAL=0
            ;;
        --help|-h)
            cat <<'EOF'
Usage: ./install_app.sh [--skip-optional]

Installs the desktop application for the current user, creates a launcher in
~/.local/bin and a desktop entry with an icon in ~/.local/share/applications.

  --skip-optional   install only base dependencies and skip Argos runtime
EOF
            exit 0
            ;;
        *)
            echo "[ERROR] Unknown argument: $arg" >&2
            exit 2
            ;;
    esac
done

if command -v python3.13 >/dev/null 2>&1; then
    PYTHON_BIN="python3.13"
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
else
    echo "[ERROR] python3 not found" >&2
    exit 1
fi

if [ ! -d .venv ]; then
    "$PYTHON_BIN" -m venv .venv
fi

VENV_PYTHON="$PROJECT_ROOT/.venv/bin/python"
VENV_PIP="$PROJECT_ROOT/.venv/bin/pip"

"$VENV_PYTHON" -m pip install --upgrade pip setuptools wheel
"$VENV_PIP" install -r requirements.txt

if [ "$INSTALL_OPTIONAL" -eq 1 ] && [ -f requirements-optional.txt ]; then
    if "$VENV_PIP" install -r requirements-optional.txt; then
        echo "[OK] Optional Argos runtime installed."
    else
        echo "[WARN] Failed to install optional Argos runtime. You can install it later from the GUI." >&2
    fi
fi

if ! "$VENV_PYTHON" - <<'PY' >/dev/null 2>&1
import tkinter
PY
then
    echo "[WARN] tkinter is not available in the selected Python environment." >&2
    echo "[WARN] On Fedora use: sudo dnf install python3-tkinter" >&2
fi

PYTHONPATH="$PROJECT_ROOT/src" "$VENV_PYTHON" tools/install_default_dictionaries.py

mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/.local/share/applications"
mkdir -p "$HOME/.local/share/icons/hicolor/256x256/apps"

LAUNCHER_PATH="$HOME/.local/bin/pdf-word-translator-mvp"
cat > "$LAUNCHER_PATH" <<EOF
#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="$PROJECT_ROOT"
export PYTHONPATH="\$PROJECT_ROOT/src"
exec "$VENV_PYTHON" -m pdf_word_translator.app "\$@"
EOF
chmod +x "$LAUNCHER_PATH"

ICON_SOURCE="$PROJECT_ROOT/resources/pdf_word_translator_icon.png"
ICON_TARGET="$HOME/.local/share/icons/hicolor/256x256/apps/pdf-word-translator-mvp.png"
if [ -f "$ICON_SOURCE" ]; then
    cp "$ICON_SOURCE" "$ICON_TARGET"
fi

DESKTOP_PATH="$HOME/.local/share/applications/pdf-word-translator-mvp.desktop"
cat > "$DESKTOP_PATH" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=PDF Word Translator MVP
Comment=Офлайн переводчик PDF, TXT и FB2 по клику на слово
Exec=$LAUNCHER_PATH %f
Icon=$ICON_TARGET
Terminal=false
Categories=Office;Education;Utility;
MimeType=application/pdf;text/plain;application/x-fictionbook+xml;
StartupNotify=true
EOF
chmod 644 "$DESKTOP_PATH"

if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$HOME/.local/share/applications" >/dev/null 2>&1 || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -q "$HOME/.local/share/icons/hicolor" >/dev/null 2>&1 || true
fi

echo
echo "[OK] Installation complete."
echo "Launcher script: $LAUNCHER_PATH"
echo "Desktop entry:   $DESKTOP_PATH"
echo "You can now start the app from the applications menu or by running:"
echo "  $LAUNCHER_PATH"
