# Архитектура MVP v2

## Назначение

MVP реализует чтение PDF с текстовым слоем и офлайн-перевод слова по клику. Архитектура остаётся модульной, чтобы позже можно было добавить:

- новые форматы документов;
- OCR;
- дополнительные словарные паки;
- другой GUI-стек;
- нейронный переводчик как отдельный слой.

## Слои системы

### 1. UI Layer

Файлы:

- `src/pdf_word_translator/ui/main_window.py`

Ответственность:

- окно приложения;
- toolbar и statusbar;
- canvas для рендера страницы;
- нижняя панель краткой словарной подсказки;
- взаимодействие мышью и поиск.

UI не открывает PDF напрямую и не знает устройство словарной БД.

### 2. Application Layer

Файлы:

- `src/pdf_word_translator/app.py`
- `src/pdf_word_translator/plugin_loader.py`
- `src/pdf_word_translator/services/document_service.py`
- `src/pdf_word_translator/services/dictionary_service.py`
- `src/pdf_word_translator/services/translation_workflow.py`

Ответственность:

- запуск приложения;
- инициализация каталогов runtime;
- построение встроенного словаря при необходимости;
- загрузка плагинов;
- orchestration между UI, документом и словарём.

### 3. Domain Layer

Файлы:

- `src/pdf_word_translator/models.py`
- `src/pdf_word_translator/plugin_api.py`

Ответственность:

- стабильные dataclass-модели (`WordToken`, `SearchHit`, `DictionaryEntry`, `LookupResult`);
- интерфейсы плагинов документа и словаря.

### 4. Infrastructure Layer

Файлы:

- `src/pdf_word_translator/plugins/document_pdf_pymupdf.py`
- `src/pdf_word_translator/plugins/dictionary_sqlite.py`
- `src/pdf_word_translator/plugins/dictionary_composite.py`
- `src/pdf_word_translator/utils/dictionary_builder.py`
- `src/pdf_word_translator/utils/freedict_importer.py`
- `src/pdf_word_translator/utils/text_normalizer.py`
- `src/pdf_word_translator/utils/logging_utils.py`

Ответственность:

- доступ к PDF через PyMuPDF;
- lookup по SQLite;
- объединение нескольких словарных паков;
- сборка и импорт словарей;
- нормализация английских словоформ;
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

app.py
  -> AppConfig
  -> ensure_dictionary_database()
  -> PluginLoader
  -> MainWindow
```

## Поток клика по слову

1. Пользователь кликает на canvas.
2. `MainWindow` переводит координаты экрана в координаты страницы.
3. `TranslationWorkflow.translate_point()` вызывает `DocumentSession.find_token_at()`.
4. `DocumentSession` возвращает `WordToken`.
5. `TranslationWorkflow` получает контекст из `get_sentence_for_token()`.
6. `DictionaryService.lookup()` ищет слово во всех подключённых словарных паках.
7. `MainWindow` обновляет нижнюю карточку перевода.

## Поток установки словаря

1. `scripts/install_desktop.sh` создаёт `.venv` и ставит зависимости.
2. `tools/install_default_dictionaries.py`:
   - гарантирует наличие встроенного словаря;
   - пытается скачать FreeDict EN-RU TEI;
   - конвертирует его в SQLite.
3. На следующем запуске `PluginLoader` автоматически подхватывает новый `*.sqlite` файл из runtime-каталога словарей.

## Выбор словаря при lookup

Порядок приоритета:

1. встроенный технический глоссарий;
2. пользовательские SQLite-паки из `~/.local/share/pdf_word_translator_mvp/dictionaries/`.

Это позволяет техническим переводам переопределять более общие словарные значения.

## Runtime-каталоги

По XDG:

- данные: `~/.local/share/pdf_word_translator_mvp/`
- словари: `~/.local/share/pdf_word_translator_mvp/dictionaries/`
- кэш: `~/.cache/pdf_word_translator_mvp/`
- логи: `~/.cache/pdf_word_translator_mvp/logs/`
- временные загрузки словарей: `~/.cache/pdf_word_translator_mvp/downloads/`

## Границы текущего MVP

- только text-based PDF;
- только словарный EN -> RU перевод;
- без OCR;
- без Android-сборки;
- без runtime-менеджера словарей в GUI.

## Эволюция в будущем

Архитектура уже допускает:

- `DocumentPlugin` для DOCX/EPUB;
- `DictionaryPlugin` для новых backend-ов;
- отдельный `TranslationPlugin` для фраз/предложений;
- OCR-плагин, который будет превращать изображение страницы в текстовую модель.
