# Отчёт о тестировании v10

## 1. Regression suite

Команда:

```bash
PYTHONPATH=src pytest
```

Результат:

- **60 passed, 2 skipped**.

Покрыты в том числе:

- document / dictionary plugins;
- text normalization;
- context extraction;
- settings store;
- GUI-friendly dictionary/Argos helpers;
- install/update manager helper functions.

## 2. GUI smoke test

Команда:

```bash
xvfb-run -a env PYTHONPATH=src python3 tests/smoke_gui.py
```

Результат:

- smoke test прошёл успешно;
- приложение открывается;
- встроенные словари подключаются;
- PDF открывается без падения.

## 3. Ручной review в рамках v10 install/update-итерации

Проверено:

- наличие root-level скриптов `install_app.sh`, `uninstall_app.sh`, `update_app.sh`, `uninstall_previous_v9.sh`;
- отделение installed payload от runtime data;
- наличие installation manifest;
- наличие миграционного сценария для предыдущей установки `v9`;
- совместимость новой схемы с будущим переходом на RPM;
- отделение runtime requirements от dev requirements.

## 4. Вывод

Source `v10` стабилен для desktop-ветки, содержит Android source branch, проходит Python regression suite и GUI smoke test, а также добавляет управляемую схему установки, удаления и обновления без отката прежних исправлений usability-итерации.
