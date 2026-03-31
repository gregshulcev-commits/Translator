# `dictionary_sqlite.py`

## Назначение

Реализация `DictionaryPlugin`, работающая по внутренней SQLite-схеме.

## Lookup-логика

1. получает кандидатные формы из `EnglishWordNormalizer`;
2. ищет по `forms.normalized_form`;
3. fallback по `entries.normalized_headword`;
4. гидратирует `DictionaryEntry` из таблиц `entries/senses/examples/transcriptions`.

## Почему SQLite

- прозрачно;
- легко переносить и копировать как словарный пак;
- хорошо подходит для офлайн lookup.
