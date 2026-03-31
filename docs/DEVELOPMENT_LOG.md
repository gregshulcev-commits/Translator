# Development log

## 2026-03-30 — MVP v9 usability update

Сделано поверх merged source `v8`:

- проектная версия поднята до `v9`;
- добавлен root-level установщик `install_app.sh`;
- установщик создаёт launcher и desktop entry для Linux;
- добавлено отдельное notebook-окно настроек;
- размер UI-шрифта перенесён из toolbar в настройки;
- Argos runtime теперь можно установить из GUI;
- Argos-модели можно полностью вести из GUI без обязательного терминала;
- добавлен GUI-менеджмент установленных словарей с безопасным удалением пользовательских runtime-паков;
- извлечение контекста вынесено в отдельный helper и ограничено текущим блоком/строкой;
- обновлены документация и тестовые артефакты;
- Android source branch синхронизирован на `versionCode = 9`.

## Источник версии

`v9` выбран как следующая проектная версия после максимальной версии в текущих исходниках (`v8`).

## 2026-03-30 — MVP v8 merge

Сделано в рамках слияния двух исходных архивов:

- выбран `v7` как базовая ветка с Android/APK source branch;
- поверх неё перенесены исправления из fixed-ветки для `context_providers.py`, `main_window.py` и `settings_store.py`;
- сохранён `mobile_api.py` и Android layout из `v7`;
- сохранён read-only Argos help dialog с кнопкой копирования;
- возвращены responsive-исправления для каталога словарей, окна Argos и настройки провайдеров;
- возвращены улучшения LibreTranslate;
- `settings.json` переведён на атомарное сохранение и ограниченные права доступа `0600` на POSIX;
- external plugins переведены в режим explicit opt-in через `PDF_WORD_TRANSLATOR_ENABLE_EXTERNAL_PLUGINS=1`;
- `mobile_api.py` усилен проверкой dictionary paths на regular files;
- добавлены тесты на LibreTranslate/UI bugfixes и security hardening.
