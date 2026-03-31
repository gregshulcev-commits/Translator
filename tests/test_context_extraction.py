from __future__ import annotations

from pdf_word_translator.models import WordToken
from pdf_word_translator.utils.context_extraction import extract_compact_context


def _token(text: str, *, token_id: str, block_no: int, line_no: int, word_no: int) -> WordToken:
    return WordToken(
        token_id=token_id,
        text=text,
        normalized_text=text.lower(),
        page_index=0,
        rect=(0.0, 0.0, 1.0, 1.0),
        block_no=block_no,
        line_no=line_no,
        word_no=word_no,
    )


def test_extract_compact_context_returns_sentence_within_same_block() -> None:
    words = [
        ("Document", _token("Document", token_id="t0", block_no=0, line_no=0, word_no=0)),
        ("title", _token("title", token_id="t1", block_no=0, line_no=0, word_no=1)),
        ("Start", _token("Start", token_id="t2", block_no=1, line_no=0, word_no=0)),
        ("the", _token("the", token_id="t3", block_no=1, line_no=0, word_no=1)),
        ("pump.", _token("pump.", token_id="t4", block_no=1, line_no=0, word_no=2)),
        ("Continue", _token("Continue", token_id="t5", block_no=1, line_no=1, word_no=3)),
        ("carefully.", _token("carefully.", token_id="t6", block_no=1, line_no=1, word_no=4)),
    ]

    context = extract_compact_context(words, 3)

    assert context == "Start the pump."


def test_extract_compact_context_falls_back_to_current_line_for_table_like_block() -> None:
    words = [
        ("Tag", _token("Tag", token_id="t0", block_no=2, line_no=0, word_no=0)),
        ("Value", _token("Value", token_id="t1", block_no=2, line_no=0, word_no=1)),
        ("Voltage", _token("Voltage", token_id="t2", block_no=2, line_no=1, word_no=2)),
        ("230V", _token("230V", token_id="t3", block_no=2, line_no=1, word_no=3)),
    ]

    context = extract_compact_context(words, 3)

    assert context == "Voltage 230V"


def test_extract_compact_context_falls_back_to_line_when_sentence_is_too_long() -> None:
    parts = []
    for index in range(50):
        text = f"word{index}"
        if index == 49:
            text += "."
        parts.append((text, _token(text, token_id=f"t{index}", block_no=4, line_no=index // 10, word_no=index)))

    context = extract_compact_context(parts, 25, max_tokens=20, max_chars=120)

    assert context == "word20 word21 word22 word23 word24 word25 word26 word27 word28 word29"
