from pathlib import Path

import fitz

from pdf_word_translator.models import RU_EN
from pdf_word_translator.plugins.dictionary_sqlite import SQLiteDictionaryPlugin
from pdf_word_translator.plugins.document_pdf_pymupdf import PyMuPdfDocumentPlugin
from pdf_word_translator.plugins.document_txt import PlainTextDocumentPlugin
from pdf_word_translator.services.dictionary_service import DictionaryService
from pdf_word_translator.services.document_service import DocumentService
from pdf_word_translator.services.translation_workflow import TranslationWorkflow
from pdf_word_translator.utils.dictionary_builder import DictionaryMetadata, build_dictionary_from_csv


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _make_compound_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "compound.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "diagnostic\\measurement channel", fontsize=14)
    doc.save(pdf_path)
    doc.close()
    return pdf_path


def test_compound_pdf_token_is_split_into_clickable_parts(tmp_path: Path) -> None:
    pdf_path = _make_compound_pdf(tmp_path)
    session = PyMuPdfDocumentPlugin().open(pdf_path)
    texts = [token.text for token in session.get_tokens(0)]
    assert "diagnostic" in texts
    assert "measurement" in texts
    assert "diagnostic\\measurement" not in texts


def test_reverse_dictionary_lookup_supports_ru_en() -> None:
    csv_path = DATA_DIR / "starter_dictionary_ru_en.csv"
    db_path = DATA_DIR / "starter_dictionary_ru_en.sqlite"
    build_dictionary_from_csv(
        csv_path,
        db_path,
        metadata=DictionaryMetadata(pack_name="test ru en", direction=RU_EN),
    )
    plugin = SQLiteDictionaryPlugin(db_path)
    result = plugin.lookup("конфигурация", direction=RU_EN)
    assert result.found
    assert result.entry is not None
    assert result.entry.best_translation == "configuration"


def test_workflow_uses_requested_direction(tmp_path: Path) -> None:
    txt_path = tmp_path / "ru.txt"
    txt_path.write_text("конфигурация системы", encoding="utf-8")

    db_path = DATA_DIR / "starter_dictionary_ru_en.sqlite"
    build_dictionary_from_csv(
        DATA_DIR / "starter_dictionary_ru_en.csv",
        db_path,
        metadata=DictionaryMetadata(pack_name="test ru en", direction=RU_EN),
    )

    doc_service = DocumentService(PlainTextDocumentPlugin())
    doc_service.open_document(txt_path)
    dict_service = DictionaryService(SQLiteDictionaryPlugin(db_path))
    workflow = TranslationWorkflow(doc_service, dict_service)

    token = next(t for t in doc_service.session.get_tokens(0) if t.normalized_text == "конфигурация")
    x0, y0, x1, y1 = token.rect
    result = workflow.translate_point(0, (x0 + x1) / 2, (y0 + y1) / 2, direction=RU_EN)
    assert result is not None
    assert result.lookup.found
    assert result.lookup.entry is not None
    assert result.lookup.entry.best_translation == "configuration"
