from __future__ import annotations

import os
from pathlib import Path

import pytest

from pdf_word_translator.config import AppConfig
from pdf_word_translator.mobile_api import configure_dictionary_paths, reset_mobile_bridge
from pdf_word_translator.plugin_loader import PluginLoader
from pdf_word_translator.utils.dictionary_builder import (
    DictionaryBuildEntry,
    DictionaryMetadata,
    build_dictionary_from_entries,
)
from pdf_word_translator.utils.settings_store import SettingsStore, UiSettings


@pytest.fixture(autouse=True)
def _reset_mobile_bridge() -> None:
    reset_mobile_bridge()
    yield
    reset_mobile_bridge()


def _build_test_db(tmp_path: Path, filename: str = "test.sqlite") -> Path:
    db_path = tmp_path / filename
    build_dictionary_from_entries(
        [
            DictionaryBuildEntry(
                headword="driver",
                best_translation="драйвер",
                alternatives=["драйвер"],
                forms=["driver", "drivers"],
                examples=[("device driver", "драйвер устройства")],
            )
        ],
        db_path,
        metadata=DictionaryMetadata(
            pack_name="test pack",
            direction="en-ru",
            pack_kind="test",
            description="temporary test pack",
            source=str(db_path),
        ),
    )
    return db_path


def test_settings_store_writes_file_with_restricted_permissions(tmp_path: Path) -> None:
    settings_file = tmp_path / "settings.json"
    store = SettingsStore(settings_file)

    store.save(UiSettings(libretranslate_api_key="secret", yandex_api_key="secret2"))

    assert settings_file.exists()
    if os.name == "posix":
        assert settings_file.stat().st_mode & 0o777 == 0o600


def test_mobile_api_rejects_directory_paths(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="regular files"):
        configure_dictionary_paths([str(tmp_path)])


def test_external_plugins_are_disabled_by_default(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "demo_plugin.py"
    plugin_file.write_text(
        """
from pathlib import Path
from pdf_word_translator.plugin_api import DocumentPlugin, DocumentSession


class DemoPlugin(DocumentPlugin):
    def plugin_id(self) -> str:
        return "demo"

    def supported_extensions(self) -> tuple[str, ...]:
        return (".demo",)

    def can_open(self, path: Path) -> bool:
        return path.suffix == ".demo"

    def open(self, path: Path) -> DocumentSession:
        raise RuntimeError("not used in test")


def register_plugins():
    return [DemoPlugin()]
""",
        encoding="utf-8",
    )
    if os.name == "posix":
        plugin_dir.chmod(0o700)
        plugin_file.chmod(0o600)

    loader = PluginLoader(AppConfig(external_plugin_dir=plugin_dir, enable_external_plugins=False))
    registry = loader.load()

    assert len(registry.document_plugins) == 3


def test_external_plugins_can_be_enabled_explicitly(tmp_path: Path) -> None:
    plugin_dir = tmp_path / "plugins"
    plugin_dir.mkdir()
    plugin_file = plugin_dir / "demo_plugin.py"
    plugin_file.write_text(
        """
from pathlib import Path
from pdf_word_translator.plugin_api import DocumentPlugin, DocumentSession


class DemoPlugin(DocumentPlugin):
    def plugin_id(self) -> str:
        return "demo"

    def supported_extensions(self) -> tuple[str, ...]:
        return (".demo",)

    def can_open(self, path: Path) -> bool:
        return path.suffix == ".demo"

    def open(self, path: Path) -> DocumentSession:
        raise RuntimeError("not used in test")


def register_plugins():
    return [DemoPlugin()]
""",
        encoding="utf-8",
    )
    if os.name == "posix":
        plugin_dir.chmod(0o700)
        plugin_file.chmod(0o600)

    loader = PluginLoader(AppConfig(external_plugin_dir=plugin_dir, enable_external_plugins=True))
    registry = loader.load()

    assert len(registry.document_plugins) == 4
    assert registry.document_plugins[-1].plugin_id() == "demo"
