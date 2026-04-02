"""Desktop installation metadata and GUI update command helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys

from .. import __version__

APP_INSTALL_DIRNAME = "pdf_word_translator_mvp_install"
MANIFEST_FILENAME = "installation.json"


def _xdg_data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))).expanduser()


def default_install_home() -> Path:
    return _xdg_data_home() / APP_INSTALL_DIRNAME


def manifest_path(install_home: Path | None = None) -> Path:
    home = Path(install_home) if install_home is not None else default_install_home()
    return home.expanduser() / "metadata" / MANIFEST_FILENAME


@dataclass(frozen=True)
class DesktopMetadata:
    version: str
    commit: str = ""
    commit_short: str = ""
    branch: str = ""
    repo_url: str = ""
    last_updated: str = ""
    install_home: str = ""
    source_type: str = ""
    manifest_found: bool = False
    update_configured: bool = False


def _read_manifest(install_home: Path | None = None) -> dict[str, object]:
    path = manifest_path(install_home)
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _git_value(project_root: Path, *args: str) -> str:
    if shutil.which("git") is None or not (project_root / ".git").exists():
        return ""
    try:
        completed = subprocess.run(
            ["git", "-C", str(project_root), *args],
            check=True,
            capture_output=True,
            text=True,
        )
    except (subprocess.CalledProcessError, OSError):
        return ""
    return completed.stdout.strip()


def collect_desktop_metadata(project_root: Path, install_home: Path | None = None) -> DesktopMetadata:
    manifest = _read_manifest(install_home)
    git_commit = _git_value(project_root, "rev-parse", "HEAD")
    git_commit_short = _git_value(project_root, "rev-parse", "--short", "HEAD")
    git_branch = _git_value(project_root, "rev-parse", "--abbrev-ref", "HEAD")
    if git_branch == "HEAD":
        git_branch = ""

    commit = str(manifest.get("source_commit") or git_commit or "").strip()
    commit_short = str(manifest.get("source_commit_short") or git_commit_short or "").strip()
    branch = str(manifest.get("branch") or git_branch or "").strip()
    repo_url = str(manifest.get("repo_url") or "").strip()
    last_updated = str(manifest.get("installed_at") or "").strip()
    install_home_text = str(manifest.get("install_home") or (install_home or default_install_home()) or "").strip()
    source_type = str(manifest.get("source_type") or ("git" if git_commit else "archive") or "").strip()

    return DesktopMetadata(
        version=str(manifest.get("installed_version") or __version__),
        commit=commit,
        commit_short=commit_short,
        branch=branch,
        repo_url=repo_url,
        last_updated=last_updated,
        install_home=install_home_text,
        source_type=source_type,
        manifest_found=bool(manifest),
        update_configured=bool(repo_url),
    )


def desktop_manager_script(project_root: Path) -> Path:
    return Path(project_root) / "tools" / "desktop_manager.py"


def update_command(
    project_root: Path,
    *,
    check_only: bool,
    yes: bool = False,
    install_home: Path | None = None,
) -> list[str]:
    command = [
        sys.executable,
        str(desktop_manager_script(project_root)),
        "update",
        "--install-home",
        str((install_home or default_install_home()).expanduser()),
    ]
    if check_only:
        command.append("--check-only")
    if yes:
        command.append("--yes")
    return command
