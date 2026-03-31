# Офлайн переводчик документов по клику на слово — MVP v3

## Что это

Это рабочий MVP настольного приложения для Linux, которое:

- открывает **PDF**, **TXT** и **FB2**;
- показывает документ в едином viewer-е;
- позволяет кликнуть по слову мышью;
- полностью выделяет выбранное слово;
- показывает короткую словарную подсказку **снизу**;
- поддерживает **непрерывную прокрутку всего документа** колесом мыши;
- поддерживает **масштабирование Ctrl + колесо мыши**;
- умеет искать по документу;
- позволяет подключать словари из меню приложения;
- работает **без интернета после установки**.

MVP ориентирован на чтение технических документов на английском языке с быстрым переводом отдельных слов на русский.

## Что нового в v3

По сравнению с предыдущей сборкой эта версия включает:

- непрерывный просмотр документа вместо режима «одна страница за раз»;
- корректную прокрутку всего документа колесом мыши;
- zoom по `Ctrl + колесо мыши`;
- верхний предел zoom увеличен до **600%**;
- поддержку форматов **TXT** и **FB2** через отдельные document plugins;
- встроенное меню **Словари** и контекстное меню для подключения словарей без командной строки;
- настройку размера шрифта интерфейса;
- дополнительную документацию по форматам, словарям, Android-статусу и оценке нейронного перевода;
- новые тесты для TXT/FB2, импорта словарей и UI-settings.

## Почему текущий MVP по-прежнему реализован на Python/Tkinter + PyMuPDF

На этапе проектирования обсуждалась архитектура на Qt/C++. Для этой итерации выбран более быстрый путь к реально работающему и тестируемому результату:

- **Python 3** — быстрые итерации и низкий порог входа;
- **Tkinter** — стандартный GUI toolkit, доступный в типовой Linux-среде;
- **PyMuPDF** — быстрый PDF-движок с доступом к словам и их координатам;
- **Pillow** — рендер reflowable-форматов (TXT/FB2) в синтетические страницы.

При этом архитектура сохранена **модульной**:

- документ открывается через document plugin;
- перевод идёт через dictionary plugin;
- словари можно добавлять пакетами без переписывания viewer-а;
- TXT/FB2 добавлены без переписывания workflow-а клика по слову.

## Что входит в MVP

- поддержка **PDF / TXT / FB2**;
- поддержка **text-based PDF** (без OCR);
- перевод **EN -> RU**;
- нижняя закреплённая панель-подсказка;
- поиск по документу;
- непрерывная прокрутка документа;
- zoom до **600%**;
- встроенный технический словарь;
- поддержка нескольких SQLite-паков словаря;
- импорт словарей из GUI и через CLI;
- документация по модулям, форматам и тестам;
- автоматические тесты и GUI smoke-проверка.

## Что не входит в MVP

- OCR;
- перевод текста внутри изображений;
- EPUB/DOCX;
- история слов;
- нейронный перевод;
- рабочая Android-сборка APK.

## Быстрый старт на Fedora / Linux

### 1. Системная зависимость для GUI

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

### 4. Запуск сразу с документом

```bash
source .venv/bin/activate
PYTHONPATH=src python -m pdf_word_translator.app /path/to/file.pdf
```

То же самое работает для `.txt` и `.fb2`.

## Работа с приложением

1. Открой документ кнопкой **Открыть** или через меню **Файл**.
2. Листай весь документ колесом мыши.
3. Удерживай `Ctrl` и крути колесо для zoom.
4. Нажми на незнакомое слово.
5. Внизу появится краткая подсказка:
   - лучший перевод;
   - пример использования;
   - альтернативные переводы.
6. Для поиска используй строку `Поиск` и кнопки `Пред.` / `След.`.
7. Для работы со словарями используй меню **Словари** или правый клик по viewer/подсказке.

## Управление словарями

Приложение работает с **SQLite-паками** словаря. При старте автоматически загружаются:

1. встроенный технический глоссарий из `data/starter_dictionary.sqlite`;
2. все `*.sqlite` файлы из пользовательского каталога:

```text
~/.local/share/pdf_word_translator_mvp/dictionaries/
```

### Из GUI

Меню **Словари** позволяет:

- скачать общий FreeDict EN→RU;
- подключить готовый SQLite-пак;
- импортировать CSV-глоссарий;
- импортировать FreeDict TEI.

Те же действия доступны из контекстного меню по правому клику.

### Из CLI

Импорт CSV:

```bash
PYTHONPATH=src python tools/import_dictionary.py my_glossary.csv ~/.local/share/pdf_word_translator_mvp/dictionaries/my_glossary.sqlite --format csv
```

Импорт FreeDict TEI:

```bash
PYTHONPATH=src python tools/import_dictionary.py eng-rus.tei ~/.local/share/pdf_word_translator_mvp/dictionaries/freedict_en_ru.sqlite --format freedict-tei
```

Установка стандартного набора:

```bash
PYTHONPATH=src python tools/install_default_dictionaries.py
```

## Настройка интерфейса

Через меню **Вид** можно:

- увеличить размер шрифта интерфейса;
- уменьшить размер шрифта интерфейса;
- сбросить размер к значению по умолчанию.

Настройка сохраняется в:

```text
~/.local/share/pdf_word_translator_mvp/settings.json
```

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
  test_*.py
  smoke_gui.py

docs/
  ARCHITECTURE.md
  USER_GUIDE.md
  TESTING.md
  KNOWN_LIMITATIONS.md
  ROADMAP.md
  MODULES_INDEX.md
  ANDROID_STATUS.md
  NEURAL_TRANSLATION_ESTIMATE.md
  modules/
```

## Важные документы

- архитектура: `docs/ARCHITECTURE.md`
- пользовательское руководство: `docs/USER_GUIDE.md`
- формат словаря: `docs/DICTIONARY_FORMAT.md`
- Android-статус: `docs/ANDROID_STATUS.md`
- оценка нейронного перевода: `docs/NEURAL_TRANSLATION_ESTIMATE.md`
- документация по каждому модулю: `docs/MODULES_INDEX.md`
- тестирование и отчёт: `docs/TESTING.md`, `docs/TEST_REPORT.md`
- журнал изменений: `docs/DEVELOPMENT_LOG.md`
