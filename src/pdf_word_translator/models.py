"""Domain models shared across the application.

These models avoid passing raw library-specific tuples through the codebase.
That makes tests easier and future provider replacement much cheaper.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple


Rect = Tuple[float, float, float, float]


@dataclass(frozen=True)
class WordToken:
    """A word-sized token extracted from a document page."""

    token_id: str
    text: str
    normalized_text: str
    page_index: int
    rect: Rect
    block_no: int
    line_no: int
    word_no: int


@dataclass(frozen=True)
class SearchHit:
    """Represents a search match in a document."""

    page_index: int
    rect: Rect
    preview: str


@dataclass(frozen=True)
class DocumentSentence:
    """Sentence or line context around a clicked token."""

    page_index: int
    text: str


@dataclass(frozen=True)
class DictionaryEntry:
    """Single dictionary entry.

    Notes:
    - ``headword`` is the canonical English base form.
    - ``best_translation`` is the first translation shown in the panel.
    - ``alternative_translations`` is an ordered list shown below it.
    - ``examples`` is optional and may stay empty in the starter dictionary.
    """

    headword: str
    normalized_headword: str
    transcription: str = ""
    best_translation: str = ""
    alternative_translations: List[str] = field(default_factory=list)
    examples: List[Tuple[str, str]] = field(default_factory=list)
    notes: str = ""


@dataclass(frozen=True)
class LookupResult:
    """Result returned by the dictionary layer."""

    query: str
    normalized_query: str
    entry: Optional[DictionaryEntry]
    resolved_headword: str = ""
    strategy: str = "not_found"
    candidate_forms: Sequence[str] = field(default_factory=tuple)

    @property
    def found(self) -> bool:
        return self.entry is not None
