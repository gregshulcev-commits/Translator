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
import urllib.error
import urllib.parse
import urllib.request
from defusedxml import ElementTree as ET

from ..models import EN_RU, RU_EN, TranslationDirection
from .dictionary_builder import DictionaryBuildEntry, DictionaryMetadata, build_dictionary_from_entries
from .text_normalizer import WordNormalizer


LOGGER = logging.getLogger(__name__)

DEFAULT_FREEDICT_ENG_RUS_URLS = (
    "https://download.freedict.org/generated/eng-rus/eng-rus.tei",
    "https://sources.debian.org/data/main/f/freedict/2022.04.21-1/eng-rus/eng-rus.tei",
)
DEFAULT_FREEDICT_RUS_ENG_URLS = (
    "https://download.freedict.org/generated/rus-eng/rus-eng.tei",
    "https://sources.debian.org/data/main/f/freedict/2022.04.21-1/rus-eng/rus-eng.tei",
)


MAX_FREEDICT_DOWNLOAD_BYTES = 128 * 1024 * 1024


@dataclass(frozen=True)
class DownloadResult:
    path: Path
    source_url: str


def default_urls_for_pair(source_lang: str, target_lang: str) -> tuple[str, ...]:
    if source_lang == "ru" and target_lang == "en":
        return DEFAULT_FREEDICT_RUS_ENG_URLS
    return DEFAULT_FREEDICT_ENG_RUS_URLS


def urls_for_direction(direction: TranslationDirection) -> tuple[str, ...]:
    if direction == RU_EN:
        return DEFAULT_FREEDICT_RUS_ENG_URLS
    return DEFAULT_FREEDICT_ENG_RUS_URLS


def download_freedict_tei(destination: Path, urls: Iterable[str]) -> DownloadResult:
    """Download a FreeDict TEI file using the first reachable URL."""
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)

    last_error: Exception | None = None
    for url in urls:
        try:
            _validate_download_url(url)
            LOGGER.info("Downloading dictionary source: %s", url)
            tmp_path = destination.parent / f".{destination.name}.tmp"
            bytes_written = 0
            with urllib.request.urlopen(url, timeout=60) as response, tmp_path.open("wb") as handle:  # nosec B310
                while True:
                    chunk = response.read(1024 * 1024)
                    if not chunk:
                        break
                    bytes_written += len(chunk)
                    if bytes_written > MAX_FREEDICT_DOWNLOAD_BYTES:
                        raise RuntimeError(
                            f"FreeDict source is too large ({bytes_written} bytes). "
                            f"Limit: {MAX_FREEDICT_DOWNLOAD_BYTES} bytes."
                        )
                    handle.write(chunk)
            tmp_path.replace(destination)
            return DownloadResult(path=destination, source_url=url)
        except (RuntimeError, urllib.error.URLError, TimeoutError, OSError) as exc:
            LOGGER.warning("Failed to download %s: %s", url, exc)
            last_error = exc
            tmp_path = destination.parent / f".{destination.name}.tmp"
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)

    raise RuntimeError(f"Не удалось скачать FreeDict TEI. Последняя ошибка: {last_error}")




def _validate_download_url(url: str) -> None:
    parsed = urllib.parse.urlsplit(str(url or "").strip())
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        raise RuntimeError(f"Unsupported FreeDict download URL: {url}")


def build_dictionary_from_freedict_tei(
    tei_path: Path,
    db_path: Path,
    *,
    direction: TranslationDirection = EN_RU,
    metadata: DictionaryMetadata | None = None,
) -> Path:
    """Convert a FreeDict TEI file into the runtime SQLite schema."""
    entries = _aggregate_freedict_entries(Path(tei_path), direction=direction)
    if metadata is None:
        metadata = DictionaryMetadata(
            pack_name=Path(db_path).stem.replace("_", " "),
            direction=direction,
            pack_kind="freedict",
            source=str(tei_path),
        )
    return build_dictionary_from_entries(entries.values(), db_path, metadata=metadata)


def install_default_freedict_dictionary(
    runtime_dictionary_dir: Path,
    download_dir: Path,
    *,
    direction: TranslationDirection = EN_RU,
    metadata: DictionaryMetadata | None = None,
) -> Path:
    """Download and build the default FreeDict pack for the requested direction."""
    runtime_dictionary_dir = Path(runtime_dictionary_dir)
    download_dir = Path(download_dir)
    runtime_dictionary_dir.mkdir(parents=True, exist_ok=True)
    download_dir.mkdir(parents=True, exist_ok=True)

    suffix = "en_ru" if direction == EN_RU else "ru_en"
    tei_path = download_dir / f"freedict-{suffix}.tei"
    db_path = runtime_dictionary_dir / f"freedict_{suffix}.sqlite"

    result = download_freedict_tei(tei_path, urls_for_direction(direction))
    LOGGER.info("Building SQLite dictionary from %s", result.source_url)
    if metadata is None:
        metadata = DictionaryMetadata(
            pack_name="FreeDict EN→RU" if direction == EN_RU else "FreeDict RU→EN",
            direction=direction,
            pack_kind="general",
            description="FreeDict TEI import",
            source=result.source_url,
        )
    return build_dictionary_from_freedict_tei(result.path, db_path, direction=direction, metadata=metadata)


def _aggregate_freedict_entries(tei_path: Path, *, direction: TranslationDirection) -> dict[str, DictionaryBuildEntry]:
    """Merge FreeDict TEI entries by normalized headword."""
    source_lang = "ru" if direction == RU_EN else "en"
    aggregated: dict[str, DictionaryBuildEntry] = {}

    context = ET.iterparse(tei_path, events=("end",))
    for _, elem in context:
        if _strip_ns(elem.tag) != "entry":
            continue

        parsed = _parse_entry(elem)
        elem.clear()
        if parsed is None:
            continue

        key = WordNormalizer.normalize(parsed.headword, language=source_lang)
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
