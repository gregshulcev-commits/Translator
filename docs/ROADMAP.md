# Roadmap

## Сделано в MVP v7

### Desktop

- просмотр PDF / TXT / FB2;
- клик по слову и компактная словарная карточка;
- поиск по документу;
- непрерывная прокрутка и zoom до 800%;
- lazy render видимых страниц;
- bundled SQLite-словари EN→RU и RU→EN;
- каталог словарных пакетов;
- optional provider layer;
- offline Argos workflow с GUI manager;
- исправления v5 по scroll-back, Treeview rowheight, async queue и `settings.json`;
- исправление v7 для **окна справки Argos**: теперь оно растягивается и позволяет копировать команды.

### Android / APK branch

- создана директория `android-client/`;
- добавлен native Android UI prototype;
- добавлен `mobile_api.py` как общий словарный bridge;
- добавлен bootstrap встроенных SQLite assets;
- добавлен PDF render prototype через Android API;
- добавлен ручной словарный lookup внутри Android-клиента.

## Ближайший следующий шаг (desktop)

- удаление словарей из GUI;
- удаление Argos-моделей из GUI;
- прогресс-бар или фоновые job-ы для сетевых операций;
- сохранить last-opened document и last-view position;
- улучшить rendering performance ещё сильнее.

## Ближайший следующий шаг (Android)

- tap-to-word selection по PDF;
- слой text/token coordinates для Android viewer;
- повторное использование контекстного provider layer там, где это уместно;
- baseline UX для планшетов и телефонов;
- добавить Gradle wrapper и зафиксировать сборочный pipeline.

## Следующий слой перевода

- расширить набор offline-моделей и направлений поверх manager pattern;
- добавить выбор источника второй строки: provider result / dictionary example / both;
- попробовать file-level neural translation как отдельный слой, не ломая словарный MVP.

## v1.1

- OCR-plugin;
- постраничное распознавание;
- редактирование OCR-результата пользователем;
- поддержка текста на изображениях.

## v1.2

- EPUB / DOCX plugins;
- пользовательские профили словарей;
- экспорт незнакомых слов.

## v2

- полноценный Android-клиент с tap-to-word workflow;
- стабильный pipeline сборки APK;
- translation plugin layer для фраз и предложений;
- нейронный перевод как optional pack / model family;
- возможная смена desktop GUI backend-а при сохранении сервисов и словарного слоя.
