from __future__ import annotations

import json
from pathlib import Path

import pytest

from pdf_word_translator.mobile_api import (
    bundled_dictionary_asset_names,
    configure_dictionary_paths,
    current_service_summary,
    lookup_word,
    lookup_word_json,
    reset_mobile_bridge,
)
from pdf_word_translator.models import EN_RU, RU_EN
from pdf_word_translator.utils.dictionary_builder import (
    DictionaryBuildEntry,
    DictionaryMetadata,
    build_dictionary_from_entries,
)


@pytest.fixture(autouse=True)
def _reset_mobile_bridge() -> None:
    reset_mobile_bridge()
    yield
    reset_mobile_bridge()


def _build_test_db(tmp_path: Path, filename: str, *, direction: str, headword: str, translation: str) -> Path:
    entry = DictionaryBuildEntry(
        headword=headword,
        best_translation=translation,
        alternatives=[translation],
        forms=[headword, f"{headword}s"],
        examples=[(f"example {headword}", f"пример {translation}")],
    )
    db_path = tmp_path / filename
    build_dictionary_from_entries(
        [entry],
        db_path,
        metadata=DictionaryMetadata(
            pack_name=filename,
            direction=direction,
            pack_kind="android-test",
            description="temporary test pack",
            source=str(db_path),
        ),
    )
    return db_path


def test_mobile_api_configures_bridge_from_json_payload_and_looks_up_word(tmp_path: Path) -> None:
    en_ru_db = _build_test_db(tmp_path, "en_ru.sqlite", direction=EN_RU, headword="driver", translation="драйвер")
    ru_en_db = _build_test_db(tmp_path, "ru_en.sqlite", direction=RU_EN, headword="драйвер", translation="driver")

    summary = configure_dictionary_paths(json.dumps([str(en_ru_db), str(ru_en_db)], ensure_ascii=False))

    assert summary["ok"] is True
    assert summary["pack_count"] == 2
    assert len(summary["configured_paths"]) == 2

    payload = lookup_word("drivers", direction=EN_RU)

    assert payload["ok"] is True
    assert payload["entry"]["headword"] == "driver"
    assert payload["entry"]["best_translation"] == "драйвер"


def test_mobile_api_current_summary_reuses_configured_paths(tmp_path: Path) -> None:
    en_ru_db = _build_test_db(tmp_path, "en_only.sqlite", direction=EN_RU, headword="window", translation="окно")

    configure_dictionary_paths([str(en_ru_db)])
    summary = current_service_summary()

    assert summary["pack_count"] == 1
    assert summary["entry_count"] == 1
    assert summary["pack_infos"][0]["direction"] == EN_RU


def test_mobile_api_lookup_json_returns_structured_error_on_invalid_direction(tmp_path: Path) -> None:
    en_ru_db = _build_test_db(tmp_path, "en_ru.sqlite", direction=EN_RU, headword="device", translation="устройство")
    configure_dictionary_paths([str(en_ru_db)])

    payload = json.loads(lookup_word_json("device", direction="bad-direction"))

    assert payload["ok"] is False
    assert payload["strategy"] == "error"
    assert "Unsupported translation direction" in payload["error"]


def test_mobile_api_exposes_expected_android_asset_names() -> None:
    assert bundled_dictionary_asset_names() == [
        "starter_dictionary.sqlite",
        "starter_dictionary_ru_en.sqlite",
    ]
