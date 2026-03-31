"""Small GUI smoke test executed under Xvfb in CI-like environments."""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
import tempfile
import tkinter as tk

import fitz

from pdf_word_translator.config import AppConfig
from pdf_word_translator.plugin_loader import PluginLoader
from pdf_word_translator.services.dictionary_service import DictionaryService
from pdf_word_translator.services.document_service import DocumentService
from pdf_word_translator.services.translation_workflow import TranslationWorkflow
from pdf_word_translator.ui.main_window import MainWindow
from pdf_word_translator.utils.dictionary_builder import build_dictionary_from_csv
from pdf_word_translator.utils.logging_utils import setup_logging
from pdf_word_translator.utils.settings_store import SettingsStore


def make_sample_pdf(path: Path) -> None:
    doc = fitz.open()
    for page_no in range(3):
        page = doc.new_page(height=1500)
        page.insert_text((72, 72), f"Driver configuration window page {page_no + 1}.", fontsize=14)
        for index in range(1, 70):
            page.insert_text((72, 72 + index * 20), f"Additional line {index} for scrolling test on page {page_no + 1}.", fontsize=12)
    doc.save(path)
    doc.close()


def main() -> int:
    project_root = Path(__file__).resolve().parents[1]
    data_dir = project_root / "data"
    build_dictionary_from_csv(data_dir / "starter_dictionary.csv", data_dir / "starter_dictionary.sqlite")

    config = AppConfig()
    config.ensure_runtime_directories()
    setup_logging(config.runtime_log_dir)

    with tempfile.TemporaryDirectory() as tmp:
        pdf_path = Path(tmp) / "gui.pdf"
        make_sample_pdf(pdf_path)

        root = tk.Tk()
        root.withdraw()  # Create widgets without showing a full window in the smoke test.
        plugin_loader = PluginLoader(config)
        registry = plugin_loader.load()
        document_service = DocumentService(registry.document_plugins)
        dictionary_service = DictionaryService(registry.default_dictionary_plugin())
        workflow = TranslationWorkflow(document_service, dictionary_service)
        settings_store = SettingsStore(config.settings_file)
        window = MainWindow(root, config, plugin_loader, document_service, dictionary_service, workflow, settings_store)
        window.open_document_path(pdf_path)
        root.update()

        token = next(t for t in document_service.session.get_tokens(0) if t.normalized_text == "configuration")
        x0, y0, x1, y1 = token.rect
        result = window.process_click_at_page_coords(0, (x0 + x1) / 2, (y0 + y1) / 2)
        root.update()
        assert result is not None
        assert window.best_translation_var.get() == "конфигурация"
        assert "window" in window.example_var.get().lower()

        before = window.canvas.canvasy(0)
        window._on_mousewheel(SimpleNamespace(num=5, delta=0, state=0, x=120, y=120))
        root.update()
        after = window.canvas.canvasy(0)
        assert after >= before

        zoom_before = window.current_zoom
        window._on_mousewheel(SimpleNamespace(num=4, delta=0, state=0x4, x=120, y=120))
        root.update()
        assert window.current_zoom > zoom_before
        assert window.current_zoom <= window.MAX_ZOOM

        root.destroy()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
