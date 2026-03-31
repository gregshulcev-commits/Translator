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

Реализованная версия:

- `PyMuPdfDocumentPlugin`

## DictionaryPlugin

Минимальный контракт:

- `plugin_id()`
- `lookup(word)` -> `LookupResult`
- `available_entries()`

Реализованные версии:

- `SQLiteDictionaryPlugin`
- `CompositeDictionaryPlugin`

## Built-in plugins

Загружаются всегда:

- `document.pdf.pymupdf`
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

## Почему словарные паки реализованы как SQLite, а не как Python-плагины

Словарь — это в первую очередь **данные**, а не код. Поэтому для словарей в MVP выбран гибридный подход:

- логика lookup — в Python-плагине;
- словарные базы — в `*.sqlite` паках.

Так проще добавлять новые словари без модификации кода приложения.
