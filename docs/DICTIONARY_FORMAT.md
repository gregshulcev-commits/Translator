# Формат словаря

## Базовый принцип

В рантайме приложение работает со словарём только через SQLite-схему. Любой внешний источник сначала конвертируется в этот формат.

## Поддерживаемые источники импорта

### 1. CSV-глоссарий

Ожидаемые колонки:

- `headword`
- `best_translation`
- `alternatives`
- `forms`
- `examples`
- `notes`
- `transcription`

Форматы полей:

- альтернативы: `вариант1|вариант2|вариант3`
- формы: `form1|form2|form3`
- примеры: `src => dst || src2 => dst2`

### 2. FreeDict TEI

Поддерживаемый поднабор TEI:

- `<entry>`
- `<form><orth>`
- `<form><pron>`
- `<sense><cit type="trans"><quote>`
- опционально примеры через `cit type="example"`

## Внутренняя SQLite-схема

### `entries`

- `id`
- `headword`
- `normalized_headword`
- `best_translation`
- `notes`

### `forms`

- `id`
- `entry_id`
- `form`
- `normalized_form`

### `transcriptions`

- `entry_id`
- `ipa`

### `senses`

- `id`
- `entry_id`
- `priority`
- `translation`

### `examples`

- `id`
- `entry_id`
- `example_src`
- `example_dst`

## Lookup-стратегия

1. нормализация исходного слова;
2. генерация кандидатных форм (`systems -> system`, `configured -> configure` и т.д.);
3. lookup по `forms.normalized_form`;
4. fallback по `entries.normalized_headword`.

## Добавление нового словаря

### Готовый SQLite-пак

Просто положите файл в:

```text
~/.local/share/pdf_word_translator_mvp/dictionaries/
```

### Импорт из CSV

```bash
PYTHONPATH=src python tools/import_dictionary.py source.csv ~/.local/share/pdf_word_translator_mvp/dictionaries/custom.sqlite --format csv
```

### Импорт из FreeDict TEI

```bash
PYTHONPATH=src python tools/import_dictionary.py source.tei ~/.local/share/pdf_word_translator_mvp/dictionaries/freedict_custom.sqlite --format freedict-tei
```
