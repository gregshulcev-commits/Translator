# `context_providers.py`

## Назначение

Provider layer для второй строки нижней панели.

## Доступные провайдеры

- `DisabledContextProvider`
- `ArgosContextProvider`
- `LibreTranslateContextProvider`
- `YandexCloudContextProvider`

## `ContextTranslationService`

Сервис:

- хранит активный provider id;
- пересобирает провайдеры при изменении настроек;
- выполняет перевод асинхронно;
- выдаёт `ContextTranslationResult` в UI callback.

## Почему это отдельный модуль

Словарный перевод слова и контекстный перевод предложения — разные задачи. Этот слой позволяет добавлять новые online / offline-провайдеры без изменений в document workflow.
