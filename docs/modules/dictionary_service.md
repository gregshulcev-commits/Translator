# `dictionary_service.py`

## Назначение

Тонкий facade над активным `DictionaryPlugin`.

## Методы

- `lookup(word)`
- `entry_count()`
- `pack_count()`

## Зачем нужен

Даже при текущей простоте он удерживает UI и workflow от прямой зависимости на конкретную реализацию словаря.
