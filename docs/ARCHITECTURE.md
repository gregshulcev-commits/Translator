# Архитектура MVP v4

## Назначение

MVP реализует чтение документов и офлайн-перевод слова по клику. Архитектура остаётся модульной, чтобы позже можно было добавить:

- новые форматы документов;
- OCR;
- дополнительные словарные паки;
- отдельный нейронный/онлайн слой перевода;
- другой GUI-стек;
- отдельный Android-клиент.

## Слои системы

### 1. UI Layer

Файл:

- `src/pdf_word_translator/ui/main_window.py`

Ответственность:

- окно приложения;
- toolbar, statusbar, меню и контекстное меню;
- scrolling canvas со всем документом;
- **ленивая перерисовка страниц** только в видимой области;
- нижняя компактная панель словарной справки;
- click / scroll / zoom / search interactions;
- hot-reload словарей после импорта;
- direction toggle и настройка контекстного провайдера.

### 2. Application Layer

Файлы:

- `src/pdf_word_translator/app.py`
- `src/pdf_word_translator/plugin_loader.py`
- `src/pdf_word_translator/services/document_service.py`
- `src/pdf_word_translator/services/dictionary_service.py`
- `src/pdf_word_translator/services/translation_workflow.py`
- `src/pdf_word_translator/providers/context_providers.py`

Ответственность:

- запуск приложения;
- подготовка встроенных стартовых словарей для обоих направлений;
- загрузка document plugins и dictionary plugins;
- orchestration между UI, документом, словарём и контекстным переводом.

### 3. Domain Layer

Файлы:

- `src/pdf_word_translator/models.py`
- `src/pdf_word_translator/plugin_api.py`

Ответственность:

- стабильные dataclass-модели (`WordToken`, `SearchHit`, `DictionaryEntry`, `LookupResult`, `ContextTranslationResult`, `DictionaryPackInfo`);
- интерфейсы `DocumentPlugin`, `DocumentSession`, `DictionaryPlugin`, `ContextTranslationProvider`.

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
- `src/pdf_word_translator/utils/dictionary_catalog.py`
- `src/pdf_word_translator/utils/text_normalizer.py`
- `src/pdf_word_translator/utils/token_splitter.py`
- `src/pdf_word_translator/utils/settings_store.py`
- `src/pdf_word_translator/utils/logging_utils.py`

Ответственность:

- доступ к PDF через PyMuPDF;
- pagination and token mapping for TXT / FB2;
- split compound tokens (`a/b`, `a\b`) into clickable sub-tokens;
- lookup по SQLite;
- объединение нескольких словарных паков;
- сборка и импорт словарей;
- каталог доступных паков;
- нормализация английских и русских словоформ;
- сохранение UI-настроек;
- логирование.

### 5. Tooling Layer

Файлы:

- `tools/build_dictionary.py`
- `tools/import_dictionary.py`
- `tools/install_default_dictionaries.py`
- `tools/install_argos_model.py`
- `scripts/install_desktop.sh`

Ответственность:

- сборка встроенных словарей;
- импорт внешних словарей;
- автоматическая установка зависимостей и словарей;
- optional установка Argos-моделей.

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
  -> ContextTranslationService
      -> Disabled / Argos / LibreTranslate / Yandex providers
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
6. `TranslationWorkflow` получает контекст из `get_sentence_for_token()`, но UI не показывает его напрямую.
7. `DictionaryService.lookup()` ищет слово во всех подключённых словарных паках для выбранного направления.
8. `MainWindow` обновляет нижнюю карточку перевода и подсветку слова.
9. Если включён контекстный провайдер, `ContextTranslationService.translate_async()` переводит скрытый контекст и пишет результат во вторую строку панели.

## Поток прокрутки и zoom

### Прокрутка

- Canvas хранит `CanvasPageLayout` для каждой страницы.
- Колесо мыши двигает viewport по всему документу.
- При прокрутке UI только пересчитывает текущую видимую область и при необходимости рендерит новые страницы.

### Zoom

- `Ctrl + колесо мыши` вызывает `MainWindow.change_zoom()`.
- Перед zoom сохраняется document point под курсором.
- После перестройки layout viewer возвращает ту же логическую точку под курсор.
- При этом pages images пересоздаются **лениво**, а не для всего документа сразу.

## Поток установки словаря из GUI

1. Пользователь открывает меню **Словари** или контекстное меню.
2. GUI либо открывает **каталог пакетов**, либо запускает функцию из `dictionary_installer.py`.
3. Функция либо копирует SQLite-пак, либо импортирует CSV / TEI во внутренний SQLite-формат, либо скачивает FreeDict.
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
- TXT / FB2 рендерятся как synthetic pages и не дают системного выделения текста;
- нет OCR;
- Android-ветка отделена и не собрана как APK в этом архиве.

## Эволюция

Архитектура уже допускает:

- новые `DocumentPlugin` для EPUB / DOCX;
- OCR-plugin, который строит такую же `WordToken`-модель;
- отдельный `TranslationPlugin` для фраз и предложений;
- смену UI-стека при сохранении сервисов и словарного слоя.
