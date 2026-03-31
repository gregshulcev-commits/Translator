# `models.py`

## Назначение

Набор стабильных dataclass-моделей, которыми обмениваются UI, сервисы и плагины.

## Основные модели

### `WordToken`

Слово на странице PDF:

- `token_id`
- `text`
- `normalized_text`
- `page_index`
- `rect`
- `block_no`
- `line_no`
- `word_no`

### `SearchHit`

Результат поиска по документу.

### `DocumentSentence`

Контекстная строка или предложение вокруг выбранного слова.

### `DictionaryEntry`

Запись словаря:

- headword
- transcription
- best_translation
- alternative_translations
- examples
- notes

### `LookupResult`

Ответ словаря с информацией о стратегии поиска и списке проверенных форм.
