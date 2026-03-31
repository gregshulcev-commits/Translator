# `main_window.py`

## Назначение

Главное окно desktop-приложения на Tkinter.

## Основные части

- menu bar;
- toolbar;
- scrolling canvas;
- нижняя панель краткой словарной подсказки;
- statusbar;
- context menu для словарей;
- каталог словарных паков;
- меню и диалог настроек контекстных провайдеров;
- GUI manager для офлайн-моделей Argos;
- **resizable help dialog** для длинной справки по Argos.

## Основные сценарии

- открытие PDF / TXT / FB2 через `DocumentService`;
- непрерывный scroll всего документа;
- zoom через кнопки и `Ctrl + колесо мыши`;
- ленивый рендер видимых страниц;
- клик по слову;
- подсветка слова;
- поиск и навигация по поиску;
- импорт словарей без выхода из программы;
- выбор направления EN ↔ RU;
- запуск контекстного перевода через provider layer;
- установка и импорт Argos-моделей из GUI;
- изменение размера интерфейса с сохранением в settings.

## Важные детали v5/v6/v7

- `_redraw_overlays()` больше не вызывает принудительный scroll-back к highlight;
- `Catalog.Treeview` и Argos model manager используют rowheight, завязанный на реальные метрики текущего UI font size;
- результаты async контекстного перевода сначала попадают в очередь, а потом применяются в Tk main thread;
- окно **Перевод → Офлайн-модели Argos…** использует общий стиль каталога;
- `show_argos_installation_help()` больше не использует узкий `messagebox`; теперь длинный текст выводится через `_show_readonly_text_dialog()`.

## Ключевые методы

- `render_document()` — перестраивает layout страниц без обязательного рендера всех изображений;
- `_refresh_visible_pages()` — рендерит только видимые и соседние страницы;
- `change_zoom()` — меняет масштаб, сохраняя логическую точку под курсором;
- `process_click_at_page_coords()` — запускает workflow перевода по клику;
- `_start_context_translation()` — передаёт скрытый контекст выбранному провайдеру;
- `show_dictionary_catalog()` — открывает каталог устанавливаемых словарей;
- `show_argos_model_manager()` — открывает менеджер офлайн-моделей Argos;
- `install_selected_argos_model()` — ставит модель из индекса Argos;
- `import_argos_model_from_dialog()` — импортирует локальный `.argosmodel` файл;
- `_show_readonly_text_dialog()` — общее растягиваемое окно с длинным read-only текстом и кнопкой копирования.
