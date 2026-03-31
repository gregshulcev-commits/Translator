"""Plugin interfaces for the MVP.

The application currently ships with document, dictionary and optional context
translation providers, but the interfaces are deliberately separated so that a
future OCR or DOCX provider can be plugged in without changing the UI logic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, List

from .models import (
    ContextTranslationResult,
    DictionaryPackInfo,
    DocumentSentence,
    LookupResult,
    SearchHit,
    TranslationDirection,
    WordToken,
)


class DocumentSession(ABC):
    """An opened document instance."""

    @abstractmethod
    def page_count(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def page_size(self, page_index: int) -> tuple[float, float]:
        """Return page width/height in document coordinates (zoom == 1.0)."""
        raise NotImplementedError

    @abstractmethod
    def render_page(self, page_index: int, zoom: float):
        """Return a PIL image for the requested page."""
        raise NotImplementedError

    @abstractmethod
    def get_tokens(self, page_index: int) -> List[WordToken]:
        raise NotImplementedError

    @abstractmethod
    def find_token_at(self, page_index: int, x: float, y: float) -> WordToken | None:
        raise NotImplementedError

    @abstractmethod
    def get_sentence_for_token(self, token: WordToken) -> DocumentSentence:
        raise NotImplementedError

    @abstractmethod
    def search(self, query: str) -> List[SearchHit]:
        raise NotImplementedError


class DocumentPlugin(ABC):
    """Provider for a document format."""

    @abstractmethod
    def plugin_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def supported_extensions(self) -> Iterable[str]:
        raise NotImplementedError

    @abstractmethod
    def can_open(self, path: Path) -> bool:
        raise NotImplementedError

    @abstractmethod
    def open(self, path: Path) -> DocumentSession:
        raise NotImplementedError


class DictionaryPlugin(ABC):
    """Provider for dictionary lookup."""

    @abstractmethod
    def plugin_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def pack_info(self) -> DictionaryPackInfo:
        raise NotImplementedError

    @abstractmethod
    def supports(self, direction: TranslationDirection) -> bool:
        raise NotImplementedError

    @abstractmethod
    def lookup(self, word: str, direction: TranslationDirection = "en-ru") -> LookupResult:
        raise NotImplementedError

    @abstractmethod
    def available_entries(self) -> int:
        raise NotImplementedError


class ContextTranslationProvider(ABC):
    """Optional contextual translator for the second line in the compact panel."""

    @abstractmethod
    def provider_id(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def display_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def translate_text(self, text: str, direction: TranslationDirection) -> ContextTranslationResult:
        raise NotImplementedError
