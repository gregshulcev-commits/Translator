# Отчёт о тестировании

## 1. Pytest

Результат:

- **16/16 тестов проходят**.

Покрыты:

- config;
- normalizer;
- SQLite dictionary;
- FreeDict importer;
- TXT / FB2 plugins;
- dictionary installer helpers;
- workflow;
- реальные PDF пользователя;
- settings store.

См. `docs/test_artifacts/pytest_output.txt`.

## 2. GUI smoke test

Проверено:

- окно создаётся;
- многостраничный PDF открывается;
- слово `configuration` переводится корректно;
- scroll двигает viewport;
- `Ctrl + колесо` меняет zoom.

См. `docs/test_artifacts/smoke_output.txt`.

## 3. Реальные PDF пользователя

Проверено в `tests/test_real_pdfs.py`:

- загруженные PDF имеют текстовый слой;
- PyMuPDF может получить по ним word tokens;
- на реальном PDF находится слово `driver`.

## 4. Установщик словарей

В sandbox внешняя сеть для скачивания FreeDict была недоступна, поэтому проверен fallback-сценарий:

- встроенный технический словарь собирается корректно;
- приложение продолжает работать даже без скачанного общего словаря;
- GUI и CLI импорт локальных паков покрыт отдельными тестами.

См. `docs/test_artifacts/install_default_output.txt`.

## 5. CMake targets

Проверено:

- `cmake --build build --target test` — успешно;
- `cmake --build build --target install_dictionaries` — успешно, с корректным fallback при отсутствии сети.

См. `docs/test_artifacts/cmake_test_output.txt` и `docs/test_artifacts/cmake_install_dictionaries_output.txt`.
