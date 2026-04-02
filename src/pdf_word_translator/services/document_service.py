"""Document service.

This module isolates document opening and caching from the UI.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence
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

    def __init__(self, document_plugins: DocumentPlugin | Sequence[DocumentPlugin] | Iterable[DocumentPlugin]):
        if isinstance(document_plugins, DocumentPlugin):
            self._document_plugins = [document_plugins]
        else:
            self._document_plugins = list(document_plugins)
        self._active_plugin: Optional[DocumentPlugin] = None
        self._session: Optional[DocumentSession] = None
        self._render_cache: Dict[tuple[int, float], RenderedPage] = {}
        self._path: Optional[Path] = None
        self._page_size_cache: Dict[int, tuple[float, float]] = {}

    @staticmethod
    def _close_session(session: DocumentSession) -> None:
        try:
            session.close()
        except Exception as exc:  # pragma: no cover - defensive cleanup only
            LOGGER.warning("Failed to close document session cleanly: %s", exc)

    @property
    def session(self) -> DocumentSession:
        if self._session is None:
            raise RuntimeError("Документ еще не открыт")
        return self._session

    @property
    def current_path(self) -> Optional[Path]:
        return self._path

    def supported_extensions(self) -> list[str]:
        values: list[str] = []
        for plugin in self._document_plugins:
            for extension in plugin.supported_extensions():
                if extension not in values:
                    values.append(extension)
        return values

    def plugin_for_path(self, path: Path) -> DocumentPlugin | None:
        for plugin in self._document_plugins:
            if plugin.can_open(path):
                return plugin
        return None

    def open_document(self, path: Path) -> None:
        plugin = self.plugin_for_path(path)
        if plugin is None:
            raise RuntimeError(f"Формат файла не поддерживается: {path.suffix or path.name}")
        LOGGER.info("Opening document with %s: %s", plugin.plugin_id(), path)
        new_session = plugin.open(path)
        previous_session = self._session

        self._active_plugin = plugin
        self._session = new_session
        self._render_cache.clear()
        self._page_size_cache.clear()
        self._path = path

        if previous_session is not None and previous_session is not new_session:
            self._close_session(previous_session)

    def page_count(self) -> int:
        return self.session.page_count()

    def page_dimensions(self, page_index: int) -> tuple[float, float]:
        if page_index not in self._page_size_cache:
            self._page_size_cache[page_index] = self.session.page_size(page_index)
        return self._page_size_cache[page_index]

    def render_page(self, page_index: int, zoom: float) -> RenderedPage:
        cache_key = (page_index, round(zoom, 2))
        if cache_key not in self._render_cache:
            image = self.session.render_page(page_index, zoom)
            self._render_cache[cache_key] = RenderedPage(page_index=page_index, zoom=zoom, image=image)
        return self._render_cache[cache_key]

    def clear_cache(self) -> None:
        """Drop rendered page images, e.g. after a zoom change."""
        self._render_cache.clear()
