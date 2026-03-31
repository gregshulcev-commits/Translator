"""Build the starter SQLite dictionary from a CSV source file."""
from __future__ import annotations

from pathlib import Path
import csv
import logging
import sqlite3

import pronouncing

from .text_normalizer import EnglishWordNormalizer


LOGGER = logging.getLogger(__name__)


ARPABET_TO_IPA = {
    "AA": "ɑ", "AE": "æ", "AH": "ʌ", "AO": "ɔ", "AW": "aʊ", "AY": "aɪ",
    "B": "b", "CH": "tʃ", "D": "d", "DH": "ð", "EH": "e", "ER": "ɝ",
    "EY": "eɪ", "F": "f", "G": "g", "HH": "h", "IH": "ɪ", "IY": "i",
    "JH": "dʒ", "K": "k", "L": "l", "M": "m", "N": "n", "NG": "ŋ",
    "OW": "oʊ", "OY": "ɔɪ", "P": "p", "R": "r", "S": "s", "SH": "ʃ",
    "T": "t", "TH": "θ", "UH": "ʊ", "UW": "u", "V": "v", "W": "w",
    "Y": "j", "Z": "z", "ZH": "ʒ",
}


def arpabet_to_ipa(phones: str) -> str:
    parts = []
    for phone in phones.split():
        base = ''.join(ch for ch in phone if not ch.isdigit())
        parts.append(ARPABET_TO_IPA.get(base, base.lower()))
    return ''.join(parts)


def generate_transcription(headword: str) -> str:
    pronunciations = pronouncing.phones_for_word(headword.lower())
    if not pronunciations:
        return ""
    return f"/{arpabet_to_ipa(pronunciations[0])}/"


def ensure_dictionary_database(csv_path: Path, db_path: Path) -> Path:
    """Build the SQLite file when missing or stale."""
    if db_path.exists() and db_path.stat().st_mtime >= csv_path.stat().st_mtime:
        return db_path
    build_dictionary_from_csv(csv_path, db_path)
    return db_path


def build_dictionary_from_csv(csv_path: Path, db_path: Path) -> Path:
    LOGGER.info("Building starter dictionary: %s -> %s", csv_path, db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    try:
        cursor = connection.cursor()
        cursor.executescript(
            """
            DROP TABLE IF EXISTS entries;
            DROP TABLE IF EXISTS forms;
            DROP TABLE IF EXISTS transcriptions;
            DROP TABLE IF EXISTS senses;
            DROP TABLE IF EXISTS examples;

            CREATE TABLE entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                headword TEXT NOT NULL,
                normalized_headword TEXT NOT NULL,
                best_translation TEXT NOT NULL,
                notes TEXT DEFAULT ''
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
        )

        with csv_path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                headword = row["headword"].strip()
                normalized_headword = EnglishWordNormalizer.normalize(headword)
                best_translation = row["best_translation"].strip()
                notes = row.get("notes", "").strip()
                cursor.execute(
                    "INSERT INTO entries(headword, normalized_headword, best_translation, notes) VALUES (?, ?, ?, ?)",
                    (headword, normalized_headword, best_translation, notes),
                )
                entry_id = int(cursor.lastrowid)

                forms = {normalized_headword}
                raw_forms = row.get("forms", "")
                if raw_forms:
                    for form in raw_forms.split("|"):
                        normalized_form = EnglishWordNormalizer.normalize(form)
                        if normalized_form:
                            forms.add(normalized_form)
                for normalized_form in sorted(forms):
                    cursor.execute(
                        "INSERT INTO forms(entry_id, form, normalized_form) VALUES (?, ?, ?)",
                        (entry_id, normalized_form, normalized_form),
                    )

                ipa = row.get("transcription", "").strip() or generate_transcription(headword)
                if ipa:
                    cursor.execute(
                        "INSERT INTO transcriptions(entry_id, ipa) VALUES (?, ?)",
                        (entry_id, ipa),
                    )

                senses = [best_translation]
                raw_alternatives = row.get("alternatives", "")
                if raw_alternatives:
                    senses.extend([item.strip() for item in raw_alternatives.split("|") if item.strip()])
                for priority, translation in enumerate(dict.fromkeys(senses).keys(), start=1):
                    cursor.execute(
                        "INSERT INTO senses(entry_id, priority, translation) VALUES (?, ?, ?)",
                        (entry_id, priority, translation),
                    )

                raw_examples = row.get("examples", "")
                if raw_examples:
                    for chunk in raw_examples.split("||"):
                        if "=>" not in chunk:
                            continue
                        src, dst = chunk.split("=>", 1)
                        cursor.execute(
                            "INSERT INTO examples(entry_id, example_src, example_dst) VALUES (?, ?, ?)",
                            (entry_id, src.strip(), dst.strip()),
                        )

        connection.commit()
    finally:
        connection.close()
    return db_path
