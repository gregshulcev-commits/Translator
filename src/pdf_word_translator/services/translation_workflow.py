"""Core selection-to-translation workflow.

The UI uses this service to keep the click handling deterministic and easy to
unit test.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..models import DocumentSentence, LookupResult, TranslationDirection, WordToken
from .dictionary_service import DictionaryService
from .document_service import DocumentService


@dataclass(frozen=True)
class TranslationViewModel:
    token: WordToken
    context: DocumentSentence
    lookup: LookupResult
    direction: TranslationDirection


class TranslationWorkflow:
    """Resolve a click on the page into token, context, and translation."""

    def __init__(self, document_service: DocumentService, dictionary_service: DictionaryService):
        self._document_service = document_service
        self._dictionary_service = dictionary_service

    def translate_point(
        self,
        page_index: int,
        x: float,
        y: float,
        direction: TranslationDirection = "en-ru",
    ) -> TranslationViewModel | None:
        token = self._document_service.session.find_token_at(page_index, x, y)
        if token is None:
            return None
        context = self._document_service.session.get_sentence_for_token(token)
        lookup = self._dictionary_service.lookup(token.text, direction=direction)
        return TranslationViewModel(token=token, context=context, lookup=lookup, direction=direction)
