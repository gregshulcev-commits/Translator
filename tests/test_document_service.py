from __future__ import annotations

from pathlib import Path

import pytest
from PIL import Image

from pdf_word_translator.models import DocumentSentence, SearchHit, WordToken
from pdf_word_translator.plugin_api import DocumentPlugin, DocumentSession
from pdf_word_translator.services.document_service import DocumentService


class _FakeSession(DocumentSession):
    def __init__(self, name: str):
        self.name = name
        self.closed = False

    def page_count(self) -> int:
        return 1

    def page_size(self, page_index: int) -> tuple[float, float]:
        return (100.0, 100.0)

    def render_page(self, page_index: int, zoom: float):
        return Image.new("RGB", (10, 10), "white")

    def get_tokens(self, page_index: int) -> list[WordToken]:
        return []

    def find_token_at(self, page_index: int, x: float, y: float) -> WordToken | None:
        return None

    def get_sentence_for_token(self, token: WordToken) -> DocumentSentence:
        return DocumentSentence(page_index=0, text="")

    def search(self, query: str) -> list[SearchHit]:
        return []

    def close(self) -> None:
        self.closed = True


class _FakePlugin(DocumentPlugin):
    def plugin_id(self) -> str:
        return "document.fake"

    def supported_extensions(self):
        return [".demo"]

    def can_open(self, path: Path) -> bool:
        return path.suffix.lower() == ".demo"

    def open(self, path: Path) -> DocumentSession:
        if path.name == "broken.demo":
            raise RuntimeError("broken document")
        return _FakeSession(path.name)


def test_open_document_closes_previous_session_after_successful_switch(tmp_path: Path) -> None:
    service = DocumentService([_FakePlugin()])
    first = tmp_path / "first.demo"
    second = tmp_path / "second.demo"

    service.open_document(first)
    first_session = service.session
    assert isinstance(first_session, _FakeSession)
    assert first_session.closed is False

    service.open_document(second)

    assert first_session.closed is True
    assert service.current_path == second
    assert isinstance(service.session, _FakeSession)
    assert service.session.name == "second.demo"


def test_failed_open_keeps_previous_session_active(tmp_path: Path) -> None:
    service = DocumentService([_FakePlugin()])
    first = tmp_path / "first.demo"
    broken = tmp_path / "broken.demo"

    service.open_document(first)
    first_session = service.session
    assert isinstance(first_session, _FakeSession)

    with pytest.raises(RuntimeError, match="broken document"):
        service.open_document(broken)

    assert service.session is first_session
    assert service.current_path == first
    assert first_session.closed is False
