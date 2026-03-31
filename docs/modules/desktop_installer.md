# Desktop install/update manager

## Назначение

Начиная с `v10` desktop-установка больше не ограничивается одним `install_app.sh`.

За установку, удаление и обновление отвечает связка:

- `install_app.sh`
- `uninstall_app.sh`
- `update_app.sh`
- `uninstall_previous_v9.sh`
- `tools/desktop_manager.py`

## Почему это важно

Это ответ на несколько пользовательских сценариев сразу:

- установить приложение одним файлом;
- удалить его без ручной чистки `~/.local/*`;
- убрать старую схему установки `v9`, где launcher зависел от текущей распакованной папки;
- получать обновления из GitHub без ручного переноса исходников.

## Роли компонентов

### `install_app.sh`

Тонкий shell-wrapper, который вызывает:

```text
tools/desktop_manager.py install
```

Он нужен для UX-сценария «запустить один файл из терминала».

### `uninstall_app.sh`

Вызывает:

```text
tools/desktop_manager.py uninstall
```

Удаляет установленный payload и системную интеграцию.

### `update_app.sh`

Вызывает:

```text
tools/desktop_manager.py update
```

Используется для проверки remote branch и переустановки из новой ревизии.

### `uninstall_previous_v9.sh`

Вызывает:

```text
tools/desktop_manager.py uninstall-v9
```

Служит миграционным скриптом для удаления старой v9 launcher-based схемы.

### `tools/desktop_manager.py`

Главный управляющий скрипт на Python stdlib.

Он:

- копирует исходники в управляемый install-home;
- создаёт `.venv` внутри установленной копии;
- использует `--system-site-packages`;
- устанавливает runtime dependencies;
- вызывает установку базовых словарей;
- пишет installation manifest;
- создаёт launcher / updater / uninstaller;
- может удалить установленную копию;
- может обновить её из Git-репозитория.

## Layout установки

### Installed payload

```text
~/.local/share/pdf_word_translator_mvp_install/app/current/
```

### Installation manifest

```text
~/.local/share/pdf_word_translator_mvp_install/metadata/installation.json
```

### User launchers

```text
~/.local/bin/pdf-word-translator-mvp
~/.local/bin/pdf-word-translator-mvp-update
~/.local/bin/pdf-word-translator-mvp-uninstall
```

### Desktop integration

```text
~/.local/share/applications/pdf-word-translator-mvp.desktop
~/.local/share/icons/hicolor/256x256/apps/pdf-word-translator-mvp.png
```

### User runtime data

Остаются отдельно от installed payload:

```text
~/.local/share/pdf_word_translator_mvp/
~/.cache/pdf_word_translator_mvp/
```

## Почему используется `--system-site-packages`

Это компромисс между чистой изоляцией и будущей RPM-совместимостью.

Плюсы:

- можно использовать уже установленные системные пакеты Python;
- если нужного пакета нет, `pip` доустанавливает его в `.venv`;
- установка остаётся предсказуемой и не трогает глобальный Python пользователя.

## Manifest

`installation.json` хранит:

- установленную версию;
- путь к текущему payload;
- путь к launcher;
- флаг optional dependencies;
- `repo_url` и `branch` для обновлений;
- установленный `source_commit`, если он известен.

## Update workflow

1. пользователь задаёт `repo_url` и `branch`;
2. manager делает `git ls-remote`;
3. сравнивает remote commit с установленным commit;
4. при наличии обновления делает временный `git clone --depth 1`;
5. запускает install-команду из новой ревизии;
6. переключает `app/current` на свежий payload.

## Почему это хорошо для будущего RPM

Новая структура уже отделяет:

- приложение как payload;
- runtime user data;
- install metadata;
- launchers и desktop-файлы.

Это уменьшает объём будущих изменений при переходе к RPM и упрощает определение того, что относится к пакету, а что относится к пользовательским данным.
