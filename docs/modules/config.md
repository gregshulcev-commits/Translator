# `config.py`

## Назначение

Хранит вычисление путей проекта, runtime-каталогов и runtime flags.

## Основные пути

- `PROJECT_ROOT`
- `DATA_ROOT`
- `RUNTIME_DATA_DIR`
- `RUNTIME_CACHE_DIR`
- `RUNTIME_LOG_DIR`
- `RUNTIME_DICTIONARY_DIR`
- `RUNTIME_DOWNLOAD_DIR`
- `EXTERNAL_PLUGIN_DIR`
- `SETTINGS_FILE`

## `AppConfig`

Dataclass, которая собирает ключевые пути и runtime flags в одном объекте.

## Что важно в v8

- исправленный `PROJECT_ROOT` сохранён;
- добавлен flag `enable_external_plugins`;
- значение по умолчанию берётся из `PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS`.
