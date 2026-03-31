"""Plain-text document plugin."""
from __future__ import annotations

from pathlib import Path

from .document_text_base import TextDocumentPlugin, TextDocumentSession, TextParagraph


class PlainTextDocumentPlugin(TextDocumentPlugin):
    """Open UTF-8 TXT files as paginated documents."""

    def __init__(self):
        super().__init__([".txt"])

    def plugin_id(self) -> str:
        return "document.txt"

    def open(self, path: Path) -> TextDocumentSession:
        raw_text = Path(path).read_text(encoding="utf-8")
        paragraphs = []
        for chunk in raw_text.replace("\r\n", "\n").split("\n\n"):
            text = " ".join(line.strip() for line in chunk.splitlines() if line.strip())
            if text:
                paragraphs.append(TextParagraph(text=text, style="body"))
        if not paragraphs:
            paragraphs = [TextParagraph(text="(пустой документ)", style="body")]
        return TextDocumentSession(path, paragraphs)
