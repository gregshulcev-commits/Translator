# Android-статус v7

## Короткий вывод

В v7 проект перешёл от «Android как следующая идея» к **реальной APK-ветке с исходным кодом**.

В архив теперь входят:

- `android-client/` — отдельный Android Gradle project;
- `src/pdf_word_translator/mobile_api.py` — bridge-модуль для мобильного клиента;
- встроенные starter SQLite-словари как Android assets.

Готовый release/debug APK в архив **не включён**: в рабочем окружении не было Android SDK и системного Gradle, поэтому ветка оформлена как **исходный проект для Android Studio**, а не как уже собранный бинарь.

## Почему Android ветка отдельная

Текущий desktop viewer построен на **Tkinter**. Для Android это не является рабочим UI-путём, поэтому v7 делает правильное архитектурное разделение:

- **desktop** остаётся reference implementation;
- **android-client** получает нативный Android UI;
- общий словарный слой остаётся в `src/pdf_word_translator/`;
- Android вызывает Python только через узкий bridge `mobile_api.py`.

## Что уже реализовано

### 1. Android project skeleton

Есть:

- `settings.gradle.kts`
- `build.gradle.kts`
- `gradle.properties`
- `app/build.gradle.kts`
- `AndroidManifest.xml`
- `activity_main.xml`

### 2. Kotlin слой

Есть:

- `MainActivity.kt` — основной UI;
- `DictionaryBridge.kt` — вызов Python через Chaquopy;
- `AssetBootstrap.kt` — копирование SQLite-словарей из assets;
- `PdfPageRenderer.kt` — нативный рендер PDF-страниц.

### 3. Python bridge

Есть модуль:

- `src/pdf_word_translator/mobile_api.py`

Он умеет:

- принимать пути к SQLite-словарям;
- кешировать словарный service;
- возвращать краткое summary подключённых словарей;
- выполнять lookup слова;
- отдавать JSON-friendly ответ для Kotlin.

### 4. Bundled assets

Android-клиент уже содержит:

- `starter_dictionary.sqlite`
- `starter_dictionary_ru_en.sqlite`

Это позволяет запустить первый Android prototype без отдельного импорта словарей вручную.

## Что уже умеет Android prototype

- открыть PDF через системный picker;
- отрендерить страницу PDF;
- листать страницы кнопками;
- ввести слово руками и получить словарный перевод;
- переключить `EN → RU` / `RU → EN`;
- использовать тот же словарный SQLite-формат, что и desktop-приложение.

## Что ещё не реализовано

- tap-to-word selection по PDF;
- координатный text layer для Android viewer;
- OCR;
- контекстный provider layer внутри APK;
- GUI-менеджер Argos-моделей внутри Android-клиента;
- готовый `gradlew` wrapper и автоматический pipeline сборки внутри этого архива.

## Как открыть в Android Studio

1. Откройте директорию `android-client/`.
2. Дождитесь sync проекта.
3. Проверьте, что Android SDK установлен.
4. Соберите `debug` APK из IDE.

## Следующий технический шаг для Android

Самый важный следующий этап не «ещё один красивый экран», а именно **text selection / tap-to-word pipeline** для PDF:

1. определить источник word/token coordinates в Android viewer;
2. привязать их к render scale и scroll state;
3. вызывать тот же `mobile_api.lookup_word_json()` уже не по введённому слову, а по токену под пальцем;
4. после этого подключать контекстный перевод как отдельный слой.
