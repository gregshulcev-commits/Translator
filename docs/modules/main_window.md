# `main_window.py`

## Назначение

Главное окно Tkinter-приложения.

## Основные части

- menu bar;
- toolbar;
- scrolling canvas;
- нижняя панель краткой словарной подсказки;
- statusbar;
- context menu для словарей;
- каталог словарных паков;
- меню и диалог настроек контекстных провайдеров;
- **GUI manager для офлайн-моделей Argos**.

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

## Внутренние структуры

### `CanvasPageLayout`

Хранит положение каждой страницы внутри canvas и идентификаторы canvas items:

- прямоугольник-фон страницы;
- подпись номера страницы;
- image item, если страница уже отрендерена.

Это позволяет быстро вычислять:

- mapping canvas coords -> page coords;
- scroll to page;
- scroll to search hit / word highlight;
- page virtualization / lazy rendering.

## Важные детали v5/v6

- `_redraw_overlays()` больше не вызывает принудительный scroll-back к highlight;
- `Catalog.Treeview` и Argos model manager используют rowheight, завязанный на реальные метрики текущего UI font size;
- результаты async контекстного перевода сначала попадают в очередь, а потом применяются в Tk main thread;
- окно **Перевод → Офлайн-модели Argos…** использует тот же общий стиль, что и каталог словарей.

## Ключевые методы

- `render_document()` — перестраивает layout страниц без обязательного рендера всех изображений;
- `_refresh_visible_pages()` — рендерит только видимые и окрестные страницы;
- `change_zoom()` — меняет масштаб, сохраняя логическую точку под курсором;
- `process_click_at_page_coords()` — запускает workflow перевода по клику;
- `_start_context_translation()` — передаёт скрытый контекст выбранному провайдеру;
- `show_dictionary_catalog()` — открывает каталог устанавливаемых словарей;
- `show_argos_model_manager()` — открывает менеджер офлайн-моделей Argos;
- `install_selected_argos_model()` — ставит модель из индекса Argos;
- `import_argos_model_from_dialog()` — импортирует локальный `.argosmodel` файл.
