# Актуальные ограничения MVP v9

## Desktop

- PDF-ветка по-прежнему требует **text layer**; OCR нет;
- перевод текста на изображениях не поддерживается;
- поддерживаются только **PDF / TXT / FB2**;
- Argos ориентирован на **EN ↔ RU**;
- удаление Argos-моделей из GUI пока не реализовано.

## Android branch

- Android-ветка включена как **исходный проект**, а не как уже собранный APK;
- tap-to-word selection по PDF ещё не реализован;
- координатная выборка слова внутри Android PDF viewer пока отсутствует;
- OCR и context provider layer внутри Android-клиента пока не подключены.

## Provider layer

- LibreTranslate требует либо self-hosted сервер, либо API key для публичного `libretranslate.com`;
- Yandex Cloud требует `Folder ID` и `API key` или `IAM token`;
- cloud credentials пока не вынесены в OS keychain и хранятся локально.

## Security / runtime

- external plugins по умолчанию отключены и требуют явного opt-in;
- `settings.json` сохраняется с ограниченными правами доступа, но это всё ещё локальный JSON-файл, а не отдельное secret storage;
- Android APK в этой среде не собирался, поэтому release-пайплайн не проверялся.
