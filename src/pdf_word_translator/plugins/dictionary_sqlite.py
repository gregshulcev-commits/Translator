"""SQLite-backed dictionary plugin.

The runtime database is intentionally small and transparent. A future importer
can replace the starter dictionary with richer datasets without changing the UI
or the document provider.
"""
from __future__ import annotations

from pathlib import Path
import logging
import sqlite3

from ..models import DictionaryEntry, DictionaryPackInfo, EN_RU, LookupResult, TranslationDirection
from ..plugin_api import DictionaryPlugin
from ..utils.text_normalizer import WordNormalizer


LOGGER = logging.getLogger(__name__)


class SQLiteDictionaryPlugin(DictionaryPlugin):
    def __init__(self, db_path: Path):
        self._db_path = Path(db_path)
        self._connection = sqlite3.connect(self._db_path)
        self._connection.row_factory = sqlite3.Row
        LOGGER.info("SQLite dictionary connected: %s", self._db_path)
        metadata = self._load_metadata()
        self._pack_name = metadata.get("pack_name", self._db_path.stem.replace("_", " "))
        self._source_lang = metadata.get("source_lang", "en")
        self._target_lang = metadata.get("target_lang", "ru")
        self._pack_kind = metadata.get("pack_kind", "general")
        self._description = metadata.get("description", "")
        self._source = metadata.get("source", str(self._db_path))
        self._direction = f"{self._source_lang}-{self._target_lang}"

    def plugin_id(self) -> str:
        return f"dictionary.sqlite.{self._db_path.stem}"

    def pack_info(self) -> DictionaryPackInfo:
        return DictionaryPackInfo(
            pack_id=self._db_path.stem,
            title=self._pack_name,
            direction=self._direction,
            category=self._pack_kind,
            description=self._description,
            source=self._source,
        )

    def supports(self, direction: TranslationDirection) -> bool:
        return direction == self._direction

    def lookup(self, word: str, direction: TranslationDirection = EN_RU) -> LookupResult:
        normalized_query = WordNormalizer.normalize(word, language=self._source_lang)
        if direction != self._direction:
            return LookupResult(query=word, normalized_query=normalized_query, entry=None, strategy="unsupported_direction")
        candidate_forms = WordNormalizer.candidate_forms(word, language=self._source_lang)
        if not candidate_forms:
            return LookupResult(query=word, normalized_query=normalized_query, entry=None, strategy="empty")

        for candidate in candidate_forms:
            exact = self._lookup_exact_form(candidate)
            if exact is not None:
                return LookupResult(
                    query=word,
                    normalized_query=normalized_query,
                    entry=exact,
                    resolved_headword=exact.headword,
                    strategy="form",
                    candidate_forms=tuple(candidate_forms),
                )

        return LookupResult(
            query=word,
            normalized_query=normalized_query,
            entry=None,
            strategy="not_found",
            candidate_forms=tuple(candidate_forms),
        )

    def available_entries(self) -> int:
        row = self._connection.execute("SELECT COUNT(*) AS count FROM entries").fetchone()
        return int(row["count"])

    def close(self) -> None:
        self._connection.close()

    def _load_metadata(self) -> dict[str, str]:
        try:
            rows = self._connection.execute("SELECT key, value FROM metadata").fetchall()
        except sqlite3.OperationalError:
            return {}
        return {str(row["key"]): str(row["value"]) for row in rows}

    def _lookup_exact_form(self, normalized_form: str) -> DictionaryEntry | None:
        row = self._connection.execute(
            """
            SELECT e.id, e.headword, e.normalized_headword, e.best_translation, e.notes, COALESCE(t.ipa, '') AS ipa
            FROM forms f
            JOIN entries e ON e.id = f.entry_id
            LEFT JOIN transcriptions t ON t.entry_id = e.id
            WHERE f.normalized_form = ?
            ORDER BY CASE WHEN e.normalized_headword = ? THEN 0 ELSE 1 END, e.headword
            LIMIT 1
            """,
            (normalized_form, normalized_form),
        ).fetchone()
        if row is None:
            row = self._connection.execute(
                """
                SELECT e.id, e.headword, e.normalized_headword, e.best_translation, e.notes, COALESCE(t.ipa, '') AS ipa
                FROM entries e
                LEFT JOIN transcriptions t ON t.entry_id = e.id
                WHERE e.normalized_headword = ?
                LIMIT 1
                """,
                (normalized_form,),
            ).fetchone()
        if row is None:
            return None
        return self._hydrate_entry(int(row["id"]))

    def _hydrate_entry(self, entry_id: int) -> DictionaryEntry:
        head_row = self._connection.execute(
            """
            SELECT e.headword, e.normalized_headword, e.best_translation, e.notes, COALESCE(t.ipa, '') AS ipa
            FROM entries e
            LEFT JOIN transcriptions t ON t.entry_id = e.id
            WHERE e.id = ?
            """,
            (entry_id,),
        ).fetchone()
        alternatives = [
            row["translation"]
            for row in self._connection.execute(
                "SELECT translation FROM senses WHERE entry_id = ? ORDER BY priority ASC, id ASC",
                (entry_id,),
            ).fetchall()
        ]
        examples = [
            (row["example_src"], row["example_dst"])
            for row in self._connection.execute(
                "SELECT example_src, example_dst FROM examples WHERE entry_id = ? ORDER BY id ASC",
                (entry_id,),
            ).fetchall()
        ]
        best = head_row["best_translation"] or (alternatives[0] if alternatives else "")
        unique_alternatives = []
        for item in alternatives:
            if item != best and item not in unique_alternatives:
                unique_alternatives.append(item)
        return DictionaryEntry(
            headword=head_row["headword"],
            normalized_headword=head_row["normalized_headword"],
            transcription=head_row["ipa"],
            best_translation=best,
            alternative_translations=unique_alternatives,
            examples=examples,
            notes=head_row["notes"] or "",
        )
