"""FB2 (FictionBook 2) document plugin."""
from __future__ import annotations

from pathlib import Path
from defusedxml import ElementTree as ET

from .document_text_base import TextDocumentPlugin, TextDocumentSession, TextParagraph


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _clean_text(value: str | None) -> str:
    return " ".join((value or "").split()).strip()


def _title_from_node(node: ET.Element) -> str:
    parts = []
    for paragraph in node.findall("./{*}p"):
        text = _clean_text(" ".join(paragraph.itertext()))
        if text:
            parts.append(text)
    return " — ".join(parts)


def _walk_fb2(node: ET.Element, paragraphs: list[TextParagraph]) -> None:
    for child in list(node):
        tag = _strip_ns(child.tag)
        if tag == "title":
            title_text = _title_from_node(child)
            if title_text:
                paragraphs.append(TextParagraph(text=title_text, style="title"))
        elif tag in {"p", "subtitle"}:
            text = _clean_text(" ".join(child.itertext()))
            if text:
                paragraphs.append(TextParagraph(text=text, style="body"))
        elif tag in {"section", "body", "poem", "stanza", "epigraph", "annotation"}:
            _walk_fb2(child, paragraphs)


class Fb2DocumentPlugin(TextDocumentPlugin):
    """Open FictionBook 2 documents as paginated text."""

    def __init__(self):
        super().__init__([".fb2"])

    def plugin_id(self) -> str:
        return "document.fb2"

    def open(self, path: Path) -> TextDocumentSession:
        root = ET.parse(path).getroot()
        paragraphs: list[TextParagraph] = []

        book_title = root.find(".//{*}description/{*}title-info/{*}book-title")
        if book_title is not None:
            title = _clean_text(" ".join(book_title.itertext()))
            if title:
                paragraphs.append(TextParagraph(text=title, style="title"))

        for body in root.findall(".//{*}body"):
            _walk_fb2(body, paragraphs)

        if not paragraphs:
            paragraphs = [TextParagraph(text="(FB2 не содержит извлекаемого текста)", style="body")]
        return TextDocumentSession(path, paragraphs)
