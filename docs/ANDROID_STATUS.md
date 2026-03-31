# Android-статус

## Короткий вывод

В этой итерации **рабочий APK не включён**.

Причина не в словарном или document-core слое, а в GUI-стеке: текущая версия приложения использует **Tkinter**, а официальный Android support в CPython прямо перечисляет `tkinter` среди unsupported modules на Android. Это значит, что честный перенос требует **отдельного мобильного UI-слоя**, а не просто "собрать текущий проект в APK".

## Что уже готово для будущей Android-ветки

Полезная часть проекта уже отделена от GUI:

- `services/`
- `models.py`
- `plugin_api.py`
- словарный SQLite-формат
- document plugins
- import/install tools

Это позволяет переносить не всё приложение, а только UI-слой.

## Реалистичные варианты Android-ветки

### Вариант A. Kivy

Плюсы:

- один Python codebase;
- Android packaging через Buildozer / python-for-android;
- быстрый путь к touch UI.

Минусы:

- нужно переписывать viewer и interaction layer;
- PDF stack и Android packaging для PyMuPDF придётся проверять отдельно.

### Вариант B. BeeWare / Toga

Плюсы:

- более native-looking UI;
- сильная долгосрочная стратегия для mobile Python.

Минусы:

- сейчас это более дорогой путь по времени;
- viewer и document interactions всё равно нужно проектировать отдельно.

### Вариант C. Qt/QML rewrite

Плюсы:

- хороший путь для desktop + Android в долгую;
- сильный нативный viewer-стек.

Минусы:

- это уже не "следующий маленький патч", а новая фаза проекта.

## Что рекомендовано дальше

Если Android важен уже в ближайшем цикле, практичный план такой:

1. заморозить desktop MVP на текущей архитектуре;
2. переиспользовать `services/`, `models.py`, dictionary format и import tools;
3. начать **отдельную Android-ветку** на Kivy или Qt/QML;
4. сначала поддержать TXT/FB2 и словари;
5. затем отдельно решать PDF viewer для Android.

## Источники для следующего этапа

- CPython Android support / unsupported modules:
  - `https://peps.python.org/pep-0738/`
- Kivy Android packaging:
  - `https://kivy.org/doc/stable-2.3.0/guide/packaging-android.html`
- BeeWare / Toga:
  - `https://beeware.org/docs/toga/`
