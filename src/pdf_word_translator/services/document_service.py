"""Document service.

This module isolates document opening and caching from the UI.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional
import logging

from PIL.Image import Image as PILImage

from ..plugin_api import DocumentPlugin, DocumentSession


LOGGER = logging.getLogger(__name__)


@dataclass
class RenderedPage:
    page_index: int
    zoom: float
    image: PILImage


class DocumentService:
    """Coordinates document session lifecycle and a tiny page render cache."""

    def __init__(self, document_plugin: DocumentPlugin):
        self._document_plugin = document_plugin
        self._session: Optional[DocumentSession] = None
        self._render_cache: Dict[tuple[int, float], RenderedPage] = {}
        self._path: Optional[Path] = None

    @property
    def session(self) -> DocumentSession:
        if self._session is None:
            raise RuntimeError("Документ еще не открыт")
        return self._session

    @property
    def current_path(self) -> Optional[Path]:
        return self._path

    def open_document(self, path: Path) -> None:
        LOGGER.info("Opening document: %s", path)
        self._session = self._document_plugin.open(path)
        self._render_cache.clear()
        self._path = path

    def page_count(self) -> int:
        return self.session.page_count()

    def render_page(self, page_index: int, zoom: float) -> RenderedPage:
        cache_key = (page_index, round(zoom, 2))
        if cache_key not in self._render_cache:
            image = self.session.render_page(page_index, zoom)
            self._render_cache[cache_key] = RenderedPage(page_index=page_index, zoom=zoom, image=image)
        return self._render_cache[cache_key]

    def prewarm_neighbors(self, current_page: int, zoom: float) -> None:
        """Pre-render adjacent pages.

        The MVP keeps the implementation synchronous and tiny, but the method is
        intentionally isolated so a future background worker can take it over.
        """
        for page_index in (current_page - 1, current_page + 1):
            if 0 <= page_index < self.page_count():
                self.render_page(page_index, zoom)
