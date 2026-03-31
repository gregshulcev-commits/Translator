# Архитектура MVP

## 1. Цель архитектуры

Сделать не просто одноразовый скрипт, а основание для дальнейшей разработки:

- PDF-viewer с переводом по клику;
- минимальные зависимости между слоями;
- возможность заменить словарь без переписывания UI;
- возможность позже добавить OCR и новые форматы.

## 2. Слои

### UI layer

`ui/main_window.py`

Отвечает только за:

- главное окно;
- toolbar;
- canvas просмотра страницы;
- правую панель перевода;
- статусы;
- навигацию по страницам и поиску.

### Workflow / Application layer

`services/translation_workflow.py`
`services/document_service.py`
`services/dictionary_service.py`

Отвечает за orchestration:

- открыть документ;
- получить слово по координате;
- получить контекст;
- сделать lookup;
- вернуть готовую модель данных для UI.

### Domain layer

`models.py`

Содержит независимые от GUI и библиотеки доменные сущности:

- `WordToken`
- `SearchHit`
- `DocumentSentence`
- `DictionaryEntry`
- `LookupResult`

### Infrastructure / Plugin layer

`plugins/document_pdf_pymupdf.py`
`plugins/dictionary_sqlite.py`
`plugin_api.py`
`plugin_loader.py`

Отвечает за конкретные реализации:

- чтение PDF;
- получение координат слов;
- поиск по текстовому слою;
- словарный lookup через SQLite.

### Utility layer

`utils/text_normalizer.py`
`utils/dictionary_builder.py`
`utils/logging_utils.py`

Отвечает за:

- нормализацию английских слов;
- сборку словаря из CSV;
- логирование.

## 3. Поток клика по слову

```text
Canvas click
  -> MainWindow.on_canvas_click()
  -> TranslationWorkflow.translate_point()
  -> DocumentSession.find_token_at()
  -> DocumentSession.get_sentence_for_token()
  -> DictionaryService.lookup()
  -> SQLiteDictionaryPlugin.lookup()
  -> TranslationViewModel
  -> MainWindow._populate_panel()
```

## 4. Поток поиска по документу

```text
Search query
  -> MainWindow.execute_search()
  -> DocumentSession.search(query)
  -> SearchHit[]
  -> MainWindow.navigate_search()
  -> highlight result + page jump
```

## 5. Почему архитектура модульная, хотя MVP маленький

Потому что это снижает будущую стоимость изменений:

- PDF-плагин можно заменить на другой renderer;
- SQLite-слой можно заменить на import из внешних словарей;
- UI можно переписать позже на Qt, сохранив services и plugins;
- OCR можно добавить отдельным plugin-ом документа.

## 6. Реализованные точки расширения

### Document plugins

Интерфейс: `DocumentPlugin`, `DocumentSession`

Сейчас реализован:

- `PyMuPdfDocumentPlugin`

Потом можно добавить:

- `DocxDocumentPlugin`
- `EpubDocumentPlugin`
- `OcrPdfDocumentPlugin`

### Dictionary plugins

Интерфейс: `DictionaryPlugin`

Сейчас реализован:

- `SQLiteDictionaryPlugin`

Потом можно добавить:

- `StarDictDictionaryPlugin`
- `CsvDictionaryPlugin`
- `HybridDictionaryPlugin`
- `NeuralTranslationPlugin`

## 7. Почему страницы рендерятся page-by-page

Это самый простой и устойчивый вариант для MVP:

- не держит весь документ как гигантскую картинку;
- работает на больших PDF;
- легко кешируется;
- легко масштабируется для соседних страниц.

## 8. Почему словарь SQLite

SQLite удобен для MVP потому что:

- локальный и офлайн;
- не требует сервера;
- легко импортировать из CSV;
- быстро ищет словоформы по индексу;
- легко заменить на более полный словарь в будущем.
