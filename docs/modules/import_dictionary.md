# `tools/import_dictionary.py`

## Назначение

CLI-инструмент для конвертации внешних словарей во внутренний SQLite-пак.

## Поддерживаемые форматы

- `csv`
- `freedict-tei`

## Примеры

### CSV

```bash
PYTHONPATH=src python tools/import_dictionary.py glossary.csv ~/.local/share/pdf_word_translator_mvp/dictionaries/glossary.sqlite --format csv
```

### FreeDict TEI

```bash
PYTHONPATH=src python tools/import_dictionary.py eng-rus.tei ~/.local/share/pdf_word_translator_mvp/dictionaries/freedict_en_ru.sqlite --format freedict-tei
```
