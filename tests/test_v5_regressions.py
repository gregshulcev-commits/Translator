import json
import queue
from pathlib import Path
from types import SimpleNamespace

from pdf_word_translator.models import ContextTranslationResult, EN_RU
from pdf_word_translator.providers.context_providers import YandexCloudContextProvider
from pdf_word_translator.ui.main_window import MainWindow
from pdf_word_translator.utils.settings_store import SettingsStore


class _DummyVar:
    def __init__(self, value: str = "") -> None:
        self.value = value

    def set(self, value: str) -> None:
        self.value = value

    def get(self) -> str:
        return self.value


class _ImmediateContextService:
    def __init__(self, result: ContextTranslationResult, provider_id: str = "argos") -> None:
        self._result = result
        self._provider_id = provider_id
        self._request_counter = 0

    def active_provider_id(self) -> str:
        return self._provider_id

    def provider_name(self) -> str:
        return "Argos (офлайн)"

    def next_request_id(self) -> int:
        self._request_counter += 1
        return self._request_counter

    def translate_async(self, text, direction, callback, request_id=None):
        callback(request_id, self._result)
        return request_id


def test_redraw_overlays_does_not_force_scroll() -> None:
    window = MainWindow.__new__(MainWindow)
    window.current_highlight_token = object()
    window.current_search_hits = [object()]
    window.current_search_index = 0

    calls: list[tuple[str, bool]] = []

    def draw_word(_token, *, scroll_into_view: bool = True) -> None:
        calls.append(("word", scroll_into_view))

    def draw_search(_hit, *, scroll_into_view: bool = True) -> None:
        calls.append(("search", scroll_into_view))

    window._draw_word_highlight = draw_word  # type: ignore[method-assign]
    window._draw_search_highlight = draw_search  # type: ignore[method-assign]

    MainWindow._redraw_overlays(window)

    assert calls == [("word", False), ("search", False)]


def test_start_context_translation_applies_immediate_results_via_queue() -> None:
    translated = ContextTranslationResult(
        provider_id="argos",
        provider_name="Argos (офлайн)",
        status="ok",
        text="переведённый контекст",
    )
    window = MainWindow.__new__(MainWindow)
    window.context_service = _ImmediateContextService(translated)
    window.settings = SimpleNamespace(direction=EN_RU)
    window.example_var = _DummyVar()
    window._context_result_queue = queue.Queue()
    window._active_context_request_id = 0

    view_model = SimpleNamespace(context=SimpleNamespace(text="Driver configuration is available."))

    MainWindow._start_context_translation(window, view_model)
    MainWindow._drain_context_result_queue(window)

    assert window._active_context_request_id == 1
    assert window.example_var.get() == "переведённый контекст"


def test_settings_store_load_ignores_unknown_keys_and_invalid_values(tmp_path: Path) -> None:
    settings_file = tmp_path / "settings.json"
    settings_file.write_text(
        json.dumps(
            {
                "ui_font_size": "not-a-number",
                "direction": "unsupported",
                "context_provider_id": "ARGOS",
                "extra": "ignored",
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    loaded = SettingsStore(settings_file).load()

    assert loaded.ui_font_size == 11
    assert loaded.direction == EN_RU
    assert loaded.context_provider_id == "argos"


def test_yandex_provider_requires_folder_id_before_network_call() -> None:
    provider = YandexCloudContextProvider(api_key="secret", folder_id="")

    result = provider.translate_text("hello", EN_RU)

    assert not result.ok
    assert "Folder ID" in result.text


def test_treeview_rowheight_scales_with_font_linespace() -> None:
    assert MainWindow._treeview_rowheight(18) == 28
    assert MainWindow._treeview_rowheight(40) == 50
