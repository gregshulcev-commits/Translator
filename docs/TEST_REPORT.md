# Отчёт о тестировании v9

## Дата

- 2026-03-30

## Проверенный объём

### 1. Автоматические Python-тесты

Запуск:

```bash
PYTHONPATH=src pytest
```

Результат:

- **58 passed, 2 skipped**.

В проверку вошли:

- document plugins и dictionary workflow;
- Argos manager;
- compact context extraction;
- dictionary manager;
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
- словарный lookup и базовый viewer workflow сохраняются рабочими;
- интеграция нового окна настроек не ломает desktop bootstrap.

### 3. Ручной review в рамках v9 usability-итерации

Проверены и обновлены:

- `install_app.sh` и сценарий desktop integration;
- `settings_dialog.py`;
- `dictionary_manager.py`;
- `context_extraction.py`;
- интеграция новых UX-сценариев в `main_window.py`.

## Что не проверено в этой среде

- Gradle sync Android-проекта;
- финальная сборка APK;
- запуск Android-клиента на устройстве;
- реальный сетевой вызов cloud providers с production credentials.

## Вывод

Source `v9` стабилен для desktop-ветки, содержит Android source branch, проходит Python regression suite и GUI smoke test, а также добавляет установщик приложения, отдельное окно настроек и GUI-управление словарями / Argos без отката прежних исправлений.
