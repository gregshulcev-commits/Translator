# `settings_store.py`

## Назначение

Хранит пользовательские настройки интерфейса.

## Что сохраняется сейчас

- `ui_font_size`

## Основные сущности

### `UiSettings`

Dataclass с end-user settings.

### `SettingsStore`

Маленький JSON-backed store.

## Почему это отдельный модуль

Даже одна настройка лучше вынесена из GUI-кода:

- проще тестировать;
- проще расширять;
- не смешивается с viewer и translation workflow.
