from pathlib import Path

import fitz

from pdf_word_translator.plugins.document_pdf_pymupdf import PyMuPdfDocumentPlugin


def _make_sample_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "sample.pdf"
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), "System configuration guide. Driver support is available.", fontsize=14)
    doc.save(pdf_path)
    doc.close()
    return pdf_path


def test_pdf_tokens_and_sentence_extraction(tmp_path: Path) -> None:
    pdf_path = _make_sample_pdf(tmp_path)
    session = PyMuPdfDocumentPlugin().open(pdf_path)
    tokens = session.get_tokens(0)
    assert any(token.normalized_text == "configuration" for token in tokens)

    config_token = next(token for token in tokens if token.normalized_text == "configuration")
    sentence = session.get_sentence_for_token(config_token)
    assert "System configuration guide." in sentence.text


def test_pdf_search(tmp_path: Path) -> None:
    pdf_path = _make_sample_pdf(tmp_path)
    session = PyMuPdfDocumentPlugin().open(pdf_path)
    hits = session.search("Driver")
    assert hits
    assert hits[0].page_index == 0
