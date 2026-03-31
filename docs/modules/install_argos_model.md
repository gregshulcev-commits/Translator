# `install_argos_model.py`

## Назначение

Optional helper для установки модели Argos Translate по одному направлению.

## Параметры

- `--from-lang`
- `--to-lang`

## Что делает

1. обновляет Argos package index;
2. ищет пакет нужного направления;
3. скачивает `.argosmodel`;
4. устанавливает его в пользовательское окружение.

## Примечание

Скрипт не ставит сам пакет `argostranslate`. Его нужно установить отдельно как optional dependency.
