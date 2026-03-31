# Тестирование MVP v8

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
- LibreTranslate URL normalization и diagnostics;
- fallback JSON -> form-urlencoded;
- Yandex provider configuration checks.

### UI regressions

- Argos help dialog;
- responsive helper-функции `MainWindow`;
- Android branch layout smoke checks;
- mobile bridge tests.

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
- отсутствие падения после `v8` merge.

## Что не покрыто в этой среде

- реальная сборка Android APK;
- запуск на устройстве/эмуляторе;
- end-to-end проверка cloud providers с реальными сетевыми credentials.

## Актуальный результат

На зафиксированном merged source `v8`:

- `pytest`: **49 passed, 2 skipped**;
- desktop GUI smoke test: проходит.
