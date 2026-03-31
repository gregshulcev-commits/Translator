# Архитектура MVP v3

## Назначение

MVP реализует чтение документов и офлайн-перевод слова по клику. Архитектура остаётся модульной, чтобы позже можно было добавить:

- новые форматы документов;
- OCR;
- дополнительные словарные паки;
- другой GUI-стек;
- нейронный переводчик как отдельный слой.

## Слои системы

### 1. UI Layer

Файл:

- `src/pdf_word_translator/ui/main_window.py`

Ответственность:

- окно приложения;
- toolbar, statusbar, меню и контекстное меню;
- scrolling canvas со всем документом;
- нижняя панель краткой словарной подсказки;
- click/scroll/zoom/search interactions;
- hot-reload словарей после импорта.

UI не знает внутренностей PDF-парсера, формата словаря и не работает с файлами словарей напрямую.

### 2. Application Layer

Файлы:

- `src/pdf_word_translator/app.py`
- `src/pdf_word_translator/plugin_loader.py`
- `src/pdf_word_translator/services/document_service.py`
- `src/pdf_word_translator/services/dictionary_service.py`
- `src/pdf_word_translator/services/translation_workflow.py`

Ответственность:

- запуск приложения;
- инициализация runtime-каталогов;
- построение встроенного словаря при необходимости;
- загрузка document plugins и dictionary plugins;
- orchestration между UI, документом и словарём.

### 3. Domain Layer

Файлы:

- `src/pdf_word_translator/models.py`
- `src/pdf_word_translator/plugin_api.py`

Ответственность:

- стабильные dataclass-модели (`WordToken`, `SearchHit`, `DictionaryEntry`, `LookupResult`);
- интерфейсы `DocumentPlugin`, `DocumentSession`, `DictionaryPlugin`.

### 4. Infrastructure Layer

Файлы:

- `src/pdf_word_translator/plugins/document_pdf_pymupdf.py`
- `src/pdf_word_translator/plugins/document_text_base.py`
- `src/pdf_word_translator/plugins/document_txt.py`
- `src/pdf_word_translator/plugins/document_fb2.py`
- `src/pdf_word_translator/plugins/dictionary_sqlite.py`
- `src/pdf_word_translator/plugins/dictionary_composite.py`
- `src/pdf_word_translator/utils/dictionary_builder.py`
- `src/pdf_word_translator/utils/freedict_importer.py`
- `src/pdf_word_translator/utils/dictionary_installer.py`
- `src/pdf_word_translator/utils/text_normalizer.py`
- `src/pdf_word_translator/utils/settings_store.py`
- `src/pdf_word_translator/utils/logging_utils.py`

Ответственность:

- доступ к PDF через PyMuPDF;
- pagination and token mapping for TXT/FB2;
- lookup по SQLite;
- объединение нескольких словарных паков;
- сборка и импорт словарей;
- нормализация английских словоформ;
- сохранение UI-настроек;
- логирование.

### 5. Tooling Layer

Файлы:

- `tools/build_dictionary.py`
- `tools/import_dictionary.py`
- `tools/install_default_dictionaries.py`
- `scripts/install_desktop.sh`

Ответственность:

- сборка встроенного словаря;
- импорт внешних словарей;
- автоматическая установка зависимостей и словарей.

## Диаграмма зависимостей

```text
MainWindow
  -> TranslationWorkflow
      -> DocumentService
          -> DocumentPlugin / DocumentSession
      -> DictionaryService
          -> DictionaryPlugin
              -> CompositeDictionaryPlugin
                  -> SQLiteDictionaryPlugin[*]

MainWindow
  -> dictionary_installer utilities
  -> SettingsStore

app.py
  -> AppConfig
  -> ensure_dictionary_database()
  -> PluginLoader
  -> MainWindow
```

## Поток клика по слову

1. Пользователь кликает по canvas.
2. `MainWindow` определяет, на какой визуальной странице произошёл клик.
3. Координаты canvas переводятся в page coordinates.
4. `TranslationWorkflow.translate_point()` вызывает `DocumentSession.find_token_at()`.
5. `DocumentSession` возвращает `WordToken`.
6. `TranslationWorkflow` получает контекст из `get_sentence_for_token()`.
7. `DictionaryService.lookup()` ищет слово во всех подключённых словарных паках.
8. `MainWindow` обновляет нижнюю карточку перевода и подсветку слова.

## Поток прокрутки и zoom

### Прокрутка

- Все страницы документа рендерятся как единый scrolling document.
- Canvas хранит `CanvasPageLayout` для каждой страницы.
- Колесо мыши двигает viewport по всему документу, а не только внутри одной страницы.

### Zoom

- `Ctrl + колесо мыши` вызывает `MainWindow.change_zoom()`.
- Перед zoom сохраняется document point под курсором.
- После перерендера viewer возвращает ту же логическую точку под курсор.

## Поток установки словаря из GUI

1. Пользователь открывает меню **Словари** или контекстное меню.
2. GUI запускает функцию из `dictionary_installer.py`.
3. Функция либо копирует SQLite-пак, либо импортирует CSV / TEI во внутренний SQLite-формат.
4. `MainWindow` вызывает `PluginLoader.create_dictionary_plugin()`.
5. `DictionaryService` hot-swap'ит активный composite plugin без перезапуска приложения.

## Runtime-каталоги

По XDG:

- данные: `~/.local/share/pdf_word_translator_mvp/`
- словари: `~/.local/share/pdf_word_translator_mvp/dictionaries/`
- настройки: `~/.local/share/pdf_word_translator_mvp/settings.json`
- кэш: `~/.cache/pdf_word_translator_mvp/`
- логи: `~/.cache/pdf_word_translator_mvp/logs/`
- временные загрузки словарей: `~/.cache/pdf_word_translator_mvp/downloads/`

## Поддерживаемые форматы документов

### PDF

- provider: `PyMuPdfDocumentPlugin`
- источник координат: PyMuPDF `page.get_text("words")`
- сильные стороны: высокая точность токенов и поиска.

### TXT

- provider: `PlainTextDocumentPlugin`
- источник координат: синтетическая page layout модель на базе Pillow.

### FB2

- provider: `Fb2DocumentPlugin`
- источник текста: XML parsing + reflow into synthetic pages.

## Границы текущего MVP

- PDF только с текстовым слоем;
- TXT/FB2 рендерятся как synthetic pages и не дают системного выделения текста;
- только словарный EN → RU перевод;
- без OCR;
- без APK-сборки Android.

## Эволюция

Архитектура уже допускает:

- новые `DocumentPlugin` для EPUB / DOCX;
- OCR-plugin, который строит такую же `WordToken`-модель;
- отдельный `TranslationPlugin` для фраз/предложений;
- смену UI-стека при сохранении сервисов и словарного слоя.
