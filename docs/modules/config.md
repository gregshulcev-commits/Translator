# config.py

## Назначение

Единая точка для путей проекта и runtime configuration.

## Основные элементы

- `PROJECT_ROOT`
- `DATA_ROOT`
- `DEFAULT_STARTER_CSV`
- `DEFAULT_STARTER_DB`
- `AppConfig`

## Почему модуль нужен отдельно

Чтобы UI, tests и utilities не размазывали логику путей по всему коду.
