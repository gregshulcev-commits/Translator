"""Helpers for splitting compound tokens into individually clickable parts."""
from __future__ import annotations

import re
from typing import Iterable, List, Tuple

from ..models import WordToken
from .text_normalizer import WordNormalizer


SPLIT_RE = re.compile(r"(?<=[A-Za-zА-Яа-яЁё0-9])[\\/](?=[A-Za-zА-Яа-яЁё0-9])")


def split_token_rect(
    text: str,
    rect: tuple[float, float, float, float],
    *,
    token_id_prefix: str,
    page_index: int,
    block_no: int,
    line_no: int,
    word_no: int,
) -> list[WordToken]:
    """Split a token on slash/backslash and distribute the rect proportionally."""
    parts = SPLIT_RE.split(text)
    if len(parts) <= 1:
        return [
            WordToken(
                token_id=f"{token_id_prefix}-0",
                text=text,
                normalized_text=WordNormalizer.normalize(text),
                page_index=page_index,
                rect=rect,
                block_no=block_no,
                line_no=line_no,
                word_no=word_no,
            )
        ]
    x0, y0, x1, y1 = rect
    total_units = sum(max(1, len(part)) for part in parts)
    width = max(1e-6, x1 - x0)
    current_x = x0
    tokens: list[WordToken] = []
    for index, part in enumerate(parts):
        units = max(1, len(part))
        part_width = width * (units / total_units)
        part_rect = (current_x, y0, current_x + part_width, y1)
        tokens.append(
            WordToken(
                token_id=f"{token_id_prefix}-{index}",
                text=part,
                normalized_text=WordNormalizer.normalize(part),
                page_index=page_index,
                rect=part_rect,
                block_no=block_no,
                line_no=line_no,
                word_no=word_no + index,
            )
        )
        current_x += part_width
    return tokens
