# Android client prototype (APK branch v10)

Эта директория содержит **отдельную Android-ветку** проекта `pdf_word_translator_mvp_v10`.

## Что находится внутри

- Kotlin UI prototype;
- Chaquopy bridge к Python-коду словарного ядра;
- PdfRenderer-based viewer prototype;
- bootstrap встроенных SQLite-словарей из assets.

## Что обновлено в v10

- Android markers синхронизированы с общей версией проекта;
- `versionCode = 10`;
- `versionName = "1.0.0-v10-install-management"`;
- desktop-часть проекта переведена на новую install/update архитектуру, Android-исходники оставлены как source branch без изменений модели взаимодействия с `mobile_api.py`.

## Что уже умеет ветка

- открыть PDF через системный picker;
- отрендерить страницу;
- переключать страницы;
- выполнить lookup по введённому слову;
- переключать направление `EN ↔ RU`;
- использовать bundled SQLite dictionaries.

## Что ещё не закрыто

- tap-to-word selection внутри PDF viewer;
- финальная reproducible APK-сборка;
- готовый release APK в архиве.

## Почему в архиве нет APK

В текущем рабочем окружении не было Android SDK и системного Gradle, поэтому в `v10` включён **исходный код Android-ветки**, документация и bridge-слой, но не выполнена финальная сборка `apk`.
