from __future__ import annotations

import io
import json
import urllib.error

import pytest

from pdf_word_translator.models import EN_RU
from pdf_word_translator.providers.context_providers import (
    ContextTranslationService,
    LibreTranslateContextProvider,
    libretranslate_configuration_diagnostic,
    libretranslate_translate_url,
    normalize_libretranslate_url,
)
from pdf_word_translator.ui.main_window import MainWindow
from pdf_word_translator.utils.settings_store import UiSettings


class _FakeResponse:
    def __init__(self, payload: dict[str, object]):
        self._payload = payload

    def read(self) -> bytes:
        return json.dumps(self._payload, ensure_ascii=False).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


def _http_error(url: str, code: int, body: str) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(url, code, "error", hdrs=None, fp=io.BytesIO(body.encode("utf-8")))


def test_normalize_libretranslate_url_accepts_full_endpoint_and_missing_scheme() -> None:
    assert normalize_libretranslate_url("localhost:5000/translate") == "http://localhost:5000"
    assert normalize_libretranslate_url("http://127.0.0.1:5000/api/translate") == "http://127.0.0.1:5000/api"
    assert libretranslate_translate_url("http://127.0.0.1:5000/api/translate") == "http://127.0.0.1:5000/api/translate"


def test_libretranslate_configuration_diagnostic_requires_api_key_for_public_host() -> None:
    diagnostic = libretranslate_configuration_diagnostic("https://libretranslate.com", "")

    assert diagnostic.state == "error"
    assert "API key" in diagnostic.message


def test_context_service_uses_libretranslate_configuration_diagnostic() -> None:
    service = ContextTranslationService(
        UiSettings(
            direction=EN_RU,
            context_provider_id="libretranslate",
            libretranslate_url="https://libretranslate.com",
            libretranslate_api_key="",
        )
    )

    diagnostic = service.provider_status(EN_RU)

    assert diagnostic.state == "error"
    assert "API key" in diagnostic.message


def test_libretranslate_provider_uses_normalized_endpoint_once(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def fake_urlopen(request, timeout=0):
        calls.append(request.full_url)
        return _FakeResponse({"translatedText": "Привет"})

    monkeypatch.setattr("pdf_word_translator.providers.context_providers.urllib.request.urlopen", fake_urlopen)
    provider = LibreTranslateContextProvider("http://localhost:5000/translate")

    result = provider.translate_text("Hello", EN_RU)

    assert result.ok
    assert calls == ["http://localhost:5000/translate"]


def test_libretranslate_provider_falls_back_to_form_encoded_request(monkeypatch: pytest.MonkeyPatch) -> None:
    content_types: list[str] = []

    def fake_urlopen(request, timeout=0):
        content_type = request.headers.get("Content-type", "")
        content_types.append(content_type)
        if content_type == "application/json":
            raise _http_error(request.full_url, 415, '{"error":"Unsupported Content-Type"}')
        assert request.data is not None
        assert b"q=Hello" in request.data
        return _FakeResponse({"translatedText": "Привет"})

    monkeypatch.setattr("pdf_word_translator.providers.context_providers.urllib.request.urlopen", fake_urlopen)
    provider = LibreTranslateContextProvider("http://localhost:5000")

    result = provider.translate_text("Hello", EN_RU)

    assert result.ok
    assert content_types == ["application/json", "application/x-www-form-urlencoded"]


def test_libretranslate_provider_surfaces_json_error_message(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout=0):
        raise _http_error(request.full_url, 403, '{"error":"API key required"}')

    monkeypatch.setattr("pdf_word_translator.providers.context_providers.urllib.request.urlopen", fake_urlopen)
    provider = LibreTranslateContextProvider("http://localhost:5000")

    result = provider.translate_text("Hello", EN_RU)

    assert not result.ok
    assert "API key required" in result.text


def test_responsive_wraplength_has_floor() -> None:
    assert MainWindow._responsive_wraplength(140, padding=40, minimum=220) == 220
    assert MainWindow._responsive_wraplength(640, padding=40, minimum=220) == 600


def test_responsive_tree_widths_scale_columns() -> None:
    widths = MainWindow._responsive_tree_widths(
        1000,
        minimums=(120, 140, 160),
        weights=(1, 2, 3),
        reserve=40,
    )

    assert len(widths) == 3
    assert sum(widths) == 960
    assert widths[0] >= 120
    assert widths[1] >= 140
    assert widths[2] >= 160
    assert widths[2] > widths[1] > widths[0]


def test_popup_anchor_position_aligns_to_menu_button_right_edge() -> None:
    x, y = MainWindow._popup_anchor_position(
        root_left=100,
        anchor_left=640,
        anchor_top=48,
        anchor_width=40,
        anchor_height=28,
        popup_width=220,
    )

    assert x == 460
    assert y == 82


def test_popup_anchor_position_respects_root_margin() -> None:
    x, y = MainWindow._popup_anchor_position(
        root_left=100,
        anchor_left=140,
        anchor_top=48,
        anchor_width=30,
        anchor_height=28,
        popup_width=220,
    )

    assert x == 108
    assert y == 82
