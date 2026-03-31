from pathlib import Path

from pdf_word_translator.plugins.dictionary_sqlite import SQLiteDictionaryPlugin
from pdf_word_translator.utils.dictionary_builder import build_dictionary_from_csv


DATA_DIR = Path(__file__).resolve().parents[1] / "data"


def _plugin() -> SQLiteDictionaryPlugin:
    csv_path = DATA_DIR / "starter_dictionary.csv"
    db_path = DATA_DIR / "starter_dictionary.sqlite"
    build_dictionary_from_csv(csv_path, db_path)
    return SQLiteDictionaryPlugin(db_path)


def test_dictionary_exact_lookup() -> None:
    plugin = _plugin()
    result = plugin.lookup("driver")
    assert result.found
    assert result.entry is not None
    assert result.entry.best_translation == "драйвер"


def test_dictionary_heuristic_lookup() -> None:
    plugin = _plugin()
    result = plugin.lookup("systems")
    assert result.found
    assert result.entry is not None
    assert result.resolved_headword == "system"
