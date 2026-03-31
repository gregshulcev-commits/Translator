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
from .utils.dictionary_builder import ensure_dictionary_database
from .utils.logging_utils import setup_logging


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Offline PDF word translator MVP")
    parser.add_argument("pdf", nargs="?", help="Optional PDF path to open on startup")
    return parser


def main() -> int:
    args = build_argument_parser().parse_args()

    config = AppConfig()
    config.ensure_runtime_directories()
    ensure_dictionary_database(config.starter_dictionary_csv, config.starter_dictionary_db)
    setup_logging(config.runtime_log_dir)

    registry = PluginLoader(config).load()
    dictionary_plugin = registry.default_dictionary_plugin()
    if dictionary_plugin is None:
        raise RuntimeError("Не найден словарный плагин")

    root = tk.Tk()
    root.option_add("*tearOff", False)

    if args.pdf:
        candidate = Path(args.pdf).expanduser().resolve()
        document_plugin = registry.document_plugin_for(candidate)
    else:
        candidate = None
        document_plugin = registry.document_plugins[0] if registry.document_plugins else None

    if document_plugin is None:
        raise RuntimeError("Не найден плагин для PDF")

    document_service = DocumentService(document_plugin)
    dictionary_service = DictionaryService(dictionary_plugin)
    workflow = TranslationWorkflow(document_service, dictionary_service)
    window = MainWindow(root, config, document_service, dictionary_service, workflow)

    if candidate is not None and candidate.exists():
        window.open_document_path(candidate)

    root.mainloop()
    return 0


if __name__ == "__main__":  # pragma: no cover - manual entry point only
    raise SystemExit(main())
