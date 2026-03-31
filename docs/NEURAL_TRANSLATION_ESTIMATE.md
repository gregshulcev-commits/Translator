# Neural/context translation layer: статус для v8

## Что остаётся неизменным

Для проекта по-прежнему верно главное архитектурное решение:

- словарный lookup слова — базовый сценарий;
- контекстный/нейронный перевод — отдельный optional provider layer;
- офлайн-модели не должны быть жёстко встроены в ядро lookup;
- Android не должен тащить на себя desktop Tkinter viewer.

## Практический вывод для v8

В `v8` это решение подтверждено и кодом, и merge-структурой:

- desktop использует `ContextTranslationService` как отдельный слой;
- Argos models управляются отдельным lifecycle helper;
- `mobile_api.py` обслуживает Android только на уровне словарного bridge, без desktop UI и без жёсткой привязки к provider layer.

## Что это даёт

- desktop остаётся offline-first и словарным по умолчанию;
- optional providers можно развивать отдельно;
- Android может развиваться как собственный клиент поверх общего словарного ядра.

## Следующий реалистичный этап

Развивать offline/context translation дальше, но не размывать базовый click-to-translate workflow и не превращать проект в «только нейронный переводчик».
