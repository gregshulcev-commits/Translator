# `mobile_api.py`

## Назначение

UI-free bridge для Android/mobile клиента.

Он отделяет словарный lookup от desktop GUI и даёт мобильному клиенту узкий, устойчивый и JSON-friendly интерфейс.

## Что делает модуль

- принимает список путей к SQLite-словарям;
- кеширует `DictionaryService` для повторных вызовов;
- возвращает summary подключённых словарных паков;
- выполняет lookup слова в выбранном направлении;
- сериализует результат в простой JSON payload для Kotlin/Chaquopy.

## Основные функции

- `bundled_dictionary_asset_names()` — список SQLite assets для Android bootstrap;
- `configure_dictionary_paths()` — конфигурирует активные словари;
- `current_service_summary()` — краткое состояние bridge-сервиса;
- `pack_infos()` — список metadata подключённых паков;
- `lookup_word()` — lookup слова;
- `reset_mobile_bridge()` — сброс кеша для тестов или завершения приложения.

## Что изменилось в v8

- bridge принимает только существующие **обычные файлы**;
- директории и другие non-file paths теперь отклоняются явной ошибкой;
- summary использует metadata реально открытого `DictionaryService`, а не косвенную повторную конфигурацию.

## Где используется

- `android-client/app/src/main/java/com/oai/pdfwordtranslator/DictionaryBridge.kt`
