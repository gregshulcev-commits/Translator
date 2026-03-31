"""English token normalization and heuristic lemmatization.

The MVP intentionally uses a lightweight heuristic normalizer so the app stays
self-contained and does not depend on large NLP models. The rules are simple
but effective enough for technical PDFs and a starter dictionary.
"""
from __future__ import annotations

from typing import Iterable, List
import re


WORD_EDGE_RE = re.compile(r"(^[^A-Za-z0-9]+|[^A-Za-z0-9]+$)")
INNER_APOSTROPHE_RE = re.compile(r"[’`]", re.UNICODE)


class EnglishWordNormalizer:
    """Utility that produces lookup candidates for an English token."""

    STOPLIKE_PUNCTUATION = "-_'"

    @staticmethod
    def normalize(word: str) -> str:
        cleaned = INNER_APOSTROPHE_RE.sub("'", word.strip())
        cleaned = WORD_EDGE_RE.sub("", cleaned)
        return cleaned.lower()

    @classmethod
    def candidate_forms(cls, word: str) -> List[str]:
        """Return lookup candidates ordered from safest to most heuristic."""
        normalized = cls.normalize(word)
        if not normalized:
            return []

        candidates: List[str] = []

        def add(item: str) -> None:
            item = item.strip().lower()
            if item and item not in candidates:
                candidates.append(item)

        add(normalized)
        add(normalized.replace("-", ""))
        if "-" in normalized:
            for part in normalized.split("-"):
                add(part)

        # Possessive and apostrophe forms.
        if normalized.endswith("'s"):
            add(normalized[:-2])
        if normalized.endswith("s'"):
            add(normalized[:-1])

        # Very common plural rules.
        if normalized.endswith("ies") and len(normalized) > 4:
            add(normalized[:-3] + "y")
        if normalized.endswith("es") and len(normalized) > 3:
            add(normalized[:-2])
            add(normalized[:-1])
        if normalized.endswith("s") and len(normalized) > 3:
            add(normalized[:-1])

        # Past tense.
        if normalized.endswith("ied") and len(normalized) > 4:
            add(normalized[:-3] + "y")
        if normalized.endswith("ed") and len(normalized) > 4:
            add(normalized[:-2])
            add(normalized[:-1])
            if normalized[:-2].endswith(tuple("bcdfghjklmnpqrstvwxyz")):
                add(normalized[:-2] + "e")
            # doubled consonant, e.g. stopped -> stop
            if len(normalized) > 4 and normalized[-3] == normalized[-4]:
                add(normalized[:-3])

        # Gerund / present participle.
        if normalized.endswith("ing") and len(normalized) > 5:
            stem = normalized[:-3]
            add(stem)
            add(stem + "e")
            if len(stem) > 2 and stem[-1] == stem[-2]:
                add(stem[:-1])

        return candidates
