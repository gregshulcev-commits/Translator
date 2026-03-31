"""Settings window for provider, UI and dictionary management."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..models import EN_RU, RU_EN, TranslationDirection
from ..providers.context_providers import (
    LIBRETRANSLATE_DEFAULT_URL,
    libretranslate_configuration_diagnostic,
    libretranslate_translate_url,
    normalize_libretranslate_url,
    probe_libretranslate_directions,
    yandex_configuration_diagnostic,
)
from ..utils.argos_manager import (
    ArgosManagerError,
    import_argos_model_from_path,
    install_argos_model_for_direction,
    install_argos_runtime,
    list_argos_models,
)
from ..utils.dictionary_manager import (
    DictionaryManagerError,
    InstalledDictionaryRecord,
    list_installed_dictionary_records,
    remove_installed_dictionary,
)
from ..utils.settings_store import UiSettings

if TYPE_CHECKING:  # pragma: no cover - import only for typing
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
        self.window.title("Настройки")
        self.window.geometry("1180x780")
        self.window.minsize(900, 620)
        self.window.transient(main_window.root)
        self.window.configure(background="#eef2f7")
        self.window.rowconfigure(0, weight=1)
        self.window.columnconfigure(0, weight=1)
        self.window.protocol("WM_DELETE_WINDOW", self.close)

        self._dictionary_records: dict[str, InstalledDictionaryRecord] = {}
        self._argos_state = None
        self._tabs: dict[str, ttk.Frame] = {}
        self._argos_tree: ttk.Treeview | None = None
        self._dictionary_tree: ttk.Treeview | None = None
        self._argos_status_var: tk.StringVar | None = None
        self._argos_hint_var: tk.StringVar | None = None
        self._dictionary_description_var: tk.StringVar | None = None
        self._dictionary_source_var: tk.StringVar | None = None

        self._build()
        self.refresh_all()

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

    def refresh_all(self) -> None:
        self._load_general_values()
        self._refresh_provider_tabs()
        self.refresh_argos_models(update_index=False)
        self.refresh_dictionary_records()

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

    def _build_general_tab(self) -> None:
        frame = self._add_tab("general", "Общие")
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Основные настройки", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")

        self.general_direction_var = tk.StringVar(value=EN_RU)
        self.general_provider_var = tk.StringVar(value="disabled")
        self.general_font_var = tk.StringVar(value="11")
        self.general_status_var = tk.StringVar(value="")

        direction_box = ttk.LabelFrame(frame, text="Направление перевода")
        direction_box.grid(row=1, column=0, sticky="ew", pady=(14, 10))
        ttk.Radiobutton(direction_box, text="EN → RU", value=EN_RU, variable=self.general_direction_var).grid(row=0, column=0, sticky="w", padx=10, pady=8)
        ttk.Radiobutton(direction_box, text="RU → EN", value=RU_EN, variable=self.general_direction_var).grid(row=0, column=1, sticky="w", padx=10, pady=8)

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
        ttk.Label(interface_box, text="Размер шрифта интерфейса:").grid(row=0, column=0, sticky="w", padx=(10, 6), pady=10)
        self.general_font_spinbox = tk.Spinbox(interface_box, from_=9, to=24, textvariable=self.general_font_var, width=6)
        self.general_font_spinbox.grid(row=0, column=1, sticky="w", pady=10)
        ttk.Label(interface_box, text="pt").grid(row=0, column=2, sticky="w", padx=(6, 0), pady=10)

        buttons = ttk.Frame(frame, style="App.TFrame")
        buttons.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(buttons, text="Применить общие настройки", command=self.apply_general_settings).grid(row=0, column=0, sticky="w")
        ttk.Button(buttons, text="Сбросить размер шрифта", command=self.reset_font_size).grid(row=0, column=1, padx=(8, 0), sticky="w")

        status_label = ttk.Label(frame, textvariable=self.general_status_var, style="Muted.TLabel", justify=tk.LEFT)
        status_label.grid(row=5, column=0, sticky="ew", pady=(12, 0))
        self.main_window._bind_wraplength_widgets(frame, (status_label,), padding=24, minimum=320)

    def _build_libretranslate_tab(self) -> None:
        frame = self._add_tab("libretranslate", "LibreTranslate")
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Настройка LibreTranslate", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        self.libre_url_var = tk.StringVar(value="")
        self.libre_api_var = tk.StringVar(value="")
        self.libre_endpoint_var = tk.StringVar(value="")
        self.libre_status_var = tk.StringVar(value="")

        ttk.Label(frame, text="URL сервера:").grid(row=1, column=0, sticky="w", pady=(14, 2))
        libre_url_entry = ttk.Entry(frame, textvariable=self.libre_url_var)
        libre_url_entry.grid(row=2, column=0, sticky="ew")
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
        ttk.Button(buttons, text="Сохранить настройки LibreTranslate", command=self.save_libretranslate_settings).grid(row=0, column=0, sticky="w")
        ttk.Button(buttons, text="Проверить EN ↔ RU", command=self.test_libretranslate_settings).grid(row=0, column=1, padx=(8, 0), sticky="w")

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
        ttk.Button(buttons, text="Сохранить настройки Yandex", command=self.save_yandex_settings).grid(row=0, column=0, sticky="w")

    def _build_argos_tab(self) -> None:
        frame = self._add_tab("argos", "Argos")
        frame.rowconfigure(2, weight=1)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Argos (офлайн)", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")
        intro_label = ttk.Label(
            frame,
            text=(
                "Здесь можно установить Python-зависимость Argos, обновить индекс моделей, "
                "скачать или импортировать .argosmodel и сразу выбрать Argos текущим провайдером."
            ),
            style="Context.TLabel",
            justify=tk.LEFT,
        )
        intro_label.grid(row=1, column=0, sticky="ew", pady=(8, 10))

        tree_container = ttk.Frame(frame, style="App.TFrame")
        tree_container.grid(row=2, column=0, sticky="nsew")
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        columns = ("direction", "status", "version", "package")
        tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=8, style="Catalog.Treeview")
        tree.heading("direction", text="Направление")
        tree.heading("status", text="Статус")
        tree.heading("version", text="Версия")
        tree.heading("package", text="Пакет")
        tree.column("direction", anchor="center")
        tree.column("status", anchor="center")
        tree.column("version", anchor="center")
        tree.column("package", anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        tree.bind("<<TreeviewSelect>>", self._on_argos_selection_changed)
        self._argos_tree = tree

        yscroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=tree.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=tree.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.main_window._bind_tree_column_layout(
            tree_container,
            tree,
            (
                _TreeColumnSpec("direction", 160, 18),
                _TreeColumnSpec("status", 200, 20),
                _TreeColumnSpec("version", 120, 12),
                _TreeColumnSpec("package", 320, 50),
            ),
        )

        self._argos_status_var = tk.StringVar(value="")
        self._argos_hint_var = tk.StringVar(value="")
        status_label = ttk.Label(frame, textvariable=self._argos_status_var, style="Context.TLabel", justify=tk.LEFT)
        status_label.grid(row=3, column=0, sticky="ew", pady=(12, 4))
        hint_label = ttk.Label(frame, textvariable=self._argos_hint_var, style="Muted.TLabel", justify=tk.LEFT)
        hint_label.grid(row=4, column=0, sticky="ew")
        self.main_window._bind_wraplength_widgets(frame, (intro_label, status_label, hint_label), padding=24, minimum=320)

        buttons = ttk.Frame(frame, style="App.TFrame")
        buttons.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(buttons, text="Установить поддержку Argos", command=self.install_argos_dependency).grid(row=0, column=0, sticky="w")
        ttk.Button(buttons, text="Обновить список из сети", command=lambda: self.refresh_argos_models(update_index=True)).grid(row=0, column=1, padx=(8, 0), sticky="w")
        ttk.Button(buttons, text="Установить выбранную модель", command=self.install_selected_argos_model).grid(row=0, column=2, padx=(8, 0), sticky="w")
        ttk.Button(buttons, text="Импортировать .argosmodel…", command=self.import_argos_model_from_dialog).grid(row=0, column=3, padx=(8, 0), sticky="w")
        ttk.Button(buttons, text="Использовать Argos", command=self.use_argos_provider).grid(row=0, column=4, padx=(8, 0), sticky="w")

    def _build_dictionary_tab(self) -> None:
        frame = self._add_tab("dictionaries", "Словари")
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        ttk.Label(frame, text="Управление словарями", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w")

        tree_container = ttk.Frame(frame, style="App.TFrame")
        tree_container.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        columns = ("title", "direction", "category", "location")
        tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=10, style="Catalog.Treeview")
        tree.heading("title", text="Пакет")
        tree.heading("direction", text="Направление")
        tree.heading("category", text="Категория")
        tree.heading("location", text="Где находится")
        tree.column("title", anchor="w")
        tree.column("direction", anchor="center")
        tree.column("category", anchor="center")
        tree.column("location", anchor="w")
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
                _TreeColumnSpec("title", 240, 28),
                _TreeColumnSpec("direction", 120, 14),
                _TreeColumnSpec("category", 140, 14),
                _TreeColumnSpec("location", 300, 44),
            ),
        )

        self._dictionary_description_var = tk.StringVar(value="")
        self._dictionary_source_var = tk.StringVar(value="")
        description_label = ttk.Label(frame, textvariable=self._dictionary_description_var, style="Context.TLabel", justify=tk.LEFT)
        description_label.grid(row=2, column=0, sticky="ew", pady=(12, 4))
        source_label = ttk.Label(frame, textvariable=self._dictionary_source_var, style="Muted.TLabel", justify=tk.LEFT)
        source_label.grid(row=3, column=0, sticky="ew")
        self.main_window._bind_wraplength_widgets(frame, (description_label, source_label), padding=24, minimum=320)

        buttons = ttk.Frame(frame, style="App.TFrame")
        buttons.grid(row=4, column=0, sticky="ew", pady=(14, 0))
        ttk.Button(buttons, text="Обновить список", command=self.refresh_dictionary_records).grid(row=0, column=0, sticky="w")
        ttk.Button(buttons, text="Каталог…", command=self._open_dictionary_catalog_from_settings).grid(row=0, column=1, padx=(8, 0), sticky="w")
        ttk.Button(buttons, text="Подключить SQLite…", command=self._install_sqlite_from_settings).grid(row=0, column=2, padx=(8, 0), sticky="w")
        ttk.Button(buttons, text="Импортировать CSV…", command=self._import_csv_from_settings).grid(row=0, column=3, padx=(8, 0), sticky="w")
        ttk.Button(buttons, text="Импортировать FreeDict TEI…", command=self._import_freedict_from_settings).grid(row=0, column=4, padx=(8, 0), sticky="w")
        ttk.Button(buttons, text="Удалить выбранный", command=self.delete_selected_dictionary).grid(row=0, column=5, padx=(8, 0), sticky="w")

    # ------------------------------------------------------------------
    # General settings tab
    # ------------------------------------------------------------------
    def _load_general_values(self) -> None:
        settings = self.main_window.settings.normalized()
        self.general_direction_var.set(settings.direction)
        self.general_provider_var.set(settings.context_provider_id)
        self.general_font_var.set(str(settings.ui_font_size))
        self.general_status_var.set(
            f"Текущий провайдер: {self.main_window.context_service.provider_name()} · "
            f"направление: {self.main_window._direction_display(settings.direction)}"
        )

    def apply_general_settings(self) -> None:
        updated = UiSettings(**self.main_window.settings.__dict__)
        updated.direction = self.general_direction_var.get()
        updated.context_provider_id = self.general_provider_var.get()
        updated.ui_font_size = self.general_font_var.get()  # normalized later
        self._apply_settings(updated, status_message="Общие настройки сохранены")
        self._load_general_values()
        self._refresh_provider_tabs()

    def reset_font_size(self) -> None:
        self.general_font_var.set(str(UiSettings().ui_font_size))
        self.apply_general_settings()

    def _apply_settings(self, settings: UiSettings, *, status_message: str) -> None:
        mw = self.main_window
        previous = mw.settings.normalized()
        updated = settings.normalized()
        direction_changed = updated.direction != previous.direction
        provider_changed = updated.context_provider_id != previous.context_provider_id
        font_changed = updated.ui_font_size != previous.ui_font_size

        mw.settings = updated
        mw.settings_store.save(mw.settings)
        mw.context_service.update_settings(mw.settings)
        mw.provider_var.set(mw.settings.context_provider_id)
        mw.direction_var.set(mw.settings.direction)
        mw.direction_button.configure(text=mw._direction_display(mw.settings.direction))
        mw._refresh_dictionary_footer()

        if font_changed:
            mw._configure_styles()
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
        self._load_general_values()
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
            yandex_configuration_diagnostic(
                api_key=api_key,
                folder_id=folder_id,
                iam_token=iam_token,
            ).message
        )

    def save_yandex_settings(self) -> None:
        updated = UiSettings(**self.main_window.settings.__dict__)
        updated.yandex_folder_id = self.yandex_folder_var.get()
        updated.yandex_api_key = self.yandex_api_var.get()
        updated.yandex_iam_token = self.yandex_iam_var.get()
        self._apply_settings(updated, status_message="Настройки Yandex сохранены")
        if self.main_window.context_service.active_provider_id() == "yandex" and self.main_window.current_view_model is not None:
            self.main_window._start_context_translation(self.main_window.current_view_model)
        self._load_general_values()
        self._refresh_yandex_tab()

    # ------------------------------------------------------------------
    # Argos tab
    # ------------------------------------------------------------------
    def refresh_argos_models(self, *, update_index: bool) -> None:
        if self._argos_tree is None:
            return
        tree = self._argos_tree
        for item in tree.get_children():
            tree.delete(item)

        with self._busy_cursor():
            self._argos_state = list_argos_models(update_index=update_index)

        if self._argos_state is None:
            return

        for model in self._argos_state.models:
            tree.insert(
                "",
                tk.END,
                iid=model.direction,
                values=(
                    model.display_name,
                    self._argos_model_status_text(model),
                    model.package_version or "—",
                    model.package_name or "—",
                ),
            )
        current_direction = self.main_window.settings.direction
        if current_direction in tree.get_children(""):
            tree.selection_set(current_direction)
            tree.focus(current_direction)
        self._on_argos_selection_changed()
        if update_index:
            self.main_window._update_status("Argos: список моделей обновлён")

    def install_argos_dependency(self) -> None:
        requirements_file = self.main_window.config.project_root / "requirements-optional.txt"
        try:
            with self._busy_cursor():
                result = install_argos_runtime(requirements_file)
        except ArgosManagerError as exc:
            messagebox.showerror("Argos", str(exc))
            return
        self.main_window._update_status(result.message)
        messagebox.showinfo("Argos", result.message)
        self.refresh_argos_models(update_index=False)

    def install_selected_argos_model(self) -> None:
        direction = self._selected_argos_direction()
        if direction is None:
            messagebox.showinfo("Argos", "Сначала выберите направление в списке.")
            return
        try:
            with self._busy_cursor():
                result = install_argos_model_for_direction(direction)
        except ArgosManagerError as exc:
            messagebox.showerror("Argos", str(exc))
            return
        self.main_window._update_status(result.message)
        messagebox.showinfo("Argos", result.message)
        self.refresh_argos_models(update_index=False)
        if self.main_window.context_service.active_provider_id() == "argos" and self.main_window.current_view_model is not None:
            self.main_window._start_context_translation(self.main_window.current_view_model)

    def import_argos_model_from_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите локальную модель Argos",
            filetypes=[("Argos model", "*.argosmodel"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        try:
            with self._busy_cursor():
                result = import_argos_model_from_path(Path(path))
        except ArgosManagerError as exc:
            messagebox.showerror("Argos", str(exc))
            return
        self.main_window._update_status(result.message)
        messagebox.showinfo("Argos", result.message)
        self.refresh_argos_models(update_index=False)

    def use_argos_provider(self) -> None:
        updated = UiSettings(**self.main_window.settings.__dict__)
        updated.context_provider_id = "argos"
        self._apply_settings(updated, status_message="Контекстный провайдер переключён на Argos")
        self._load_general_values()
        self._refresh_provider_tabs()

    def _selected_argos_direction(self) -> TranslationDirection | None:
        if self._argos_tree is None:
            return None
        selection = self._argos_tree.selection()
        if selection:
            return str(selection[0])
        return self.main_window.settings.direction

    def _on_argos_selection_changed(self, _event: tk.Event | None = None) -> None:
        if self._argos_status_var is None or self._argos_hint_var is None:
            return
        if self._argos_state is None:
            self._argos_status_var.set("Argos ещё не инициализирован.")
            self._argos_hint_var.set("")
            return
        direction = self._selected_argos_direction()
        model = self._argos_state.for_direction(direction) if direction is not None else None
        if model is None:
            self._argos_status_var.set("Выберите направление, чтобы увидеть состояние модели Argos.")
            self._argos_hint_var.set("")
            return
        if not self._argos_state.dependency_ready:
            self._argos_status_var.set("Python-зависимость Argos ещё не установлена.")
            self._argos_hint_var.set(self._argos_state.dependency_error)
            return
        if model.installed:
            self._argos_status_var.set(f"{model.display_name}: локальная модель установлена.")
        elif model.available_for_download:
            self._argos_status_var.set(f"{model.display_name}: модель доступна для загрузки из сети.")
        else:
            self._argos_status_var.set(f"{model.display_name}: пакет пока не найден.")

        notes = model.notes
        if self._argos_state.index_error and not model.installed:
            notes = self._argos_state.index_error
        if model.download_url:
            notes = f"{notes} Источник: {model.download_url}".strip()
        self._argos_hint_var.set(notes)

    @staticmethod
    def _argos_model_status_text(model) -> str:
        if model.installed:
            return "Установлена"
        if model.available_for_download:
            return "Доступна из сети"
        return "Нет пакета"

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
        self._dictionary_description_var.set(
            f"{description} Удаление из GUI: {removable}."
        )
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
    # Refresh helpers for provider tabs
    # ------------------------------------------------------------------
    def _load_provider_values(self) -> None:
        settings = self.main_window.settings.normalized()
        self.libre_url_var.set(settings.libretranslate_url)
        self.libre_api_var.set(settings.libretranslate_api_key)
        self.yandex_folder_var.set(settings.yandex_folder_id)
        self.yandex_api_var.set(settings.yandex_api_key)
        self.yandex_iam_var.set(settings.yandex_iam_token)

    def _refresh_provider_tabs(self) -> None:
        self._load_provider_values()
        self._refresh_libretranslate_tab()
        self._refresh_yandex_tab()

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
