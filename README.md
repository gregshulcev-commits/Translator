# Офлайн переводчик документов по клику на слово — MVP v4

## Что это

Это рабочий MVP настольного приложения для Linux, которое:

- открывает **PDF**, **TXT** и **FB2**;
- показывает документ в едином viewer-е;
- позволяет кликнуть по слову мышью;
- полностью выделяет выбранное слово;
- показывает компактную словарную справку **снизу**;
- листает **весь документ** колесом мыши;
- поддерживает **масштабирование `Ctrl + колесо мыши`** и кнопками `+ / -`;
- умеет искать по документу;
- позволяет подключать словари из меню приложения и через каталог пакетов;
- поддерживает **EN → RU** и **RU → EN**;
- имеет порт для **контекстного перевода** (Argos / LibreTranslate / Yandex Cloud / отключено);
- работает **без интернета после установки**, если словари и optional-провайдеры уже установлены.

MVP ориентирован на чтение технических документов на английском и русском языке с быстрым переводом отдельных слов и, при желании, контекстным переводом предложения через отдельный провайдер.

## Что нового в v4

По сравнению с предыдущей сборкой эта версия включает:

- **ленивую перерисовку страниц**: viewer больше не рендерит весь многостраничный документ при каждом zoom;
- zoom увеличен до **800%**;
- исправление compound tokens: `diagnostic\measurement` и `diagnostic/measurement` разбиваются на отдельные кликабельные части;
- нижняя панель больше не показывает «сырое» предложение из документа;
- добавлен слой **контекстных провайдеров перевода**:
  - `Отключено`
  - `Argos (офлайн)`
  - `LibreTranslate`
  - `Yandex Cloud`
- добавлено **переключение направления EN ↔ RU**;
- добавлены кнопки **A− / A+** для размера интерфейса;
- добавлен **каталог словарных пакетов** в самой программе;
- bundled packs теперь включают:
  - `technical_en_ru`
  - `technical_ru_en`
  - `literary_en_ru`
  - `literary_ru_en`
- в проект добавлен скрипт установки модели **Argos** для выбранного направления.

## Технологический стек

Текущая рабочая реализация — это прагматичный Linux desktop MVP на:

- **Python 3** — быстрые итерации и удобная поставка исходников;
- **Tkinter** — стандартный GUI toolkit, доступный в типовой Linux-среде;
- **PyMuPDF** — быстрый PDF-движок с доступом к словам и их координатам;
- **Pillow** — рендер reflowable-форматов (TXT/FB2) в синтетические страницы;
- **SQLite** — единый внутренний формат словарных паков.

При этом архитектура сохранена **модульной**:

- документы открываются через `DocumentPlugin`;
- перевод слов идёт через `DictionaryPlugin`;
- контекстный перевод идёт через отдельный `ContextTranslationProvider`;
- словари можно добавлять пакетами без переписывания viewer-а;
- TXT/FB2 добавлены без переписывания workflow-а клика по слову.

## Что входит в MVP v4

- поддержка **PDF / TXT / FB2**;
- поддержка **text-based PDF** (без OCR);
- перевод **EN → RU** и **RU → EN**;
- компактная нижняя панель-подсказка;
- поиск по документу;
- непрерывная прокрутка документа;
- zoom по `Ctrl + колесо мыши`;
- zoom до **800%**;
- lazy rendering страниц для больших документов;
- встроенные и устанавливаемые словарные пакеты;
- каталог словарей в GUI;
- optional порт для контекстного перевода;
- документация по архитектуре и модулям;
- автоматические тесты и GUI smoke test.

## Что не входит в MVP v4

- OCR;
- перевод текста внутри изображений;
- DOCX / EPUB;
- история слов;
- удаление словарных паков из GUI;
- готовый протестированный APK для Android.

## Быстрый старт на Fedora / Linux

### 1. Системная зависимость для GUI

Если модуль Tkinter не установлен системно, добавьте его:

```bash
sudo dnf install python3-tkinter
```

### 2. Автоматическая установка (рекомендуется)

Скрипт делает всё необходимое:

- создаёт `.venv`;
- обновляет `pip` / `setuptools` / `wheel`;
- ставит Python-зависимости;
- собирает встроенные словари EN→RU и RU→EN;
- устанавливает bundled technical / literary packs;
- пытается скачать и импортировать общие словари FreeDict в оба направления.

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

## Optional: контекстный перевод через Argos / LibreTranslate / Yandex Cloud

### Argos (офлайн)

Базовый проект **не требует** Argos. Если нужен офлайн-контекстный перевод предложений, установи optional provider:

```bash
source .venv/bin/activate
python -m pip install -r requirements-optional.txt
PYTHONPATH=src python tools/install_argos_model.py --from-lang en --to-lang ru
PYTHONPATH=src python tools/install_argos_model.py --from-lang ru --to-lang en
```

После этого в меню **Перевод → Контекстный перевод** выбери `Argos (офлайн)`.

### LibreTranslate

Если у тебя есть self-hosted сервер или managed endpoint:

1. выбери в меню **Перевод → Контекстный перевод → LibreTranslate**;
2. открой **Перевод → Настроить текущий провайдер…**;
3. укажи URL и, при необходимости, API key.

### Yandex Cloud

Провайдер уже включён как адаптер. Для реальной работы:

1. выбери в меню **Перевод → Контекстный перевод → Yandex Cloud**;
2. открой **Перевод → Настроить текущий провайдер…**;
3. укажи `Folder ID` и `API key` или `IAM token`.

Если Yandex Cloud не нужен, можно его просто не использовать — базовая Linux-версия никак от него не зависит.

## Работа с приложением

1. Открой документ кнопкой **Открыть** или через меню **Файл**.
2. Листай документ колесом мыши.
3. Удерживай `Ctrl` и крути колесо для zoom под курсором.
4. Для переключения направления нажимай кнопку `EN → RU` / `RU → EN` на toolbar или используй меню **Перевод**.
5. Нажми на незнакомое слово.
6. Внизу появится компактная справка:
   - форма слова / транскрипция;
   - лучший перевод;
   - контекстный перевод или пример;
   - альтернативные переводы.
7. Для поиска используй строку `Поиск` и кнопки `Пред.` / `След.`.
8. Для словарей используй меню **Словари** или правый клик по viewer / панели.

## Управление словарями

Приложение работает с **SQLite-паками** словаря. При старте автоматически загружаются:

1. встроенный технический EN→RU пакет;
2. встроенный технический RU→EN пакет;
3. все `*.sqlite` файлы из пользовательского каталога:

```text
~/.local/share/pdf_word_translator_mvp/dictionaries/
```

### Из GUI

Меню **Словари** позволяет:

- открыть **каталог словарных пакетов**;
- установить FreeDict для текущего направления;
- подключить готовый SQLite-пак;
- импортировать CSV-глоссарий;
- импортировать FreeDict TEI.

Те же действия доступны из контекстного меню по правому клику.

### Каталог пакетов

Каталог показывает:

- название пакета;
- направление;
- категорию;
- источник;
- описание;
- кнопку установки;
- кнопку открытия источника.

Сейчас в каталоге есть:

- общий `FreeDict EN→RU`;
- общий `FreeDict RU→EN`;
- bundled `technical_en_ru` / `technical_ru_en`;
- bundled `literary_en_ru` / `literary_ru_en`.

### Из CLI

Импорт CSV для текущего runtime-каталога:

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

Через toolbar и меню **Вид** можно:

- увеличить размер интерфейса `A+`;
- уменьшить размер интерфейса `A−`;
- сбросить размер к значению по умолчанию.

Настройка сохраняется в:

```text
~/.local/share/pdf_word_translator_mvp/settings.json
```

## Запуск тестов

```bash
source .venv/bin/activate
PYTHONPATH=src pytest
PYTHONPATH=src xvfb-run -a python tests/smoke_gui.py
```

## Запуск через CMake

Если рядом есть `.venv`, `run`, `test` и `install_dictionaries` используют именно его.

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
  providers/
  services/
  plugins/
  ui/
  utils/

data/
  starter_dictionary.csv
  starter_dictionary_ru_en.csv
  starter_dictionary.sqlite
  packs/

tools/
  build_dictionary.py
  import_dictionary.py
  install_default_dictionaries.py
  install_argos_model.py

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

## Основные документы

- архитектура: `docs/ARCHITECTURE.md`
- пользовательское руководство: `docs/USER_GUIDE.md`
- формат словаря: `docs/DICTIONARY_FORMAT.md`
- Android-статус: `docs/ANDROID_STATUS.md`
- оценка нейронного перевода: `docs/NEURAL_TRANSLATION_ESTIMATE.md`
- документация по каждому модулю: `docs/MODULES_INDEX.md`
- тестирование и отчёт: `docs/TESTING.md`, `docs/TEST_REPORT.md`
- журнал изменений: `docs/DEVELOPMENT_LOG.md`
