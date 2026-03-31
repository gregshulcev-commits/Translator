# Android client prototype (APK branch v7)

Эта директория содержит **первую Android-ветку** проекта.

Важный смысл ветки:

- текущий desktop GUI остаётся на **Tkinter**;
- Android-клиент строится **отдельно**, на нативном Android UI;
- словарный слой переиспользуется из Python через **Chaquopy**;
- PDF-страницы рендерятся нативно через `PdfRenderer`.

## Что уже есть

- `MainActivity.kt` — стартовый Android UI;
- `DictionaryBridge.kt` — вызов `pdf_word_translator.mobile_api` из Kotlin;
- `AssetBootstrap.kt` — копирование встроенных SQLite-словарей из assets в `filesDir`;
- `PdfPageRenderer.kt` — базовый рендер PDF-страниц;
- assets со стартовыми EN→RU и RU→EN словарями;
- Gradle-конфиги для `com.android.application`, Kotlin и `com.chaquo.python`.

## Что уже умеет APK-ветка

- открывать PDF через системный picker;
- рендерить страницы PDF внутри Android-клиента;
- листать страницы кнопками;
- выполнять словарный lookup по введённому слову;
- переключать направления `EN → RU` и `RU → EN`;
- использовать те же SQLite-словари, что и desktop-ветка.

## Что ещё не реализовано

- tap-to-word selection по PDF-странице;
- точное восстановление word coordinates внутри Android PDF viewer;
- OCR;
- контекстный neural translation provider внутри APK;
- packaging pipeline с готовым `gradlew` и собранным `apk` прямо в этом архиве.

## Почему ветка сделана именно так

Текущий desktop viewer завязан на Tkinter, а Android требует другой UI-стек. Поэтому в v7 проект разделён так:

- **desktop** продолжает развиваться как reference implementation;
- **android-client** получает собственный UI;
- общий словарный код остаётся в `src/pdf_word_translator/`;
- мобильный клиент использует узкий bridge-модуль `mobile_api.py`.

## Как открыть проект в Android Studio

1. Откройте Android Studio.
2. Выберите **Open** и укажите директорию `android-client/`.
3. Дайте IDE синхронизировать Gradle-проект.
4. Убедитесь, что Android SDK установлен, а `minSdk 24+` поддерживается выбранным эмулятором/устройством.
5. Запустите `app` на устройстве или эмуляторе.

## Сборка

В этом архиве **нет готового APK** и **нет Gradle wrapper**.

Это сознательно: в текущем окружении не было Android SDK и системного Gradle, поэтому в v7 включён **исходный код Android-ветки**, документация и bridge-слой, но не выполнена финальная сборка `apk`.

Рекомендуемый путь сборки:

- открыть `android-client/` в Android Studio;
- позволить IDE подтянуть Android Gradle Plugin и зависимости;
- после успешного sync собрать `debug` APK из IDE.

## Как связаны Android и desktop-ветки

Python-модуль `src/pdf_word_translator/mobile_api.py` не зависит от Tkinter и viewer-части. Он отвечает только за:

- подключение SQLite-словарей;
- краткое описание активных паков;
- lookup слова;
- JSON-friendly ответы для Kotlin.

Поэтому дальнейшее развитие Android-клиента можно делать отдельно, не ломая desktop GUI.
