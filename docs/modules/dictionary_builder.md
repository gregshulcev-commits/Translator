# `dictionary_builder.py`

## Назначение

Унифицированная сборка SQLite-словари из нормализованных записей.

## Что умеет

- гарантировать наличие встроенного словаря;
- читать CSV-глоссарий;
- строить SQLite из `DictionaryBuildEntry`;
- записывать внутреннюю схему БД.

## Основная dataclass-модель

`DictionaryBuildEntry`:

- `headword`
- `best_translation`
- `alternatives`
- `forms`
- `examples`
- `notes`
- `transcription`

## Изменение в v2

Удалена зависимость от `pronouncing`. Автоматическая генерация транскрипций больше не выполняется; транскрипция берётся из источника словаря.
