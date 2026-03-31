"""Composite dictionary plugin.

This plugin lets the application search multiple dictionary packs without
changing the lookup workflow. The first supporting pack has the highest
priority for the selected direction.
"""
from __future__ import annotations

from typing import Iterable

from ..models import DictionaryPackInfo, LookupResult, TranslationDirection
from ..plugin_api import DictionaryPlugin


class CompositeDictionaryPlugin(DictionaryPlugin):
    def __init__(self, plugins: Iterable[DictionaryPlugin]):
        self._plugins = list(plugins)

    def plugin_id(self) -> str:
        return "dictionary.composite"

    def pack_info(self) -> DictionaryPackInfo:
        return DictionaryPackInfo(
            pack_id="composite",
            title="Composite dictionary",
            direction="multi",
            category="composite",
            description="Logical wrapper around multiple installed dictionary packs.",
            source="runtime",
        )

    def supports(self, direction: TranslationDirection) -> bool:
        return any(plugin.supports(direction) for plugin in self._plugins)

    def lookup(self, word: str, direction: TranslationDirection = "en-ru") -> LookupResult:
        fallback: LookupResult | None = None
        for plugin in self._plugins:
            if not plugin.supports(direction):
                continue
            result = plugin.lookup(word, direction=direction)
            if fallback is None:
                fallback = result
            if result.found:
                return result
        if fallback is None:
            return LookupResult(query=word, normalized_query="", entry=None, strategy="no_dictionary")
        return fallback

    def available_entries(self) -> int:
        return sum(plugin.available_entries() for plugin in self._plugins)

    def close(self) -> None:
        """Forward close() to child plugins when they provide it."""
        for plugin in self._plugins:
            closer = getattr(plugin, "close", None)
            if callable(closer):
                closer()

    @property
    def plugins(self) -> list[DictionaryPlugin]:
        return list(self._plugins)
