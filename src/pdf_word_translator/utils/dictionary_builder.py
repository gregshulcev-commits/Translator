"""Helpers for building SQLite dictionary packs.

The project stores dictionaries in a compact SQLite schema with metadata,
allowing different packs and language directions to be hot-swapped without
changing the UI or lookup workflow.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Sequence
import csv
import sqlite3

from ..models import EN_RU, RU_EN, TranslationDirection, direction_source_lang, direction_target_lang
from .text_normalizer import WordNormalizer


@dataclass
class DictionaryBuildEntry:
    headword: str
    best_translation: str
    alternatives: list[str] = field(default_factory=list)
    forms: list[str] = field(default_factory=list)
    examples: list[tuple[str, str]] = field(default_factory=list)
    notes: str = ""
    transcription: str = ""


@dataclass
class DictionaryMetadata:
    pack_name: str
    direction: TranslationDirection = EN_RU
    pack_kind: str = "custom"
    description: str = ""
    source: str = ""

    @property
    def source_lang(self) -> str:
        return direction_source_lang(self.direction)

    @property
    def target_lang(self) -> str:
        return direction_target_lang(self.direction)


# Backward-compatible alias used by older code/docs.
DictionaryPackOptions = DictionaryMetadata


SCHEMA_SQL = """
DROP TABLE IF EXISTS metadata;
DROP TABLE IF EXISTS examples;
DROP TABLE IF EXISTS senses;
DROP TABLE IF EXISTS transcriptions;
DROP TABLE IF EXISTS forms;
DROP TABLE IF EXISTS entries;

CREATE TABLE metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    headword TEXT NOT NULL,
    normalized_headword TEXT NOT NULL,
    best_translation TEXT NOT NULL,
    notes TEXT NOT NULL DEFAULT ''
);

CREATE TABLE forms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    form TEXT NOT NULL,
    normalized_form TEXT NOT NULL,
    FOREIGN KEY (entry_id) REFERENCES entries(id)
);

CREATE TABLE transcriptions (
    entry_id INTEGER PRIMARY KEY,
    ipa TEXT NOT NULL,
    FOREIGN KEY (entry_id) REFERENCES entries(id)
);

CREATE TABLE senses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    priority INTEGER NOT NULL,
    translation TEXT NOT NULL,
    FOREIGN KEY (entry_id) REFERENCES entries(id)
);

CREATE TABLE examples (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entry_id INTEGER NOT NULL,
    example_src TEXT NOT NULL,
    example_dst TEXT NOT NULL,
    FOREIGN KEY (entry_id) REFERENCES entries(id)
);

CREATE INDEX idx_forms_normalized_form ON forms(normalized_form);
CREATE INDEX idx_entries_normalized_headword ON entries(normalized_headword);
"""


def default_metadata_for_path(db_path: Path, direction: TranslationDirection = EN_RU, pack_kind: str = "custom") -> DictionaryMetadata:
    title = Path(db_path).stem.replace("_", " ")
    return DictionaryMetadata(pack_name=title, direction=direction, pack_kind=pack_kind)


def ensure_dictionary_database(csv_path: Path, db_path: Path, metadata: DictionaryMetadata | None = None) -> None:
    csv_path = Path(csv_path)
    db_path = Path(db_path)
    if not db_path.exists() or db_path.stat().st_size == 0:
        build_dictionary_from_csv(csv_path, db_path, metadata=metadata)


def build_dictionary_from_csv(csv_path: Path, db_path: Path, metadata: DictionaryMetadata | None = None) -> Path:
    csv_path = Path(csv_path)
    db_path = Path(db_path)
    entries = list(_iter_csv_entries(csv_path))
    if metadata is None:
        metadata = default_metadata_for_path(db_path, direction=EN_RU, pack_kind="csv")
    return build_dictionary_from_entries(entries, db_path, metadata=metadata)


def build_reverse_dictionary_from_csv(csv_path: Path, db_path: Path, metadata: DictionaryMetadata | None = None) -> Path:
    csv_path = Path(csv_path)
    db_path = Path(db_path)
    entries = list(_iter_csv_entries(csv_path))
    reversed_entries = _reverse_entries(entries)
    if metadata is None:
        metadata = default_metadata_for_path(db_path, direction=RU_EN, pack_kind="csv-reverse")
    return build_dictionary_from_entries(reversed_entries, db_path, metadata=metadata)


def build_dictionary_from_entries(
    entries: Sequence[DictionaryBuildEntry] | Iterable[DictionaryBuildEntry],
    db_path: Path,
    *,
    metadata: DictionaryMetadata,
) -> Path:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()
        cursor.executescript(SCHEMA_SQL)
        _insert_metadata(cursor, metadata)
        for entry in entries:
            _insert_entry(cursor, entry, source_lang=metadata.source_lang)
        connection.commit()
    finally:
        connection.close()
    return db_path


def _insert_metadata(cursor: sqlite3.Cursor, metadata: DictionaryMetadata) -> None:
    pairs = {
        "pack_name": metadata.pack_name,
        "source_lang": metadata.source_lang,
        "target_lang": metadata.target_lang,
        "pack_kind": metadata.pack_kind,
        "description": metadata.description,
        "source": metadata.source,
    }
    for key, value in pairs.items():
        cursor.execute("INSERT INTO metadata(key, value) VALUES (?, ?)", (key, value))


def _iter_csv_entries(csv_path: Path) -> Iterator[DictionaryBuildEntry]:
    with csv_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            headword = row["headword"].strip()
            best_translation = row.get("best_translation", "").strip()
            alternatives = [item.strip() for item in row.get("alternatives", "").split("|") if item.strip()]
            forms = [item.strip() for item in row.get("forms", "").split("|") if item.strip()]
            notes = row.get("notes", "").strip()
            transcription = row.get("transcription", "").strip()
            examples: list[tuple[str, str]] = []
            raw_examples = row.get("examples", "")
            if raw_examples:
                for chunk in raw_examples.split("||"):
                    if "=>" not in chunk:
                        continue
                    src, dst = chunk.split("=>", 1)
                    examples.append((src.strip(), dst.strip()))
            yield DictionaryBuildEntry(
                headword=headword,
                best_translation=best_translation,
                alternatives=alternatives,
                forms=forms,
                examples=examples,
                notes=notes,
                transcription=transcription,
            )


def _reverse_entries(entries: Sequence[DictionaryBuildEntry]) -> list[DictionaryBuildEntry]:
    aggregated: dict[str, DictionaryBuildEntry] = {}
    for entry in entries:
        english_forms = [entry.headword, *entry.forms]
        source_candidates = _unique_nonempty([entry.best_translation, *entry.alternatives])
        if not source_candidates:
            continue
        for source_headword in source_candidates:
            key = WordNormalizer.normalize(source_headword, language="ru")
            if not key:
                continue
            reverse_examples = [(dst, src) for src, dst in entry.examples if src and dst]
            if key not in aggregated:
                aggregated[key] = DictionaryBuildEntry(
                    headword=source_headword,
                    best_translation=entry.headword,
                    alternatives=[form for form in english_forms if form != entry.headword],
                    forms=[source_headword],
                    examples=reverse_examples,
                    notes=f"reverse from {entry.headword}" if entry.headword else "",
                    transcription="",
                )
                continue
            current = aggregated[key]
            current.alternatives = _unique_nonempty([*current.alternatives, entry.headword, *english_forms])
            current.forms = _unique_nonempty([*current.forms, source_headword])
            for example in reverse_examples:
                if example not in current.examples:
                    current.examples.append(example)
    return list(aggregated.values())


def _insert_entry(cursor: sqlite3.Cursor, entry: DictionaryBuildEntry, *, source_lang: str) -> None:
    headword = entry.headword.strip()
    normalized_headword = WordNormalizer.normalize(headword, language=source_lang)
    if not normalized_headword:
        return

    unique_senses = _unique_nonempty([entry.best_translation, *entry.alternatives])
    if not unique_senses:
        return
    best_translation = unique_senses[0]

    cursor.execute(
        "INSERT INTO entries(headword, normalized_headword, best_translation, notes) VALUES (?, ?, ?, ?)",
        (headword, normalized_headword, best_translation, entry.notes.strip()),
    )
    entry_id = int(cursor.lastrowid)

    for form in _normalized_forms_for_entry(headword, entry.forms, source_lang=source_lang):
        cursor.execute(
            "INSERT INTO forms(entry_id, form, normalized_form) VALUES (?, ?, ?)",
            (entry_id, form, WordNormalizer.normalize(form, language=source_lang)),
        )

    if entry.transcription.strip():
        cursor.execute(
            "INSERT INTO transcriptions(entry_id, ipa) VALUES (?, ?)",
            (entry_id, entry.transcription.strip()),
        )

    for priority, translation in enumerate(unique_senses, start=1):
        cursor.execute(
            "INSERT INTO senses(entry_id, priority, translation) VALUES (?, ?, ?)",
            (entry_id, priority, translation),
        )

    for src, dst in entry.examples:
        src = src.strip()
        dst = dst.strip()
        if src and dst:
            cursor.execute(
                "INSERT INTO examples(entry_id, example_src, example_dst) VALUES (?, ?, ?)",
                (entry_id, src, dst),
            )


def _normalized_forms_for_entry(headword: str, forms: Iterable[str], *, source_lang: str) -> list[str]:
    values: list[str] = []
    for candidate in [headword, *forms]:
        raw = candidate.strip()
        normalized = WordNormalizer.normalize(raw, language=source_lang)
        if normalized and raw not in values:
            values.append(raw)
    return values


def _unique_nonempty(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        value = item.strip()
        if value and value not in result:
            result.append(value)
    return result
