# Android-статус v9

## Текущее состояние

Android-ветка входит в архив как **исходный Gradle-проект**, но не как уже собранный APK.

В `v9` сохранены и синхронизированы:

- `android-client/`;
- `src/pdf_word_translator/mobile_api.py`;
- bundled SQLite assets;
- Kotlin UI prototype;
- Chaquopy bridge;
- PdfRenderer prototype.

## Что уже реализовано в source branch

- открытие PDF через системный picker;
- базовый рендер PDF-страниц;
- переход между страницами;
- словарный lookup по введённому слову;
- переключение `EN → RU` / `RU → EN`;
- bootstrap встроенных SQLite-словарей из assets;
- вызов общего Python-слоя через `mobile_api.py`.

## Build identifiers

В Android module сейчас зафиксировано:

- `versionCode = 9`;
- `versionName = "0.9.0-v9-usability"`.

## Что не было выполнено в этой среде

Не проверялись:

- Gradle sync;
- реальная сборка APK;
- запуск на физическом устройстве;
- запуск на Android emulator.

Причина: в рабочем окружении не было Android SDK и системного Gradle.

## Как собирать дальше

Рекомендуемый путь:

1. открыть `android-client/` в Android Studio;
2. дать IDE синхронизировать проект;
3. проверить установленный Android SDK;
4. собрать `debug` APK из IDE.

## Следующие этапы Android-ветки

- tap-to-word selection по PDF;
- точная привязка слова к координатам Android viewer;
- отдельный Android UX для context translation;
- packaging pipeline с готовым wrapper и воспроизводимой сборкой APK.
