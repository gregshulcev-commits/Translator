"""Dictionary service facade."""
from __future__ import annotations

from ..models import DictionaryPackInfo, LookupResult, TranslationDirection
from ..plugin_api import DictionaryPlugin


class DictionaryService:
    """Thin facade over the configured dictionary plugin."""

    def __init__(self, dictionary_plugin: DictionaryPlugin):
        self._dictionary_plugin = dictionary_plugin

    def replace_plugin(self, dictionary_plugin: DictionaryPlugin) -> None:
        """Hot-swap the active dictionary provider after an import/install step."""
        closer = getattr(self._dictionary_plugin, "close", None)
        if callable(closer):
            closer()
        self._dictionary_plugin = dictionary_plugin

    def lookup(self, word: str, direction: TranslationDirection = "en-ru") -> LookupResult:
        return self._dictionary_plugin.lookup(word, direction=direction)

    def supports_direction(self, direction: TranslationDirection) -> bool:
        return self._dictionary_plugin.supports(direction)

    def entry_count(self) -> int:
        return self._dictionary_plugin.available_entries()

    def pack_count(self) -> int:
        plugins = getattr(self._dictionary_plugin, "plugins", None)
        if callable(plugins):
            return len(plugins())
        if isinstance(plugins, list):
            return len(plugins)
        return 1

    def pack_infos(self) -> list[DictionaryPackInfo]:
        plugins = getattr(self._dictionary_plugin, "plugins", None)
        if callable(plugins):
            return [plugin.pack_info() for plugin in plugins()]
        if isinstance(plugins, list):
            return [plugin.pack_info() for plugin in plugins]
        return [self._dictionary_plugin.pack_info()]
