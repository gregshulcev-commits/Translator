# Отчёт о тестировании v8

## Дата

- 2026-03-30

## Проверенный объём

### 1. Автоматические Python-тесты

Запуск:

```bash
PYTHONPATH=src pytest
```

Результат:

- **49 passed, 2 skipped**.

В проверку вошли:

- document plugins и dictionary workflow;
- Argos manager;
- `mobile_api.py`;
- Android branch layout checks;
- LibreTranslate/UI regression tests;
- security hardening tests.

### 2. Desktop GUI smoke test

Запуск:

```bash
xvfb-run -a env PYTHONPATH=src python tests/smoke_gui.py
```

Результат:

- тест проходит без падения;
- приложение открывает тестовый PDF;
- словарный lookup и базовый viewer workflow сохраняются рабочими.

### 3. Ручной code review в рамках merge

Проверены и исправлены:

- откат bugfix-ветки в `context_providers.py`;
- откат bugfix-ветки в `main_window.py`;
- default URL и устойчивость `settings_store.py`;
- загрузка external plugins по умолчанию;
- обработка non-file путей в `mobile_api.py`.

## Что не проверено в этой среде

- Gradle sync Android-проекта;
- финальная сборка APK;
- запуск Android-клиента на устройстве;
- реальный сетевой вызов cloud providers с production credentials.

## Вывод

Merged source `v8` стабилен для desktop-ветки, содержит Android source branch, проходит Python regression suite и smoke test, а также включает дополнительные исправления по безопасности и устойчивости.
