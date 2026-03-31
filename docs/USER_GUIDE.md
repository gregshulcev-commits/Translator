# Руководство пользователя — MVP v8

## Какие части проекта входят в v8

В архив входят две связанные части:

1. desktop-приложение на Python + Tkinter;
2. Android source branch `android-client/`.

Готовый APK в архив **не входит**.

## Desktop: первый запуск

### Установка

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
PYTHONPATH=src python tools/install_default_dictionaries.py
PYTHONPATH=src python -m pdf_word_translator.app
```

### Открытие документа

Desktop умеет открывать:

- PDF;
- TXT;
- FB2.

Для PDF нужен текстовый слой.

## Базовый сценарий desktop

1. Откройте документ.
2. При необходимости переключите направление `EN → RU` или `RU → EN`.
3. Кликните по слову.
4. В нижней панели появится словарная карточка.
5. Если включён provider layer, во второй строке появится контекстный перевод предложения или статус провайдера.

## Поиск по документу

В toolbar есть строка поиска и кнопки:

- `Найти`;
- `Пред.`;
- `След.`.

Toolbar и строка поиска в `v8` снова работают в адаптивной раскладке.

## Масштабирование

Поддерживаются:

- кнопки `-` и `+`;
- `Ctrl + колесо мыши`.

Верхний предел масштабирования оставлен на уровне **800%**.

## Каталог словарей

Открывается через:

- кнопку **Словари**;
- меню словарей;
- контекстное меню нижней панели.

Через каталог можно:

- установить bundled CSV packs;
- скачать и собрать FreeDict packs;
- открыть источник словаря.

В `v8` открытие источника ограничено только `http/https` ссылками.

## Контекстный перевод

### LibreTranslate

Что важно:

- по умолчанию ожидается self-hosted адрес `http://127.0.0.1:5000`;
- можно указать базовый адрес или endpoint `/translate`;
- для публичного `libretranslate.com` нужен API key;
- в окне настройки есть проверка обоих направлений `EN ↔ RU`.

### Yandex Cloud

Нужно указать:

- `Folder ID`;
- `API key` или `IAM token`.

### Argos (офлайн)

Путь через GUI:

1. `python -m pip install -r requirements-optional.txt`
2. В приложении открыть **Перевод → Офлайн-модели Argos…**.
3. Нажать **Обновить список из сети**.
4. Установить модель.
5. Выбрать провайдер **Argos (офлайн)**.

Справка **«Как установить Argos…»** в `v8` открывается как отдельное растягиваемое окно с кнопкой копирования команд.

## Настройки и безопасность

Настройки сохраняются в:

```text
~/.local/share/pdf_word_translator_mvp/settings.json
```

В `v8` файл:

- сохраняется атомарно;
- на POSIX получает права `0600`.

## External plugins

Внешние Python-плагины по умолчанию **выключены**.

Для включения:

```bash
export PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS=1
```

## Android source branch

Android-клиент — это отдельный исходный Gradle-проект.

Что уже есть:

- Kotlin UI;
- Chaquopy bridge;
- PdfRenderer;
- bundled SQLite assets;
- `mobile_api.py` для словарного lookup.

Как открыть:

1. Запустите Android Studio.
2. Откройте `android-client/`.
3. Дождитесь Gradle sync.
4. Соберите `debug` APK из IDE.

Что пока не готово:

- tap-to-word selection;
- OCR;
- финальный APK в архиве.
