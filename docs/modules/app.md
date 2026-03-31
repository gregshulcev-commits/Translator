# `app.py`

## Назначение

Точка входа приложения.

## Ответственность

- создаёт `AppConfig`;
- гарантирует runtime-каталоги;
- гарантирует наличие встроенного SQLite-словаря;
- настраивает логирование;
- загружает plugins через `PluginLoader`;
- создаёт сервисы и главное окно;
- открывает стартовый документ, если путь передан через CLI.

## Важные зависимости

- `config.py`
- `plugin_loader.py`
- `document_service.py`
- `dictionary_service.py`
- `translation_workflow.py`
- `settings_store.py`
- `ui/main_window.py`

## Что изменилось в v3

- аргумент CLI теперь принимает не только PDF, а любой поддерживаемый документ;
- в `MainWindow` передаётся `PluginLoader` для hot-reload словарей;
- в `MainWindow` передаётся `SettingsStore` для сохранения размера интерфейса.
