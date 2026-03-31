# utils/dictionary_builder.py

## Назначение

Собирает стартовый SQLite словарь из CSV.

## Что создает

- `entries`
- `forms`
- `transcriptions`
- `senses`
- `examples`

## Дополнительно

Если для слова нет явной транскрипции, модуль пытается получить её через `pronouncing`.
