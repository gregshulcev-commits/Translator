# Тестирование MVP v9

## Базовый набор команд

```bash
source .venv/bin/activate
PYTHONPATH=src pytest
xvfb-run -a env PYTHONPATH=src python tests/smoke_gui.py
```

## Что покрывает `pytest`

### Desktop core

- document plugins для PDF / TXT / FB2;
- dictionary lookup;
- direction switching `EN ↔ RU`;
- workflow и регрессии предыдущих итераций.

### Provider layer

- Argos manager helpers;
- GUI-friendly установка optional runtime Argos;
- LibreTranslate URL normalization и diagnostics;
- fallback JSON -> form-urlencoded;
- Yandex provider configuration checks.

### UX / settings / dictionaries

- compact context extraction;
- безопасное удаление пользовательских словарей;
- сохранение и нормализация UI/provider settings.

### Security hardening

- restricted permissions для `settings.json`;
- external plugins disabled-by-default и explicit enable path;
- `mobile_api.py` rejects non-file dictionary paths.

## GUI smoke test

`tests/smoke_gui.py` проверяет:

- создание окна;
- открытие PDF;
- базовый click-to-translate сценарий;
- scroll / zoom;
- отсутствие падения после `v9` usability-обновления.

## Что не покрыто в этой среде

- реальная сборка Android APK;
- запуск на устройстве/эмуляторе;
- end-to-end проверка cloud providers с реальными credentials.

## Актуальный результат

На исходниках `v9`:

- `pytest`: **58 passed, 2 skipped**;
- desktop GUI smoke test: проходит.
