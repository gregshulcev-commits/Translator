# `plugin_loader.py`

## Назначение

Загрузчик builtin и внешних плагинов.

## Что делает

- регистрирует document plugins:
  - PDF / PyMuPDF;
  - TXT;
  - FB2;
- собирает composite dictionary plugin из:
  - встроенного EN→RU словаря;
  - встроенного RU→EN словаря;
  - всех runtime `*.sqlite` packs;
  - внешних dictionary plugins.

## Важная деталь v4

Теперь loader поднимает **оба встроенных направления** уже на старте, чтобы UI мог переключать EN ↔ RU без переинициализации приложения.
