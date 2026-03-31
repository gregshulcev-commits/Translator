# Офлайн переводчик документов по клику на слово — MVP v8

## Что это

Проект состоит из двух связанных частей:

1. **desktop MVP** на Python + Tkinter для Linux;
2. **android-client** как отдельная APK-ветка с нативным Android UI.

Базовый сценарий не изменился:

- открыть документ;
- быстро найти незнакомое слово;
- получить словарную подсказку по клику;
- при необходимости включить отдельный optional provider layer для контекстного перевода предложения.

## Что сделано в v8

`v8` — это результат слияния двух исходных веток:

- ветки `v7` с Android/APK-источниками и `mobile_api.py`;
- ветки `v7_fixed` с багфиксами по LibreTranslate, UI и Argos manager.

### Основные изменения

- слиты desktop-улучшения и Android-ветка в один исходный проект;
- возвращены и закреплены исправления для **LibreTranslate**:
  - нормализация URL;
  - понятная диагностика конфигурации;
  - fallback с JSON на `application/x-www-form-urlencoded`;
  - более понятные HTTP-ошибки;
  - проверка `EN → RU` и `RU → EN` из UI;
- возвращены адаптивные исправления GUI:
  - растягиваемый toolbar с нормальным поиском;
  - адаптивный каталог словарей;
  - адаптивный менеджер Argos-моделей;
  - корректный `wraplength` для длинных текстовых блоков;
- сохранено улучшение из `v7`: окно **«Как установить Argos…»** остаётся отдельным растягиваемым read-only dialog с кнопкой копирования команд;
- усилена безопасность хранения настроек:
  - `settings.json` сохраняется атомарно;
  - на POSIX файл принудительно получает права `0600`;
- усилена безопасность загрузки внешних Python-плагинов:
  - external plugins теперь **opt-in**;
  - для включения нужен `PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS=1`;
  - загрузчик игнорирует небезопасные директории/файлы с некорректными правами доступа;
- усилен `mobile_api.py`:
  - bridge принимает только существующие **обычные файлы**, а не директории;
  - summary строится из реально открытого `DictionaryService`;
- проектная версия поднята до **v8**;
- Android module получил обновлённый build identifier:
  - `versionCode = 8`;
  - `versionName = "0.8.0-v8-merge"`.

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
- сохранять настройки интерфейса и провайдеров.

## Что уже умеет Android branch

Android-ветка по-прежнему включена как **исходный код**, а не как готовый release APK.

В архиве уже есть:

- `android-client/`;
- `src/pdf_word_translator/mobile_api.py`;
- Kotlin UI prototype;
- Chaquopy bridge;
- PdfRenderer prototype;
- bundled SQLite assets.

Текущие возможности Android-ветки:

- открытие PDF через системный picker;
- базовый рендер PDF-страниц;
- перелистывание страниц;
- словарный lookup по введённому слову;
- переключение `EN → RU` / `RU → EN`;
- bootstrap встроенных SQLite-словарей из assets;
- вызов общего Python-словарного слоя через `mobile_api.py`.

## Что пока не входит

- OCR;
- перевод текста на изображениях;
- удаление словарей и Argos-моделей из GUI;
- tap-to-word selection внутри Android PDF viewer;
- готовый собранный APK внутри архива.

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

## Контекстный перевод

### Argos (офлайн)

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

CLI helper:

```bash
source .venv/bin/activate
PYTHONPATH=src python tools/install_argos_model.py --list
PYTHONPATH=src python tools/install_argos_model.py --from-lang en --to-lang ru
PYTHONPATH=src python tools/install_argos_model.py --from-lang ru --to-lang en
PYTHONPATH=src python tools/install_argos_model.py --file /path/to/model.argosmodel
```

### LibreTranslate

По умолчанию desktop теперь ориентируется на **self-hosted** адрес:

```text
http://127.0.0.1:5000
```

Что важно:

- можно указать как базовый адрес, так и полный endpoint `/translate`;
- для публичного `libretranslate.com` нужен **API key**;
- в окне настроек доступна отдельная проверка обоих направлений `EN ↔ RU`.

### Yandex Cloud

Для Yandex Cloud по-прежнему обязательны:

- `Folder ID`;
- `API key` или `IAM token`.

## External plugins

Внешние Python-плагины поддерживаются, но теперь выключены по умолчанию.

Чтобы разрешить их загрузку, включите переменную окружения:

```bash
export PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS=1
```

Папка внешних плагинов:

```text
~/.local/share/pdf_word_translator_mvp/plugins/
```

## Android branch: как открыть и собрать

В архив включён исходный код Android-клиента:

```text
android-client/
```

### Что важно понимать

- это **отдельная UI-ветка**, а не перенос Tkinter на Android;
- Android-клиент использует **тот же словарный код**, но через `mobile_api.py`;
- в архиве **нет готового Gradle wrapper** и **нет уже собранного APK**, потому что в рабочем окружении не было Android SDK/Gradle.

### Рекомендуемый способ запуска

1. откройте `android-client/` в Android Studio;
2. дайте IDE синхронизировать Gradle-проект;
3. убедитесь, что Android SDK установлен;
4. соберите `debug` APK из IDE.

Подробности:

- `android-client/README.md`
- `docs/ANDROID_STATUS.md`

## Документация по проекту

- `docs/USER_GUIDE.md` — пользовательские сценарии desktop и Android branch;
- `docs/ARCHITECTURE.md` — архитектура desktop, provider layer и mobile bridge;
- `docs/ANDROID_STATUS.md` — состояние APK-ветки;
- `docs/MODULES_INDEX.md` — индекс модулей;
- `docs/ROADMAP.md` — сделанное и следующие шаги;
- `docs/KNOWN_LIMITATIONS.md` — актуальные ограничения;
- `docs/PLUGIN_SYSTEM.md` — политика загрузки built-in и external plugins;
- `docs/modules/main_window.md` — desktop UI слой;
- `docs/modules/mobile_api.md` — bridge-модуль для Android;
- `docs/modules/context_providers.md` — optional provider layer;
- `docs/modules/plugin_loader.md` — загрузка built-in и opt-in external plugins.

## Тестирование

```bash
source .venv/bin/activate
PYTHONPATH=src pytest
xvfb-run -a env PYTHONPATH=src python tests/smoke_gui.py
```

Актуально для v8:

- `pytest`: **49 passed, 2 skipped**;
- GUI smoke test desktop: проходит;
- Android-ветка проверена на уровне структуры проекта, Python bridge и наличия bundled assets;
- финальная сборка APK в этой среде не выполнялась.

## Ограничения текущей ветки

- desktop PDF по-прежнему требует текстовый слой;
- Argos ориентирован на **EN ↔ RU**;
- Android branch пока использует **ручной ввод слова**, а не tap-to-word selection по PDF;
- APK source включён, но финальная сборка APK в этом архиве не выполнена;
- external plugins теперь требуют явного opt-in;
- credentials cloud-провайдеров хранятся локально в `settings.json`, но файл сохраняется с ограниченными правами доступа.
