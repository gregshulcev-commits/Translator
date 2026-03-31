# Система плагинов

## Что считается плагином в MVP

В текущем MVP плагинами считаются два типа расширений:

- **DocumentPlugin** — открывает документ определённого формата;
- **DictionaryPlugin** — выполняет lookup слова.

Интерфейсы описаны в `src/pdf_word_translator/plugin_api.py`.

## DocumentPlugin

Минимальный контракт:

- `plugin_id()`
- `supported_extensions()`
- `can_open(path)`
- `open(path)` -> `DocumentSession`

### Реализованные document plugins

- `PyMuPdfDocumentPlugin` — PDF
- `PlainTextDocumentPlugin` — TXT
- `Fb2DocumentPlugin` — FB2

## DictionaryPlugin

Минимальный контракт:

- `plugin_id()`
- `lookup(word)` -> `LookupResult`
- `available_entries()`

### Реализованные dictionary plugins

- `SQLiteDictionaryPlugin`
- `CompositeDictionaryPlugin`

## Built-in plugins

Загружаются всегда:

- `document.pdf.pymupdf`
- `document.txt`
- `document.fb2`
- composite dictionary plugin, который объединяет встроенный глоссарий и все найденные SQLite-паки

## External plugins

Папка для внешних Python-плагинов:

```text
~/.local/share/pdf_word_translator_mvp/plugins/
```

Каждый внешний `*.py` файл может определить функцию:

```python
def register_plugins():
    return [my_plugin_instance]
```

Внешние plugins кешируются `PluginLoader` и учитываются при `create_dictionary_plugin()`, поэтому hot-reload словарного слоя не теряет внешние dictionary plugins.

## Почему словарные паки реализованы как SQLite, а не как Python-плагины

Словарь — это в первую очередь **данные**, а не код. Поэтому для словарей в MVP выбран гибридный подход:

- логика lookup — в Python-плагине;
- словарные базы — в `*.sqlite` паках.

Так проще добавлять новые словари без модификации кода приложения.
