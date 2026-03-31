# Офлайн переводчик документов по клику на слово — MVP v10

## Что это

Проект состоит из двух связанных частей:

1. **desktop MVP** на Python + Tkinter для Linux;
2. **android-client** как отдельная APK/source-ветка.

Основной desktop-сценарий остаётся прежним:

- открыть PDF / TXT / FB2;
- кликнуть по слову;
- получить словарную подсказку;
- при необходимости использовать контекстный перевод для короткого локального фрагмента.

## Что сделано в v10

`v10` продолжает usability-ветку `v9`, но теперь фокус смещён на **удобную установку, удаление и обновление**.

### Основные изменения

- добавлен полноценный **desktop manager** на базе `tools/desktop_manager.py`;
- добавлены отдельные пользовательские скрипты:
  - `./install_app.sh`
  - `./uninstall_app.sh`
  - `./update_app.sh`
  - `./uninstall_previous_v9.sh`
- новый установщик больше **не привязывается к текущей распакованной папке**;
- при установке приложение копируется в управляемый каталог:

```text
~/.local/share/pdf_word_translator_mvp_install/app/current/
```

- launcher, updater и uninstaller ставятся в:

```text
~/.local/bin/
```

- установка теперь создаёт:
  - `~/.local/bin/pdf-word-translator-mvp`
  - `~/.local/bin/pdf-word-translator-mvp-update`
  - `~/.local/bin/pdf-word-translator-mvp-uninstall`
  - `~/.local/share/applications/pdf-word-translator-mvp.desktop`
  - `~/.local/share/icons/hicolor/256x256/apps/pdf-word-translator-mvp.png`
- добавлена миграция с предыдущей схемы установки `v9`:
  - `./uninstall_previous_v9.sh` удаляет launcher-based установку из `v9`;
  - старые исходники не удаляются, удаляются только интеграция в систему и старый `.venv`;
- установщик создаёт venv с `--system-site-packages`, чтобы:
  - использовать уже установленные системные Python-пакеты, если они подходят;
  - доустанавливать только отсутствующие зависимости;
  - не терять изоляцию приложения;
- добавлена поддержка обновления из GitHub-репозитория:
  - можно привязать repo и branch;
  - можно проверить наличие обновления;
  - можно скачать свежую ревизию и переустановить приложение поверх текущей версии;
- структура установки подготовлена так, чтобы её было проще перенести в будущий **RPM-пакет**.

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
- запускаться из меню приложений Linux после установки;
- обновляться из GitHub через отдельный update-скрипт.

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
- готовый собранный APK внутри архива;
- RPM-пакет в текущем архиве.

## Быстрая миграция с v9

Если у вас уже стоит предыдущая версия, которую я присылал раньше, сначала выполните:

```bash
./uninstall_previous_v9.sh
```

Что сделает скрипт:

- удалит старый launcher `v9`;
- удалит desktop entry и icon `v9`;
- удалит старый `.venv`, который лежал рядом с исходниками `v9`;
- **не удалит** ваши исходники и пользовательские данные.

После этого можно ставить новую схему `v10`.

## Установка desktop-приложения

### Базовая установка

```bash
./install_app.sh
```

Что делает установщик:

1. копирует проект в управляемый каталог установки;
2. создаёт `.venv` внутри установленной копии;
3. использует `--system-site-packages`, чтобы по возможности брать уже имеющиеся пакеты из системы;
4. ставит runtime-зависимости из `requirements.txt`;
5. по умолчанию пытается установить optional-зависимости из `requirements-optional.txt`;
6. устанавливает базовые словари;
7. создаёт launcher, updater, uninstaller, desktop entry и icon.

### Базовый режим без optional-зависимостей

```bash
./install_app.sh --skip-optional
```

Это полезно, если вы хотите поставить только основной desktop-режим, а Argos runtime добавить позже из GUI.

### Где оказываются файлы

Установленная копия приложения:

```text
~/.local/share/pdf_word_translator_mvp_install/app/current/
```

Команды запуска и обслуживания:

```text
~/.local/bin/pdf-word-translator-mvp
~/.local/bin/pdf-word-translator-mvp-update
~/.local/bin/pdf-word-translator-mvp-uninstall
```

Runtime-данные пользователя, как и раньше, хранятся отдельно:

```text
~/.local/share/pdf_word_translator_mvp/
~/.cache/pdf_word_translator_mvp/
```

## Удаление

### Удалить приложение, но сохранить пользовательские данные

```bash
./uninstall_app.sh
```

или после установки:

```bash
~/.local/bin/pdf-word-translator-mvp-uninstall
```

Что удаляется:

- установленная копия приложения;
- launcher, updater, uninstaller;
- desktop entry;
- icon.

Что сохраняется:

- `settings.json`;
- пользовательские словари;
- кэш и runtime-данные.

### Полное удаление вместе с пользовательскими данными

```bash
./uninstall_app.sh --purge-data
```

## Обновление из GitHub

### 1. Привязать репозиторий

Если приложение было установлено не из git clone, а из архива, сначала привяжите GitHub-источник:

```bash
./update_app.sh --set-repo https://github.com/USER/REPO.git --branch main
```

### 2. Проверить наличие обновления

```bash
./update_app.sh --check-only
```

### 3. Обновить приложение

```bash
./update_app.sh
```

Скрипт:

- сравнивает установленную ревизию с remote branch;
- сообщает, есть ли обновление;
- спрашивает подтверждение;
- скачивает свежий код через `git clone --depth 1`;
- запускает installer из новой ревизии;
- переключает установленную копию на новый payload.

Для неинтерактивного режима:

```bash
./update_app.sh --yes
```

## Как загрузить проект на GitHub

### Вариант 1. Если вы начинаете с распакованного архива

```bash
git init
git add .
git commit -m "Initial import v10"
git branch -M main
git remote add origin https://github.com/USER/REPO.git
git push -u origin main
```

### Вариант 2. Если хотите продолжать работу из локального git clone

```bash
git clone https://github.com/USER/REPO.git
cd REPO
# перенесите сюда файлы проекта, если нужно
git add .
git commit -m "Import current sources"
git push
```

### Рекомендуемый рабочий порядок

1. распаковать архив;
2. загрузить исходники в GitHub;
3. выполнить `./install_app.sh`;
4. если установка была сделана до привязки GitHub, выполнить `./update_app.sh --set-repo ...`;
5. в дальнейшем обновлять приложение через `./update_app.sh`.

Подробная инструкция сохранена также в `docs/GITHUB_UPDATE_WORKFLOW.md`.

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

Единое окно **«Настройки»** используется как главный центр конфигурации.

Во вкладках доступны:

- **Общие** — направление перевода, активный провайдер, размер UI-шрифта;
- **LibreTranslate** — URL, API key, проверка EN ↔ RU;
- **Yandex Cloud** — Folder ID, API key, IAM token;
- **Argos** — установка runtime, список моделей, download/import/use;
- **Словари** — просмотр пакетов, импорт и удаление пользовательских словарей.

## Контекстный фрагмент

Провайдерам передаётся более короткий и локальный контекст:

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
- `docs/ARCHITECTURE.md` — архитектура desktop, provider layer, install/update layer и mobile bridge;
- `docs/GITHUB_UPDATE_WORKFLOW.md` — как публиковать исходники в GitHub и обновлять установленную копию;
- `docs/ANDROID_STATUS.md` — состояние APK-ветки;
- `docs/MODULES_INDEX.md` — индекс модулей;
- `docs/ROADMAP.md` — сделанное и следующие шаги;
- `docs/KNOWN_LIMITATIONS.md` — актуальные ограничения;
- `docs/PLUGIN_SYSTEM.md` — политика загрузки built-in и external plugins;
- `docs/modules/desktop_installer.md` — install/update/uninstall manager;
- `docs/modules/main_window.md` — desktop UI слой;
- `docs/modules/settings_dialog.md` — окно настроек;
- `docs/modules/dictionary_manager.md` — безопасное управление runtime-словарями;
- `docs/modules/context_extraction.md` — извлечение короткого контекста;
- `docs/modules/mobile_api.md` — bridge-модуль для Android;
- `docs/modules/context_providers.md` — optional provider layer;
- `docs/modules/plugin_loader.md` — загрузка built-in и opt-in external plugins.

## Тестирование

```bash
python3 -m pip install -r requirements-dev.txt
PYTHONPATH=src pytest
xvfb-run -a env PYTHONPATH=src python tests/smoke_gui.py
```

Актуально для `v10`:

- `pytest`: см. `docs/TEST_REPORT.md`;
- desktop GUI smoke test: см. `docs/TEST_REPORT.md`;
- Android-ветка проверена на уровне структуры проекта, Python bridge и bundled assets;
- финальная сборка APK в этой среде не выполнялась.

## Ограничения текущей ветки

- desktop PDF по-прежнему требует текстовый слой;
- Argos ориентирован на **EN ↔ RU**;
- Android branch пока использует **ручной ввод слова**, а не tap-to-word selection по PDF;
- APK source включён, но финальная сборка APK в этом архиве не выполнена;
- external plugins требуют явного opt-in;
- cloud credentials хранятся локально в `settings.json`, хотя файл сохраняется с ограниченными правами доступа;
- update-скрипт доверяет только тому Git-репозиторию, который пользователь сам указал в `--set-repo`.
