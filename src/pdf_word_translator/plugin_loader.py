"""Builtin and optional external plugin loading.

Builtin plugins are always available. External Python plugins remain supported,
but are now opt-in and loaded only when
``PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS=1`` (or the matching
``AppConfig.enable_external_plugins`` flag) is enabled. This reduces accidental
execution of arbitrary ``*.py`` files dropped into the runtime plugin directory.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from importlib import util as importlib_util
from pathlib import Path
from types import ModuleType
from typing import List
import hashlib
import logging
import os
import stat

from .config import AppConfig
from .plugin_api import DictionaryPlugin, DocumentPlugin
from .plugins.dictionary_composite import CompositeDictionaryPlugin
from .plugins.dictionary_sqlite import SQLiteDictionaryPlugin
from .plugins.document_fb2 import Fb2DocumentPlugin
from .plugins.document_pdf_pymupdf import PyMuPdfDocumentPlugin
from .plugins.document_txt import PlainTextDocumentPlugin


LOGGER = logging.getLogger(__name__)


@dataclass
class PluginRegistry:
    document_plugins: List[DocumentPlugin] = field(default_factory=list)
    dictionary_plugins: List[DictionaryPlugin] = field(default_factory=list)

    def document_plugin_for(self, path: Path) -> DocumentPlugin | None:
        for plugin in self.document_plugins:
            if plugin.can_open(path):
                return plugin
        return None

    def default_dictionary_plugin(self) -> DictionaryPlugin | None:
        return self.dictionary_plugins[0] if self.dictionary_plugins else None


def _module_name_for_path(path: Path) -> str:
    digest = hashlib.sha1(str(path.resolve()).encode("utf-8")).hexdigest()[:12]
    safe_stem = "".join(ch if ch.isalnum() else "_" for ch in path.stem) or "plugin"
    return f"pdf_word_translator_external_{safe_stem}_{digest}"


def _load_external_module(path: Path) -> ModuleType | None:
    spec = importlib_util.spec_from_file_location(_module_name_for_path(path), path)
    if spec is None or spec.loader is None:
        return None
    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _has_insecure_permissions(path: Path) -> bool:
    if os.name != "posix":
        return False
    try:
        mode = path.stat().st_mode
    except OSError:
        return True
    return bool(mode & (stat.S_IWGRP | stat.S_IWOTH))


class PluginLoader:
    """Loads builtin plugins and optional external plugins."""

    def __init__(self, config: AppConfig):
        self._config = config
        self._external_document_plugins: list[DocumentPlugin] = []
        self._external_dictionary_plugins: list[DictionaryPlugin] = []
        self._external_plugins_loaded = False

    def load(self) -> PluginRegistry:
        self._ensure_external_plugins_loaded()
        registry = PluginRegistry(
            document_plugins=[
                PyMuPdfDocumentPlugin(),
                PlainTextDocumentPlugin(),
                Fb2DocumentPlugin(),
                *self._external_document_plugins,
            ],
            dictionary_plugins=[self.create_dictionary_plugin()],
        )
        LOGGER.info(
            "Loaded %s document plugin(s) and %s dictionary plugin(s)",
            len(registry.document_plugins),
            len(registry.dictionary_plugins),
        )
        return registry

    def create_dictionary_plugin(self) -> DictionaryPlugin:
        """Rebuild the active composite dictionary from all installed packs."""
        self._ensure_external_plugins_loaded()
        plugins = [*self._load_builtin_dictionary_plugins(), *self._external_dictionary_plugins]
        return CompositeDictionaryPlugin(plugins)

    def _load_builtin_dictionary_plugins(self) -> list[DictionaryPlugin]:
        plugins: list[DictionaryPlugin] = []

        # Built-in starter packs are always available for both directions.
        for bundled_db in (self._config.starter_dictionary_db, self._config.starter_dictionary_ru_en_db):
            if bundled_db.exists():
                plugins.append(SQLiteDictionaryPlugin(bundled_db))

        # User-installed dictionary packs are loaded afterwards.
        for db_path in sorted(self._config.runtime_dictionary_dir.glob("*.sqlite")):
            try:
                plugins.append(SQLiteDictionaryPlugin(db_path))
            except Exception as exc:  # pragma: no cover - protective logging only
                LOGGER.exception("Failed to load dictionary pack %s: %s", db_path, exc)

        if not plugins and not self._external_dictionary_plugins:
            raise RuntimeError("Не найдено ни одного словарного пакета SQLite")
        return plugins

    def _ensure_external_plugins_loaded(self) -> None:
        if self._external_plugins_loaded:
            return
        self._external_plugins_loaded = True
        self._load_external_plugins()

    def _load_external_plugins(self) -> None:
        if not self._config.enable_external_plugins:
            LOGGER.info(
                "External plugins are disabled by default. Set PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS=1 to enable loading from %s",
                self._config.external_plugin_dir,
            )
            return

        plugin_dir = self._config.external_plugin_dir
        if not plugin_dir.exists():
            return
        if plugin_dir.is_symlink() or not plugin_dir.is_dir():
            LOGGER.warning("External plugin directory is not a regular directory: %s", plugin_dir)
            return
        if _has_insecure_permissions(plugin_dir):
            LOGGER.warning("External plugin directory has insecure permissions and will be ignored: %s", plugin_dir)
            return

        for plugin_file in sorted(plugin_dir.glob("*.py")):
            if plugin_file.is_symlink() or not plugin_file.is_file():
                LOGGER.warning("Skipping non-regular external plugin path: %s", plugin_file)
                continue
            if _has_insecure_permissions(plugin_file):
                LOGGER.warning("Skipping external plugin with insecure permissions: %s", plugin_file)
                continue
            try:
                module = _load_external_module(plugin_file)
                if module is None:
                    LOGGER.warning("Skipping plugin without import spec: %s", plugin_file)
                    continue
                register = getattr(module, "register_plugins", None)
                if register is None:
                    LOGGER.warning("Skipping external plugin without register_plugins(): %s", plugin_file)
                    continue
                plugin_instances = register()
                for instance in plugin_instances:
                    if isinstance(instance, DocumentPlugin):
                        self._external_document_plugins.append(instance)
                    elif isinstance(instance, DictionaryPlugin):
                        self._external_dictionary_plugins.append(instance)
                    else:
                        LOGGER.warning("Unsupported plugin instance from %s: %r", plugin_file, instance)
            except Exception as exc:  # pragma: no cover - error path only
                LOGGER.exception("Failed to load external plugin %s: %s", plugin_file, exc)
