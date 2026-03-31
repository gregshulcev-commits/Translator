# Тестирование MVP v10

## Автоматические проверки

### Python regression suite

Запуск:

```bash
python3 -m pip install -r requirements-dev.txt
PYTHONPATH=src pytest
```

Что покрывается:

- базовая конфигурация и пути;
- нормализация текста;
- словарные плагины и импорт;
- работа с контекстом;
- GUI-friendly сценарии Argos/runtime management;
- безопасное управление пользовательскими словарями;
- служебные функции install/update manager.

### GUI smoke test

Запуск:

```bash
xvfb-run -a env PYTHONPATH=src python3 tests/smoke_gui.py
```

Что проверяется:

- создание окна приложения;
- загрузка встроенных словарей;
- открытие тестового PDF;
- отсутствие падения на основном desktop-сценарии.

## Текущее состояние на исходниках v10

- `pytest`: **60 passed, 2 skipped**;
- GUI smoke test: проходит;
- Android-ветка проверена на уровне структуры проекта и Python bridge;
- финальная APK-сборка в этой среде не выполнялась.

## Артефакты

- `docs/test_artifacts/pytest_output.txt`
- `docs/test_artifacts/smoke_output.txt`
