# Тестирование

## Что покрыто

### Unit-тесты

- нормализация словоформ;
- lookup в SQLite-словаре;
- import CSV / FreeDict TEI / SQLite packs;
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
- понятные подсказки провайдера при отсутствии модели;
- **mobile_api bridge**: конфигурация путей, summary и lookup;
- **v7 regression** для Argos help dialog;
- **Android branch layout**: наличие Gradle/Kotlin/asset-файлов и Chaquopy-конфигурации.

### Интеграционные тесты

- чтение и токенизация приложенных реальных PDF;
- поиск токена `driver` в пользовательском PDF.

### GUI smoke test

- создание desktop-окна;
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

## Актуальный результат в v7

- `pytest`: **37 passed, 2 skipped**;
- GUI smoke test: проходит.

## Что не проверяется автоматически

- сборка Android APK;
- запуск Android UI на устройстве/эмуляторе;
- Gradle sync и Android Studio integration;
- real tap-to-word selection внутри Android PDF viewer, потому что этот слой ещё не реализован.
