# `dictionary_service.py`

## Назначение

Тонкий фасад над активным `DictionaryPlugin`.

## Возможности

- lookup с учётом направления;
- hot-swap активного dictionary provider после импорта паков;
- информация о количестве паков и суммарном числе entries;
- список `DictionaryPackInfo` для UI / отладки.
