from __future__ import annotations

from types import SimpleNamespace

from pdf_word_translator.models import EN_RU, RU_EN
from pdf_word_translator.ui.main_window import MainWindow


def test_argos_help_uses_resizable_dialog_for_en_ru() -> None:
    window = MainWindow.__new__(MainWindow)
    window.settings = SimpleNamespace(direction=EN_RU)

    captured: dict[str, str] = {}

    def fake_show_dialog(title: str, message: str, *, geometry: str = "860x620") -> None:
        captured["title"] = title
        captured["message"] = message
        captured["geometry"] = geometry

    window._show_readonly_text_dialog = fake_show_dialog  # type: ignore[method-assign]

    MainWindow.show_argos_installation_help(window)

    assert captured["title"] == "Установка Argos"
    assert captured["geometry"] == "860x620"
    assert "Перевод → Офлайн-модели Argos…" in captured["message"]
    assert "--from-lang en --to-lang ru" in captured["message"]


def test_argos_help_reflects_current_direction_for_ru_en() -> None:
    window = MainWindow.__new__(MainWindow)
    window.settings = SimpleNamespace(direction=RU_EN)
    captured: dict[str, str] = {}

    def fake_show_dialog(title: str, message: str, *, geometry: str = "860x620") -> None:
        captured["title"] = title
        captured["message"] = message

    window._show_readonly_text_dialog = fake_show_dialog  # type: ignore[method-assign]

    MainWindow.show_argos_installation_help(window)

    assert captured["title"] == "Установка Argos"
    assert "--from-lang ru --to-lang en" in captured["message"]
