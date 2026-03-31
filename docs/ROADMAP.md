# Roadmap

## Сделано в MVP v6

- просмотр PDF;
- просмотр TXT и FB2;
- клик по слову и выделение;
- компактная нижняя карточка перевода;
- поиск по документу;
- непрерывная прокрутка всего документа;
- zoom по `Ctrl + колесо мыши`;
- zoom до 800%;
- ленивый рендер видимых страниц;
- split compound tokens (`a/b`, `a\b`);
- встроенные словари EN→RU и RU→EN;
- bundled technical / literary packs;
- каталог словарных пакетов;
- переключение EN ↔ RU;
- optional layer для контекстных провайдеров;
- настройка размера интерфейса;
- исправление scroll-back к выделенному слову;
- корректное масштабирование строк в списках при крупном UI font size;
- thread-safe доставка async provider result в Tk UI;
- устойчивый `settings.json`;
- явная валидация `Folder ID` для Yandex Cloud;
- **штатный сценарий офлайн-нейроперевода через Argos**;
- **GUI manager для установки и импорта Argos-моделей**;
- расширенный CLI helper `tools/install_argos_model.py`;
- автотесты и GUI smoke test.

## Ближайший следующий шаг (desktop)

- удаление словарей из GUI;
- удаление Argos-моделей из GUI;
- прогресс-бар или фоновые job-ы для тяжёлых сетевых установок;
- сохранить last-opened document и last-view position;
- добавить историю слов как отдельный plugin / service;
- улучшить rendering performance ещё сильнее (фоновые page jobs / prefetch queue);
- добавить clipboard helper.

## Следующий слой перевода

- расширить набор offline-моделей и направлений поверх того же manager pattern;
- добавить выбор источника второй строки: provider result / dictionary example / both;
- попробовать file-level neural translation как отдельный слой, не ломая словарный MVP.

## v1.1

- OCR-plugin;
- постраничное распознавание;
- редактирование OCR-результата пользователем;
- поддержка текста на изображениях;
- простая карточка истории слов.

## v1.2

- EPUB / DOCX plugins;
- пользовательские профили словарей;
- экспорт незнакомых слов.

## v2

- отдельный Android-клиент на другом UI-слое;
- полноценный translation plugin layer для фраз и предложений;
- нейронный перевод как optional pack / model family;
- смена GUI backend-а (Qt/QML, Kivy или другой мобильный стек);
- сборка и упаковка APK как отдельный pipeline, а не прямой перенос текущего Tkinter UI.
