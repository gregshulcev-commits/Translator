# `plugin_api.py`

## Назначение

Абстрактные интерфейсы плагинов документа и словаря.

## `DocumentSession`

Контракт открытого документа:

- `page_count()`
- `render_page()`
- `get_tokens()`
- `find_token_at()`
- `get_sentence_for_token()`
- `search()`

## `DocumentPlugin`

Контракт формата документа.

## `DictionaryPlugin`

Контракт словаря:

- `plugin_id()`
- `lookup()`
- `available_entries()`
