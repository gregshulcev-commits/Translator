# Архитектура MVP v9

## Назначение

`v9` сохраняет принятую архитектуру проекта:

1. **desktop application** на Python + Tkinter;
2. **android-client** как отдельная APK/source-ветка;
3. **shared dictionary core** и модели данных внутри `src/pdf_word_translator/`.

Главный принцип не меняется:

- viewer и platform UI могут быть разными;
- словарный формат, модели данных и lookup-логика остаются общими;
- контекстный/нейронный перевод остаётся optional-слоем и не раздувает ядро.

## Слои системы

### 1. Desktop UI Layer

Основные файлы:

- `src/pdf_word_translator/ui/main_window.py`
- `src/pdf_word_translator/ui/settings_dialog.py`

Ответственность:

- главное окно и viewer документа;
- поиск, zoom, scroll и highlight слова;
- нижняя карточка словарной подсказки;
- отдельное окно настроек;
- GUI-управление словарями;
- GUI-управление Argos runtime и моделями.

### 2. Application Layer

Основные файлы:

- `src/pdf_word_translator/app.py`
- `src/pdf_word_translator/plugin_loader.py`
- `src/pdf_word_translator/services/document_service.py`
- `src/pdf_word_translator/services/dictionary_service.py`
- `src/pdf_word_translator/services/translation_workflow.py`
- `src/pdf_word_translator/providers/context_providers.py`

Ответственность:

- orchestration между UI, document layer, dictionary layer и provider layer;
- загрузка built-in и opt-in external plugins;
- запуск приложения и сохранение настроек;
- связка `token -> dictionary lookup -> optional context translation`.

### 3. Domain Layer

Основные файлы:

- `src/pdf_word_translator/models.py`
- `src/pdf_word_translator/plugin_api.py`

Ответственность:

- dataclass-модели;
- контракты document plugins, dictionary plugins и providers.

### 4. Plugins / Infrastructure / Utils

Основные файлы:

- `src/pdf_word_translator/plugins/document_pdf_pymupdf.py`
- `src/pdf_word_translator/plugins/document_text_base.py`
- `src/pdf_word_translator/plugins/document_txt.py`
- `src/pdf_word_translator/plugins/document_fb2.py`
- `src/pdf_word_translator/plugins/dictionary_sqlite.py`
- `src/pdf_word_translator/plugins/dictionary_composite.py`
- `src/pdf_word_translator/utils/context_extraction.py`
- `src/pdf_word_translator/utils/dictionary_manager.py`
- `src/pdf_word_translator/utils/argos_manager.py`
- `src/pdf_word_translator/utils/settings_store.py`

Ответственность:

- открытие и рендер PDF/TXT/FB2;
- SQLite dictionaries;
- import/install словарей;
- безопасное перечисление и удаление runtime-паков;
- извлечение компактного контекста вокруг слова;
- persistence пользовательских настроек;
- lifecycle helper для Argos.

### 5. Mobile Bridge Layer

Файл:

- `src/pdf_word_translator/mobile_api.py`

Bridge остаётся:

- JSON-friendly;
- UI-free;
- без привязки к desktop viewer;
- с минимальной поверхностью API.

Он отвечает за:

- конфигурацию путей к SQLite dictionaries;
- summary активных packs;
- lookup слова;
- JSON-friendly payloads для Kotlin/Chaquopy.

### 6. Android Client Layer

Директория:

- `android-client/`

Там живёт отдельная UI-ветка с:

- Kotlin UI;
- Chaquopy integration;
- PdfRenderer;
- dictionary bridge;
- asset bootstrap.

## Что именно меняется в `v9`

### Удобство использования вынесено в отдельные узлы

Новые крупные элементы архитектуры:

- `SettingsDialog` как единый центр GUI-настроек;
- `install_app.sh` как пользовательский desktop installer;
- `context_extraction.py` как отдельный слой подготовки короткого контекста;
- `dictionary_manager.py` как слой безопасного GUI-удаления runtime-словарей.

### Provider layer остаётся отдельным

Словарный перевод слова и перевод предложения — разные задачи. Поэтому provider layer не встроен в ядро lookup и не ломает основной словарный сценарий.

### External plugins остаются opt-in

Загрузка внешних Python-плагинов не происходит автоматически. Для включения нужен `PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS=1`.

Дополнительно загрузчик:

- игнорирует небезопасные symlink/non-regular paths;
- пропускает каталоги и файлы с небезопасными POSIX permission bits;
- создаёт уникальные module names для внешних плагинов.

### Settings file сохраняется безопаснее

`settings.json`:

- сохраняется через временный файл и `os.replace()`;
- на POSIX получает права `0600`.

### GUI-удаление словарей ограничено runtime-папкой

Даже при работе из окна настроек приложение не должно иметь возможность удалять произвольные файлы. Поэтому GUI-удаление разрешено только для пользовательских SQLite-паков внутри runtime directory.
