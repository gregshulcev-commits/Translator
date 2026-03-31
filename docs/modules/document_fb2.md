# `document_fb2.py`

## Назначение

Document plugin для FictionBook 2 (`.fb2`).

## Как работает

- парсит XML;
- извлекает `book-title`, `title`, `p`, `subtitle` и части body/section;
- сводит их к `TextParagraph`;
- передаёт в `TextDocumentSession`.

## Что игнорируется

- изображения;
- сложная decorative markup;
- точная типографика исходного FB2.

## Цель

Дать читаемый текстовый просмотр и click-to-translate, а не полный FB2 reader.
