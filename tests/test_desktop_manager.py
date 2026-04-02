from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import tempfile


def _load_manager_module():
    project_root = Path(__file__).resolve().parents[1]
    module_path = project_root / "tools" / "desktop_manager.py"
    spec = spec_from_file_location("desktop_manager", module_path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_version_from_project() -> None:
    manager = _load_manager_module()
    project_root = Path(__file__).resolve().parents[1]
    assert manager.parse_version(project_root) == "10.0.1"


def test_read_v9_project_root_from_launcher() -> None:
    manager = _load_manager_module()
    with tempfile.TemporaryDirectory() as tmp_dir_raw:
        tmp_dir = Path(tmp_dir_raw)
        launcher = tmp_dir / "pdf-word-translator-mvp"
        launcher.write_text(
            '#!/usr/bin/env bash\nPROJECT_ROOT="/tmp/pdf_word_translator_mvp_v9"\n',
            encoding="utf-8",
        )
        detected = manager.read_v9_project_root_from_launcher(launcher)
        assert detected == Path("/tmp/pdf_word_translator_mvp_v9")
