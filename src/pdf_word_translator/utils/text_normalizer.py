"""Language-aware token normalization and lightweight heuristic lemmatization.

The MVP intentionally keeps normalization lightweight so the app stays
self-contained and does not depend on large NLP models. The rules are simple
but effective enough for technical PDFs and bundled glossaries.
"""
from __future__ import annotations

from typing import List
import re


LATIN_EDGE_RE = re.compile(r"(^[^A-Za-z0-9]+|[^A-Za-z0-9]+$)")
CYRILLIC_EDGE_RE = re.compile(r"(^[^A-Za-zА-Яа-яЁё0-9]+|[^A-Za-zА-Яа-яЁё0-9]+$)")
INNER_APOSTROPHE_RE = re.compile(r"[’`]", re.UNICODE)
CYRILLIC_RE = re.compile(r"[А-Яа-яЁё]")
LATIN_RE = re.compile(r"[A-Za-z]")


class WordNormalizer:
    """Produce lookup candidates for a token in English or Russian."""

    @staticmethod
    def detect_language(word: str) -> str:
        if CYRILLIC_RE.search(word) and not LATIN_RE.search(word):
            return "ru"
        return "en"

    @classmethod
    def normalize(cls, word: str, language: str = "auto") -> str:
        language = language if language != "auto" else cls.detect_language(word)
        cleaned = INNER_APOSTROPHE_RE.sub("'", word.strip())
        if language == "ru":
            cleaned = CYRILLIC_EDGE_RE.sub("", cleaned)
            return cleaned.lower().replace("ё", "е")
        cleaned = LATIN_EDGE_RE.sub("", cleaned)
        return cleaned.lower()

    @classmethod
    def candidate_forms(cls, word: str, language: str = "auto") -> List[str]:
        language = language if language != "auto" else cls.detect_language(word)
        normalized = cls.normalize(word, language=language)
        if not normalized:
            return []
        candidates: List[str] = []

        def add(item: str) -> None:
            item = cls.normalize(item, language=language)
            if item and item not in candidates:
                candidates.append(item)

        add(normalized)
        add(normalized.replace("-", ""))
        if "-" in normalized:
            for part in normalized.split("-"):
                add(part)

        if language == "ru":
            cls._add_russian_variants(normalized, add)
        else:
            cls._add_english_variants(normalized, add)
        return candidates

    @staticmethod
    def _add_english_variants(normalized: str, add) -> None:
        if normalized.endswith("'s"):
            add(normalized[:-2])
        if normalized.endswith("s'"):
            add(normalized[:-1])
        if normalized.endswith("ies") and len(normalized) > 4:
            add(normalized[:-3] + "y")
        if normalized.endswith("es") and len(normalized) > 3:
            add(normalized[:-2])
            add(normalized[:-1])
        if normalized.endswith("s") and len(normalized) > 3:
            add(normalized[:-1])
        if normalized.endswith("ied") and len(normalized) > 4:
            add(normalized[:-3] + "y")
        if normalized.endswith("ed") and len(normalized) > 4:
            add(normalized[:-2])
            add(normalized[:-1])
            if normalized[:-2].endswith(tuple("bcdfghjklmnpqrstvwxyz")):
                add(normalized[:-2] + "e")
            if len(normalized) > 4 and normalized[-3] == normalized[-4]:
                add(normalized[:-3])
        if normalized.endswith("ing") and len(normalized) > 5:
            stem = normalized[:-3]
            add(stem)
            add(stem + "e")
            if len(stem) > 2 and stem[-1] == stem[-2]:
                add(stem[:-1])

    @staticmethod
    def _add_russian_variants(normalized: str, add) -> None:
        # Conservative heuristics: enough for simple reverse dictionary lookups.
        endings = (
            "ами", "ями", "ого", "ему", "ому", "ыми", "ими", "ее", "ие", "ые", "ое", "ая", "яя",
            "ам", "ям", "ах", "ях", "ом", "ем", "ой", "ей", "ою", "ею", "у", "ю", "а", "я", "ы", "и", "е", "о"
        )
        for ending in endings:
            if normalized.endswith(ending) and len(normalized) > len(ending) + 1:
                add(normalized[:-len(ending)])
        # frequent noun lemmas
        if normalized.endswith("ии") and len(normalized) > 4:
            add(normalized[:-2] + "я")
            add(normalized[:-2] + "й")
        if normalized.endswith("ов") and len(normalized) > 4:
            add(normalized[:-2])


class EnglishWordNormalizer:
    @staticmethod
    def normalize(word: str) -> str:
        return WordNormalizer.normalize(word, language="en")

    @staticmethod
    def candidate_forms(word: str) -> List[str]:
        return WordNormalizer.candidate_forms(word, language="en")


class RussianWordNormalizer:
    @staticmethod
    def normalize(word: str) -> str:
        return WordNormalizer.normalize(word, language="ru")

    @staticmethod
    def candidate_forms(word: str) -> List[str]:
        return WordNormalizer.candidate_forms(word, language="ru")
