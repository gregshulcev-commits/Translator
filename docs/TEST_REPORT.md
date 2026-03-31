# Отчёт о тестировании

## 1. Pytest

Результат:

- **19/19 тестов проходят**.

Покрыты:

- config;
- normalizer;
- SQLite dictionary;
- FreeDict importer;
- TXT / FB2 plugins;
- dictionary installer helpers;
- workflow;
- переключение направления EN ↔ RU;
- split compound tokens (`diagnostic\measurement`);
- реальные PDF пользователя;
- settings store.

## 2. GUI smoke test

Проверено:

- окно создаётся;
- многостраничный PDF открывается;
- слово `configuration` переводится корректно;
- scroll двигает viewport;
- `Ctrl + колесо` меняет zoom;
- compact help panel не показывает сырое предложение из документа.

## 3. Реальные PDF пользователя

Проверено в `tests/test_real_pdfs.py`:

- загруженные PDF имеют текстовый слой;
- PyMuPDF может получить по ним word tokens;
- на реальном PDF находится слово `driver`.

## 4. Установщик словарей

В sandbox внешняя сеть для скачивания FreeDict была недоступна, поэтому проверен fallback-сценарий:

- встроенные словари собираются корректно;
- bundled technical / literary packs устанавливаются корректно;
- приложение продолжает работать даже без скачанного общего словаря;
- GUI и CLI импорт локальных паков покрыт отдельными тестами.

## 5. CMake targets

Проверено:

- `cmake --build build --target test` — успешно;
- `cmake --build build --target install_dictionaries` — успешно, с корректным fallback при отсутствии сети.
