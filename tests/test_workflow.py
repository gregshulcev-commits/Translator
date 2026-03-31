from pathlib import Path

import fitz

from pdf_word_translator.plugins.dictionary_sqlite import SQLiteDictionaryPlugin
from pdf_word_translator.plugins.document_pdf_pymupdf import PyMuPdfDocumentPlugin
from pdf_word_translator.services.dictionary_service import DictionaryService
from pdf_word_translator.services.document_service import DocumentService
from pdf_word_translator.services.translation_workflow import TranslationWorkflow
from pdf_word_translator.utils.dictionary_builder import build_dictionary_from_csv


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _make_sample_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "workflow.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "Driver configuration is available.", fontsize=14)
    doc.save(pdf_path)
    doc.close()
    return pdf_path


def test_workflow_translates_clicked_word(tmp_path: Path) -> None:
    pdf_path = _make_sample_pdf(tmp_path)
    csv_path = DATA_DIR / "starter_dictionary.csv"
    db_path = DATA_DIR / "starter_dictionary.sqlite"
    build_dictionary_from_csv(csv_path, db_path)

    doc_service = DocumentService(PyMuPdfDocumentPlugin())
    doc_service.open_document(pdf_path)
    dict_service = DictionaryService(SQLiteDictionaryPlugin(db_path))
    workflow = TranslationWorkflow(doc_service, dict_service)

    token = next(t for t in doc_service.session.get_tokens(0) if t.normalized_text == "configuration")
    x0, y0, x1, y1 = token.rect
    result = workflow.translate_point(0, (x0 + x1) / 2, (y0 + y1) / 2)

    assert result is not None
    assert result.lookup.found
    assert result.lookup.entry is not None
    assert result.lookup.entry.best_translation == "конфигурация"
