"""Settings window for provider, UI, updates and dictionary management."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Callable
import queue
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk

from ..models import EN_RU, RU_EN, TranslationDirection
from ..providers.context_providers import (
    LIBRETRANSLATE_DEFAULT_URL,
    libretranslate_configuration_diagnostic,
    libretranslate_translate_url,
    normalize_libretranslate_url,
    probe_libretranslate_directions,
    yandex_configuration_diagnostic,
)
from ..utils.argos_manager import list_argos_models
from ..utils.desktop_metadata import collect_desktop_metadata, update_command
from ..utils.dictionary_manager import (
    DictionaryManagerError,
    InstalledDictionaryRecord,
    list_installed_dictionary_records,
    remove_installed_dictionary,
)
from ..utils.settings_store import UiSettings

if TYPE_CHECKING:  # pragma: no cover - typing only
    from .main_window import MainWindow


@dataclass(frozen=True)
class _TreeColumnSpec:
    column_id: str
    min_width: int
    weight: int


class SettingsDialog:
    """Notebook-based settings window used by :class:`MainWindow`."""

    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window
        self.window = tk.Toplevel(main_window.root)
        self.window.title("Параметры")
        self.main_window._apply_window_size(self.window, columns=100, rows=30, extra_width=260, extra_height=220)
        self.window.transient(main_window.root)
        self.window.rowconfigure(0, weight=1)
        self.window.columnconfigure(0, weight=1)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self._tabs: dict[str, ttk.Frame] = {}
        self._dictionary_records: dict[str, InstalledDictionaryRecord] = {}
        self._dictionary_tree: ttk.Treeview | None = None
        self._dictionary_description_var: tk.StringVar | None = None
        self._dictionary_source_var: tk.StringVar | None = None
        self._themed_text_widgets: list[tk.Text] = []

        self._event_queue: queue.Queue[tuple[str, str, object]] = queue.Queue()
        self._job_contexts: dict[str, dict[str, object]] = {}

        self._build()
        self.refresh_theme()
        self.refresh_all()
        self.window.after(120, self._poll_async_events)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def close(self) -> None:
        if self.window.winfo_exists():
            self.window.destroy()
        self.main_window._settings_dialog = None

    def focus_tab(self, tab_key: str) -> None:
        tab = self._tabs.get(tab_key)
        if tab is not None:
            self.notebook.select(tab)
        self.window.deiconify()
        self.window.lift()
        self.window.focus_force()

    def refresh_theme(self) -> None:
        palette = self.main_window._theme_palette()
        try:
            self.window.configure(background=palette["app_bg"])
        except tk.TclError:
            return
        for widget in list(self._themed_text_widgets):
            if not widget.winfo_exists():
                continue
            widget.configure(
                background=palette["surface_bg"],
                foreground=palette["text"],
                insertbackground=palette["text"],
                selectbackground=palette["selected_bg"],
                selectforeground=palette["selected_fg"],
            )

    def refresh_all(self) -> None:
        self._load_general_values()
        self._refresh_provider_tabs()
        self.refresh_argos_models(update_index=False)
        self.refresh_dictionary_records()
        self.refresh_update_metadata()

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------
    def _build(self) -> None:
        root_frame = ttk.Frame(self.window, padding=12, style="App.TFrame")
        root_frame.grid(row=0, column=0, sticky="nsew")
        root_frame.rowconfigure(0, weight=1)
        root_frame.columnconfigure(0, weight=1)

        self.notebook = ttk.Notebook(root_frame)
        self.notebook.grid(row=0, column=0, sticky="nsew")

        self._build_general_tab()
        self._build_updates_tab()
        self._build_libretranslate_tab()
        self._build_yandex_tab()
        self._build_argos_tab()
        self._build_dictionary_tab()

        actions = ttk.Frame(root_frame, style="App.TFrame")
        actions.grid(row=1, column=0, sticky="ew", pady=(10, 0))
        actions.columnconfigure(0, weight=1)
        ttk.Button(actions, text="Закрыть", command=self.close).grid(row=0, column=1, sticky="e")

    def _add_tab(self, key: str, title: str) -> ttk.Frame:
        frame = ttk.Frame(self.notebook, padding=14, style="App.TFrame")
        self.notebook.add(frame, text=title)
        self._tabs[key] = frame
        return frame

    def _register_text_widget(self, widget: tk.Text) -> None:
        self._themed_text_widgets.append(widget)
        self.refresh_theme()

    def _build_general_tab(self) -> None:
        frame = self._add_tab("general", "Общие")
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Основные настройки", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")

        self.general_direction_var = tk.StringVar(value=EN_RU)
        self.general_provider_var = tk.StringVar(value="disabled")
        self.general_font_var = tk.StringVar(value="11")
        self.general_scale_var = tk.StringVar(value="100")
        self.general_theme_var = tk.StringVar(value="dark")
        self.general_status_var = tk.StringVar(value="")

        direction_box = ttk.LabelFrame(frame, text="Направление перевода")
        direction_box.grid(row=1, column=0, sticky="ew", pady=(14, 10))
        ttk.Radiobutton(direction_box, text="EN → RU", value=EN_RU, variable=self.general_direction_var).grid(
            row=0, column=0, sticky="w", padx=10, pady=8
        )
        ttk.Radiobutton(direction_box, text="RU → EN", value=RU_EN, variable=self.general_direction_var).grid(
            row=0, column=1, sticky="w", padx=10, pady=8
        )

        provider_box = ttk.LabelFrame(frame, text="Контекстный перевод")
        provider_box.grid(row=2, column=0, sticky="ew", pady=(0, 10))
        for row_index, choice in enumerate(self.main_window.context_service.provider_choices()):
            ttk.Radiobutton(
                provider_box,
                text=f"{choice.display_name} — {choice.description}",
                value=choice.provider_id,
                variable=self.general_provider_var,
            ).grid(row=row_index, column=0, sticky="w", padx=10, pady=6)

        interface_box = ttk.LabelFrame(frame, text="Интерфейс")
        interface_box.grid(row=3, column=0, sticky="ew")
        ttk.Label(interface_box, text="Тема оформления:").grid(row=0, column=0, sticky="w", padx=(10, 6), pady=(10, 6))
        ttk.Radiobutton(interface_box, text="Светлая", value="light", variable=self.general_theme_var).grid(
            row=0, column=1, sticky="w", padx=(0, 10), pady=(10, 6)
        )
        ttk.Radiobutton(interface_box, text="Тёмная", value="dark", variable=self.general_theme_var).grid(
            row=0, column=2, sticky="w", pady=(10, 6)
        )

        ttk.Label(interface_box, text="Размер шрифта интерфейса:").grid(row=1, column=0, sticky="w", padx=(10, 6), pady=6)
        self.general_font_spinbox = tk.Spinbox(interface_box, from_=9, to=24, textvariable=self.general_font_var, width=6)
        self.general_font_spinbox.grid(row=1, column=1, sticky="w", pady=6)
        ttk.Label(interface_box, text="pt").grid(row=1, column=2, sticky="w", padx=(6, 0), pady=6)

        ttk.Label(interface_box, text="Масштаб интерфейса:").grid(row=2, column=0, sticky="w", padx=(10, 6), pady=(6, 10))
        self.general_scale_spinbox = tk.Spinbox(interface_box, from_=80, to=180, increment=10, textvariable=self.general_scale_var, width=6)
        self.general_scale_spinbox.grid(row=2, column=1, sticky="w", pady=(6, 10))
        ttk.Label(interface_box, text="%").grid(row=2, column=2, sticky="w", padx=(6, 0), pady=(6, 10))

        buttons = ttk.Frame(frame, style="App.TFrame")
        buttons.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(buttons, text="Применить настройки", command=self.apply_general_settings).grid(row=0, column=0, sticky="w")
        ttk.Button(buttons, text="Сбросить размер шрифта", command=self.reset_font_size).grid(
            row=0, column=1, padx=(8, 0), sticky="w"
        )

        status_label = ttk.Label(frame, textvariable=self.general_status_var, style="Muted.TLabel", justify=tk.LEFT)
        status_label.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        self.main_window._bind_wraplength_widgets(frame, (status_label,), padding=24, minimum=320)

    def _build_updates_tab(self) -> None:
        frame = self._add_tab("updates", "Обновления")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(4, weight=1)

        ttk.Label(frame, text="Обновление приложения", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        intro_label = ttk.Label(
            frame,
            text=(
                "Проверка обновлений и установка выполняются через desktop manager. "
                "Если источник GitHub ещё не привязан к установленной версии, в журнале будет подсказка, "
                "какую команду один раз выполнить в терминале."
            ),
            style="Context.TLabel",
            justify=tk.LEFT,
        )
        intro_label.grid(row=1, column=0, sticky="ew", pady=(8, 10))

        self.update_metadata_var = tk.StringVar(value="")
        self.update_status_var = tk.StringVar(value="")
        metadata_label = ttk.Label(frame, textvariable=self.update_metadata_var, style="Muted.TLabel", justify=tk.LEFT)
        metadata_label.grid(row=2, column=0, sticky="ew")

        buttons = ttk.Frame(frame, style="App.TFrame")
        buttons.grid(row=3, column=0, sticky="ew", pady=(10, 8))
        self.update_check_button = ttk.Button(buttons, text="Проверить наличие обновлений", command=self.check_updates_via_gui)
        self.update_check_button.pack(side=tk.LEFT)
        self.update_apply_button = ttk.Button(buttons, text="Обновить", command=self.apply_updates_via_gui)
        self.update_apply_button.pack(side=tk.LEFT, padx=(8, 0))

        self.update_progress = ttk.Progressbar(frame, mode="indeterminate")
        self.update_progress.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        self.update_log = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=14, relief="flat", borderwidth=0)
        self.update_log.grid(row=5, column=0, sticky="nsew")
        self._register_text_widget(self.update_log)

        status_label = ttk.Label(frame, textvariable=self.update_status_var, style="Muted.TLabel", justify=tk.LEFT)
        status_label.grid(row=6, column=0, sticky="ew", pady=(8, 0))
        self.main_window._bind_wraplength_widgets(frame, (intro_label, metadata_label, status_label), padding=24, minimum=320)

    def _build_libretranslate_tab(self) -> None:
        frame = self._add_tab("libretranslate", "LibreTranslate")
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Настройка LibreTranslate", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.libre_url_var = tk.StringVar(value="")
        self.libre_api_var = tk.StringVar(value="")
        self.libre_endpoint_var = tk.StringVar(value="")
        self.libre_status_var = tk.StringVar(value="")

        ttk.Label(frame, text="URL сервера:").grid(row=1, column=0, sticky="w", pady=(14, 2))
        ttk.Entry(frame, textvariable=self.libre_url_var).grid(row=2, column=0, sticky="ew")
        ttk.Label(frame, text="API key:").grid(row=3, column=0, sticky="w", pady=(10, 2))
        ttk.Entry(frame, textvariable=self.libre_api_var, show="*").grid(row=4, column=0, sticky="ew")

        endpoint_label = ttk.Label(frame, textvariable=self.libre_endpoint_var, style="Muted.TLabel", justify=tk.LEFT)
        endpoint_label.grid(row=5, column=0, sticky="ew", pady=(8, 4))
        hint_label = ttk.Label(
            frame,
            text=(
                f"Self-hosted по умолчанию: {LIBRETRANSLATE_DEFAULT_URL}. "
                "Можно указать базовый URL или полный endpoint /translate."
            ),
            style="Context.TLabel",
            justify=tk.LEFT,
        )
        hint_label.grid(row=6, column=0, sticky="ew")
        status_label = ttk.Label(frame, textvariable=self.libre_status_var, style="Muted.TLabel", justify=tk.LEFT)
        status_label.grid(row=7, column=0, sticky="ew", pady=(8, 0))
        self.main_window._bind_wraplength_widgets(frame, (endpoint_label, hint_label, status_label), padding=24, minimum=320)

        self.libre_url_var.trace_add("write", lambda *_args: self._refresh_libretranslate_tab())
        self.libre_api_var.trace_add("write", lambda *_args: self._refresh_libretranslate_tab())

        buttons = ttk.Frame(frame, style="App.TFrame")
        buttons.grid(row=8, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(buttons, text="Сохранить настройки LibreTranslate", command=self.save_libretranslate_settings).grid(
            row=0, column=0, sticky="w"
        )
        ttk.Button(buttons, text="Проверить EN ↔ RU", command=self.test_libretranslate_settings).grid(
            row=0, column=1, padx=(8, 0), sticky="w"
        )

    def _build_yandex_tab(self) -> None:
        frame = self._add_tab("yandex", "Yandex Cloud")
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Настройка Yandex Cloud", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.yandex_folder_var = tk.StringVar(value="")
        self.yandex_api_var = tk.StringVar(value="")
        self.yandex_iam_var = tk.StringVar(value="")
        self.yandex_status_var = tk.StringVar(value="")

        ttk.Label(frame, text="Folder ID:").grid(row=1, column=0, sticky="w", pady=(14, 2))
        ttk.Entry(frame, textvariable=self.yandex_folder_var).grid(row=2, column=0, sticky="ew")
        ttk.Label(frame, text="API key:").grid(row=3, column=0, sticky="w", pady=(10, 2))
        ttk.Entry(frame, textvariable=self.yandex_api_var, show="*").grid(row=4, column=0, sticky="ew")
        ttk.Label(frame, text="IAM token:").grid(row=5, column=0, sticky="w", pady=(10, 2))
        ttk.Entry(frame, textvariable=self.yandex_iam_var, show="*").grid(row=6, column=0, sticky="ew")

        status_label = ttk.Label(frame, textvariable=self.yandex_status_var, style="Muted.TLabel", justify=tk.LEFT)
        status_label.grid(row=7, column=0, sticky="ew", pady=(10, 0))
        self.main_window._bind_wraplength_widgets(frame, (status_label,), padding=24, minimum=320)

        buttons = ttk.Frame(frame, style="App.TFrame")
        buttons.grid(row=8, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(buttons, text="Сохранить настройки Yandex", command=self.save_yandex_settings).grid(
            row=0, column=0, sticky="w"
        )

    def _build_argos_tab(self) -> None:
        frame = self._add_tab("argos", "Argos")
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(5, weight=1)

        ttk.Label(frame, text="Argos (офлайн)", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        intro_label = ttk.Label(
            frame,
            text=(
                "Кнопка ниже запускает полный сценарий: установка optional dependency, загрузка моделей EN → RU и RU → EN, "
                "затем Argos автоматически выбирается провайдером по умолчанию. Ход выполнения пишется в журнал прямо в этом окне."
            ),
            style="Context.TLabel",
            justify=tk.LEFT,
        )
        intro_label.grid(row=1, column=0, sticky="ew", pady=(8, 10))

        self.argos_summary_var = tk.StringVar(value="")
        self.argos_status_var = tk.StringVar(value="")
        summary_label = ttk.Label(frame, textvariable=self.argos_summary_var, style="Muted.TLabel", justify=tk.LEFT)
        summary_label.grid(row=2, column=0, sticky="ew")

        self.argos_install_button = ttk.Button(frame, text="Установить поддержку Argos", command=self.install_argos_support)
        self.argos_install_button.grid(row=3, column=0, sticky="w", pady=(10, 8))

        self.argos_progress = ttk.Progressbar(frame, mode="indeterminate")
        self.argos_progress.grid(row=4, column=0, sticky="ew", pady=(0, 8))

        self.argos_log = scrolledtext.ScrolledText(frame, wrap=tk.WORD, height=14, relief="flat", borderwidth=0)
        self.argos_log.grid(row=5, column=0, sticky="nsew")
        self._register_text_widget(self.argos_log)

        status_label = ttk.Label(frame, textvariable=self.argos_status_var, style="Muted.TLabel", justify=tk.LEFT)
        status_label.grid(row=6, column=0, sticky="ew", pady=(8, 0))
        self.main_window._bind_wraplength_widgets(frame, (intro_label, summary_label, status_label), padding=24, minimum=320)

    def _build_dictionary_tab(self) -> None:
        frame = self._add_tab("dictionaries", "Словари")
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Управление словарями", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")

        tree_container = ttk.Frame(frame, style="App.TFrame")
        tree_container.grid(row=1, column=0, sticky="nsew", pady=(10, 0))
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        columns = ("title", "direction", "category", "location")
        tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=10, style="Catalog.Treeview")
        tree.heading("title", text="Словарь")
        tree.heading("direction", text="Направление")
        tree.heading("category", text="Категория")
        tree.heading("location", text="Расположение")
        tree.column("title", anchor="w")
        tree.column("direction", anchor="center")
        tree.column("category", anchor="center")
        tree.column("location", anchor="center")
        tree.grid(row=0, column=0, sticky="nsew")
        tree.bind("<<TreeviewSelect>>", self._on_dictionary_selection_changed)
        self._dictionary_tree = tree

        yscroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=tree.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=tree.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.main_window._bind_tree_column_layout(
            tree_container,
            tree,
            (
                _TreeColumnSpec("title", 240, 34),
                _TreeColumnSpec("direction", 120, 12),
                _TreeColumnSpec("category", 150, 18),
                _TreeColumnSpec("location", 180, 20),
            ),
        )

        details = ttk.Frame(frame, style="App.TFrame")
        details.grid(row=2, column=0, sticky="ew", pady=(10, 0))
        details.columnconfigure(0, weight=1)
        self._dictionary_description_var = tk.StringVar(value="Выберите словарь, чтобы увидеть его описание и доступные действия.")
        self._dictionary_source_var = tk.StringVar(value="")
        description_label = ttk.Label(details, textvariable=self._dictionary_description_var, style="Context.TLabel", justify=tk.LEFT)
        description_label.grid(row=0, column=0, sticky="ew")
        source_label = ttk.Label(details, textvariable=self._dictionary_source_var, style="Muted.TLabel", justify=tk.LEFT)
        source_label.grid(row=1, column=0, sticky="ew", pady=(4, 10))
        self.main_window._bind_wraplength_widgets(details, (description_label, source_label), padding=20, minimum=260)

        buttons = ttk.Frame(details, style="App.TFrame")
        buttons.grid(row=2, column=0, sticky="ew")
        buttons.columnconfigure(6, weight=1)
        ttk.Button(buttons, text="Каталог словарей…", command=self._open_dictionary_catalog_from_settings).grid(row=0, column=0, sticky="w")
        ttk.Button(buttons, text="FreeDict для текущего направления", command=self.main_window.install_default_dictionary_pack).grid(
            row=0, column=1, padx=(6, 0), sticky="w"
        )
        ttk.Button(buttons, text="SQLite…", command=self._install_sqlite_from_settings).grid(row=0, column=2, padx=(6, 0), sticky="w")
        ttk.Button(buttons, text="CSV…", command=self._import_csv_from_settings).grid(row=0, column=3, padx=(6, 0), sticky="w")
        ttk.Button(buttons, text="FreeDict TEI…", command=self._import_freedict_from_settings).grid(row=0, column=4, padx=(6, 0), sticky="w")
        ttk.Button(buttons, text="Удалить выбранный", command=self.delete_selected_dictionary).grid(row=0, column=5, padx=(6, 0), sticky="w")

    # ------------------------------------------------------------------
    # Value loading
    # ------------------------------------------------------------------
    def _load_general_values(self) -> None:
        settings = self.main_window.settings.normalized()
        self.general_direction_var.set(settings.direction)
        self.general_provider_var.set(settings.context_provider_id)
        self.general_font_var.set(str(settings.ui_font_size))
        self.general_scale_var.set(str(settings.ui_scale_percent))
        self.general_theme_var.set(settings.ui_theme)
        self.general_status_var.set(
            f"Текущий провайдер: {self.main_window.context_service.provider_name()} · "
            f"тема: {'тёмная' if settings.ui_theme == 'dark' else 'светлая'} · "
            f"масштаб UI: {settings.ui_scale_percent}%"
        )

    def _load_provider_values(self) -> None:
        settings = self.main_window.settings.normalized()
        self.libre_url_var.set(settings.libretranslate_url)
        self.libre_api_var.set(settings.libretranslate_api_key)
        self.yandex_folder_var.set(settings.yandex_folder_id)
        self.yandex_api_var.set(settings.yandex_api_key)
        self.yandex_iam_var.set(settings.yandex_iam_token)

    # ------------------------------------------------------------------
    # General settings
    # ------------------------------------------------------------------
    def apply_general_settings(self) -> None:
        updated = UiSettings(**self.main_window.settings.__dict__)
        updated.direction = self.general_direction_var.get()
        updated.context_provider_id = self.general_provider_var.get()
        updated.ui_font_size = int(self.general_font_var.get() or self.main_window.settings.ui_font_size)
        updated.ui_scale_percent = int(self.general_scale_var.get() or self.main_window.settings.ui_scale_percent)
        updated.ui_theme = self.general_theme_var.get() or self.main_window.settings.ui_theme
        self._apply_settings(updated, status_message="Настройки сохранены")
        self.general_status_var.set("Настройки сохранены и применены.")

    def reset_font_size(self) -> None:
        self.general_font_var.set(str(UiSettings.ui_font_size))
        self.apply_general_settings()

    def _apply_settings(self, settings: UiSettings, *, status_message: str) -> None:
        mw = self.main_window
        previous = mw.settings.normalized()
        updated = settings.normalized()
        direction_changed = updated.direction != previous.direction
        provider_changed = updated.context_provider_id != previous.context_provider_id

        mw.settings = updated
        mw.settings_store.save(mw.settings)
        mw.context_service.update_settings(mw.settings)
        mw.provider_var.set(mw.settings.context_provider_id)
        mw.direction_var.set(mw.settings.direction)
        mw._apply_ui_preferences(save=False)
        mw._refresh_dictionary_footer()
        mw._cancel_pending_context_translation()

        if direction_changed:
            mw._update_status(f"{status_message}: {mw._direction_display(mw.settings.direction)}")
            mw._retranslate_current_selection()
        elif provider_changed:
            mw._update_status(f"{status_message}: {mw.context_service.provider_name()}")
            if mw.current_view_model is not None:
                mw._populate_panel(mw.current_view_model)
                mw._start_context_translation(mw.current_view_model)
            else:
                mw.example_var.set(mw._provider_idle_text())
        else:
            mw._update_status(status_message)
        self._load_general_values()
        self._refresh_provider_tabs()

    # ------------------------------------------------------------------
    # Update tab
    # ------------------------------------------------------------------
    def refresh_update_metadata(self) -> None:
        metadata = collect_desktop_metadata(self.main_window.config.project_root)
        repo_text = metadata.repo_url or "не настроен"
        commit_text = metadata.commit_short or metadata.commit or "—"
        self.update_metadata_var.set(
            f"Версия: {metadata.version or '—'}\n"
            f"Commit: {commit_text}\n"
            f"Последнее обновление: {metadata.last_updated or '—'}\n"
            f"GitHub: {repo_text}"
        )

    def check_updates_via_gui(self) -> None:
        command = update_command(self.main_window.config.project_root, check_only=True)
        self._start_command_job(
            job_key="updates",
            commands=[command],
            log_widget=self.update_log,
            progressbar=self.update_progress,
            status_var=self.update_status_var,
            buttons=(self.update_check_button, self.update_apply_button),
            start_message="Проверяем наличие обновлений…",
            success_message="Проверка обновлений завершена.",
            success_callback=self.refresh_update_metadata,
        )

    def apply_updates_via_gui(self) -> None:
        command = update_command(self.main_window.config.project_root, check_only=False, yes=True)
        self._start_command_job(
            job_key="updates",
            commands=[command],
            log_widget=self.update_log,
            progressbar=self.update_progress,
            status_var=self.update_status_var,
            buttons=(self.update_check_button, self.update_apply_button),
            start_message="Устанавливаем обновление…",
            success_message="Обновление завершено. Перезапустите приложение.",
            success_callback=self._on_update_job_success,
        )

    def _on_update_job_success(self) -> None:
        self.refresh_update_metadata()
        self._append_log(self.update_log, "\n[OK] Обновление завершено. Перезапустите приложение.\n")

    # ------------------------------------------------------------------
    # LibreTranslate tab
    # ------------------------------------------------------------------
    def _refresh_libretranslate_tab(self) -> None:
        base_url = self.libre_url_var.get().strip() or self.main_window.settings.libretranslate_url
        api_key = self.libre_api_var.get().strip() or self.main_window.settings.libretranslate_api_key
        normalized = normalize_libretranslate_url(base_url)
        endpoint = libretranslate_translate_url(normalized)
        self.libre_endpoint_var.set(f"Эффективный endpoint: {endpoint or '—'}")
        self.libre_status_var.set(libretranslate_configuration_diagnostic(base_url, api_key).message)

    def save_libretranslate_settings(self) -> None:
        updated = UiSettings(**self.main_window.settings.__dict__)
        updated.libretranslate_url = self.libre_url_var.get()
        updated.libretranslate_api_key = self.libre_api_var.get()
        self._apply_settings(updated, status_message="Настройки LibreTranslate сохранены")
        if self.main_window.context_service.active_provider_id() == "libretranslate" and self.main_window.current_view_model is not None:
            self.main_window._start_context_translation(self.main_window.current_view_model)
        self._refresh_libretranslate_tab()

    def test_libretranslate_settings(self) -> None:
        diagnostic = libretranslate_configuration_diagnostic(self.libre_url_var.get(), self.libre_api_var.get())
        self.libre_status_var.set(diagnostic.message)
        if diagnostic.state == "error":
            messagebox.showwarning("LibreTranslate", diagnostic.message)
            return
        with self._busy_cursor():
            ok, report = self._probe_libretranslate_settings(self.libre_url_var.get(), self.libre_api_var.get())
        if ok:
            messagebox.showinfo("Проверка LibreTranslate", report)
        else:
            messagebox.showwarning("Проверка LibreTranslate", report)

    def _probe_libretranslate_settings(self, base_url: str, api_key: str) -> tuple[bool, str]:
        normalized = normalize_libretranslate_url(base_url)
        endpoint = libretranslate_translate_url(normalized)
        results = probe_libretranslate_directions(base_url, api_key, timeout=8)
        lines = [f"Сервер: {normalized or '—'}", f"Endpoint: {endpoint or '—'}"]
        all_ok = True
        for direction in (EN_RU, RU_EN):
            result = results.get(direction)
            if result is None or not result.ok:
                all_ok = False
                message = result.text if result is not None else "результат не получен"
                lines.append(f"{self.main_window._direction_display(direction)}: ошибка — {message}")
                continue
            lines.append(f"{self.main_window._direction_display(direction)}: OK — {result.text}")
        return all_ok, "\n".join(lines)

    # ------------------------------------------------------------------
    # Yandex tab
    # ------------------------------------------------------------------
    def _refresh_yandex_tab(self) -> None:
        folder_id = self.yandex_folder_var.get().strip() or self.main_window.settings.yandex_folder_id
        api_key = self.yandex_api_var.get().strip() or self.main_window.settings.yandex_api_key
        iam_token = self.yandex_iam_var.get().strip() or self.main_window.settings.yandex_iam_token
        self.yandex_status_var.set(
            yandex_configuration_diagnostic(api_key=api_key, folder_id=folder_id, iam_token=iam_token).message
        )

    def save_yandex_settings(self) -> None:
        updated = UiSettings(**self.main_window.settings.__dict__)
        updated.yandex_folder_id = self.yandex_folder_var.get()
        updated.yandex_api_key = self.yandex_api_var.get()
        updated.yandex_iam_token = self.yandex_iam_var.get()
        self._apply_settings(updated, status_message="Настройки Yandex сохранены")
        if self.main_window.context_service.active_provider_id() == "yandex" and self.main_window.current_view_model is not None:
            self.main_window._start_context_translation(self.main_window.current_view_model)
        self._refresh_yandex_tab()

    # ------------------------------------------------------------------
    # Argos tab
    # ------------------------------------------------------------------
    def refresh_argos_models(self, *, update_index: bool) -> None:
        state = list_argos_models(update_index=update_index)
        lines: list[str] = []
        if not state.dependency_ready:
            lines.append("Python-зависимость Argos пока не установлена.")
            if state.dependency_error:
                lines.append(state.dependency_error)
        else:
            lines.append("Состояние офлайн-моделей Argos:")
            for model in state.models:
                if model.installed:
                    status = "установлена"
                elif model.available_for_download:
                    status = "доступна для загрузки"
                else:
                    status = "пакет не найден"
                version = f" ({model.package_version})" if model.package_version else ""
                lines.append(f"• {model.display_name}: {status}{version}")
            if state.index_error:
                lines.append(state.index_error)
        self.argos_summary_var.set("\n".join(lines))

    def install_argos_support(self) -> None:
        project_root = self.main_window.config.project_root
        requirements_file = project_root / "requirements-optional.txt"
        script = project_root / "tools" / "install_argos_model.py"
        commands = [
            [sys.executable, "-m", "pip", "install", "--upgrade", "-r", str(requirements_file)],
            [sys.executable, str(script), "--from-lang", "en", "--to-lang", "ru"],
            [sys.executable, str(script), "--from-lang", "ru", "--to-lang", "en"],
        ]
        self._start_command_job(
            job_key="argos",
            commands=commands,
            log_widget=self.argos_log,
            progressbar=self.argos_progress,
            status_var=self.argos_status_var,
            buttons=(self.argos_install_button,),
            start_message="Устанавливаем поддержку Argos…",
            success_message="Поддержка Argos установлена и готова к работе.",
            success_callback=self._on_argos_install_success,
        )

    def _on_argos_install_success(self) -> None:
        updated = UiSettings(**self.main_window.settings.__dict__)
        updated.context_provider_id = "argos"
        self._apply_settings(updated, status_message="Argos выбран провайдером по умолчанию")
        self.refresh_argos_models(update_index=False)
        self._append_log(self.argos_log, "\n[OK] Поддержка Argos установлена. Провайдер Argos выбран по умолчанию.\n")

    # ------------------------------------------------------------------
    # Dictionary tab
    # ------------------------------------------------------------------
    def refresh_dictionary_records(self) -> None:
        if self._dictionary_tree is None:
            return
        tree = self._dictionary_tree
        for item in tree.get_children():
            tree.delete(item)
        self._dictionary_records = {}
        for record in list_installed_dictionary_records(self.main_window.config):
            iid = str(record.db_path)
            self._dictionary_records[iid] = record
            location = "Встроенный" if record.bundled else "Пользовательский"
            tree.insert(
                "",
                tk.END,
                iid=iid,
                values=(record.title, record.direction.upper(), record.category, location),
            )
        self._set_dictionary_details(None)

    def delete_selected_dictionary(self) -> None:
        record = self._selected_dictionary_record()
        if record is None:
            messagebox.showinfo("Словари", "Сначала выберите словарь в списке.")
            return
        if not record.removable:
            messagebox.showinfo("Словари", "Этот словарь встроен в приложение и не удаляется из GUI.")
            return
        confirmed = messagebox.askyesno(
            "Удаление словаря",
            f"Удалить пользовательский словарь «{record.title}»?\n\nФайл: {record.db_path.name}",
        )
        if not confirmed:
            return
        try:
            removed_path = remove_installed_dictionary(record, self.main_window.config)
        except DictionaryManagerError as exc:
            messagebox.showerror("Словари", str(exc))
            return
        self.main_window._reload_dictionary_plugin()
        self.main_window._update_status(f"Словарь удалён: {removed_path.name}")
        self.refresh_dictionary_records()

    def _selected_dictionary_record(self) -> InstalledDictionaryRecord | None:
        if self._dictionary_tree is None:
            return None
        selection = self._dictionary_tree.selection()
        if not selection:
            return None
        return self._dictionary_records.get(selection[0])

    def _on_dictionary_selection_changed(self, _event: tk.Event | None = None) -> None:
        self._set_dictionary_details(self._selected_dictionary_record())

    def _set_dictionary_details(self, record: InstalledDictionaryRecord | None) -> None:
        if self._dictionary_description_var is None or self._dictionary_source_var is None:
            return
        if record is None:
            self._dictionary_description_var.set("Выберите словарь, чтобы увидеть его описание и доступные действия.")
            self._dictionary_source_var.set("")
            return
        description = record.description or "Описание не указано."
        removable = "да" if record.removable else "нет"
        self._dictionary_description_var.set(f"{description} Удаление из GUI: {removable}.")
        self._dictionary_source_var.set(f"Файл: {record.db_path} · источник: {record.source or '—'}")

    def _open_dictionary_catalog_from_settings(self) -> None:
        self.main_window.show_dictionary_catalog()
        self.refresh_dictionary_records()

    def _install_sqlite_from_settings(self) -> None:
        self.main_window.install_sqlite_dictionary_pack()
        self.refresh_dictionary_records()

    def _import_csv_from_settings(self) -> None:
        self.main_window.import_csv_dictionary_pack()
        self.refresh_dictionary_records()

    def _import_freedict_from_settings(self) -> None:
        self.main_window.import_freedict_dictionary_pack()
        self.refresh_dictionary_records()

    # ------------------------------------------------------------------
    # Refresh helpers
    # ------------------------------------------------------------------
    def _refresh_provider_tabs(self) -> None:
        self._load_provider_values()
        self._refresh_libretranslate_tab()
        self._refresh_yandex_tab()

    # ------------------------------------------------------------------
    # Async job helpers
    # ------------------------------------------------------------------
    def _append_log(self, widget: tk.Text, text: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.insert(tk.END, text)
        widget.see(tk.END)
        widget.configure(state=tk.DISABLED)

    def _clear_log(self, widget: tk.Text) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.configure(state=tk.DISABLED)

    def _start_command_job(
        self,
        *,
        job_key: str,
        commands: list[list[str]],
        log_widget: tk.Text,
        progressbar: ttk.Progressbar,
        status_var: tk.StringVar,
        buttons: tuple[ttk.Button, ...],
        start_message: str,
        success_message: str,
        success_callback: Callable[[], None] | None = None,
    ) -> None:
        context = self._job_contexts.get(job_key)
        if context is not None and context.get("running"):
            status_var.set("Операция уже выполняется. Дождитесь завершения.")
            return

        self._clear_log(log_widget)
        status_var.set(start_message)
        progressbar.start(10)
        for button in buttons:
            button.configure(state=tk.DISABLED)
        self._job_contexts[job_key] = {
            "running": True,
            "log_widget": log_widget,
            "progressbar": progressbar,
            "status_var": status_var,
            "buttons": buttons,
            "success_message": success_message,
            "success_callback": success_callback,
        }

        def worker() -> None:
            try:
                for command in commands:
                    self._event_queue.put(("log", job_key, f"$ {' '.join(command)}\n"))
                    process = subprocess.Popen(
                        command,
                        cwd=str(self.main_window.config.project_root),
                        stdout=subprocess.PIPE,
                        stderr=subprocess.STDOUT,
                        text=True,
                        bufsize=1,
                    )
                    assert process.stdout is not None
                    with process.stdout:
                        for line in process.stdout:
                            self._event_queue.put(("log", job_key, line))
                    return_code = process.wait()
                    if return_code != 0:
                        self._event_queue.put(("finish", job_key, return_code))
                        return
                self._event_queue.put(("finish", job_key, 0))
            except Exception as exc:  # pragma: no cover - background worker failure path
                self._event_queue.put(("log", job_key, f"[ERROR] {exc}\n"))
                self._event_queue.put(("finish", job_key, 1))

        threading.Thread(target=worker, daemon=True).start()

    def _poll_async_events(self) -> None:
        try:
            while True:
                event_type, job_key, payload = self._event_queue.get_nowait()
                context = self._job_contexts.get(job_key)
                if context is None:
                    continue
                if event_type == "log":
                    self._append_log(context["log_widget"], str(payload))
                    continue
                if event_type == "finish":
                    context["running"] = False
                    context["progressbar"].stop()
                    for button in context["buttons"]:
                        button.configure(state=tk.NORMAL)
                    if int(payload) == 0:
                        context["status_var"].set(str(context["success_message"]))
                        callback = context.get("success_callback")
                        if callable(callback):
                            callback()
                    else:
                        context["status_var"].set("Операция завершилась с ошибкой. Подробности смотрите в журнале выше.")
        except queue.Empty:
            pass
        if self.window.winfo_exists():
            self.window.after(120, self._poll_async_events)

    # ------------------------------------------------------------------
    # Utilities
    # ------------------------------------------------------------------
    class _BusyCursor:
        def __init__(self, dialog: "SettingsDialog"):
            self.dialog = dialog

        def __enter__(self):
            self.dialog.main_window.root.configure(cursor="watch")
            self.dialog.window.configure(cursor="watch")
            self.dialog.window.update_idletasks()
            return self

        def __exit__(self, exc_type, exc, tb):
            self.dialog.main_window.root.configure(cursor="")
            self.dialog.window.configure(cursor="")
            return False

    def _busy_cursor(self) -> "SettingsDialog._BusyCursor":
        return SettingsDialog._BusyCursor(self)
