# Roadmap MVP v10

## Что уже сделано

### Desktop usability

- сохранено отдельное окно настроек;
- размер UI-шрифта вынесен из главной панели в настройки;
- Argos runtime и модели доступны через GUI;
- пользовательские словари можно удалять из GUI;
- контекстный перевод ограничен локальным блоком/строкой.

### Desktop install/update lifecycle

- добавлен новый install manager на базе `tools/desktop_manager.py`;
- добавлены `install_app.sh`, `uninstall_app.sh`, `update_app.sh`;
- добавлен миграционный скрипт `uninstall_previous_v9.sh`;
- desktop payload теперь ставится в отдельный install-home;
- install/update manifest хранится отдельно от runtime user data;
- update flow может использовать GitHub/Git remote как источник обновлений.

### Desktop stability и security

- сохранены merge-исправления `v8` и usability-правки `v9`;
- `settings.json` сохраняется атомарно и с правами `0600` на POSIX;
- external Python plugins остаются opt-in;
- удаление словарей из GUI ограничено только пользовательской runtime-папкой.

### Mobile / APK branch

- сохранена директория `android-client/`;
- сохранён `mobile_api.py` как узкий bridge-модуль;
- обновлены Android version markers до `v10`.

## Ближайшие шаги

1. Подготовить RPM-пакет поверх новой install-архитектуры.
2. Добавить rollback или отдельную команду для возврата к предыдущему payload.
3. Добавить удаление Argos-моделей из GUI.
4. Продолжить развитие Android как отдельного клиента поверх `mobile_api.py`.

## Следующие практические задачи

- RPM spec и сборка пакета для Linux;
- более формальный dependency split для runtime / dev / package build;
- опциональный GUI-индикатор доступного обновления;
- tap-to-word selection для Android PDF viewer;
- подготовка Gradle wrapper и воспроизводимой APK-сборки.
