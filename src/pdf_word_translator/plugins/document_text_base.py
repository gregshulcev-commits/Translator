"""Shared text-document session logic for TXT and FB2.

The desktop MVP renders text-based formats into synthetic pages using Pillow so
that the rest of the application can keep the same click-to-translate workflow
used for PDF. Each word receives a bounding box in page coordinates, which
means search, scrolling, highlighting and dictionary lookup all work through the
same domain model.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence
import re

from PIL import Image, ImageDraw, ImageFont

from ..models import DocumentSentence, SearchHit, WordToken
from ..plugin_api import DocumentPlugin, DocumentSession
from ..utils.context_extraction import extract_compact_context
from ..utils.text_normalizer import WordNormalizer
from ..utils.token_splitter import split_token_rect


PAGE_WIDTH = 820
PAGE_HEIGHT = 1180
MARGIN_X = 72
MARGIN_Y = 72
PAGE_BODY_BOTTOM = PAGE_HEIGHT - MARGIN_Y
BODY_FONT_SIZE = 20
TITLE_FONT_SIZE = 28
BODY_FONT = ImageFont.truetype("DejaVuSans.ttf", BODY_FONT_SIZE)
TITLE_FONT = ImageFont.truetype("DejaVuSans.ttf", TITLE_FONT_SIZE)
BODY_LINE_HEIGHT = BODY_FONT_SIZE + 10
TITLE_LINE_HEIGHT = TITLE_FONT_SIZE + 12
PARAGRAPH_SPACING = 12
TITLE_SPACING = 18
MAX_NEAREST_DISTANCE = 12.0


@dataclass(frozen=True)
class TextParagraph:
    """One semantic text block extracted from a source file."""

    text: str
    style: str = "body"


@dataclass
class _TextPage:
    image: Image.Image
    tokens: list[WordToken]
    sentence_words: list[tuple[str, WordToken]]
    token_indexes: dict[str, int]
    page_text: str


class TextDocumentSession(DocumentSession):
    """Synthetic document session for reflowable text formats."""

    def __init__(self, path: Path, paragraphs: Sequence[TextParagraph]):
        self._path = Path(path)
        self._paragraphs = [paragraph for paragraph in paragraphs if paragraph.text.strip()]
        self._pages = self._paginate(self._paragraphs)

    def page_count(self) -> int:
        return len(self._pages)

    def page_size(self, page_index: int) -> tuple[float, float]:
        return float(PAGE_WIDTH), float(PAGE_HEIGHT)

    def render_page(self, page_index: int, zoom: float):
        page = self._pages[page_index]
        if zoom == 1.0:
            return page.image
        width = max(1, int(page.image.width * zoom))
        height = max(1, int(page.image.height * zoom))
        return page.image.resize((width, height), Image.Resampling.LANCZOS)

    def get_tokens(self, page_index: int) -> List[WordToken]:
        return list(self._pages[page_index].tokens)

    def find_token_at(self, page_index: int, x: float, y: float) -> WordToken | None:
        tokens = self._pages[page_index].tokens
        for token in tokens:
            x0, y0, x1, y1 = token.rect
            if x0 <= x <= x1 and y0 <= y <= y1:
                return token
        nearest: WordToken | None = None
        nearest_distance = float("inf")
        for token in tokens:
            x0, y0, x1, y1 = token.rect
            cx = min(max(x, x0), x1)
            cy = min(max(y, y0), y1)
            distance = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if distance < nearest_distance:
                nearest_distance = distance
                nearest = token
        return nearest if nearest_distance <= MAX_NEAREST_DISTANCE else None

    def get_sentence_for_token(self, token: WordToken) -> DocumentSentence:
        page = self._pages[token.page_index]
        sentence_words = page.sentence_words
        token_index = page.token_indexes.get(token.token_id)
        if token_index is None:
            return DocumentSentence(page_index=token.page_index, text=token.text)

        sentence = extract_compact_context(sentence_words, token_index)
        return DocumentSentence(page_index=token.page_index, text=sentence or token.text)

    def search(self, query: str) -> List[SearchHit]:
        lower_query = query.strip().lower()
        if not lower_query:
            return []

        hits: list[SearchHit] = []
        for page_index, page in enumerate(self._pages):
            matching_tokens = [token for token in page.tokens if lower_query in token.text.lower() or lower_query in token.normalized_text]
            if matching_tokens:
                for token in matching_tokens:
                    hits.append(
                        SearchHit(
                            page_index=page_index,
                            rect=token.rect,
                            preview=self._preview_for_query(page.page_text, query),
                        )
                    )
                continue

            if lower_query in page.page_text.lower() and page.tokens:
                hits.append(
                    SearchHit(
                        page_index=page_index,
                        rect=page.tokens[0].rect,
                        preview=self._preview_for_query(page.page_text, query),
                    )
                )
        return hits

    def _paginate(self, paragraphs: Sequence[TextParagraph]) -> list[_TextPage]:
        pages: list[_TextPage] = []
        image, draw = self._new_page_canvas()
        tokens: list[WordToken] = []
        sentence_words: list[tuple[str, WordToken]] = []
        token_indexes: dict[str, int] = {}
        page_text_words: list[str] = []
        page_index = 0
        token_counter = 0
        y = MARGIN_Y

        def flush_page() -> None:
            nonlocal image, draw, tokens, sentence_words, token_indexes, page_text_words, page_index, token_counter, y
            pages.append(
                _TextPage(
                    image=image,
                    tokens=list(tokens),
                    sentence_words=list(sentence_words),
                    token_indexes=dict(token_indexes),
                    page_text=self._join_words(page_text_words),
                )
            )
            page_index += 1
            token_counter = 0
            image, draw = self._new_page_canvas()
            tokens = []
            sentence_words = []
            token_indexes = {}
            page_text_words = []
            y = MARGIN_Y

        for paragraph_index, paragraph in enumerate(paragraphs):
            font = TITLE_FONT if paragraph.style == "title" else BODY_FONT
            line_height = TITLE_LINE_HEIGHT if paragraph.style == "title" else BODY_LINE_HEIGHT
            spacing_after = TITLE_SPACING if paragraph.style == "title" else PARAGRAPH_SPACING
            words = paragraph.text.split()
            if not words:
                continue

            paragraph_block_no = paragraph_index
            paragraph_line_no = 0
            x = MARGIN_X
            for word in words:
                word_width = self._text_width(font, word)
                word_height = self._text_height(font, word)
                space_width = self._text_width(font, " ")
                if x > MARGIN_X and x + word_width > PAGE_WIDTH - MARGIN_X:
                    x = MARGIN_X
                    y += line_height
                    paragraph_line_no += 1
                if y + line_height > PAGE_BODY_BOTTOM:
                    flush_page()
                    font = TITLE_FONT if paragraph.style == "title" else BODY_FONT
                    line_height = TITLE_LINE_HEIGHT if paragraph.style == "title" else BODY_LINE_HEIGHT
                    spacing_after = TITLE_SPACING if paragraph.style == "title" else PARAGRAPH_SPACING
                    x = MARGIN_X
                    paragraph_line_no = 0
                draw.text((x, y), word, fill="#111827", font=font)
                split_tokens = split_token_rect(
                    word,
                    (x, y, x + word_width, y + word_height),
                    token_id_prefix=f"p{page_index}-w{token_counter}",
                    page_index=page_index,
                    block_no=paragraph_block_no,
                    line_no=paragraph_line_no,
                    word_no=token_counter,
                )
                for token in split_tokens:
                    token_indexes[token.token_id] = len(sentence_words)
                    tokens.append(token)
                    sentence_words.append((token.text, token))
                    token_counter += 1
                page_text_words.extend(token.text for token in split_tokens)
                x += word_width + space_width

            y += line_height + spacing_after
            if y + BODY_LINE_HEIGHT > PAGE_BODY_BOTTOM and paragraph is not paragraphs[-1]:
                flush_page()

        pages.append(
            _TextPage(
                image=image,
                tokens=list(tokens),
                sentence_words=list(sentence_words),
                token_indexes=dict(token_indexes),
                page_text=self._join_words(page_text_words),
            )
        )
        return pages

    @staticmethod
    def _new_page_canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
        image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
        draw = ImageDraw.Draw(image)
        return image, draw

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

    @staticmethod
    def _text_width(font: ImageFont.ImageFont, text: str) -> int:
        bbox = font.getbbox(text)
        return bbox[2] - bbox[0]

    @staticmethod
    def _text_height(font: ImageFont.ImageFont, text: str) -> int:
        bbox = font.getbbox(text)
        return bbox[3] - bbox[1]


class TextDocumentPlugin(DocumentPlugin):
    """Base class for lightweight reflowable text document plugins."""

    def __init__(self, supported_extensions: Sequence[str]):
        self._supported_extensions = tuple(extension.lower() for extension in supported_extensions)

    def plugin_id(self) -> str:
        raise NotImplementedError

    def supported_extensions(self):
        return self._supported_extensions

    def can_open(self, path: Path) -> bool:
        return path.suffix.lower() in self.supported_extensions()

    def open(self, path: Path) -> DocumentSession:
        raise NotImplementedError
