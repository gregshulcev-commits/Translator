# `document_service.py`

## Назначение

Facade над document plugins и document session.

## Что делает

- хранит список доступных document plugins;
- выбирает plugin по расширению файла;
- открывает документ;
- кэширует отрендеренные страницы;
- отдаёт page count;
- умеет очищать render cache при zoom.

## Что изменилось в v3

Раньше сервис работал только с одним PDF-plugin. Теперь он:

- принимает несколько `DocumentPlugin`;
- умеет открывать PDF/TXT/FB2;
- отдаёт список поддерживаемых расширений для file dialog.
