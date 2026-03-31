# Отчёт о тестировании

## 1. Pytest

Результат:

- **28/28 тестов проходят**, **2 пропущены** как ожидаемые environment-specific сценарии.

Покрыты:

- config;
- normalizer;
- SQLite dictionary;
- FreeDict importer;
- TXT / FB2 plugins;
- dictionary installer helpers;
- workflow;
- переключение направления EN ↔ RU;
- split compound tokens (`diagnostic\measurement`);
- реальные PDF пользователя;
- settings store;
- регрессии v5;
- Argos model manager и provider hints.

## 2. GUI smoke test

Проверено:

- окно создаётся;
- многостраничный PDF открывается;
- слово `configuration` переводится корректно;
- scroll двигает viewport;
- `Ctrl + колесо` меняет zoom;
- compact help panel не показывает сырое предложение из документа.

## 3. Реальные PDF пользователя

Проверено в `tests/test_real_pdfs.py`:

- загруженные PDF имеют текстовый слой;
- PyMuPDF может получить по ним word tokens;
- на реальном PDF находится слово `driver`.

## 4. Что дополнительно покрыто в v6

- отсутствие `argostranslate` не ломает приложение, а даёт мягкий статус;
- GUI/CLI сценарии установки Argos-моделей используют общий helper layer;
- локальный импорт `.argosmodel` обновляет статус направления;
- провайдер `Argos (офлайн)` возвращает понятную подсказку, если модель ещё не установлена.
