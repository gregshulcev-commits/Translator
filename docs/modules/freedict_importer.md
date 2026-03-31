# `freedict_importer.py`

## Назначение

Скачивание и импорт FreeDict TEI в SQLite-формат приложения.

## Основные функции

### `download_freedict_tei(destination, urls=...)`

Пробует скачать TEI из списка URL по очереди.

### `build_dictionary_from_freedict_tei(tei_path, db_path)`

Парсит TEI и строит SQLite-пак.

### `install_default_freedict_dictionary(runtime_dictionary_dir, download_dir)`

Сценарий для стандартной установки общего EN-RU словаря.

## Поддерживаемый поднабор TEI

- `<entry>`
- `<form><orth>`
- `<form><pron>`
- `<sense><cit type="trans"><quote>`
- частичная поддержка примеров

## Особенность

Повторяющиеся headword-entries агрегируются, чтобы lookup был устойчивее и не терял альтернативные переводы.
