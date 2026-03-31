# `dictionary_installer.py`

## Назначение

Набор helper-функций, которые GUI использует для установки и импорта словарей.

## Функции

### `install_sqlite_pack()`

Копирует готовый SQLite-пак в runtime-каталог словарей.

### `import_csv_pack()`

Строит SQLite-пак из CSV и кладёт его в runtime-каталог.

### `import_freedict_pack()`

Строит SQLite-пак из FreeDict TEI.

### `install_default_pack()`

Скачивает и собирает словарь по умолчанию.

## Зачем отдельный модуль

Это позволяет:

- использовать один и тот же код из GUI и CLI;
- держать file operations вне `main_window.py`;
- упростить тестирование импорта словарей.
