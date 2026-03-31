# Android-статус v10

## Общий статус

Android-ветка по-прежнему включена в архив как **исходный код**, а не как собранный APK.

В `v10` сохранены и синхронизированы:

- `android-client/`;
- `src/pdf_word_translator/mobile_api.py`;
- Kotlin UI prototype;
- Chaquopy bridge;
- PdfRenderer prototype;
- bundled SQLite assets.

## Что умеет Android branch сейчас

- открывать PDF через системный picker;
- выполнять базовый рендер страниц через `PdfRenderer`;
- листать страницы;
- выполнять dictionary lookup по введённому слову;
- переключать направление `EN → RU` / `RU → EN`;
- использовать общую Python dictionary logic через `mobile_api.py`.

## Что пока не закрыто

- tap-to-word selection в PDF viewer;
- финальная воспроизводимая APK-сборка в текущем рабочем окружении;
- готовый Gradle wrapper внутри поставки.

## Маркеры версии Android branch

- `versionCode = 10`;
- `versionName = "1.0.0-v10-install-management"`.

## Почему APK не собран в этом архиве

Причина не изменилась: в текущем рабочем окружении не было Android SDK и системного Gradle, поэтому в `v10` включён **исходный код Android-ветки**, документация и bridge-слой, но не выполнена финальная сборка `apk`.
