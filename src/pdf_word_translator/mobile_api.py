"""JSON-friendly dictionary bridge for the Android/mobile client.

The desktop application keeps using the full Tkinter UI, while the Android
branch needs a narrow, UI-free API surface which can be called from Kotlin via
Chaquopy. This module exposes exactly that surface: configure SQLite dictionary
paths, inspect which packs are active, and perform word lookup without pulling
in the desktop viewer layer.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence
import json

from .config import DEFAULT_STARTER_DB, DEFAULT_STARTER_RU_EN_DB
from .models import EN_RU, SUPPORTED_DIRECTIONS, LookupResult, TranslationDirection
from .plugins.dictionary_composite import CompositeDictionaryPlugin
from .plugins.dictionary_sqlite import SQLiteDictionaryPlugin
from .services.dictionary_service import DictionaryService

ANDROID_BUNDLED_DICTIONARY_FILENAMES: tuple[str, ...] = (
    "starter_dictionary.sqlite",
    "starter_dictionary_ru_en.sqlite",
)

_configured_dictionary_paths: tuple[str, ...] = ()
_cached_service: tuple[tuple[str, ...], DictionaryService] | None = None


def bundled_dictionary_asset_names() -> list[str]:
    """Return the asset filenames expected by the Android client bootstrap."""

    return list(ANDROID_BUNDLED_DICTIONARY_FILENAMES)


def bundled_dictionary_asset_names_json() -> str:
    return json.dumps(bundled_dictionary_asset_names(), ensure_ascii=False)


def default_desktop_dictionary_paths() -> list[str]:
    """Return bundled desktop dictionaries when they exist in the local tree."""

    return [
        str(path)
        for path in (DEFAULT_STARTER_DB, DEFAULT_STARTER_RU_EN_DB)
        if Path(path).exists()
    ]


def configure_dictionary_paths(payload: object | None = None) -> dict[str, object]:
    """Persist the active SQLite dictionary paths for later bridge calls."""

    global _configured_dictionary_paths
    resolved = tuple(str(path) for path in _resolve_dictionary_paths(payload))
    _configured_dictionary_paths = resolved
    service = _dictionary_service_for_paths(resolved)
    return _serialize_service_summary(service, resolved)


def configure_dictionary_paths_json(payload: object | None = None) -> str:
    return json.dumps(configure_dictionary_paths(payload), ensure_ascii=False)


def current_service_summary() -> dict[str, object]:
    """Return metadata about the currently configured bridge dictionaries."""

    paths = tuple(str(path) for path in _resolve_dictionary_paths(None))
    service = _dictionary_service_for_paths(paths)
    return _serialize_service_summary(service, paths)


def current_service_summary_json() -> str:
    return json.dumps(current_service_summary(), ensure_ascii=False)


def pack_infos() -> list[dict[str, object]]:
    service = _dictionary_service_for_paths(tuple(str(path) for path in _resolve_dictionary_paths(None)))
    return _serialize_pack_infos(service)


def pack_infos_json() -> str:
    return json.dumps(pack_infos(), ensure_ascii=False)


def lookup_word(word: str, direction: TranslationDirection = EN_RU) -> dict[str, object]:
    """Look up a word in the configured mobile dictionary service."""

    direction = _normalize_direction(direction)
    service = _dictionary_service_for_paths(tuple(str(path) for path in _resolve_dictionary_paths(None)))
    result = service.lookup(word, direction=direction)
    return _serialize_lookup_result(word, direction, result)


def lookup_word_json(word: str, direction: TranslationDirection = EN_RU) -> str:
    try:
        payload = lookup_word(word, direction=direction)
    except Exception as exc:  # pragma: no cover - defensive bridge for Android runtime
        payload = {
            "ok": False,
            "query": word,
            "direction": direction,
            "error": str(exc),
            "entry": None,
            "candidate_forms": [],
            "strategy": "error",
        }
    return json.dumps(payload, ensure_ascii=False)


def reset_mobile_bridge() -> None:
    """Drop cached SQLite connections, for tests or Android app shutdown."""

    global _cached_service, _configured_dictionary_paths
    if _cached_service is not None:
        _cached_service[1].replace_plugin(CompositeDictionaryPlugin([]))
        _cached_service = None
    _configured_dictionary_paths = ()


def _normalize_direction(direction: TranslationDirection) -> TranslationDirection:
    if direction not in SUPPORTED_DIRECTIONS:
        raise ValueError(f"Unsupported translation direction: {direction}")
    return direction


def _dictionary_service_for_paths(raw_paths: Sequence[str]) -> DictionaryService:
    global _cached_service
    if _cached_service is not None and _cached_service[0] == tuple(raw_paths):
        return _cached_service[1]

    if _cached_service is not None:
        _cached_service[1].replace_plugin(CompositeDictionaryPlugin([]))

    plugins = [SQLiteDictionaryPlugin(Path(path)) for path in raw_paths]
    if not plugins:
        raise ValueError("No SQLite dictionaries configured for mobile bridge.")

    service = DictionaryService(CompositeDictionaryPlugin(plugins))
    _cached_service = (tuple(raw_paths), service)
    return service


def _resolve_dictionary_paths(payload: object | None) -> tuple[Path, ...]:
    if payload is None:
        candidate_paths = _configured_dictionary_paths or tuple(default_desktop_dictionary_paths())
        if not candidate_paths:
            raise ValueError(
                "No dictionary paths configured. Call configure_dictionary_paths(...) first, "
                "or provide bundled desktop dictionaries."
            )
        return _deduplicate_existing_paths(candidate_paths)

    if isinstance(payload, Path):
        return _deduplicate_existing_paths((str(payload),))

    if isinstance(payload, str):
        text = payload.strip()
        if not text:
            return _resolve_dictionary_paths(None)
        if text.startswith("["):
            try:
                parsed = json.loads(text)
            except json.JSONDecodeError:
                return _deduplicate_existing_paths((text,))
            return _resolve_dictionary_paths(parsed)
        return _deduplicate_existing_paths((text,))

    if isinstance(payload, Iterable):
        return _deduplicate_existing_paths(str(item) for item in payload)

    raise ValueError(f"Unsupported dictionary path payload: {type(payload)!r}")


def _deduplicate_existing_paths(paths: Iterable[str]) -> tuple[Path, ...]:
    resolved: list[Path] = []
    seen: set[str] = set()
    missing: list[str] = []
    invalid: list[str] = []
    for raw_path in paths:
        path = Path(raw_path).expanduser().resolve()
        key = str(path)
        if key in seen:
            continue
        seen.add(key)
        if not path.exists():
            missing.append(key)
            continue
        if not path.is_file():
            invalid.append(key)
            continue
        resolved.append(path)
    if missing:
        raise ValueError(f"Dictionary file(s) not found: {', '.join(missing)}")
    if invalid:
        raise ValueError(f"Dictionary path(s) must point to regular files: {', '.join(invalid)}")
    if not resolved:
        raise ValueError("No existing SQLite dictionaries found for mobile bridge.")
    return tuple(resolved)


def _serialize_pack_infos(service: DictionaryService) -> list[dict[str, object]]:
    return [
        {
            "pack_id": info.pack_id,
            "title": info.title,
            "direction": info.direction,
            "category": info.category,
            "description": info.description,
            "source": info.source,
        }
        for info in service.pack_infos()
    ]


def _serialize_service_summary(service: DictionaryService, paths: Sequence[str]) -> dict[str, object]:
    return {
        "ok": True,
        "configured_paths": list(paths),
        "entry_count": service.entry_count(),
        "pack_count": service.pack_count(),
        "pack_infos": _serialize_pack_infos(service),
        "bundled_asset_names": bundled_dictionary_asset_names(),
    }


def _serialize_lookup_result(
    query: str,
    direction: TranslationDirection,
    result: LookupResult,
) -> dict[str, object]:
    entry = result.entry
    payload: dict[str, object] = {
        "ok": result.found,
        "query": query,
        "direction": direction,
        "normalized_query": result.normalized_query,
        "resolved_headword": result.resolved_headword,
        "strategy": result.strategy,
        "candidate_forms": list(result.candidate_forms),
        "entry": None,
        "error": "",
    }
    if entry is None:
        return payload
    payload["entry"] = {
        "headword": entry.headword,
        "normalized_headword": entry.normalized_headword,
        "transcription": entry.transcription,
        "best_translation": entry.best_translation,
        "alternative_translations": list(entry.alternative_translations),
        "examples": [
            {"source": source, "target": target}
            for source, target in entry.examples
        ],
        "notes": entry.notes,
    }
    return payload
