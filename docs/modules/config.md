# `config.py`

## Назначение

Хранит вычисление путей проекта и runtime-каталогов.

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

Dataclass, которая собирает все пути в одном объекте и умеет создавать runtime-каталоги.

## Что важно в v3

- исправленный `PROJECT_ROOT` сохранён;
- добавлен `settings_file` для persistent UI settings.
