# plugin_loader.py

## Назначение

Загружает builtin plugins и внешние Python-плагины из runtime directory.

## Что делает

- регистрирует встроенный PDF provider;
- регистрирует встроенный SQLite dictionary provider;
- при наличии загружает внешние `.py` плагины через `register_plugins()`.

## Расширение

Внешний плагин должен вернуть список инстансов, реализующих интерфейсы из `plugin_api.py`.
