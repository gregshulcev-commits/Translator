# `plugin_loader.py`

## Назначение

Загрузчик built-in и optional external plugins.

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

## Что важно в текущей версии

### Built-in поведение остаётся стабильным

Loader по-прежнему поднимает оба встроенных направления уже на старте, поэтому UI может свободно переключать EN ↔ RU.

### External plugins остаются opt-in

По умолчанию внешний Python-код из runtime plugin directory не исполняется. Для включения нужен `PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS=1` или `AppConfig.enable_external_plugins=True`.

### Сохраняются базовые ограничения безопасности

Loader:

- пропускает небезопасные symlink/non-regular paths;
- пропускает файлы и каталоги с небезопасными POSIX permission bits;
- даёт внешним модулям уникальные имена, чтобы избежать коллизий.

## Почему это важно для `v9`

В `v9` приложение стало удобнее в GUI-части, но политика загрузки внешнего кода не была ослаблена: новые удобства не должны автоматически расширять attack surface.
