"""Helpers for extracting a compact sentence/line context around a clicked word.

The original MVP collected context by walking left/right through the whole page
until it met punctuation. That worked for paragraphs, but on technical PDFs it
could accidentally grab unrelated titles, table headers or neighbouring blocks.

This module keeps the heuristic deliberately conservative:

* never cross a PDF/text block boundary;
* prefer the sentence inside the current block when it is clearly delimited;
* fall back to the current line when the block looks like a table/header or the
  sentence becomes too large.
"""
from __future__ import annotations

from collections import defaultdict
import re
from typing import Sequence

from ..models import WordToken


SENTENCE_END_RE = re.compile(r"[.!?](?:[\"')\]]*)$")
PUNCTUATION_RE = re.compile(r"[.!?]")


def extract_compact_context(
    sentence_words: Sequence[tuple[str, WordToken]],
    token_index: int,
    *,
    max_tokens: int = 40,
    max_chars: int = 260,
) -> str:
    """Return a conservative context string around ``token_index``.

    The function prefers a sentence fragment within the current ``block_no``.
    If the block has no visible sentence punctuation or if the extracted
    sentence would be too large, the current line is returned instead.
    """

    if token_index < 0 or token_index >= len(sentence_words):
        return ""

    token = sentence_words[token_index][1]
    block_start, block_end = _block_bounds(sentence_words, token_index, token.block_no)
    block_words = sentence_words[block_start : block_end + 1]
    local_index = token_index - block_start

    line_text = _line_text(block_words, token.line_no)
    if not block_words:
        return line_text or token.text

    if not _block_has_sentence_markers(block_words):
        return line_text or token.text

    sentence_text = _sentence_from_block(block_words, local_index)
    if not sentence_text:
        return line_text or token.text

    if _word_count(sentence_text) > max_tokens or len(sentence_text) > max_chars:
        return line_text or token.text

    return sentence_text


def _block_bounds(
    sentence_words: Sequence[tuple[str, WordToken]],
    token_index: int,
    block_no: int,
) -> tuple[int, int]:
    left = token_index
    while left > 0 and sentence_words[left - 1][1].block_no == block_no:
        left -= 1

    right = token_index
    while right + 1 < len(sentence_words) and sentence_words[right + 1][1].block_no == block_no:
        right += 1
    return left, right


def _block_has_sentence_markers(block_words: Sequence[tuple[str, WordToken]]) -> bool:
    return any(PUNCTUATION_RE.search(text) for text, _token in block_words)


def _sentence_from_block(block_words: Sequence[tuple[str, WordToken]], token_index: int) -> str:
    left = token_index
    while left > 0:
        previous_text = block_words[left - 1][0]
        if SENTENCE_END_RE.search(previous_text):
            break
        left -= 1

    right = token_index
    while right + 1 < len(block_words):
        current_text = block_words[right][0]
        if SENTENCE_END_RE.search(current_text):
            break
        right += 1
        if SENTENCE_END_RE.search(block_words[right][0]):
            break

    parts = [text for text, _token in block_words[left : right + 1]]
    return _join_words(parts)


def _line_text(block_words: Sequence[tuple[str, WordToken]], line_no: int) -> str:
    parts = [text for text, token in block_words if token.line_no == line_no]
    return _join_words(parts)


def _join_words(words: Sequence[str]) -> str:
    sentence = " ".join(str(word) for word in words if str(word).strip())
    sentence = re.sub(r"\s+([,.;:!?])", r"\1", sentence)
    sentence = re.sub(r"\(\s+", "(", sentence)
    sentence = re.sub(r"\s+\)", ")", sentence)
    sentence = re.sub(r"\s+", " ", sentence)
    return sentence.strip()


def _word_count(text: str) -> int:
    return len([chunk for chunk in text.split() if chunk])
