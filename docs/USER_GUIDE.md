# Пользовательское руководство

## Открытие документа

1. Нажмите `Открыть PDF`.
2. Выберите PDF с текстовым слоем.
3. После загрузки отобразится первая страница.

## Перевод слова

1. Прокрутите документ к интересующему месту.
2. Нажмите на незнакомое слово.
3. Слово выделится рамкой.
4. Внизу появится краткая словарная подсказка:
   - лучший перевод;
   - пример использования из текущего документа;
   - альтернативные переводы.

## Прокрутка

- колесо мыши — вертикальная прокрутка страницы;
- кнопки `◀` и `▶` — переход между страницами;
- `PageUp` / `PageDown` — переход между страницами;
- `-` и `+` — изменение масштаба.

## Поиск

1. Введите слово или фразу в поле `Поиск`.
2. Нажмите `Найти`.
3. Переключайтесь кнопками `Пред.` и `След.`.

## Запуск с конкретным PDF

```bash
source .venv/bin/activate
PYTHONPATH=src python -m pdf_word_translator.app /path/to/file.pdf
```

## Где находятся словари

Встроенный словарь лежит в проекте:

```text
data/starter_dictionary.sqlite
```

Дополнительные словари подключаются из пользовательского каталога:

```text
~/.local/share/pdf_word_translator_mvp/dictionaries/
```

## Добавление словаря

### Вариант 1. Импорт CSV

```bash
PYTHONPATH=src python tools/import_dictionary.py my_glossary.csv ~/.local/share/pdf_word_translator_mvp/dictionaries/my_glossary.sqlite --format csv
```

### Вариант 2. Импорт FreeDict TEI

```bash
PYTHONPATH=src python tools/import_dictionary.py eng-rus.tei ~/.local/share/pdf_word_translator_mvp/dictionaries/freedict_en_ru.sqlite --format freedict-tei
```

### Вариант 3. Автоматическая установка стандартного набора

```bash
PYTHONPATH=src python tools/install_default_dictionaries.py
```

## Логи

Логи пишутся в каталог:

```text
~/.cache/pdf_word_translator_mvp/logs/
```
