# Офлайн переводчик документов по клику на слово — MVP v7

## Что это

Проект состоит уже из двух связанных веток:

1. **desktop MVP** на Python + Tkinter для Linux;
2. **APK branch prototype** с отдельным Android UI и переиспользованием словарного Python-слоя.

Главная идея проекта не изменилась:

- открыть документ;
- быстро найти незнакомое слово;
- получить словарную подсказку по клику;
- при необходимости показать контекстный перевод предложения через optional provider layer.

## Что нового в v7

### Desktop

- окно **«Как установить Argos…»** больше не открывается как узкий `messagebox`;
- вместо этого используется **растягиваемый help dialog** с нормальным переносом текста;
- команды из справки можно **скопировать кнопкой**;
- обновлены README и профильные `.md`-документы без отдельного release notes файла.

### Android / APK branch

- добавлена директория **`android-client/`** с исходниками отдельного Android-клиента;
- добавлен **`src/pdf_word_translator/mobile_api.py`** — узкий JSON-friendly bridge для мобильного клиента;
- Android-ветка использует:
  - **native Android UI**;
  - **Chaquopy** для вызова Python-словаря;
  - **PdfRenderer** для базового рендера PDF-страниц;
  - встроенные SQLite-словари как assets;
- добавлена документация по Android-ветке, способу установки и текущим ограничениям.

## Что уже умеет desktop MVP

- открывать **PDF**, **TXT** и **FB2**;
- работать с **text-based PDF** без OCR;
- поддерживать **EN → RU** и **RU → EN**;
- искать по документу;
- показывать компактную словарную карточку внизу;
- использовать **LibreTranslate**, **Yandex Cloud** или **Argos (офлайн)** как optional provider layer;
- ставить и импортировать **Argos-модели** из GUI;
- работать со словарями через каталог, SQLite, CSV и FreeDict TEI;
- масштабировать документ до **800%**;
- сохранять настройки интерфейса.

## Что уже умеет Android branch

Текущая Android-ветка — это **первый рабочий источник кода**, а не готовый release APK.

Она уже включает:

- открытие PDF через системный picker;
- базовый рендер PDF-страниц;
- переход между страницами;
- словарный lookup по введённому слову;
- переключение `EN → RU` / `RU → EN`;
- bootstrap встроенных SQLite-словарей из assets;
- вызов общего Python-слоя через `mobile_api.py`.

## Что пока не входит

- OCR;
- перевод текста на изображениях;
- удаление словарей и Argos-моделей из GUI;
- tap-to-word selection внутри Android PDF viewer;
- готовый собранный APK внутри этого архива.

## Быстрый старт на desktop (Linux)

### 1. Системная зависимость GUI

```bash
sudo dnf install python3-tkinter
```

### 2. Автоматическая установка базового desktop-режима

```bash
./scripts/install_desktop.sh
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

## Офлайн нейронный перевод через Argos

Argos остаётся **optional-слоем** поверх словарного desktop MVP.

Чтобы он заработал, нужны:

1. Python runtime `argostranslate`;
2. модель нужного направления (`EN → RU` или `RU → EN`).

### Рекомендуемый путь через GUI

```bash
source .venv/bin/activate
python -m pip install -r requirements-optional.txt
```

Потом:

1. запустите desktop-приложение;
2. откройте **Перевод → Офлайн-модели Argos…**;
3. нажмите **Обновить список из сети**;
4. установите модель;
5. выберите провайдер **Argos (офлайн)**.

### CLI helper

```bash
source .venv/bin/activate
PYTHONPATH=src python tools/install_argos_model.py --list
PYTHONPATH=src python tools/install_argos_model.py --from-lang en --to-lang ru
PYTHONPATH=src python tools/install_argos_model.py --from-lang ru --to-lang en
PYTHONPATH=src python tools/install_argos_model.py --file /path/to/model.argosmodel
```

## Android branch: как открыть и собрать

В архив включён исходный код Android-клиента:

```text
android-client/
```

### Что важно понимать

- это **отдельная UI-ветка**, не перенос Tkinter на Android;
- Android-клиент использует **тот же словарный код**, но через `mobile_api.py`;
- в этом архиве **нет готового Gradle wrapper** и **нет уже собранного APK**, потому что в рабочем окружении не было Android SDK/Gradle.

### Рекомендуемый способ запуска

1. откройте `android-client/` в Android Studio;
2. дайте IDE синхронизировать Gradle-проект;
3. убедитесь, что Android SDK установлен;
4. соберите `debug` APK из IDE.

Подробности смотри в:

- `android-client/README.md`
- `docs/ANDROID_STATUS.md`

## Документация по проекту

- `docs/USER_GUIDE.md` — пользовательские сценарии desktop и Android branch;
- `docs/ARCHITECTURE.md` — архитектура desktop и mobile bridge;
- `docs/ANDROID_STATUS.md` — текущее состояние APK-ветки;
- `docs/MODULES_INDEX.md` — индекс модулей;
- `docs/ROADMAP.md` — сделанное и следующие шаги;
- `docs/KNOWN_LIMITATIONS.md` — актуальные ограничения;
- `docs/modules/main_window.md` — desktop UI слой;
- `docs/modules/mobile_api.md` — bridge-модуль для Android;
- `docs/modules/context_providers.md` — optional provider layer;
- `docs/modules/argos_manager.md` — lifecycle Argos моделей.

## Тестирование

```bash
source .venv/bin/activate
PYTHONPATH=src pytest
xvfb-run -a env PYTHONPATH=src python tests/smoke_gui.py
```

Актуально для v7:

- `pytest`: **37 passed, 2 skipped**;
- GUI smoke test desktop: проходит;
- Android-ветка проверена на уровне структуры проекта, Python bridge и наличия bundled assets.

## Ограничения текущей ветки

- desktop PDF по-прежнему требует текстовый слой;
- Argos сейчас ориентирован на **EN ↔ RU**;
- Android branch пока использует **ручной ввод слова**, а не tap-to-word selection по PDF;
- APK source включён, но финальная сборка APK в этом архиве не выполнена.
