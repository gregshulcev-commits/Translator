"""Builtin and external plugin loading.

The loader keeps the MVP simple: builtin plugins are always available, and any
additional ``*.py`` files placed into the external plugin directory may provide
``register_plugins()`` returning plugin instances.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from importlib import util as importlib_util
from pathlib import Path
from types import ModuleType
from typing import List
import logging

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


def _load_external_module(path: Path) -> ModuleType | None:
    spec = importlib_util.spec_from_file_location(path.stem, path)
    if spec is None or spec.loader is None:
        return None
    module = importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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

        # The small bundled technical glossary always has the highest priority.
        if self._config.starter_dictionary_db.exists():
            plugins.append(SQLiteDictionaryPlugin(self._config.starter_dictionary_db))

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
        plugin_dir = self._config.external_plugin_dir
        if not plugin_dir.exists():
            return

        for plugin_file in sorted(plugin_dir.glob("*.py")):
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
