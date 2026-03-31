# Архитектура MVP v8

## Назначение

`v8` сохраняет уже принятую архитектуру:

1. **desktop application** на Python + Tkinter;
2. **android-client** как отдельная APK-ветка;
3. **shared dictionary core** и модели данных внутри `src/pdf_word_translator/`.

Главный принцип не меняется:

- viewer и platform UI могут быть разными;
- словарный формат, модели данных и lookup-логика остаются общими;
- нейронный перевод остаётся optional-слоем и не раздувает ядро.

## Слои системы

### 1. Desktop UI Layer

Файл:

- `src/pdf_word_translator/ui/main_window.py`

Ответственность:

- основное Tkinter-окно;
- scrolling canvas для документа;
- lazy rendering страниц;
- нижняя карточка словарной подсказки;
- поиск, zoom, scroll, word highlight;
- каталог словарей;
- менеджер Argos-моделей;
- диалог настройки provider layer;
- растягиваемый read-only dialog для длинной справки по Argos.

### 2. Application Layer

Файлы:

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

Файлы:

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
- `src/pdf_word_translator/utils/*`

Ответственность:

- открытие и рендер PDF/TXT/FB2;
- SQLite dictionaries;
- import/install словарей;
- settings persistence;
- Argos model lifecycle helpers.

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

## Границы безопасности и устойчивости в v8

### Provider layer остаётся отдельным

Словарный перевод слова и перевод предложения — разные задачи. Поэтому provider layer не встроен в ядро lookup и не ломает основной словарный сценарий.

### External plugins теперь opt-in

Загрузка внешних Python-плагинов больше не происходит автоматически. Для включения нужен `PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS=1`.

Дополнительно загрузчик:

- игнорирует небезопасные symlink/non-regular paths;
- пропускает каталоги и файлы с небезопасными POSIX permission bits;
- создаёт уникальные module names для внешних плагинов.

### Settings file сохраняется безопаснее

`settings.json` теперь:

- сохраняется через временный файл и `os.replace()`;
- на POSIX получает права `0600`.

### Mobile bridge принимает только обычные файлы

`mobile_api.py` теперь отклоняет директории и другие non-file paths при конфигурации словарей.

## Что именно было слито в v8

`v8` объединяет:

- функциональность `v7` (Android branch, `mobile_api.py`, Argos help dialog);
- исправления из отдельной fixed-ветки (LibreTranslate diagnostics/fallback, responsive UI-окна, Argos status text);
- дополнительное усиление безопасности настроек, plugin loading и mobile bridge.
