from pathlib import Path

from pdf_word_translator.utils.settings_store import SettingsStore, UiSettings


def test_settings_store_roundtrip(tmp_path: Path) -> None:
    settings_file = tmp_path / 'settings.json'
    store = SettingsStore(settings_file)
    store.save(UiSettings(ui_font_size=15))
    loaded = store.load()
    assert loaded.ui_font_size == 15
