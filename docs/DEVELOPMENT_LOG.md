# Development log

## Iteration 1

- implemented package skeleton;
- separated config, models, plugin API, services, plugins and UI;
- implemented PDF plugin on PyMuPDF;
- implemented SQLite dictionary plugin;
- implemented starter dictionary CSV + SQLite builder;
- implemented Tk main window with right translation panel;
- implemented search;
- implemented page navigation and zoom.

## Iteration 2

- added automated tests;
- added integration tests for uploaded PDFs;
- added headless GUI smoke test with Xvfb.

## Iteration 3

- smoke test revealed a GUI bug: attempted to call `.see()` on `tk.Canvas`;
- replaced that logic with `_scroll_rect_into_view()`;
- reran tests and smoke test successfully.

## Next safe continuation point

If development is interrupted, continue from one of these isolated tracks:

1. improve dictionary coverage;
2. add word history module;
3. add OCR as a new document plugin;
4. replace Tk UI with Qt while keeping services/plugins intact.
