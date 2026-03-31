"""Composite dictionary plugin.

This plugin lets the application search multiple dictionary packs without
changing the lookup workflow. The first pack has the highest priority.
"""
from __future__ import annotations

from typing import Iterable

from ..models import LookupResult
from ..plugin_api import DictionaryPlugin


class CompositeDictionaryPlugin(DictionaryPlugin):
    def __init__(self, plugins: Iterable[DictionaryPlugin]):
        self._plugins = list(plugins)

    def plugin_id(self) -> str:
        return "dictionary.composite"

    def lookup(self, word: str) -> LookupResult:
        fallback: LookupResult | None = None
        for plugin in self._plugins:
            result = plugin.lookup(word)
            if fallback is None:
                fallback = result
            if result.found:
                return result
        if fallback is None:
            return LookupResult(query=word, normalized_query="", entry=None, strategy="no_dictionary")
        return fallback

    def available_entries(self) -> int:
        return sum(plugin.available_entries() for plugin in self._plugins)

    @property
    def plugins(self) -> list[DictionaryPlugin]:
        return list(self._plugins)
