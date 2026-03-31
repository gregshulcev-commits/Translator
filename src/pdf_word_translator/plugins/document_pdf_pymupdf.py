"""PDF provider implemented with PyMuPDF."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple
import logging
import re

import fitz
from PIL import Image

from ..models import DocumentSentence, SearchHit, WordToken
from ..plugin_api import DocumentPlugin, DocumentSession
from ..utils.token_splitter import split_token_rect


LOGGER = logging.getLogger(__name__)
SENTENCE_END_RE = re.compile(r"[.!?;:]$")


@dataclass
class _PageCache:
    tokens: List[WordToken]
    sentence_words: List[Tuple[str, WordToken]]
    token_indexes: Dict[str, int]


class PyMuPdfDocumentSession(DocumentSession):
    def __init__(self, path: Path):
        self._path = path
        self._doc = fitz.open(path)
        self._page_cache: Dict[int, _PageCache] = {}

    def page_count(self) -> int:
        return self._doc.page_count

    def page_size(self, page_index: int) -> tuple[float, float]:
        rect = self._doc[page_index].rect
        return float(rect.width), float(rect.height)

    def render_page(self, page_index: int, zoom: float):
        page = self._doc[page_index]
        matrix = fitz.Matrix(zoom, zoom)
        pixmap = page.get_pixmap(matrix=matrix, alpha=False)
        mode = "RGB" if pixmap.n < 4 else "RGBA"
        return Image.frombytes(mode, [pixmap.width, pixmap.height], pixmap.samples)

    def get_tokens(self, page_index: int) -> List[WordToken]:
        return self._ensure_page_cache(page_index).tokens

    def find_token_at(self, page_index: int, x: float, y: float) -> WordToken | None:
        tokens = self.get_tokens(page_index)
        point = fitz.Point(x, y)
        for token in tokens:
            if fitz.Rect(token.rect).contains(point):
                return token
        nearest: WordToken | None = None
        nearest_distance = float("inf")
        for token in tokens:
            rect = fitz.Rect(token.rect)
            cx = min(max(x, rect.x0), rect.x1)
            cy = min(max(y, rect.y0), rect.y1)
            distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if distance < nearest_distance:
                nearest_distance = distance
                nearest = token
        return nearest if nearest_distance <= 6 else None

    def get_sentence_for_token(self, token: WordToken) -> DocumentSentence:
        page_cache = self._ensure_page_cache(token.page_index)
        token_index = page_cache.token_indexes.get(token.token_id)
        if token_index is None:
            return DocumentSentence(page_index=token.page_index, text=token.text)
        left = token_index
        while left > 0:
            previous_text = page_cache.sentence_words[left - 1][0]
            if SENTENCE_END_RE.search(previous_text):
                break
            left -= 1
        right = token_index
        while right + 1 < len(page_cache.sentence_words):
            current_text = page_cache.sentence_words[right][0]
            if SENTENCE_END_RE.search(current_text):
                break
            right += 1
            if SENTENCE_END_RE.search(page_cache.sentence_words[right][0]):
                break
        parts = [page_cache.sentence_words[idx][0] for idx in range(left, right + 1)]
        return DocumentSentence(page_index=token.page_index, text=self._join_words(parts))

    def search(self, query: str) -> List[SearchHit]:
        results: List[SearchHit] = []
        if not query.strip():
            return results
        for page_index in range(self.page_count()):
            page = self._doc[page_index]
            rects = page.search_for(query)
            if not rects:
                continue
            page_text = page.get_text("text")
            preview = self._preview_for_query(page_text, query)
            for rect in rects:
                results.append(SearchHit(page_index=page_index, rect=(rect.x0, rect.y0, rect.x1, rect.y1), preview=preview))
        return results

    def _ensure_page_cache(self, page_index: int) -> _PageCache:
        if page_index in self._page_cache:
            return self._page_cache[page_index]

        page = self._doc[page_index]
        raw_words = page.get_text("words", sort=True)
        tokens: List[WordToken] = []
        sentence_words: List[Tuple[str, WordToken]] = []
        token_indexes: Dict[str, int] = {}
        running_word_no = 0
        for x0, y0, x1, y1, text, block_no, line_no, word_no in raw_words:
            split_tokens = split_token_rect(
                text,
                (x0, y0, x1, y1),
                token_id_prefix=f"p{page_index}-b{block_no}-l{line_no}-w{word_no}",
                page_index=page_index,
                block_no=block_no,
                line_no=line_no,
                word_no=running_word_no,
            )
            for token in split_tokens:
                token_indexes[token.token_id] = len(sentence_words)
                tokens.append(token)
                sentence_words.append((token.text, token))
                running_word_no += 1

        cache = _PageCache(tokens=tokens, sentence_words=sentence_words, token_indexes=token_indexes)
        self._page_cache[page_index] = cache
        return cache

    @staticmethod
    def _join_words(words: List[str]) -> str:
        sentence = " ".join(words)
        sentence = re.sub(r"\s+([,.;:!?])", r"\1", sentence)
        sentence = re.sub(r"\(\s+", "(", sentence)
        sentence = re.sub(r"\s+\)", ")", sentence)
        return sentence.strip()

    @staticmethod
    def _preview_for_query(text: str, query: str, limit: int = 140) -> str:
        lower_text = text.lower()
        lower_query = query.lower()
        position = lower_text.find(lower_query)
        if position == -1:
            return text[:limit].replace("\n", " ")
        start = max(0, position - 40)
        end = min(len(text), position + len(query) + 60)
        preview = text[start:end].replace("\n", " ")
        return preview[:limit]


class PyMuPdfDocumentPlugin(DocumentPlugin):
    def plugin_id(self) -> str:
        return "document.pdf.pymupdf"

    def supported_extensions(self):
        return [".pdf"]

    def can_open(self, path: Path) -> bool:
        return path.suffix.lower() in self.supported_extensions()

    def open(self, path: Path) -> DocumentSession:
        LOGGER.info("Using PyMuPDF document provider for %s", path)
        return PyMuPdfDocumentSession(path)
