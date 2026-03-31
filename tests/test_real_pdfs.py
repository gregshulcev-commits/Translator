from pathlib import Path
import os

import pytest

from pdf_word_translator.plugins.document_pdf_pymupdf import PyMuPdfDocumentPlugin


REAL_PDFS = [
    Path("/mnt/data/IRIO_EPICS_Device_Driver_User's_Manual__RAJ9P8_v1_7.pdf"),
    Path("/mnt/data/CODAC_Core_System_Installation_Manual_33JNKW_v7_5.pdf"),
    Path("/mnt/data/The_CODAC_-_Plant_System_Interface_34V362_v2_2.pdf"),
    Path("/mnt/data/55.E2_Calibration_plan_VQXY8P_v1_0.pdf"),
    Path("/mnt/data/55.E2_-_H-Alpha_First_Plasma_I&C_Cubicle_57WL94_v1_0.pdf"),
    Path("/mnt/data/55.E2_-_H-Alpha_First_Plasma_System_I&C_SRS_57VZSU_v1_0.pdf"),
    Path("/mnt/data/55.E2_-_System_Detailed_Design_Descripti_57WV9W_v1_0.pdf"),
    Path("/mnt/data/CODAC_Core_System_Application_Developmen_33T8LW_v5_8.pdf"),
    Path("/mnt/data/CODAC_Core_System_Overview_34SDZ5_v7_4.pdf"),
]


@pytest.mark.skipif(not all(path.exists() for path in REAL_PDFS), reason="Uploaded integration PDFs are not available")
def test_uploaded_pdfs_expose_text_layer() -> None:
    plugin = PyMuPdfDocumentPlugin()
    for path in REAL_PDFS:
        session = plugin.open(path)
        assert session.page_count() > 0
        assert len(session.get_tokens(0)) > 20


@pytest.mark.skipif(not REAL_PDFS[0].exists(), reason="IRIO sample PDF is not available")
def test_irio_pdf_contains_driver_token() -> None:
    session = PyMuPdfDocumentPlugin().open(REAL_PDFS[0])
    found = False
    for page_index in range(min(10, session.page_count())):
        if any(token.normalized_text == "driver" for token in session.get_tokens(page_index)):
            found = True
            break
    assert found
