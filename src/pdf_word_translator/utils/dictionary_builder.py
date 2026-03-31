"""Helpers for building SQLite dictionary packs.

The MVP keeps dictionary data in a small SQLite schema so multiple sources can
be merged without touching the UI or lookup workflow.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Sequence
import csv
import sqlite3

from .text_normalizer import EnglishWordNormalizer


@dataclass
class DictionaryBuildEntry:
    """Dictionary entry used by CSV and FreeDict importers before SQLite export."""

    headword: str
    best_translation: str
    alternatives: list[str] = field(default_factory=list)
    forms: list[str] = field(default_factory=list)
    examples: list[tuple[str, str]] = field(default_factory=list)
    notes: str = ""
    transcription: str = ""


SCHEMA_SQL = """
DROP TABLE IF EXISTS examples;
DROP TABLE IF EXISTS senses;
DROP TABLE IF EXISTS transcriptions;
DROP TABLE IF EXISTS forms;
DROP TABLE IF EXISTS entries;

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


def ensure_dictionary_database(csv_path: Path, db_path: Path) -> None:
    """Build the bundled SQLite dictionary if it does not exist yet."""
    csv_path = Path(csv_path)
    db_path = Path(db_path)
    if not db_path.exists() or db_path.stat().st_size == 0:
        build_dictionary_from_csv(csv_path, db_path)


def build_dictionary_from_csv(csv_path: Path, db_path: Path) -> Path:
    """Convert a CSV glossary into the runtime SQLite schema."""
    csv_path = Path(csv_path)
    db_path = Path(db_path)
    entries = list(_iter_csv_entries(csv_path))
    return build_dictionary_from_entries(entries, db_path)


def build_dictionary_from_entries(entries: Sequence[DictionaryBuildEntry] | Iterable[DictionaryBuildEntry], db_path: Path) -> Path:
    """Persist a sequence of normalized dictionary entries into SQLite."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()
        cursor.executescript(SCHEMA_SQL)

        for entry in entries:
            _insert_entry(cursor, entry)

        connection.commit()
    finally:
        connection.close()
    return db_path


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


def _insert_entry(cursor: sqlite3.Cursor, entry: DictionaryBuildEntry) -> None:
    headword = entry.headword.strip()
    normalized_headword = EnglishWordNormalizer.normalize(headword)
    if not normalized_headword:
        return

    best_translation = entry.best_translation.strip()
    unique_senses = _unique_nonempty([best_translation, *entry.alternatives])
    if not unique_senses:
        return
    best_translation = unique_senses[0]

    cursor.execute(
        "INSERT INTO entries(headword, normalized_headword, best_translation, notes) VALUES (?, ?, ?, ?)",
        (headword, normalized_headword, best_translation, entry.notes.strip()),
    )
    entry_id = int(cursor.lastrowid)

    for form in _normalized_forms_for_entry(headword, entry.forms):
        cursor.execute(
            "INSERT INTO forms(entry_id, form, normalized_form) VALUES (?, ?, ?)",
            (entry_id, form, EnglishWordNormalizer.normalize(form)),
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


def _normalized_forms_for_entry(headword: str, forms: Iterable[str]) -> list[str]:
    values: list[str] = []
    for candidate in [headword, *forms]:
        raw = candidate.strip()
        normalized = EnglishWordNormalizer.normalize(raw)
        if normalized and normalized not in values:
            values.append(normalized)
    return values


def _unique_nonempty(items: Iterable[str]) -> list[str]:
    result: list[str] = []
    for item in items:
        value = item.strip()
        if value and value not in result:
            result.append(value)
    return result
