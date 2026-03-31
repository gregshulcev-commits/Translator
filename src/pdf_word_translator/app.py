"""Application entry point for the MVP."""
from __future__ import annotations

from pathlib import Path
import argparse
import tkinter as tk

from .config import AppConfig
from .plugin_loader import PluginLoader
from .services.dictionary_service import DictionaryService
from .services.document_service import DocumentService
from .services.translation_workflow import TranslationWorkflow
from .ui.main_window import MainWindow
from .utils.dictionary_builder import DictionaryMetadata, ensure_dictionary_database
from .utils.logging_utils import setup_logging
from .utils.settings_store import SettingsStore


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline document word translator MVP")
    parser.add_argument("document", nargs="?", help="Optional document path to open on startup")
    return parser


def main() -> int:
    args = build_argument_parser().parse_args()

    config = AppConfig()
    config.ensure_runtime_directories()
    ensure_dictionary_database(
        config.starter_dictionary_csv,
        config.starter_dictionary_db,
        metadata=DictionaryMetadata(
            pack_name="Встроенный технический EN→RU",
            direction="en-ru",
            pack_kind="technical",
            description="Компактный технический словарь, входящий в дистрибутив.",
            source=str(config.starter_dictionary_csv),
        ),
    )
    ensure_dictionary_database(
        config.starter_dictionary_ru_en_csv,
        config.starter_dictionary_ru_en_db,
        metadata=DictionaryMetadata(
            pack_name="Встроенный технический RU→EN",
            direction="ru-en",
            pack_kind="technical",
            description="Компактный технический словарь, входящий в дистрибутив.",
            source=str(config.starter_dictionary_ru_en_csv),
        ),
    )
    setup_logging(config.runtime_log_dir)

    plugin_loader = PluginLoader(config)
    registry = plugin_loader.load()
    dictionary_plugin = registry.default_dictionary_plugin()
    if dictionary_plugin is None:
        raise RuntimeError("Не найден словарный плагин")

    root = tk.Tk()
    root.option_add("*tearOff", False)

    candidate = None
    if args.document:
        candidate = Path(args.document).expanduser().resolve()

    document_service = DocumentService(registry.document_plugins)
    dictionary_service = DictionaryService(dictionary_plugin)
    workflow = TranslationWorkflow(document_service, dictionary_service)
    settings_store = SettingsStore(config.settings_file)
    window = MainWindow(
        root,
        config,
        plugin_loader,
        document_service,
        dictionary_service,
        workflow,
        settings_store,
    )

    if candidate is not None and candidate.exists():
        window.open_document_path(candidate)

    root.mainloop()
    return 0


if __name__ == "__main__":  # pragma: no cover - manual entry point only
    raise SystemExit(main())
