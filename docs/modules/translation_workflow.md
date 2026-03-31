# `translation_workflow.py`

## Назначение

Связывает клик по странице, выбор токена, извлечение контекста и lookup слова.

## `TranslationViewModel`

Содержит:

- `token`
- `context`
- `lookup`

## Основной метод

`translate_point(page_index, x, y)`:

1. ищет токен по координате;
2. получает контекст;
3. выполняет lookup;
4. возвращает единый view model для UI.
