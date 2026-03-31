# `dictionary_sqlite.py`

## Назначение

Dictionary plugin поверх SQLite runtime-схемы.

## Что делает

- выполняет lookup по `forms.normalized_form`;
- делает fallback по `entries.normalized_headword`;
- hydrat'ит `DictionaryEntry` с senses, examples и transcription;
- возвращает `LookupResult` с candidate forms.

## Особенности

- использует `EnglishWordNormalizer.candidate_forms()`;
- подключается к одному SQLite-паку;
- в v3 получил `close()` для корректного освобождения SQLite connection при hot-reload словарей.
