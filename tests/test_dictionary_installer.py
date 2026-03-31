from pathlib import Path
import sqlite3

from pdf_word_translator.utils.dictionary_installer import import_csv_pack, install_sqlite_pack


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def test_import_csv_pack_builds_sqlite_dictionary(tmp_path: Path) -> None:
    destination = import_csv_pack(DATA_DIR / "starter_dictionary.csv", tmp_path)
    assert destination.exists()
    connection = sqlite3.connect(destination)
    try:
        count = connection.execute("SELECT COUNT(*) FROM entries").fetchone()[0]
        assert count > 0
    finally:
        connection.close()


def test_install_sqlite_pack_copies_existing_pack(tmp_path: Path) -> None:
    source = DATA_DIR / "starter_dictionary.sqlite"
    destination = install_sqlite_pack(source, tmp_path)
    assert destination.exists()
    assert destination.read_bytes()[:64] == source.read_bytes()[:64]
