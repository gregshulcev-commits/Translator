# Roadmap MVP v8

## Что уже сделано

### Desktop stability

- merged desktop bugfix branch и Android source branch;
- восстановлены responsive-исправления для UI;
- возвращены исправления LibreTranslate и Argos diagnostics;
- сохранён расширенный Argos help dialog;
- сохранено масштабирование документа до 800%.

### Mobile / APK branch

- сохранена директория `android-client/`;
- сохранён `mobile_api.py` как узкий bridge-модуль;
- сохранены bundled SQLite assets и базовая Kotlin/Chaquopy интеграция.

### Security hardening

- `settings.json` сохраняется атомарно и с правами `0600` на POSIX;
- external Python plugins переведены в opt-in режим;
- mobile bridge отклоняет non-file dictionary paths.

### Test coverage

- объединены старые и новые regression tests;
- добавлены проверки LibreTranslate/UI bugfixes;
- добавлены проверки security hardening;
- итоговый результат: `49 passed, 2 skipped`.

## Ближайшие шаги

1. Продолжить развитие desktop-версии без переписывания архитектуры.
2. Усилить UX и тестирование provider layer.
3. Развить Android как отдельный клиент поверх `mobile_api.py`.

## Следующие практические задачи

- tap-to-word selection для Android PDF viewer;
- подготовка Gradle wrapper и воспроизводимой APK-сборки;
- удаление словарных паков и Argos-моделей из GUI;
- расширение provider diagnostics и offline-first сценариев;
- при необходимости — отдельный UX для явного включения external plugins из GUI/CLI.
