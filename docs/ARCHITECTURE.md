# Архитектура MVP v7

## Назначение

Проект теперь состоит из двух взаимосвязанных слоёв исполнения:

1. **desktop application** на Python + Tkinter;
2. **android-client** как отдельная APK-ветка.

Общий принцип такой:

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
- resizable help dialog для длинной справки по Argos.

### 2. Application Layer

Файлы:

- `src/pdf_word_translator/app.py`
- `src/pdf_word_translator/plugin_loader.py`
- `src/pdf_word_translator/services/document_service.py`
- `src/pdf_word_translator/services/dictionary_service.py`
- `src/pdf_word_translator/services/translation_workflow.py`
- `src/pdf_word_translator/providers/context_providers.py`

Ответственность:

- запуск desktop-приложения;
- загрузка document/dictionary plugins;
- orchestration между UI, документом, словарём и provider layer;
- проверка готовности online/offline-провайдеров.

### 3. Domain Layer

Файлы:

- `src/pdf_word_translator/models.py`
- `src/pdf_word_translator/plugin_api.py`

Ответственность:

- стабильные dataclass-модели;
- интерфейсы `DocumentPlugin`, `DocumentSession`, `DictionaryPlugin`, `ContextTranslationProvider`.

### 4. Infrastructure / Utils Layer

Файлы:

- `src/pdf_word_translator/plugins/document_pdf_pymupdf.py`
- `src/pdf_word_translator/plugins/document_text_base.py`
- `src/pdf_word_translator/plugins/document_txt.py`
- `src/pdf_word_translator/plugins/document_fb2.py`
- `src/pdf_word_translator/plugins/dictionary_sqlite.py`
- `src/pdf_word_translator/plugins/dictionary_composite.py`
- `src/pdf_word_translator/utils/*`

Ответственность:

- PDF/TXT/FB2 providers;
- SQLite dictionary access;
- dictionary import/build/install;
- settings persistence;
- Argos runtime/model lifecycle.

### 5. Mobile Bridge Layer

Новый файл v7:

- `src/pdf_word_translator/mobile_api.py`

Это узкий API без Tkinter и viewer-кода.

Ответственность:

- принять пути к SQLite-словарям;
- кешировать `DictionaryService` для мобильного клиента;
- отдавать summary подключённых паков;
- делать lookup слова;
- возвращать JSON-friendly payload для Kotlin.

### 6. Android Client Layer

Новая ветка v7:

- `android-client/`

Ответственность:

- нативный Android UI;
- открытие PDF через системный picker;
- рендер PDF через `PdfRenderer`;
- bootstrap bundled dictionaries;
- вызов `mobile_api.py` через Chaquopy.

## Диаграмма зависимостей

```text
Desktop MainWindow
  -> TranslationWorkflow
      -> DocumentService
          -> DocumentPlugin / DocumentSession
      -> DictionaryService
          -> DictionaryPlugin
              -> CompositeDictionaryPlugin
                  -> SQLiteDictionaryPlugin[*]
  -> ContextTranslationService
      -> Disabled / Argos / LibreTranslate / Yandex providers
  -> argos_manager helpers
  -> SettingsStore

Android MainActivity
  -> PdfPageRenderer
  -> AssetBootstrap
  -> DictionaryBridge
      -> pdf_word_translator.mobile_api
          -> DictionaryService
              -> CompositeDictionaryPlugin
                  -> SQLiteDictionaryPlugin[*]
```

## Поток desktop-клика по слову

1. Пользователь кликает по canvas.
2. `MainWindow` переводит координаты в page coordinates.
3. `TranslationWorkflow.translate_point()` вызывает `DocumentSession.find_token_at()`.
4. `DocumentSession` возвращает `WordToken`.
5. `DictionaryService.lookup()` ищет слово в подключённых словарях.
6. `MainWindow` обновляет нижнюю панель и highlight.
7. При активном provider layer запускается асинхронный контекстный перевод.

## Поток установки Argos-модели из desktop GUI

1. Пользователь открывает **Перевод → Офлайн-модели Argos…**.
2. `argos_manager.list_argos_models()` возвращает статус EN→RU / RU→EN.
3. При установке из сети используется `install_argos_model_for_direction()`.
4. При локальном импорте используется `import_argos_model_from_path()`.
5. Если активен провайдер `Argos (офлайн)`, текущий контекст может быть переведён повторно.

## Поток Android bootstrap

1. `MainActivity` создаёт `DictionaryBridge`.
2. `DictionaryBridge` стартует Python runtime через Chaquopy.
3. `DictionaryBridge.bundledAssetNames()` получает список имён asset-файлов из `mobile_api.py`.
4. `AssetBootstrap` копирует SQLite-словари в `filesDir/dictionaries/`.
5. `DictionaryBridge.configureDictionaryPaths()` передаёт абсолютные пути в `mobile_api.py`.
6. `mobile_api.py` создаёт или переиспользует cached `DictionaryService`.

## Поток Android lookup

1. Пользователь вводит слово вручную.
2. `MainActivity` вызывает `DictionaryBridge.lookupWord()`.
3. Kotlin получает JSON payload от `mobile_api.lookup_word_json()`.
4. UI показывает headword, лучший перевод, альтернативы и примеры.

## Поток Android PDF render

1. Пользователь выбирает PDF через системный picker.
2. `MainActivity` открывает `Uri`.
3. `PdfPageRenderer` создаёт `PdfRenderer` на `ParcelFileDescriptor`.
4. При смене страницы renderer рисует `Bitmap`.
5. `ImageView` показывает страницу.

## Runtime-каталоги

### Desktop

- данные: `~/.local/share/pdf_word_translator_mvp/`
- словари: `~/.local/share/pdf_word_translator_mvp/dictionaries/`
- настройки: `~/.local/share/pdf_word_translator_mvp/settings.json`
- кэш: `~/.cache/pdf_word_translator_mvp/`
- логи: `~/.cache/pdf_word_translator_mvp/logs/`

### Android prototype

- bundled dictionaries хранятся в `app/src/main/assets/dictionaries/`;
- при первом запуске они копируются в `filesDir/dictionaries/`.

## Границы текущего v7

- desktop остаётся самым полным и функциональным клиентом;
- Android branch пока даёт рендер PDF + ручной lookup, но не tap-to-word selection;
- Argos provider и online providers пока подключены только к desktop UI.
