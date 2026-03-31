"""Import FreeDict TEI dictionaries into the SQLite runtime schema.

The importer is intentionally lightweight: it supports the subset of TEI used by
FreeDict bilingual dictionaries and keeps install-time dependencies limited to
Python's standard library.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
import logging
import tempfile
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET

from .dictionary_builder import DictionaryBuildEntry, build_dictionary_from_entries
from .text_normalizer import EnglishWordNormalizer


LOGGER = logging.getLogger(__name__)

DEFAULT_FREEDICT_ENG_RUS_URLS = (
    # Current generated source published by FreeDict.
    "https://download.freedict.org/generated/eng-rus/eng-rus.tei",
    # Debian source mirror fallback used when the generated endpoint is unavailable.
    "https://sources.debian.org/data/main/f/freedict/2022.04.21-1/eng-rus/eng-rus.tei",
)


@dataclass(frozen=True)
class DownloadResult:
    path: Path
    source_url: str


def download_freedict_tei(destination: Path, urls: Iterable[str] = DEFAULT_FREEDICT_ENG_RUS_URLS) -> DownloadResult:
    """Download a FreeDict TEI file using the first reachable URL."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    last_error: Exception | None = None
    for url in urls:
        try:
            LOGGER.info("Downloading dictionary source: %s", url)
            with urllib.request.urlopen(url, timeout=60) as response, destination.open("wb") as handle:
                handle.write(response.read())
            return DownloadResult(path=destination, source_url=url)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            LOGGER.warning("Failed to download %s: %s", url, exc)
            last_error = exc

    raise RuntimeError(f"Не удалось скачать FreeDict TEI. Последняя ошибка: {last_error}")


def build_dictionary_from_freedict_tei(tei_path: Path, db_path: Path) -> Path:
    """Convert a FreeDict TEI file into the MVP SQLite schema."""
    entries = _aggregate_freedict_entries(Path(tei_path))
    return build_dictionary_from_entries(entries.values(), db_path)


def install_default_freedict_dictionary(runtime_dictionary_dir: Path, download_dir: Path) -> Path:
    """Download and build the default general EN-RU dictionary pack."""
    runtime_dictionary_dir = Path(runtime_dictionary_dir)
    download_dir = Path(download_dir)
    runtime_dictionary_dir.mkdir(parents=True, exist_ok=True)
    download_dir.mkdir(parents=True, exist_ok=True)

    tei_path = download_dir / "freedict-eng-rus.tei"
    db_path = runtime_dictionary_dir / "freedict_en_ru.sqlite"

    result = download_freedict_tei(tei_path)
    LOGGER.info("Building SQLite dictionary from %s", result.source_url)
    return build_dictionary_from_freedict_tei(result.path, db_path)


def _aggregate_freedict_entries(tei_path: Path) -> dict[str, DictionaryBuildEntry]:
    """Merge FreeDict TEI entries by normalized headword.

    FreeDict often contains multiple TEI <entry> blocks for the same word.
    Grouping them keeps lookup deterministic and combines translations.
    """
    aggregated: dict[str, DictionaryBuildEntry] = {}

    context = ET.iterparse(tei_path, events=("end",))
    for _, elem in context:
        if _strip_ns(elem.tag) != "entry":
            continue

        parsed = _parse_entry(elem)
        elem.clear()
        if parsed is None:
            continue

        key = EnglishWordNormalizer.normalize(parsed.headword)
        if key not in aggregated:
            aggregated[key] = parsed
            continue

        current = aggregated[key]
        merged_alternatives = _merge_unique([current.best_translation, *current.alternatives, parsed.best_translation, *parsed.alternatives])
        merged_examples = list(current.examples)
        for example in parsed.examples:
            if example not in merged_examples:
                merged_examples.append(example)
        merged_forms = _merge_unique([*current.forms, *parsed.forms])
        merged_notes = _merge_unique([current.notes, parsed.notes])
        transcription = current.transcription or parsed.transcription

        aggregated[key] = DictionaryBuildEntry(
            headword=current.headword,
            best_translation=merged_alternatives[0],
            alternatives=merged_alternatives[1:],
            forms=merged_forms,
            examples=merged_examples,
            notes=" | ".join(item for item in merged_notes if item),
            transcription=transcription,
        )

    return aggregated


def _parse_entry(entry_elem: ET.Element) -> DictionaryBuildEntry | None:
    orths = [_clean_text(node.text) for node in entry_elem.findall(".//{*}form/{*}orth") if _clean_text(node.text)]
    if not orths:
        return None
    headword = orths[0]

    translations: list[str] = []
    notes: list[str] = []
    examples: list[tuple[str, str]] = []

    for sense in entry_elem.findall("./{*}sense"):
        for cit in sense.findall("./{*}cit"):
            cit_type = (cit.attrib.get("type") or "").lower()
            quote_texts = [_clean_text(quote.text) for quote in cit.findall("./{*}quote") if _clean_text(quote.text)]
            if cit_type == "trans":
                translations.extend(quote_texts)
            elif cit_type in {"example", "eg", "ex"} and quote_texts:
                example_src = quote_texts[0]
                example_dst = ""
                for nested in cit.findall("./{*}cit"):
                    nested_type = (nested.attrib.get("type") or "").lower()
                    if nested_type == "trans":
                        nested_quotes = [_clean_text(quote.text) for quote in nested.findall("./{*}quote") if _clean_text(quote.text)]
                        if nested_quotes:
                            example_dst = nested_quotes[0]
                            break
                if example_src and example_dst:
                    examples.append((example_src, example_dst))
        for note in sense.findall("./{*}note"):
            note_text = _clean_text(note.text)
            if note_text:
                notes.append(note_text)

    if not translations:
        return None

    pronunciations = [_clean_text(node.text) for node in entry_elem.findall(".//{*}form/{*}pron") if _clean_text(node.text)]

    merged_translations = _merge_unique(translations)
    return DictionaryBuildEntry(
        headword=headword,
        best_translation=merged_translations[0],
        alternatives=merged_translations[1:],
        forms=orths,
        examples=examples,
        notes=" | ".join(_merge_unique(notes)),
        transcription=pronunciations[0] if pronunciations else "",
    )


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1]


def _clean_text(value: str | None) -> str:
    return " ".join((value or "").split()).strip()


def _merge_unique(values: Iterable[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        cleaned = value.strip()
        if cleaned and cleaned not in result:
            result.append(cleaned)
    return result
