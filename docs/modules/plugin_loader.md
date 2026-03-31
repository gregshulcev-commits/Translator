# `plugin_loader.py`

## Назначение

Собирает набор доступных plugins на старте приложения.

## Что загружается

### Document plugins

- `PyMuPdfDocumentPlugin`
- `PlainTextDocumentPlugin`
- `Fb2DocumentPlugin`

### Dictionary plugins

- встроенный технический словарь из `data/starter_dictionary.sqlite`;
- все `*.sqlite` паки из `runtime_dictionary_dir`;
- итоговый `CompositeDictionaryPlugin`.

## Особенность v3

Появился метод `create_dictionary_plugin()`, который заново строит composite plugin из текущих словарных паков. Это используется GUI после установки нового словаря без перезапуска приложения.

## Внешние плагины

Поддерживаются Python-файлы из:

```text
~/.local/share/pdf_word_translator_mvp/plugins/
```

если они экспортируют `register_plugins()`.
