# plugins/dictionary_sqlite.py

## Назначение

SQLite-реализация словаря.

## Как работает lookup

1. строит candidate forms;
2. ищет совпадение среди `forms`;
3. при необходимости ищет по `entries.normalized_headword`;
4. возвращает `LookupResult`.

## Ограничение

Качество зависит от наполнения SQLite базы.
