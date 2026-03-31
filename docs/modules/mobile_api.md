# `mobile_api.py`

## Назначение

Новый модуль v7 для Android/API-ветки.

Он отделяет словарный lookup от desktop GUI и даёт мобильному клиенту узкий, устойчивый и JSON-friendly интерфейс.

## Что делает модуль

- принимает список путей к SQLite-словарям;
- кеширует `DictionaryService` для повторных вызовов;
- возвращает summary подключённых словарных паков;
- выполняет lookup слова в выбранном направлении;
- сериализует результат в простой JSON payload для Kotlin/Chaquopy.

## Почему он нужен

Android-клиент не должен импортировать `MainWindow`, document viewer или Tkinter-слой.

`mobile_api.py` позволяет переиспользовать:

- `DictionaryService`;
- `CompositeDictionaryPlugin`;
- `SQLiteDictionaryPlugin`;
- модели словаря;

без зависимости от desktop UI.

## Основные функции

- `bundled_dictionary_asset_names()` — список SQLite assets, которые Android bootstrap должен скопировать в `filesDir`;
- `configure_dictionary_paths()` — конфигурирует активные словари;
- `current_service_summary()` — краткое состояние bridge-сервиса;
- `pack_infos()` — список metadata подключённых паков;
- `lookup_word()` — lookup слова;
- JSON-обёртки `*_json()` для вызова из Kotlin.

## Поведение

- словари открываются лениво и кешируются;
- при смене набора путей старый cached service закрывается;
- для Kotlin подготовлены JSON-friendly payload-ы без привязки к Python dataclass-объектам.

## Где используется

- `android-client/app/src/main/java/com/oai/pdfwordtranslator/DictionaryBridge.kt`
