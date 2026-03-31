"""Plugin interfaces for the MVP.

The application currently ships with one document plugin and one dictionary
plugin, but the interfaces are deliberately separated so that a future OCR or
DOCX provider can be plugged in without changing the UI logic.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, List

from .models import DictionaryEntry, DocumentSentence, LookupResult, SearchHit, WordToken


class DocumentSession(ABC):
    """An opened document instance."""

    @abstractmethod
    def page_count(self) -> int:
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
    def lookup(self, word: str) -> LookupResult:
        raise NotImplementedError

    @abstractmethod
    def available_entries(self) -> int:
        raise NotImplementedError
