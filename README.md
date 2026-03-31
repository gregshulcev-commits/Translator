# Офлайн переводчик PDF по клику на слово — MVP v2

## Что это

Это рабочий MVP настольного приложения для Linux, которое:

- открывает PDF с текстовым слоем;
- показывает страницу документа как обычный просмотрщик;
- позволяет кликнуть по слову мышью;
- полностью выделяет выбранное слово;
- показывает короткую словарную подсказку **снизу**, а не отдельный «отчёт» справа;
- поддерживает прокрутку страницы колесом мыши;
- умеет искать по документу;
- работает **без интернета после установки**.

MVP ориентирован на чтение технических PDF на английском языке с быстрым переводом отдельных слов на русский.

## Что нового в этой версии

По сравнению с первой сборкой этот архив включает:

- нижнюю компактную панель-подсказку вместо перегруженной боковой панели;
- минималистичную карточку перевода: лучший перевод, пример использования, альтернативы;
- прокрутку страницы колесом мыши на Linux;
- исправление вычисления `PROJECT_ROOT`;
- исправление запуска через `cmake --build build --target run`, если рядом есть `.venv`;
- удаление зависимости `pronouncing`, из-за которой возникали проблемы на Python 3.13/3.14;
- поддержку нескольких словарных пакетов;
- автоматический установщик словарей (`tools/install_default_dictionaries.py`, `scripts/install_desktop.sh`);
- импорт FreeDict TEI -> SQLite;
- расширенный встроенный технический глоссарий.

## Почему текущий MVP реализован на Python/Tkinter + PyMuPDF

На этапе проектирования обсуждалась архитектура на Qt/C++. Для этой итерации выбран более быстрый путь к реально работающему и тестируемому результату:

- **Python 3** — быстрые итерации и низкий порог входа;
- **Tkinter** — стандартный GUI toolkit, доступный в типовой Linux-среде;
- **PyMuPDF** — быстрый PDF-движок с доступом к словам и их координатам.

При этом архитектура сохранена **модульной**:

- документ открывается через плагин документа;
- перевод идёт через плагин словаря;
- UI не знает внутренностей PDF-парсера;
- словари можно добавлять пакетами без переписывания viewer-а.

Это полезный рабочий срез, на котором уже можно читать реальные PDF и продолжать разработку без старта с нуля.

## Что входит в MVP

- поддержка **PDF**;
- поддержка **text-based PDF** (без OCR);
- перевод **EN -> RU**;
- нижняя закреплённая панель подсказки;
- поиск по документу;
- прокрутка страницы колесом мыши;
- встроенный технический словарь;
- поддержка нескольких SQLite-паков словаря;
- установочный импорт общего словаря FreeDict EN-RU;
- документация по модулям, форматам и тестам;
- автоматические тесты и GUI smoke-проверка.

## Что не входит в MVP

- OCR;
- перевод текста внутри изображений;
- DOCX/EPUB;
- история слов;
- нейронный перевод;
- Android-сборка;
- полноценный менеджер словарей в интерфейсе.

## Быстрый старт на Fedora / Linux

### 1. Минимальная системная зависимость для GUI

Если модуль Tkinter не установлен системно, добавьте его:

```bash
sudo dnf install python3-tkinter
```

### 2. Автоматическая установка (рекомендуется)

Скрипт делает всё необходимое:

- создаёт `.venv`;
- обновляет `pip`/`setuptools`/`wheel`;
- ставит Python-зависимости;
- собирает встроенный технический словарь;
- пытается скачать и импортировать общий словарь FreeDict EN-RU.

```bash
./scripts/install_desktop.sh
```

После этого запуск:

```bash
source .venv/bin/activate
PYTHONPATH=src python -m pdf_word_translator.app
```

### 3. Ручная установка

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
PYTHONPATH=src python tools/install_default_dictionaries.py
PYTHONPATH=src python -m pdf_word_translator.app
```

### 4. Запуск с PDF сразу

```bash
source .venv/bin/activate
PYTHONPATH=src python -m pdf_word_translator.app /path/to/file.pdf
```

## Установка словарей

Приложение работает с **SQLite-паками** словаря. При старте автоматически загружаются:

1. встроенный технический глоссарий из `data/starter_dictionary.sqlite`;
2. все `*.sqlite` файлы из пользовательского каталога:

```text
~/.local/share/pdf_word_translator_mvp/dictionaries/
```

### Импорт локального CSV-глоссария

```bash
PYTHONPATH=src python tools/import_dictionary.py my_glossary.csv ~/.local/share/pdf_word_translator_mvp/dictionaries/my_glossary.sqlite --format csv
```

### Импорт локального FreeDict TEI-файла

```bash
PYTHONPATH=src python tools/import_dictionary.py eng-rus.tei ~/.local/share/pdf_word_translator_mvp/dictionaries/freedict_en_ru.sqlite --format freedict-tei
```

### Установка стандартного набора словарей

```bash
PYTHONPATH=src python tools/install_default_dictionaries.py
```

## Работа с приложением

1. Открой PDF.
2. Прокручивай страницу колесом мыши.
3. Нажми на незнакомое слово.
4. Внизу появится короткая подсказка:
   - лучший перевод;
   - пример использования (контекст из текущего документа);
   - альтернативные переводы.
5. При поиске по документу можно переходить между совпадениями кнопками `Пред.` и `След.`.

## Запуск тестов

```bash
source .venv/bin/activate
PYTHONPATH=src pytest
xvfb-run -a python tests/smoke_gui.py
```

## Запуск через CMake

Если рядом есть `.venv`, `run` и `test` используют именно его.

```bash
cmake -S . -B build
cmake --build build --target run
cmake --build build --target test
cmake --build build --target install_dictionaries
```

## Структура проекта

```text
src/pdf_word_translator/
  app.py
  config.py
  models.py
  plugin_api.py
  plugin_loader.py
  services/
  plugins/
  ui/
  utils/

data/
  starter_dictionary.csv
  starter_dictionary.sqlite

tools/
  build_dictionary.py
  import_dictionary.py
  install_default_dictionaries.py

scripts/
  install_desktop.sh
  run_local.sh

tests/
  test_config.py
  test_normalizer.py
  test_dictionary_plugin.py
  test_freedict_importer.py
  test_pdf_provider.py
  test_workflow.py
  test_real_pdfs.py
  smoke_gui.py

docs/
  ARCHITECTURE.md
  USER_GUIDE.md
  TESTING.md
  KNOWN_LIMITATIONS.md
  ROADMAP.md
  MODULES_INDEX.md
  modules/
```

## Ключевые документы

- архитектура: `docs/ARCHITECTURE.md`
- пользовательское руководство: `docs/USER_GUIDE.md`
- система плагинов: `docs/PLUGIN_SYSTEM.md`
- формат словаря: `docs/DICTIONARY_FORMAT.md`
- документация по каждому модулю: `docs/MODULES_INDEX.md`
- тестирование и отчёт: `docs/TESTING.md`, `docs/TEST_REPORT.md`
- журнал изменений в этой итерации: `docs/DEVELOPMENT_LOG.md`
