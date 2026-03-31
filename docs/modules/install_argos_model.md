# `install_argos_model.py`

## Назначение

CLI helper для проверки и установки offline-моделей Argos.

Скрипт нужен как fallback и companion к GUI manager из меню **Перевод → Офлайн-модели Argos…**.

## Поддерживаемые сценарии

### 1. Показать состояние моделей EN↔RU

```bash
PYTHONPATH=src python tools/install_argos_model.py --list
```

Показывает:

- установлена ли модель локально;
- доступна ли она в индексе Argos;
- версию найденного пакета;
- поясняющий статус.

### 2. Установить модель по направлению

```bash
PYTHONPATH=src python tools/install_argos_model.py --from-lang en --to-lang ru
PYTHONPATH=src python tools/install_argos_model.py --from-lang ru --to-lang en
```

### 3. Импортировать локальный `.argosmodel`

```bash
PYTHONPATH=src python tools/install_argos_model.py --file /path/to/model.argosmodel
```

## Что делает внутри

Скрипт использует общий helper `src/pdf_word_translator/utils/argos_manager.py` и не дублирует логику GUI.

То есть одинаковые правила действуют и для GUI, и для CLI:

- проверка наличия `argostranslate`;
- проверка/обновление индекса Argos;
- выбор нужного EN↔RU пакета;
- установка через `install_from_path()`;
- мягкие и человекочитаемые ошибки.

## Важное замечание

Скрипт не ставит сам пакет `argostranslate`. Его нужно установить отдельно:

```bash
python -m pip install -r requirements-optional.txt
```
