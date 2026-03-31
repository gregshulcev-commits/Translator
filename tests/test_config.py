from pathlib import Path

from pdf_word_translator.config import DATA_ROOT, PROJECT_ROOT


def test_project_root_points_to_repository() -> None:
    assert (PROJECT_ROOT / "src" / "pdf_word_translator").exists()
    assert DATA_ROOT == PROJECT_ROOT / "data"
    assert (DATA_ROOT / "starter_dictionary.csv").exists()
