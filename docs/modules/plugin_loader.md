# `plugin_loader.py`

## Назначение

Собирает набор доступных плагинов на старте приложения.

## Что загружается

### Документы

- `PyMuPdfDocumentPlugin`

### Словари

- встроенный технический словарь из `data/starter_dictionary.sqlite`;
- все `*.sqlite` паки из `runtime_dictionary_dir`;
- итоговый composite plugin, который ищет по ним последовательно.

## Приоритет словарей

1. встроенный technical glossary;
2. пользовательские SQLite-паки.

## Внешние плагины

Поддерживаются Python-файлы из каталога `~/.local/share/pdf_word_translator_mvp/plugins/`, если они экспортируют `register_plugins()`.
