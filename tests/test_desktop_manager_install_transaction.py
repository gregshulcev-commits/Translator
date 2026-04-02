from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from types import SimpleNamespace

import pytest


def _load_manager_module():
    project_root = Path(__file__).resolve().parents[1]
    module_path = project_root / "tools" / "desktop_manager.py"
    spec = spec_from_file_location("desktop_manager", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prepare_source_tree(root: Path) -> None:
    package_dir = root / "src" / "pdf_word_translator"
    package_dir.mkdir(parents=True, exist_ok=True)
    (package_dir / "__init__.py").write_text('__version__ = "10.0.0"\n', encoding="utf-8")


def test_install_rolls_back_to_previous_payload_when_publish_fails(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    manager = _load_manager_module()
    source_root = tmp_path / "source"
    _prepare_source_tree(source_root)

    install_home = tmp_path / "install-home"
    current_dir = install_home / "app" / "current"
    current_dir.mkdir(parents=True)
    (current_dir / "marker.txt").write_text("old", encoding="utf-8")

    def fake_install_into_stage(source_root: Path, stage_dir: Path, *, python_bin: str, install_optional: bool):
        stage_dir.mkdir(parents=True, exist_ok=True)
        (stage_dir / "marker.txt").write_text("new", encoding="utf-8")
        return {"optional_installed": False}

    publish_calls: list[str] = []

    def fake_publish_runtime_artifacts(payload_dir: Path) -> None:
        marker = (payload_dir / "marker.txt").read_text(encoding="utf-8")
        publish_calls.append(marker)
        if marker == "new":
            raise RuntimeError("publish failed")

    monkeypatch.setattr(manager, "install_into_stage", fake_install_into_stage)
    monkeypatch.setattr(manager, "publish_runtime_artifacts", fake_publish_runtime_artifacts)
    monkeypatch.setattr(manager, "save_manifest", lambda install_home, manifest: None)
    monkeypatch.setattr(manager, "choose_python_binary", lambda: "python3")

    args = SimpleNamespace(
        source_root=str(source_root),
        install_home=str(install_home),
        repo_url=None,
        branch=None,
        python_bin=None,
        skip_optional=True,
        source_commit=None,
        source_type=None,
    )

    with pytest.raises(RuntimeError, match="publish failed"):
        manager.perform_install(args)

    assert publish_calls == ["new", "old"]
    assert (install_home / "app" / "current" / "marker.txt").read_text(encoding="utf-8") == "old"
    assert not (install_home / "app" / "previous").exists()
