# Актуальные ограничения MVP v10

## Desktop

- desktop PDF по-прежнему требует текстовый слой;
- OCR в проект пока не добавлен;
- Argos ориентирован на `EN ↔ RU`;
- update-скрипт требует `git` для работы с удалённым репозиторием;
- updater доверяет репозиторию, который пользователь сам указал через `--set-repo`.

## Installation lifecycle

- RPM-пакет ещё не добавлен, хотя структура уже подготовлена под него;
- rollback до предыдущего payload пока не вынесен отдельной командой;
- автоматический фоновый check-update в GUI пока не реализован.

## Android branch

- Android branch пока использует ручной ввод слова, а не tap-to-word selection по PDF;
- APK source включён, но финальная сборка APK в этом архиве не выполнена;
- Gradle wrapper и воспроизводимый APK pipeline пока не доведены до финального состояния.

## Security / operational notes

- external plugins требуют явного opt-in;
- cloud credentials хранятся локально в `settings.json`, хотя файл сохраняется с ограниченными правами доступа.
