# Тестирование

## Что покрыто

### Unit-тесты

- нормализация словоформ;
- lookup в SQLite-словаре;
- импорт FreeDict TEI;
- корректность путей конфигурации;
- PDF provider на синтетическом документе;
- workflow от клика до перевода.

### Интеграционные тесты

- чтение и токенизация приложенных реальных PDF;
- поиск токена `driver` в `IRIO_EPICS_Device_Driver_User's_Manual__RAJ9P8_v1_7.pdf`.

### GUI smoke test

- создание окна;
- открытие PDF;
- клик по слову;
- обновление нижней панели перевода.

## Как запускать

```bash
source .venv/bin/activate
PYTHONPATH=src pytest
xvfb-run -a python tests/smoke_gui.py
```

## Актуальный результат в этой сборке

- `pytest`: 11 тестов, все проходят;
- GUI smoke test: проходит;
- установщик словаря протестирован в sandbox в fallback-режиме без внешней сети.

Сырые артефакты лежат в `docs/test_artifacts/`.

## Дополнительно проверено через CMake

```bash
cmake -S . -B build
cmake --build build --target test
cmake --build build --target install_dictionaries
```

Логи сохранены в `docs/test_artifacts/cmake_test_output.txt` и `docs/test_artifacts/cmake_install_dictionaries_output.txt`.
