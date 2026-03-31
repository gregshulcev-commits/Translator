# Roadmap MVP v9

## Что уже сделано

### Desktop usability

- добавлен установщик приложения с launcher и desktop entry;
- добавлено единое окно настроек;
- размер UI-шрифта вынесен из главной панели в настройки;
- Argos runtime и модели теперь доступны через GUI;
- пользовательские словари теперь можно удалять из GUI;
- контекстный перевод ограничен локальным блоком/строкой.

### Desktop stability и security

- сохранены merge-исправления v8;
- `settings.json` сохраняется атомарно и с правами `0600` на POSIX;
- external Python plugins остаются opt-in;
- удаление словарей из GUI ограничено только пользовательской runtime-папкой.

### Mobile / APK branch

- сохранена директория `android-client/`;
- сохранён `mobile_api.py` как узкий bridge-модуль;
- обновлены Android version markers до `v9`.

### Test coverage

- добавлены тесты на извлечение компактного контекста;
- добавлены тесты на безопасное управление словарями;
- добавлены тесты на GUI-friendly установку Argos runtime;
- итоговый результат: `58 passed, 2 skipped`.

## Ближайшие шаги

1. Развить UX настроек и фоновых задач без усложнения архитектуры.
2. Добавить удаление Argos-моделей из GUI.
3. Продолжить развитие Android как отдельного клиента поверх `mobile_api.py`.

## Следующие практические задачи

- tap-to-word selection для Android PDF viewer;
- подготовка Gradle wrapper и воспроизводимой APK-сборки;
- опциональный прогресс-бар для длительных download/install операций;
- расширение provider diagnostics и offline-first сценариев;
- при необходимости — GUI для явного включения external plugins.
