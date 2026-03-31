# plugins/document_pdf_pymupdf.py

## Назначение

Реализация document plugin для PDF на базе PyMuPDF.

## Функции

- открыть PDF;
- извлечь слова и координаты;
- рендерить страницы;
- найти слово по точке;
- получить контекст;
- выполнить поиск по документу.

## Ключевые классы

- `PyMuPdfDocumentPlugin`
- `PyMuPdfDocumentSession`

## Почему выбран PyMuPDF

Он одновременно решает две критичные задачи MVP:

- быстрый рендер PDF;
- доступ к `page.get_text("words")` с геометрией слов.
