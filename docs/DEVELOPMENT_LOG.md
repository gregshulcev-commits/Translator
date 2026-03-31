# Development log

## 2026-03-30 — MVP v8 merge

Сделано в рамках слияния двух исходных архивов:

- выбран `v7` как базовая ветка с Android/APK source branch;
- поверх неё перенесены исправления из fixed-ветки для `context_providers.py`, `main_window.py` и `settings_store.py`;
- сохранён `mobile_api.py` и Android layout из `v7`;
- сохранён read-only Argos help dialog с кнопкой копирования;
- возвращены responsive-исправления для каталога словарей, окна Argos и настройки провайдеров;
- возвращены улучшения LibreTranslate:
  - нормализация URL;
  - self-hosted default `http://127.0.0.1:5000`;
  - public-host API key diagnostic;
  - fallback JSON -> form-urlencoded;
  - расширенная диагностика ошибок;
- `settings.json` переведён на атомарное сохранение и ограниченные права доступа `0600` на POSIX;
- external plugins переведены в режим explicit opt-in через `PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS=1`;
- `mobile_api.py` усилен проверкой dictionary paths на regular files;
- добавлены тесты на LibreTranslate/UI bugfixes и security hardening;
- документация синхронизирована под `v8`.

## Источник версии

`v8` выбран как следующая проектная версия после максимальной версии, найденной в исходных архивах (`v7`).
