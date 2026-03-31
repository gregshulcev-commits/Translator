"""Dictionary service facade."""
from __future__ import annotations

from ..models import LookupResult
from ..plugin_api import DictionaryPlugin


class DictionaryService:
    """Thin facade over the configured dictionary plugin."""

    def __init__(self, dictionary_plugin: DictionaryPlugin):
        self._dictionary_plugin = dictionary_plugin

    def lookup(self, word: str) -> LookupResult:
        return self._dictionary_plugin.lookup(word)

    def entry_count(self) -> int:
        return self._dictionary_plugin.available_entries()

    def pack_count(self) -> int:
        plugins = getattr(self._dictionary_plugin, "plugins", None)
        if callable(plugins):
            return len(plugins())
        if isinstance(plugins, list):
            return len(plugins)
        return 1
