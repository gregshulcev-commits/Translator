#!/usr/bin/env python3
"""Desktop install/update/uninstall manager for PDF Word Translator MVP.

The manager keeps the desktop installation self-contained under the user's
``~/.local/share`` tree, creates launchers in ``~/.local/bin`` and stores a
small JSON manifest so future updates know where the current payload lives.

The script intentionally uses only the Python standard library because it is
invoked before the application virtual environment exists.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any
import uuid

APP_COMMAND = "pdf-word-translator-mvp"
APP_NAME = "PDF Word Translator MVP"
APP_RUNTIME_DIRNAME = "pdf_word_translator_mvp"
APP_INSTALL_DIRNAME = "pdf_word_translator_mvp_install"
DESKTOP_FILENAME = f"{APP_COMMAND}.desktop"
ICON_FILENAME = f"{APP_COMMAND}.png"
MANIFEST_FILENAME = "installation.json"


def _xdg_data_home() -> Path:
    return Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))).expanduser()


def _xdg_cache_home() -> Path:
    return Path(os.environ.get("XDG_CACHE_HOME", str(Path.home() / ".cache"))).expanduser()


def default_install_home() -> Path:
    return _xdg_data_home() / APP_INSTALL_DIRNAME


def default_runtime_data_home() -> Path:
    return _xdg_data_home() / APP_RUNTIME_DIRNAME


def default_runtime_cache_home() -> Path:
    return _xdg_cache_home() / APP_RUNTIME_DIRNAME


def local_bin_dir() -> Path:
    return Path.home() / ".local" / "bin"


def desktop_dir() -> Path:
    return _xdg_data_home() / "applications"


def icon_dir() -> Path:
    return _xdg_data_home() / "icons" / "hicolor" / "256x256" / "apps"


def manifest_path(install_home: Path) -> Path:
    return install_home / "metadata" / MANIFEST_FILENAME


def current_payload_dir(install_home: Path) -> Path:
    return install_home / "app" / "current"


def previous_payload_dir(install_home: Path) -> Path:
    return install_home / "app" / "previous"


def launcher_path() -> Path:
    return local_bin_dir() / APP_COMMAND


def update_wrapper_path() -> Path:
    return local_bin_dir() / f"{APP_COMMAND}-update"


def uninstall_wrapper_path() -> Path:
    return local_bin_dir() / f"{APP_COMMAND}-uninstall"


def app_desktop_path() -> Path:
    return desktop_dir() / DESKTOP_FILENAME


def app_icon_path() -> Path:
    return icon_dir() / ICON_FILENAME


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def print_info(message: str) -> None:
    print(f"[INFO] {message}", flush=True)


def print_warn(message: str) -> None:
    print(f"[WARN] {message}", file=sys.stderr, flush=True)


def print_error(message: str) -> None:
    print(f"[ERROR] {message}", file=sys.stderr, flush=True)


def fail(message: str, code: int = 1) -> int:
    print_error(message)
    return code


def run_command(
    command: list[str],
    *,
    cwd: Path | None = None,
    env: dict[str, str] | None = None,
    capture_output: bool = False,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=str(cwd) if cwd else None,
        env=env,
        check=check,
        capture_output=capture_output,
        text=True,
    )


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def choose_python_binary() -> str:
    candidates = [sys.executable, "python3.13", "python3", "python"]
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        resolved = shutil.which(candidate) if os.sep not in candidate else candidate
        if resolved and Path(resolved).exists():
            return resolved
    raise RuntimeError("python3 not found")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, content: str, executable: bool = False) -> None:
    ensure_dir(path.parent)
    path.write_text(content, encoding="utf-8")
    mode = 0o755 if executable else 0o644
    path.chmod(mode)


def remove_path(path: Path) -> bool:
    if path.is_symlink() or path.is_file():
        path.unlink(missing_ok=True)
        return True
    if path.is_dir():
        shutil.rmtree(path)
        return True
    return False


def copy_source_tree(source_root: Path, destination: Path) -> None:
    ignore_names = {
        ".git",
        ".venv",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "build",
        "dist",
        ".DS_Store",
    }

    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored = {name for name in names if name in ignore_names}
        if Path(directory).resolve() == source_root.resolve():
            ignored.update({APP_INSTALL_DIRNAME, "coverage", "htmlcov"})
        return ignored

    shutil.copytree(source_root, destination, ignore=ignore)


def parse_version(source_root: Path) -> str:
    init_file = source_root / "src" / "pdf_word_translator" / "__init__.py"
    content = read_text(init_file)
    match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
    if not match:
        raise RuntimeError(f"Could not determine version from {init_file}")
    return match.group(1)


def load_manifest(install_home: Path) -> dict[str, Any]:
    path = manifest_path(install_home)
    if not path.exists():
        return {}
    try:
        return json.loads(read_text(path))
    except json.JSONDecodeError:
        print_warn(f"Manifest is corrupted and will be ignored: {path}")
        return {}


def save_manifest(install_home: Path, manifest: dict[str, Any]) -> None:
    path = manifest_path(install_home)
    ensure_dir(path.parent)
    payload = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True)
    tmp_path = path.with_suffix(".tmp")
    tmp_path.write_text(payload + "\n", encoding="utf-8")
    tmp_path.replace(path)
    path.chmod(0o600)


def detect_git_source(source_root: Path) -> dict[str, Any]:
    git_dir = source_root / ".git"
    if not git_dir.exists() or shutil.which("git") is None:
        return {}
    result: dict[str, Any] = {}
    try:
        run_command(["git", "-C", str(source_root), "rev-parse", "--is-inside-work-tree"], capture_output=True)
    except subprocess.CalledProcessError:
        return {}

    def read_git(args: list[str]) -> str | None:
        try:
            completed = run_command(["git", "-C", str(source_root), *args], capture_output=True)
        except subprocess.CalledProcessError:
            return None
        value = completed.stdout.strip()
        return value or None

    result["source_type"] = "git"
    result["repo_url"] = read_git(["config", "--get", "remote.origin.url"])
    branch = read_git(["rev-parse", "--abbrev-ref", "HEAD"])
    if branch == "HEAD":
        branch = None
    result["branch"] = branch
    result["source_commit"] = read_git(["rev-parse", "HEAD"])
    result["source_commit_short"] = read_git(["rev-parse", "--short", "HEAD"])
    return {key: value for key, value in result.items() if value}


def detect_remote_default_branch(repo_url: str) -> str | None:
    if shutil.which("git") is None:
        return None
    try:
        completed = run_command(["git", "ls-remote", "--symref", repo_url, "HEAD"], capture_output=True)
    except subprocess.CalledProcessError:
        return None
    for line in completed.stdout.splitlines():
        if line.startswith("ref:") and "HEAD" in line:
            match = re.search(r"refs/heads/(\S+)\s+HEAD", line)
            if match:
                return match.group(1)
    return None


def remote_branch_hash(repo_url: str, branch: str) -> str:
    if shutil.which("git") is None:
        raise RuntimeError("git is required for update checks")
    try:
        completed = run_command(["git", "ls-remote", repo_url, f"refs/heads/{branch}"], capture_output=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(f"Could not query remote branch {branch!r} for {repo_url!r}") from exc
    for line in completed.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[1] == f"refs/heads/{branch}":
            return parts[0]
    raise RuntimeError(f"Remote branch {branch!r} not found in {repo_url!r}")


def read_v9_project_root_from_launcher(path: Path) -> Path | None:
    if not path.exists():
        return None
    content = read_text(path)
    match = re.search(r'^PROJECT_ROOT="([^"]+)"$', content, flags=re.MULTILINE)
    if not match:
        return None
    return Path(match.group(1)).expanduser()


def maybe_update_desktop_cache() -> None:
    binary = shutil.which("update-desktop-database")
    if binary:
        try:
            run_command([binary, str(desktop_dir())], check=False)
        except OSError:
            pass


def maybe_update_icon_cache() -> None:
    binary = shutil.which("gtk-update-icon-cache")
    if binary:
        try:
            run_command([binary, "-q", str(_xdg_data_home() / "icons" / "hicolor")], check=False)
        except OSError:
            pass


def create_runtime_wrappers(payload_dir: Path) -> None:
    ensure_dir(local_bin_dir())
    launcher = f'''#!/usr/bin/env bash
set -euo pipefail
PROJECT_ROOT="{payload_dir}"
export PYTHONPATH="$PROJECT_ROOT/src"
exec "$PROJECT_ROOT/.venv/bin/python" -m pdf_word_translator.app "$@"
'''
    updater = f'''#!/usr/bin/env bash
set -euo pipefail
exec "{payload_dir / 'update_app.sh'}" "$@"
'''
    uninstaller = f'''#!/usr/bin/env bash
set -euo pipefail
exec "{payload_dir / 'uninstall_app.sh'}" "$@"
'''
    write_text(launcher_path(), launcher, executable=True)
    write_text(update_wrapper_path(), updater, executable=True)
    write_text(uninstall_wrapper_path(), uninstaller, executable=True)


def create_desktop_entry(payload_dir: Path) -> None:
    ensure_dir(desktop_dir())
    ensure_dir(icon_dir())
    icon_source = payload_dir / "resources" / "pdf_word_translator_icon.png"
    if icon_source.exists():
        shutil.copy2(icon_source, app_icon_path())
    entry = f'''[Desktop Entry]
Version=1.0
Type=Application
Name={APP_NAME}
Comment=Офлайн переводчик PDF, TXT и FB2 по клику на слово
Exec={launcher_path()} %f
Icon={app_icon_path()}
Terminal=false
Categories=Office;Education;Utility;
MimeType=application/pdf;text/plain;application/x-fictionbook+xml;
StartupNotify=true
'''
    write_text(app_desktop_path(), entry, executable=False)
    maybe_update_desktop_cache()
    maybe_update_icon_cache()




def publish_runtime_artifacts(payload_dir: Path) -> None:
    create_runtime_wrappers(payload_dir)
    create_desktop_entry(payload_dir)


def install_into_stage(
    source_root: Path,
    stage_dir: Path,
    *,
    python_bin: str,
    install_optional: bool,
) -> dict[str, Any]:
    print_info(f"Copying project into staging directory: {stage_dir}")
    copy_source_tree(source_root, stage_dir)

    print_info("Creating virtual environment with access to system site-packages")
    run_command([python_bin, "-m", "venv", "--system-site-packages", str(stage_dir / ".venv")])
    venv_python = stage_dir / ".venv" / "bin" / "python"
    venv_pip = stage_dir / ".venv" / "bin" / "pip"

    print_info("Installing Python dependencies")
    run_command([str(venv_python), "-m", "pip", "install", "--upgrade", "pip", "setuptools", "wheel"], cwd=stage_dir)
    run_command([str(venv_pip), "install", "-r", "requirements.txt"], cwd=stage_dir)

    optional_installed = False
    if install_optional and (stage_dir / "requirements-optional.txt").exists():
        try:
            run_command([str(venv_pip), "install", "-r", "requirements-optional.txt"], cwd=stage_dir)
            optional_installed = True
            print_info("Optional dependencies installed successfully")
        except subprocess.CalledProcessError:
            print_warn("Optional dependencies could not be installed. They can be installed later from GUI.")

    try:
        run_command([str(venv_python), "-c", "import tkinter"], cwd=stage_dir)
    except subprocess.CalledProcessError:
        print_warn("tkinter is not available in the selected Python environment.")
        print_warn("On Fedora use: sudo dnf install python3-tkinter")
        print_warn("On Debian/Ubuntu use: sudo apt install python3-tk")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(stage_dir / "src")
    print_info("Installing default dictionaries")
    run_command([str(venv_python), "tools/install_default_dictionaries.py"], cwd=stage_dir, env=env)

    return {
        "venv_python": str(venv_python),
        "venv_pip": str(venv_pip),
        "optional_installed": optional_installed,
    }


def perform_install(args: argparse.Namespace) -> int:
    source_root = Path(args.source_root).resolve()
    if not source_root.exists():
        return fail(f"Source root does not exist: {source_root}")

    install_home = Path(args.install_home).expanduser().resolve()
    app_dir = install_home / "app"
    ensure_dir(app_dir)

    version = parse_version(source_root)
    git_info = detect_git_source(source_root)
    repo_url = args.repo_url or git_info.get("repo_url")
    branch = args.branch or git_info.get("branch")
    if repo_url and not branch:
        branch = detect_remote_default_branch(repo_url) or "main"

    python_bin = args.python_bin or choose_python_binary()
    stage_dir = app_dir / f"_staging_{uuid.uuid4().hex}"
    current_dir = current_payload_dir(install_home)
    previous_dir = previous_payload_dir(install_home)

    try:
        stage_result = install_into_stage(
            source_root,
            stage_dir,
            python_bin=python_bin,
            install_optional=not args.skip_optional,
        )

        previous_backup_available = False
        promoted_stage = False
        try:
            if previous_dir.exists():
                shutil.rmtree(previous_dir)
            if current_dir.exists():
                current_dir.rename(previous_dir)
                previous_backup_available = True
            stage_dir.rename(current_dir)
            promoted_stage = True

            publish_runtime_artifacts(current_dir)

            manifest = {
                "app_command": APP_COMMAND,
                "app_name": APP_NAME,
                "branch": branch,
                "current_payload_dir": str(current_dir),
                "install_home": str(install_home),
                "installed_at": now_iso(),
                "installed_version": version,
                "launcher_path": str(launcher_path()),
                "optional_installed": stage_result["optional_installed"],
                "optional_requested": not args.skip_optional,
                "previous_payload_dir": str(previous_dir) if previous_dir.exists() else "",
                "python_bin": python_bin,
                "repo_url": repo_url or "",
                "source_commit": args.source_commit or git_info.get("source_commit", ""),
                "source_commit_short": git_info.get("source_commit_short", ""),
                "source_project_root": str(source_root),
                "source_type": args.source_type or git_info.get("source_type", "archive"),
                "update_strategy": "git" if repo_url else "manual",
                "venv_python": str(current_dir / ".venv" / "bin" / "python"),
            }
            save_manifest(install_home, manifest)
        except Exception:
            if promoted_stage and current_dir.exists():
                shutil.rmtree(current_dir, ignore_errors=True)
            if previous_backup_available and previous_dir.exists() and not current_dir.exists():
                previous_dir.rename(current_dir)
                try:
                    publish_runtime_artifacts(current_dir)
                except Exception as restore_exc:
                    print_warn(
                        f"Rollback restored the previous payload, but desktop integration refresh failed: {restore_exc}"
                    )
            raise

        print()
        print_info("Installation complete")
        print(f"Version:         {version}")
        print(f"Payload:         {current_dir}")
        print(f"Launcher:        {launcher_path()}")
        print(f"Desktop entry:   {app_desktop_path()}")
        if repo_url:
            print(f"Update source:   {repo_url} [{branch}]")
        else:
            print("Update source:   not configured yet")
        return 0
    finally:
        if stage_dir.exists():
            shutil.rmtree(stage_dir, ignore_errors=True)


def perform_uninstall(args: argparse.Namespace) -> int:
    install_home = Path(args.install_home).expanduser().resolve()
    manifest = load_manifest(install_home)

    removed: list[str] = []
    for path in (launcher_path(), update_wrapper_path(), uninstall_wrapper_path(), app_desktop_path(), app_icon_path()):
        if remove_path(path):
            removed.append(str(path))

    current_dir = current_payload_dir(install_home)
    previous_dir = previous_payload_dir(install_home)
    metadata_dir = install_home / "metadata"
    app_dir = install_home / "app"
    for path in (current_dir, previous_dir, metadata_dir, app_dir):
        if remove_path(path):
            removed.append(str(path))

    try:
        if install_home.exists() and not any(install_home.iterdir()):
            install_home.rmdir()
            removed.append(str(install_home))
    except OSError:
        pass

    if args.purge_data:
        for path in (default_runtime_data_home(), default_runtime_cache_home()):
            if remove_path(path):
                removed.append(str(path))

    maybe_update_desktop_cache()
    maybe_update_icon_cache()

    print()
    if removed:
        print_info("Removed the following paths:")
        for item in removed:
            print(f"  - {item}")
    else:
        print_info("Nothing to remove. No desktop installation was found.")

    if manifest and not args.purge_data:
        print_info("User dictionaries, settings and caches were preserved.")
        print_info(f"Use --purge-data if you want to remove {default_runtime_data_home()} and {default_runtime_cache_home()} too.")
    return 0


def _looks_like_v9_install(project_root: Path | None) -> bool:
    if project_root is None:
        return False
    try:
        version = parse_version(project_root)
    except Exception:
        version = ""
    if version.startswith("9."):
        return True
    if "pdf_word_translator_mvp_v9" in str(project_root):
        return True
    readme_path = project_root / "README.md"
    if readme_path.exists():
        readme_text = read_text(readme_path)
        if "MVP v9" in readme_text:
            return True
    return False


def perform_uninstall_previous_v9(args: argparse.Namespace) -> int:
    v9_launcher = launcher_path()
    project_root = read_v9_project_root_from_launcher(v9_launcher)
    if not _looks_like_v9_install(project_root):
        print()
        print_info("No confirmed v9 launcher-based installation was detected.")
        print_info("Safety check prevented removal of a newer installation.")
        return 0

    removed: list[str] = []
    for path in (v9_launcher, app_desktop_path(), app_icon_path()):
        if remove_path(path):
            removed.append(str(path))

    old_venv = project_root / ".venv" if project_root else None
    if old_venv and old_venv.exists():
        shutil.rmtree(old_venv)
        removed.append(str(old_venv))

    maybe_update_desktop_cache()
    maybe_update_icon_cache()

    print()
    if project_root:
        print_info(f"Detected previous v9 project root: {project_root}")
    if removed:
        print_info("Removed previous v9 installation artifacts:")
        for item in removed:
            print(f"  - {item}")
    else:
        print_info("No previous v9 launcher-based installation was detected.")
    print_info("Project sources were left untouched. Only launcher integration and old .venv were removed.")
    return 0


def prompt_yes_no(message: str) -> bool:
    reply = input(f"{message} [y/N]: ").strip().lower()
    return reply in {"y", "yes", "д", "да"}


def clone_repo(repo_url: str, branch: str, destination: Path) -> None:
    if shutil.which("git") is None:
        raise RuntimeError("git is required to clone updates")
    run_command(["git", "clone", "--depth", "1", "--branch", branch, repo_url, str(destination)])


def perform_update(args: argparse.Namespace) -> int:
    install_home = Path(args.install_home).expanduser().resolve()
    manifest = load_manifest(install_home)
    if not manifest:
        return fail("The application is not installed yet. Run ./install_app.sh first.")

    changed = False
    repo_url = args.repo_url or manifest.get("repo_url") or ""
    branch = args.branch or manifest.get("branch") or ""

    if args.set_repo:
        repo_url = args.set_repo
        changed = True
    if repo_url and not branch:
        branch = detect_remote_default_branch(repo_url) or "main"
        changed = True
    if args.branch:
        changed = True

    if changed:
        manifest["repo_url"] = repo_url
        manifest["branch"] = branch
        manifest["update_strategy"] = "git" if repo_url else "manual"
        save_manifest(install_home, manifest)
        print_info(f"Saved update source: {repo_url or 'not configured'} [{branch or 'default'}]")

    if not repo_url:
        return fail(
            "Update source is not configured. Use ./update_app.sh --set-repo https://github.com/USER/REPO.git --branch main"
        )
    if not branch:
        branch = detect_remote_default_branch(repo_url) or "main"
        manifest["branch"] = branch
        save_manifest(install_home, manifest)

    try:
        remote_hash = remote_branch_hash(repo_url, branch)
    except RuntimeError as exc:
        return fail(str(exc))

    installed_hash = str(manifest.get("source_commit") or "").strip()
    installed_version = str(manifest.get("installed_version") or "unknown").strip()
    remote_short = remote_hash[:12]

    print_info(f"Installed version: {installed_version}")
    if installed_hash:
        print_info(f"Installed commit:  {installed_hash[:12]}")
    else:
        print_info("Installed commit:  unknown (initial install was not bound to a git commit)")
    print_info(f"Remote branch:     {branch}")
    print_info(f"Remote commit:     {remote_short}")

    if installed_hash == remote_hash:
        print_info("The installed version is already up to date.")
        return 0

    if args.check_only:
        print_info("Update is available.")
        return 0

    if not args.yes and not prompt_yes_no("A newer revision is available. Install the update now?"):
        print_info("Update cancelled by user.")
        return 0

    with tempfile.TemporaryDirectory(prefix="pdf_word_translator_update_") as temp_dir_raw:
        temp_dir = Path(temp_dir_raw)
        repo_dir = temp_dir / "repo"
        print_info(f"Cloning update source from {repo_url}")
        clone_repo(repo_url, branch, repo_dir)

        python_bin = args.python_bin or choose_python_binary()
        command = [
            python_bin,
            str(repo_dir / "tools" / "desktop_manager.py"),
            "install",
            "--source-root",
            str(repo_dir),
            "--install-home",
            str(install_home),
            "--repo-url",
            repo_url,
            "--branch",
            branch,
            "--source-type",
            "git",
            "--source-commit",
            remote_hash,
        ]
        if not manifest.get("optional_requested", True):
            command.append("--skip-optional")

        print_info("Applying update")
        run_command(command)

    print_info("Update completed successfully.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage the desktop installation of PDF Word Translator MVP")
    subparsers = parser.add_subparsers(dest="command", required=True)

    install_parser = subparsers.add_parser("install", help="Install the application into the user profile")
    install_parser.add_argument("--source-root", required=True, help="Source project directory to install from")
    install_parser.add_argument("--install-home", default=str(default_install_home()), help="Installation home directory")
    install_parser.add_argument("--skip-optional", action="store_true", help="Skip optional dependencies such as Argos runtime")
    install_parser.add_argument("--repo-url", help="Git repository URL to store for future updates")
    install_parser.add_argument("--branch", help="Git branch to track for updates")
    install_parser.add_argument("--python-bin", help="Python interpreter to use for creating the virtual environment")
    install_parser.add_argument("--source-type", help="Override detected source type (git/archive)")
    install_parser.add_argument("--source-commit", help="Override detected git commit hash")
    install_parser.set_defaults(func=perform_install)

    uninstall_parser = subparsers.add_parser("uninstall", help="Remove the installed application")
    uninstall_parser.add_argument("--install-home", default=str(default_install_home()), help="Installation home directory")
    uninstall_parser.add_argument("--purge-data", action="store_true", help="Also remove runtime settings, dictionaries and caches")
    uninstall_parser.set_defaults(func=perform_uninstall)

    update_parser = subparsers.add_parser("update", help="Check GitHub and install a newer revision if available")
    update_parser.add_argument("--install-home", default=str(default_install_home()), help="Installation home directory")
    update_parser.add_argument("--set-repo", help="Save the Git repository URL for future updates")
    update_parser.add_argument("--repo-url", help="Temporarily use a specific Git repository URL")
    update_parser.add_argument("--branch", help="Branch to track, defaults to remote HEAD/main")
    update_parser.add_argument("--check-only", action="store_true", help="Only check whether an update exists")
    update_parser.add_argument("--yes", action="store_true", help="Install the update without confirmation prompt")
    update_parser.add_argument("--python-bin", help="Python interpreter to use for the update installer")
    update_parser.set_defaults(func=perform_update)

    uninstall_v9_parser = subparsers.add_parser(
        "uninstall-v9",
        help="Remove the previous v9 launcher-based installation created by the old installer",
    )
    uninstall_v9_parser.set_defaults(func=perform_uninstall_previous_v9)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except RuntimeError as exc:
        return fail(str(exc))
    except KeyboardInterrupt:
        return fail("Operation cancelled", code=130)


if __name__ == "__main__":
    raise SystemExit(main())
