# Офлайн переводчик документов по клику на слово — MVP v9

## Что это

Проект состоит из двух связанных частей:

1. **desktop MVP** на Python + Tkinter для Linux;
2. **android-client** как отдельная APK-ветка с нативным Android UI.

Основной desktop-сценарий остаётся прежним:

- открыть PDF / TXT / FB2;
- кликнуть по слову;
- получить словарную подсказку;
- при необходимости использовать контекстный перевод для короткого фрагмента рядом с выделенным словом.

## Что сделано в v9

`v9` продолжает merged-ветку `v8` и фокусируется на удобстве использования.

### Основные изменения

- добавлен **отдельный установщик приложения**: `./install_app.sh`;
- установщик создаёт:
  - виртуальное окружение;
  - launcher в `~/.local/bin/pdf-word-translator-mvp`;
  - desktop entry в `~/.local/share/applications/`;
  - icon в `~/.local/share/icons/hicolor/256x256/apps/`;
- toolbar упрощён: размер UI-шрифта больше не на главной панели и перенесён в **окно настроек**;
- добавлено **единое окно настроек** с вкладками:
  - общие параметры;
  - LibreTranslate;
  - Yandex Cloud;
  - Argos;
  - словари;
- Argos стал полностью ближе к сценарию **без терминала**:
  - из GUI можно установить Python runtime для Argos;
  - из GUI можно обновить список моделей;
  - из GUI можно скачать модель;
  - из GUI можно импортировать локальный `.argosmodel`;
  - из GUI можно сразу выбрать Argos активным провайдером;
- добавлено **управление словарями из GUI**:
  - просмотр установленных словарей;
  - импорт SQLite / CSV / FreeDict TEI;
  - открытие каталога словарей;
  - удаление пользовательских runtime-словарей;
- переработано извлечение контекста:
  - контекстный перевод больше не тянет текст со всей страницы;
  - извлечение ограничено текущим **блоком**;
  - для табличных и заголовочных фрагментов используется текущая **строка**, а не большой кусок страницы;
  - слишком длинный контекст автоматически сужается до короткой локальной строки;
- версия проекта поднята до **v9**;
- Android source branch синхронизирован по версии:
  - `versionCode = 9`;
  - `versionName = "0.9.0-v9-usability"`.

## Что умеет desktop MVP сейчас

- открывать **PDF**, **TXT** и **FB2**;
- работать с **text-based PDF** без OCR;
- поддерживать **EN → RU** и **RU → EN**;
- искать по документу;
- показывать компактную словарную карточку;
- использовать **LibreTranslate**, **Yandex Cloud** или **Argos (офлайн)** как provider layer;
- устанавливать и импортировать **Argos-модели** из GUI;
- устанавливать, импортировать и удалять пользовательские словари из GUI;
- сохранять настройки интерфейса и провайдеров;
- запускаться из меню приложений Linux после установки.

## Что умеет Android branch сейчас

Android-ветка по-прежнему включена как **исходный код**, а не как готовый release APK.

В архиве есть:

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
- удаление Argos-моделей из GUI;
- tap-to-word selection внутри Android PDF viewer;
- готовый собранный APK внутри архива.

## Быстрый старт на desktop (Linux)

### 1. Системная зависимость GUI

```bash
sudo dnf install python3-tkinter
```

### 2. Установка приложения с launcher и иконкой

```bash
./install_app.sh
```

Что делает установщик:

- создаёт `.venv`;
- ставит `requirements.txt`;
- пытается поставить `requirements-optional.txt`;
- устанавливает базовые словари;
- создаёт launcher и desktop entry.

Важно: launcher ссылается на текущую распакованную директорию проекта. Если потом перенести или переименовать папку с исходниками, установщик нужно запустить заново.

Если нужен только базовый режим без optional-зависимостей:

```bash
./install_app.sh --skip-optional
```

### 3. Запуск после установки

Из меню приложений Linux или так:

```bash
~/.local/bin/pdf-word-translator-mvp
```

### 4. Ручной запуск из исходников

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
PYTHONPATH=src python tools/install_default_dictionaries.py
PYTHONPATH=src python -m pdf_word_translator.app
```

## Контекстный перевод

### Argos (офлайн)

Рекомендуемый путь теперь через GUI:

1. запустите приложение;
2. откройте **Настройки → Argos** или **Перевод → Офлайн-модели Argos…**;
3. нажмите **Установить поддержку Argos**;
4. затем **Обновить список из сети**;
5. установите модель;
6. нажмите **Использовать Argos** или выберите его в общих настройках.

CLI helper сохранён для диагностики и автоматизации:

```bash
source .venv/bin/activate
PYTHONPATH=src python tools/install_argos_model.py --list
PYTHONPATH=src python tools/install_argos_model.py --from-lang en --to-lang ru
PYTHONPATH=src python tools/install_argos_model.py --from-lang ru --to-lang en
PYTHONPATH=src python tools/install_argos_model.py --file /path/to/model.argosmodel
```

### LibreTranslate

По умолчанию desktop ориентируется на **self-hosted** адрес:

```text
http://127.0.0.1:5000
```

Что важно:

- можно указать как базовый адрес, так и полный endpoint `/translate`;
- для публичного `libretranslate.com` нужен **API key**;
- в окне настроек доступна отдельная проверка обоих направлений `EN ↔ RU`.

### Yandex Cloud

Для Yandex Cloud обязательны:

- `Folder ID`;
- `API key` или `IAM token`.

## Окно настроек

Единое окно **«Настройки»** теперь используется как главный центр конфигурации.

Во вкладках доступны:

- **Общие** — направление перевода, активный провайдер, размер UI-шрифта;
- **LibreTranslate** — URL, API key, проверка EN ↔ RU;
- **Yandex Cloud** — Folder ID, API key, IAM token;
- **Argos** — установка runtime, список моделей, download/import/use;
- **Словари** — просмотр пакетов, импорт и удаление пользовательских словарей.

## Контекстный фрагмент

В `v9` провайдерам передаётся более короткий и локальный контекст:

- сначала пытается использоваться предложение в пределах текущего текстового блока;
- если блок похож на таблицу/заголовок или фрагмент слишком длинный, используется только текущая строка;
- это уменьшает шанс утащить название документа, заголовок или лишнюю часть таблицы.

## External plugins

Внешние Python-плагины поддерживаются, но выключены по умолчанию.

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

Что важно:

- это **отдельная UI-ветка**, а не перенос Tkinter на Android;
- Android-клиент использует **тот же словарный код**, но через `mobile_api.py`;
- в архиве **нет готового Gradle wrapper** и **нет уже собранного APK**, потому что в этой рабочей среде не было Android SDK/Gradle.

Рекомендуемый путь:

1. открыть `android-client/` в Android Studio;
2. дождаться Gradle sync;
3. убедиться, что Android SDK установлен;
4. собрать `debug` APK из IDE.

## Документация по проекту

- `docs/USER_GUIDE.md` — пользовательские сценарии desktop и Android branch;
- `docs/ARCHITECTURE.md` — архитектура desktop, provider layer и mobile bridge;
- `docs/ANDROID_STATUS.md` — состояние APK-ветки;
- `docs/MODULES_INDEX.md` — индекс модулей;
- `docs/ROADMAP.md` — сделанное и следующие шаги;
- `docs/KNOWN_LIMITATIONS.md` — актуальные ограничения;
- `docs/PLUGIN_SYSTEM.md` — политика загрузки built-in и external plugins;
- `docs/modules/main_window.md` — desktop UI слой;
- `docs/modules/settings_dialog.md` — окно настроек;
- `docs/modules/dictionary_manager.md` — безопасное управление runtime-словарями;
- `docs/modules/context_extraction.md` — извлечение короткого контекста;
- `docs/modules/mobile_api.md` — bridge-модуль для Android;
- `docs/modules/context_providers.md` — optional provider layer;
- `docs/modules/plugin_loader.md` — загрузка built-in и opt-in external plugins.

## Тестирование

```bash
source .venv/bin/activate
PYTHONPATH=src pytest
xvfb-run -a env PYTHONPATH=src python tests/smoke_gui.py
```

Актуально для `v9`:

- `pytest`: **58 passed, 2 skipped**;
- desktop GUI smoke test: проходит;
- Android-ветка проверена на уровне структуры проекта, Python bridge и bundled assets;
- финальная сборка APK в этой среде не выполнялась.

## Ограничения текущей ветки

- desktop PDF по-прежнему требует текстовый слой;
- Argos ориентирован на **EN ↔ RU**;
- Android branch пока использует **ручной ввод слова**, а не tap-to-word selection по PDF;
- APK source включён, но финальная сборка APK в этом архиве не выполнена;
- external plugins требуют явного opt-in;
- cloud credentials хранятся локально в `settings.json`, хотя файл сохраняется с ограниченными правами доступа.
