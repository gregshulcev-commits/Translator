# `config.py`

## Назначение

Единая точка для путей проекта и runtime-каталогов.

## Основные константы

- `PROJECT_ROOT`
- `DATA_ROOT`
- `DEFAULT_STARTER_CSV`
- `DEFAULT_STARTER_DB`
- `RUNTIME_DATA_DIR`
- `RUNTIME_CACHE_DIR`
- `RUNTIME_LOG_DIR`
- `RUNTIME_DICTIONARY_DIR`
- `RUNTIME_DOWNLOAD_DIR`
- `EXTERNAL_PLUGIN_DIR`

## `AppConfig`

Содержит все разрешённые приложению пути и умеет создавать runtime-каталоги.

## Изменение в v2

Исправлена ошибка вычисления `PROJECT_ROOT`: теперь конфиг больше не выходит на уровень выше каталога проекта.
