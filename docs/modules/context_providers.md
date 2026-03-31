# `context_providers.py`

## Назначение

Provider layer для второй строки нижней панели desktop UI.

## Доступные провайдеры

- `DisabledContextProvider`
- `ArgosContextProvider`
- `LibreTranslateContextProvider`
- `YandexCloudContextProvider`

## `ArgosContextProvider`

Провайдер перед реальным вызовом проверяет `argos_direction_ready(direction)`.

Если runtime или модель не готовы, пользователь получает понятное сообщение вместо неясной runtime-ошибки.

## `LibreTranslateContextProvider`

В `v8` для него важны следующие вещи:

- URL сначала нормализуется;
- можно указывать как базовый адрес, так и полный endpoint;
- public-host `libretranslate.com` требует API key;
- запрос сначала отправляется как JSON;
- при несовместимости сервера автоматически выполняется fallback на `application/x-www-form-urlencoded`;
- HTTP-ошибки стараются извлечь текст из JSON-ответа.

## `YandexCloudContextProvider`

Провайдер требует:

- `Folder ID`;
- `API key` или `IAM token`.

Если конфигурация неполная, запрос даже не уходит в сеть.

## `ContextTranslationService`

Сервис:

- хранит активный provider id;
- пересобирает провайдеры при изменении настроек;
- умеет давать diagnostics через `provider_status()`;
- выполняет перевод асинхронно;
- возвращает `ContextTranslationResult` в UI callback.

## Почему это отдельный модуль

Словарный перевод слова и контекстный перевод предложения — разные задачи. Этот слой позволяет развивать online/offline providers без переписывания document workflow и без вмешательства в Android bridge.
