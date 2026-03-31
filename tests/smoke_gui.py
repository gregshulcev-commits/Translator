"""Small GUI smoke test executed under Xvfb in CI-like environments."""
from __future__ import annotations

from pathlib import Path
import tempfile
import tkinter as tk

import fitz

from pdf_word_translator.config import AppConfig
from pdf_word_translator.plugins.dictionary_sqlite import SQLiteDictionaryPlugin
from pdf_word_translator.plugins.document_pdf_pymupdf import PyMuPdfDocumentPlugin
from pdf_word_translator.services.dictionary_service import DictionaryService
from pdf_word_translator.services.document_service import DocumentService
from pdf_word_translator.services.translation_workflow import TranslationWorkflow
from pdf_word_translator.ui.main_window import MainWindow
from pdf_word_translator.utils.dictionary_builder import build_dictionary_from_csv
from pdf_word_translator.utils.logging_utils import setup_logging


def make_sample_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Driver configuration window.", fontsize=14)
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
        document_service = DocumentService(PyMuPdfDocumentPlugin())
        dictionary_service = DictionaryService(SQLiteDictionaryPlugin(data_dir / "starter_dictionary.sqlite"))
        workflow = TranslationWorkflow(document_service, dictionary_service)
        window = MainWindow(root, config, document_service, dictionary_service, workflow)
        window.open_document_path(pdf_path)
        root.update_idletasks()

        token = next(t for t in document_service.session.get_tokens(0) if t.normalized_text == "configuration")
        x0, y0, x1, y1 = token.rect
        result = window.process_click_at_page_coords((x0 + x1) / 2, (y0 + y1) / 2)
        root.update_idletasks()
        assert result is not None
        assert window.best_translation_var.get() == "конфигурация"
        root.destroy()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
