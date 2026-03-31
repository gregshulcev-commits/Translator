# Test report for the delivered MVP

## Environment used

- Python 3.13
- Tk 8.6
- PyMuPDF
- Pillow
- pronouncing
- pytest
- Xvfb for headless GUI smoke test

## Automated test results

### 1. Unit + integration tests

Command:

```bash
PYTHONPATH=src pytest
```

Result:

```text
9 passed
```

### 2. GUI smoke test

Command:

```bash
xvfb-run -a env PYTHONPATH=src python3 tests/smoke_gui.py
```

Result:

- passed;
- main window created;
- sample PDF opened;
- click-to-translate workflow updated the right panel correctly.

## Real PDF verification performed in this environment

A direct workflow check was executed on:

- `IRIO_EPICS_Device_Driver_User's_Manual__RAJ9P8_v1_7.pdf`

Verified scenario:

- the real uploaded PDF opens successfully;
- the token `driver` is found in the document;
- lookup returns `драйвер`;
- context sentence is extracted from the document.

## Bug fixed during testing

### Bug

`tk.Canvas` does not have a `.see()` method.

### Symptom

GUI smoke test crashed while trying to keep the selected rectangle visible.

### Fix

A dedicated helper `_scroll_rect_into_view()` was added to `ui/main_window.py`, and both word-highlight and search-highlight now scroll the canvas using `xview_moveto()` / `yview_moveto()`.

## Remaining warnings

The package `pronouncing` emits a deprecation warning about `pkg_resources`. This does **not** break the MVP, but it is worth cleaning up in a later iteration by pinning or replacing the transcription helper.


## Raw outputs stored in repository

- `docs/test_artifacts/pytest_output.txt`
- `docs/test_artifacts/smoke_output.txt`
