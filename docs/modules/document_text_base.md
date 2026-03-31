# `document_text_base.py`

## Назначение

Общая база для reflowable text formats (`TXT`, `FB2`).

## Главная идея

TXT/FB2 не имеют готовых page coordinates, как PDF. Поэтому модуль:

1. принимает текстовые paragraph blocks;
2. раскладывает их по synthetic pages;
3. рисует страницы через Pillow;
4. создаёт `WordToken` с координатами каждого слова.

Это позволяет reuse-ить тот же click-to-translate workflow, что и для PDF.

## Основные сущности

### `TextParagraph`

Текстовый блок с простым стилем (`body` / `title`).

### `_TextPage`

Внутренняя структура страницы:

- изображение страницы;
- tokens;
- sentence_words;
- page_text.

### `TextDocumentSession`

Реализация `DocumentSession` для текстовых форматов.

Поддерживает:

- `render_page()`
- `get_tokens()`
- `find_token_at()`
- `get_sentence_for_token()`
- `search()`

## Ограничения

- pages synthetic, а не оригинальные;
- typography простая и ориентирована на читаемость, а не на book-quality rendering.
