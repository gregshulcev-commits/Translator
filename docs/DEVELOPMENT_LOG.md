# Development log

## v7 highlights

- replaced the narrow Argos installation `messagebox` with a resizable read-only dialog;
- added copy-to-clipboard for long Argos setup commands;
- introduced `src/pdf_word_translator/mobile_api.py` as a JSON-friendly bridge for Android;
- added `android-client/` with Kotlin + Chaquopy + native PDF render prototype;
- bundled starter SQLite dictionaries into Android assets;
- refreshed README, Android docs, user guide, architecture, roadmap and module docs;
- added tests for `mobile_api.py`, v7 help dialog regression and Android branch layout.

## v6 highlights

- finished the v5 regression fixes and kept zoom ceiling at 800%;
- added `argos_manager.py` as a shared runtime/model lifecycle helper;
- added GUI window **Перевод → Офлайн-модели Argos…**;
- added online install and local `.argosmodel` import from GUI;
- extended `tools/install_argos_model.py` with `--list` and `--file`;
- made `ArgosContextProvider` return actionable setup hints instead of opaque runtime failures;
- refreshed README, user guide, architecture, roadmap and module docs to describe the new offline neural workflow;
- added tests for Argos runtime detection, install/import logic and provider hints.

## v5 highlights

- fixed highlight-induced scroll back on lazy redraw;
- fixed Treeview row height scaling for enlarged UI fonts;
- moved async provider result delivery into a queue processed on the Tk main thread;
- hardened `settings.json` loading against unknown keys and invalid values;
- clarified and validated `Folder ID` for Yandex Cloud.
