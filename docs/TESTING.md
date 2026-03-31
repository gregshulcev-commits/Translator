# Тестирование

## Что покрыто

### Unit-тесты

- нормализация словоформ;
- lookup в SQLite-словаре;
- импорт FreeDict TEI;
- импорт CSV/копирование SQLite-паков;
- корректность путей конфигурации;
- PDF provider на синтетическом документе;
- TXT plugin;
- FB2 plugin;
- workflow от клика до перевода;
- сохранение UI settings;
- регрессии v5 по highlight/scroll, Treeview rowheight, async context queue и Yandex folder validation;
- Argos runtime detection;
- определение статуса EN↔RU моделей Argos;
- установка модели Argos по направлению;
- импорт локального `.argosmodel`;
- понятные подсказки провайдера при отсутствии модели.

### Интеграционные тесты

- чтение и токенизация приложенных реальных PDF;
- поиск токена `driver` в `IRIO_EPICS_Device_Driver_User's_Manual__RAJ9P8_v1_7.pdf`.

### GUI smoke test

- создание окна;
- открытие многостраничного PDF;
- клик по слову;
- обновление нижней панели перевода;
- scroll документа колесом мыши;
- zoom по `Ctrl + колесо мыши`.

## Как запускать

```bash
source .venv/bin/activate
PYTHONPATH=src pytest
xvfb-run -a env PYTHONPATH=src python tests/smoke_gui.py
```

## Актуальный результат в этой сборке

- `pytest`: **28 passed, 2 skipped**;
- GUI smoke test: проходит.
