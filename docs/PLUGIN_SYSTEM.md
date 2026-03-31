# Plugin system

## Что реализовано сейчас

В MVP есть два типа плагинов:

- document plugins;
- dictionary plugins.

## Builtin plugins

- `document.pdf.pymupdf`
- `dictionary.sqlite`

## Внешние плагины

Если положить Python-файл в runtime plugin directory, loader попытается его импортировать.

Плагин должен предоставить функцию:

```python
def register_plugins():
    return [plugin_instance_1, plugin_instance_2]
```

## Ограничение текущего варианта

Это не ABI-совместимая система модулей, а легкий Python-level plugin mechanism для быстрого расширения MVP.
