# Development log

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

## v4 highlights

- fixed text-plugin base class mismatch;
- fixed composite dictionary plugin to fully implement the plugin API;
- added starter EN→RU and starter RU→EN packs;
- added bundled technical / literary packs;
- added lazy page rendering to reduce zoom freezes on large PDFs;
- added compound token splitting for `a/b` and `a\b`;
- added direction switching EN ↔ RU;
- added context provider port with Disabled / Argos / LibreTranslate / Yandex adapters;
- removed raw document sentence from the compact panel;
- added in-app dictionary catalog;
- added initial Argos model install helper;
- expanded test coverage and refreshed docs.
