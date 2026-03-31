# Лог разработки

## 2026-03-31 — MVP v10 install/update lifecycle

Сделано:

- проектная версия поднята до `v10`;
- добавлен `tools/desktop_manager.py` как единая точка install/update/uninstall логики;
- добавлены пользовательские скрипты `install_app.sh`, `uninstall_app.sh`, `update_app.sh`;
- добавлен миграционный скрипт `uninstall_previous_v9.sh` для удаления старой установки `v9`;
- схема установки изменена: payload больше не зависит от исходной распакованной папки;
- установленный desktop payload теперь живёт в `~/.local/share/pdf_word_translator_mvp_install/app/current/`;
- launcher, updater и uninstaller устанавливаются в `~/.local/bin/`;
- добавлен installation manifest с полями версии, payload path, repo URL, branch и source commit;
- update flow теперь может проверять Git remote через `git ls-remote`, скачивать свежую ревизию и переустанавливать приложение;
- installer переведён на `venv --system-site-packages`, чтобы использовать уже имеющиеся системные пакеты и доустанавливать только недостающее;
- runtime requirements отделены от dev requirements: добавлен `requirements-dev.txt`.

Почему принято именно так:

- пользователь явно попросил удобную установку, удаление и обновление;
- новая схема ближе к будущему RPM и меньше зависит от расположения исходников;
- separation между payload, runtime data и install metadata уменьшает хрупкость системы.

Ограничения итерации:

- RPM пока не собран;
- update flow ориентирован на Git/GitHub branch, а не на GitHub Releases;
- rollback до предыдущего payload пока не вынесен отдельной пользовательской командой.
