# `config.py`

## Назначение

Вычисление путей проекта, runtime-каталогов и runtime flags.

Этот модуль даёт приложению единое представление о том, где лежат:

- bundled словари;
- runtime словари пользователя;
- кэш и логи;
- файл настроек;
- каталог внешних плагинов.

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

## Что важно в `v9`

- исправленный `PROJECT_ROOT` сохранён;
- flag `enable_external_plugins` по-прежнему берётся из `PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS`;
- пути из `AppConfig` используются не только core-модулями, но и новым GUI-управлением словарями.

## Почему это важно

Когда приложение устанавливает/подключает словари из GUI, открывает настройки или работает с runtime-директориями, оно должно использовать один и тот же источник путей, а не набор разрозненных строк в разных модулях.
