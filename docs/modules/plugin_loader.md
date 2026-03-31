# `plugin_loader.py`

## Назначение

Загрузчик builtin и optional external plugins.

## Что делает

- регистрирует document plugins:
  - PDF / PyMuPDF;
  - TXT;
  - FB2;
- собирает composite dictionary plugin из:
  - встроенного EN→RU словаря;
  - встроенного RU→EN словаря;
  - всех runtime `*.sqlite` packs;
  - внешних dictionary plugins, если они явно разрешены.

## Что изменилось в v8

### Built-in поведение не сломано

Loader по-прежнему поднимает оба встроенных направления уже на старте, поэтому UI может свободно переключать EN ↔ RU.

### External plugins стали opt-in

По умолчанию внешний Python-код из runtime plugin directory больше не исполняется. Для включения нужен `PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS=1` или `AppConfig.enable_external_plugins=True`.

### Добавлены базовые ограничения безопасности

Loader:

- пропускает небезопасные symlink/non-regular paths;
- пропускает файлы и каталоги с небезопасными POSIX permission bits;
- даёт внешним модулям уникальные имена, чтобы избежать коллизий.
