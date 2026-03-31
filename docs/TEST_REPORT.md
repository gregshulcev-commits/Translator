# Отчёт о тестировании v7

## 1. Pytest

Результат:

- **37 тестов проходят**;
- **2 теста пропущены** как ожидаемые environment-specific сценарии.

Покрыты:

- config;
- normalizer;
- SQLite dictionary;
- FreeDict importer;
- TXT / FB2 plugins;
- dictionary installer helpers;
- workflow;
- переключение направления EN ↔ RU;
- реальные PDF пользователя;
- settings store;
- регрессии v5;
- Argos model manager и provider hints;
- `mobile_api.py`;
- v7 regression для Argos help dialog;
- Android branch layout smoke checks.

## 2. GUI smoke test (desktop)

Проверено:

- окно создаётся;
- многостраничный PDF открывается;
- слово `configuration` переводится корректно;
- scroll двигает viewport;
- `Ctrl + колесо` меняет zoom;
- нижняя панель не ломается после v7-изменений.

## 3. Android branch

Автоматически проверено в Python-тестах:

- присутствуют ключевые файлы `android-client/`;
- в Android module включён `com.chaquo.python`;
- Python source подключается из общего `../../src`;
- bundled SQLite assets лежат на ожидаемом месте.

Не проверено автоматически в этой среде:

- Gradle sync;
- реальная сборка APK;
- запуск на устройстве/эмуляторе.

Причина проста: в рабочем окружении не было Android SDK и системного Gradle.

## 4. Вывод

v7 стабилен для desktop-ветки и уже содержит **исходный код Android branch** с bridge-слоем, документацией и тестовым покрытием Python-части.
