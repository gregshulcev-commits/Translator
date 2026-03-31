# Формат словаря и способы добавления словарей

## Базовый принцип

В рантайме приложение работает со словарём только через SQLite-схему. Любой внешний источник сначала конвертируется в этот формат.

Это даёт:

- стабильный lookup runtime;
- единый формат для GUI и CLI;
- возможность подключать несколько словарных паков одновременно.

## Поддерживаемые способы добавления словаря

### 1. Готовый SQLite-пак

Это самый простой путь. Достаточно:

- положить `*.sqlite` в `~/.local/share/pdf_word_translator_mvp/dictionaries/`, либо
- выбрать меню **Словари → Подключить SQLite-словарь…**, либо
- использовать правый клик и тот же пункт контекстного меню.

GUI-операция использует `install_sqlite_pack()` из `dictionary_installer.py`.

### 2. CSV-глоссарий

Подходит для собственных словарей и ручных подборок.

Можно:

- импортировать через GUI: **Словари → Импортировать CSV-словарь…**;
- импортировать через CLI:

```bash
PYTHONPATH=src python tools/import_dictionary.py source.csv ~/.local/share/pdf_word_translator_mvp/dictionaries/custom.sqlite --format csv
```

GUI-операция использует `import_csv_pack()`.

### 3. FreeDict TEI

Подходит для полноценных общих словарей.

Можно:

- импортировать локальный `*.tei` / `*.xml` через GUI;
- импортировать через CLI:

```bash
PYTHONPATH=src python tools/import_dictionary.py source.tei ~/.local/share/pdf_word_translator_mvp/dictionaries/freedict_custom.sqlite --format freedict-tei
```

GUI-операция использует `import_freedict_pack()`.

### 4. Общий словарь по умолчанию

Можно скачать и собрать автоматически:

- через GUI: **Словари → Скачать общий FreeDict EN→RU**;
- через CLI:

```bash
PYTHONPATH=src python tools/install_default_dictionaries.py
```

Эта операция использует `install_default_pack()` и сохраняет SQLite-пак в runtime-каталог словарей.

## Поддерживаемые источники импорта

### CSV-глоссарий

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

### FreeDict TEI

Поддерживаемый поднабор TEI:

- `<entry>`
- `<form><orth>`
- `<form><pron>`
- `<sense><cit type="trans"><quote>`
- примеры через `cit type="example"`

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
2. генерация candidate forms (`systems -> system`, `configured -> configure` и т.д.);
3. lookup по `forms.normalized_form`;
4. fallback по `entries.normalized_headword`.

## Порядок приоритета словарей

1. встроенный technical glossary;
2. все пользовательские `*.sqlite`-паки из runtime-каталога.

Это позволяет держать маленький технический словарь приоритетнее большого общего.
