# Офлайн переводчик документов по клику на слово — MVP v6

## Что это

Это настольное Linux-приложение для чтения документов и быстрого перевода по клику на слово.

Приложение:

- открывает **PDF**, **TXT** и **FB2**;
- показывает документ в едином viewer-е с непрерывной прокруткой;
- позволяет кликнуть по слову и сразу получить словарную подсказку снизу;
- поддерживает **EN → RU** и **RU → EN**;
- умеет искать по документу;
- поддерживает масштабирование `Ctrl + колесо мыши` и кнопками `+ / -`;
- позволяет подключать и импортировать словари из GUI;
- умеет показывать **контекстный перевод предложения** через optional provider layer;
- теперь поддерживает **офлайн-нейроперевод Argos** с установкой моделей **из GUI** или через CLI.

Базовый режим остаётся словарным и полностью офлайн после установки словарей. Нейронный перевод вынесен в отдельный optional-слой и не раздувает ядро приложения.

## Что нового в v6

### Исправления, унаследованные от v5

- viewer больше не возвращает viewport к выделенному слову при обычной прокрутке;
- search/word highlight больше не перетягивает документ назад при lazy re-render;
- каталог словарей корректно масштабируется вместе с увеличением UI font size;
- async-результат контекстного перевода доставляется в Tk UI через очередь в главном потоке;
- загрузка `settings.json` устойчива к лишним ключам и повреждённым значениям;
- `Yandex Cloud` теперь явно требует `Folder ID` и подсказывает это в UI и документации.

### Новое в v6

- добавлен **встроенный менеджер офлайн-моделей Argos**: `Перевод → Офлайн-модели Argos…`;
- из GUI можно:
  - проверить наличие `argostranslate`;
  - увидеть состояние моделей **EN → RU** и **RU → EN**;
  - обновить индекс пакетов Argos из сети;
  - установить выбранную модель прямо из интерфейса;
  - импортировать локальный `.argosmodel` файл;
  - сразу переключиться на провайдер `Argos (офлайн)`;
- `ArgosContextProvider` теперь проверяет, действительно ли optional runtime и нужная модель готовы, и даёт понятную подсказку вместо неясной ошибки;
- CLI helper `tools/install_argos_model.py` расширен:
  - `--list` показывает состояние EN↔RU моделей;
  - `--file` импортирует локальный `.argosmodel`;
  - `--from-lang/--to-lang` по-прежнему ставит модель по направлению;
- обновлена документация: README, user guide, architecture, roadmap, module docs и тестовая документация синхронизированы с новым сценарием офлайн-нейроперевода.

## Технологический стек

Текущая реализация — прагматичный Linux desktop MVP на:

- **Python 3**;
- **Tkinter** для GUI;
- **PyMuPDF** для PDF и координат слов;
- **Pillow** для synthetic pages у TXT/FB2;
- **SQLite** как внутренний формат словарных паков;
- **Argos Translate** как optional offline neural provider;
- **LibreTranslate / Yandex Cloud** как optional online providers.

Архитектура остаётся модульной:

- документы открываются через `DocumentPlugin`;
- перевод слов идёт через `DictionaryPlugin`;
- контекстный перевод идёт через отдельный `ContextTranslationProvider`;
- офлайн-модели Argos управляются отдельным helper-модулем и GUI-менеджером, не ломая базовый workflow.

## Что входит в MVP v6

- поддержка **PDF / TXT / FB2**;
- поддержка **text-based PDF** (без OCR);
- словарный перевод **EN → RU** и **RU → EN**;
- компактная нижняя панель перевода;
- поиск по документу;
- непрерывная прокрутка документа;
- zoom по `Ctrl + колесо мыши`;
- zoom до **800%**;
- lazy rendering видимых страниц;
- встроенные и устанавливаемые словарные пакеты;
- каталог словарей в GUI;
- optional provider layer для контекстного перевода;
- **Argos GUI model manager** для офлайн-нейроперевода;
- CLI helper для установки и импорта Argos моделей;
- документация по архитектуре и модулям;
- unit tests, integration tests и GUI smoke test.

## Что пока не входит

- OCR;
- перевод текста на изображениях;
- DOCX / EPUB;
- удаление словарных паков из GUI;
- удаление Argos-моделей из GUI;
- готовый APK для Android.

## Быстрый старт на Fedora / Linux

### 1. Системная зависимость для GUI

Если модуль Tkinter не установлен системно, добавьте его:

```bash
sudo dnf install python3-tkinter
```

### 2. Автоматическая установка базового словарного режима

Скрипт:

- создаёт `.venv`;
- обновляет `pip` / `setuptools` / `wheel`;
- ставит базовые Python-зависимости;
- собирает встроенные словари EN→RU и RU→EN;
- устанавливает bundled technical / literary packs;
- пытается скачать и импортировать общие словари FreeDict.

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

То же работает для `.txt` и `.fb2`.

## Офлайн нейронный перевод через Argos

### Что нужно понимать

Argos — **optional** слой. Базовое приложение без него работает нормально. Чтобы получить локальный контекстный перевод предложений без интернета, нужны две отдельные вещи:

1. Python runtime `argostranslate`;
2. установленная модель нужного направления (`EN → RU` или `RU → EN`).

После однократной установки модели интернет больше не нужен.

### Вариант 1. Рекомендуемый путь через GUI

1. Установите optional dependency:

```bash
source .venv/bin/activate
python -m pip install -r requirements-optional.txt
```

2. Запустите приложение.
3. Откройте меню **Перевод → Офлайн-модели Argos…**.
4. Нажмите **Обновить список из сети**.
5. Выберите направление `EN → RU` или `RU → EN`.
6. Нажмите **Установить выбранную модель**.
7. Затем выберите **Выбрать Argos** или переключите провайдер вручную через **Перевод → Контекстный перевод → Argos (офлайн)**.

### Вариант 2. Импорт локального `.argosmodel` из GUI

Если `.argosmodel` уже скачан заранее:

1. установите `argostranslate` как optional dependency;
2. откройте **Перевод → Офлайн-модели Argos…**;
3. нажмите **Импортировать .argosmodel…**;
4. выберите локальный файл модели;
5. переключитесь на `Argos (офлайн)`.

Это полезно для сценария «сеть есть один раз на другом устройстве, а установка модели должна происходить локально и дальше работать полностью офлайн».

### Вариант 3. CLI helper

Показать состояние EN↔RU моделей:

```bash
source .venv/bin/activate
PYTHONPATH=src python tools/install_argos_model.py --list
```

Установить модель по направлению:

```bash
source .venv/bin/activate
PYTHONPATH=src python tools/install_argos_model.py --from-lang en --to-lang ru
PYTHONPATH=src python tools/install_argos_model.py --from-lang ru --to-lang en
```

Импортировать локальный `.argosmodel`:

```bash
source .venv/bin/activate
PYTHONPATH=src python tools/install_argos_model.py --file /path/to/model.argosmodel
```

### Что пользователь увидит в приложении

- если `argostranslate` не установлен, Argos-провайдер покажет понятную подсказку, что сначала нужно поставить optional dependency;
- если runtime есть, но модели для текущего направления нет, приложение подскажет открыть **Перевод → Офлайн-модели Argos…**;
- если модель установлена, вторая строка нижней панели начинает показывать локальный перевод контекста.

## Online optional providers: LibreTranslate и Yandex Cloud

### LibreTranslate

1. выберите **Перевод → Контекстный перевод → LibreTranslate**;
2. откройте **Перевод → Настроить текущий провайдер…**;
3. укажите URL и, при необходимости, API key.

### Yandex Cloud

1. выберите **Перевод → Контекстный перевод → Yandex Cloud**;
2. откройте **Перевод → Настроить текущий провайдер…**;
3. укажите:
   - `Folder ID`;
   - `API key` **или** `IAM token`.

## Работа с приложением

1. Откройте документ кнопкой **Открыть** или через меню **Файл**.
2. Листайте документ колесом мыши.
3. Удерживайте `Ctrl` и крутите колесо для zoom под курсором.
4. Для переключения направления используйте кнопку `EN → RU` / `RU → EN` или меню **Перевод → Направление**.
5. Нажмите на незнакомое слово.
6. Внизу появится компактная справка:
   - форма слова / транскрипция;
   - лучший перевод;
   - контекстный перевод провайдера или пример из словаря;
   - альтернативные переводы.
7. Для поиска используйте строку `Поиск` и кнопки `Пред.` / `След.`.
8. Для словарей используйте меню **Словари** или правый клик по viewer / панели.

## Управление словарями

Приложение работает со **SQLite-паками** словаря. При старте автоматически загружаются:

1. встроенный технический EN→RU пакет;
2. встроенный технический RU→EN пакет;
3. все `*.sqlite` файлы из пользовательского каталога:

```text
~/.local/share/pdf_word_translator_mvp/dictionaries/
```

### Из GUI

Меню **Словари** позволяет:

- открыть каталог словарных пакетов;
- установить FreeDict для текущего направления;
- подключить готовый SQLite-пак;
- импортировать CSV-глоссарий;
- импортировать FreeDict TEI.

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

Через toolbar и меню **Вид** можно:

- увеличить размер интерфейса `A+`;
- уменьшить размер интерфейса `A−`;
- сбросить размер к значению по умолчанию.

Высота строк каталога словарей и Argos-менеджера пересчитывается под текущий UI font size.

## Где лежат данные

### Словари

```text
~/.local/share/pdf_word_translator_mvp/dictionaries/
```

### Настройки

```text
~/.local/share/pdf_word_translator_mvp/settings.json
```

### Кэш и логи

```text
~/.cache/pdf_word_translator_mvp/
~/.cache/pdf_word_translator_mvp/logs/
```

## Документация по проекту

- `docs/USER_GUIDE.md` — пользовательские сценарии;
- `docs/ARCHITECTURE.md` — архитектура слоёв;
- `docs/MODULES_INDEX.md` — индекс модулей;
- `docs/ROADMAP.md` — сделанное и следующие шаги;
- `docs/NEURAL_TRANSLATION_ESTIMATE.md` — место нейронного перевода в проекте;
- `docs/modules/context_providers.md` — provider layer;
- `docs/modules/argos_manager.md` — lifecycle Argos моделей;
- `docs/modules/install_argos_model.md` — CLI helper для моделей.

## Тестирование

```bash
source .venv/bin/activate
PYTHONPATH=src pytest
xvfb-run -a env PYTHONPATH=src python tests/smoke_gui.py
```

Актуально для этой версии:

- `pytest`: **28 passed, 2 skipped**;
- GUI smoke test: проходит.

## Ограничения текущей ветки

- PDF только с текстовым слоем;
- Argos сейчас ориентирован на **EN ↔ RU**;
- установка моделей Argos из GUI пока без отдельного progress bar;
- удаление моделей Argos и словарей из GUI ещё не реализовано;
- Android-ветка и APK остаются следующей фазой.
