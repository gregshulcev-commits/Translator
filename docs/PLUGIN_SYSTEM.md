# Система плагинов

## Что считается плагином в MVP

В текущем MVP плагинами считаются два типа расширений:

- **DocumentPlugin** — открывает документ определённого формата;
- **DictionaryPlugin** — выполняет lookup слова.

Интерфейсы описаны в `src/pdf_word_translator/plugin_api.py`.

## Built-in plugins

Загружаются всегда:

- `document.pdf.pymupdf`
- `document.txt`
- `document.fb2`
- composite dictionary plugin, который объединяет:
  - встроенный EN→RU словарь;
  - встроенный RU→EN словарь;
  - все найденные runtime `*.sqlite` packs.

## External plugins в v8

Внешние Python-плагины поддерживаются, но теперь работают по принципу **explicit opt-in**.

Папка для внешних плагинов:

```text
~/.local/share/pdf_word_translator_mvp/plugins/
```

Для включения загрузки нужно явно выставить:

```bash
export PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS=1
```

Без этой переменной `PluginLoader` не импортирует внешние `*.py` файлы.

## Дополнительные ограничения безопасности

Если external plugins включены, загрузчик дополнительно:

- игнорирует symlink/non-regular paths;
- игнорирует директории и файлы с небезопасными POSIX permission bits;
- использует уникальные module names, чтобы не сталкивать внешние модули между собой.

## Формат внешнего плагина

Каждый внешний `*.py` файл может определить функцию:

```python
def register_plugins():
    return [my_plugin_instance]
```

Возвращаемые объекты должны реализовывать `DocumentPlugin` или `DictionaryPlugin`.

## Почему словарные паки реализованы как SQLite, а не как Python-плагины

Словарь — это в первую очередь **данные**, а не код. Поэтому для словарей выбран гибридный подход:

- логика lookup — в Python-плагине;
- словарные базы — в `*.sqlite` паках.

Так проще добавлять новые словари без модификации кода приложения и без лишнего расширения attack surface.
