# `translation_workflow.py`

## Назначение

Ядро сценария «клик по слову → перевод».

## Вход

- `page_index`
- `x`, `y` в координатах страницы
- `direction` (`en-ru` или `ru-en`)

## Выход

`TranslationViewModel`:

- `token`
- `context`
- `lookup`
- `direction`

## Что изменилось в v4

Workflow теперь принимает **явное направление перевода**, а не полагается на один жёстко зашитый сценарий EN→RU.
