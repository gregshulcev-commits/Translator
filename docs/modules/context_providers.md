# `context_providers.py`

## Назначение

Provider layer для второй строки нижней панели.

## Доступные провайдеры

- `DisabledContextProvider`
- `ArgosContextProvider`
- `LibreTranslateContextProvider`
- `YandexCloudContextProvider`

## `ArgosContextProvider`

В v6 провайдер стал более «бережным» к пользователю:

- перед переводом он вызывает `argos_direction_ready(direction)`;
- если `argostranslate` не установлен, возвращается понятная подсказка;
- если runtime есть, но модели для нужного направления нет, пользователь получает сообщение с путём **Перевод → Офлайн-модели Argos…**;
- только после проверки готовности вызывается `argostranslate.translate.translate()`.

То есть ошибка «нет модели / нет optional dependency» теперь обрабатывается на уровне UX, а не только как runtime exception.

## `YandexCloudContextProvider`

Провайдер требует:

- `Folder ID`;
- `API key` или `IAM token`.

Если `Folder ID` не указан, запрос даже не уходит в сеть.

## `ContextTranslationService`

Сервис:

- хранит активный provider id;
- пересобирает провайдеры при изменении настроек;
- выполняет перевод асинхронно;
- выдаёт `ContextTranslationResult` в UI callback.

В связке с `MainWindow` результат теперь сначала кладётся в очередь, а потом применяется в главном Tk-потоке.

## Почему это отдельный модуль

Словарный перевод слова и контекстный перевод предложения — разные задачи. Этот слой позволяет добавлять новые online / offline-провайдеры без изменений в document workflow и без переписывания viewer-а.
