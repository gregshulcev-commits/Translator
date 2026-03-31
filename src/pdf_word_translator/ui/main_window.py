"""Tkinter main window for the offline document word translator MVP.

The UI deliberately keeps a small, readable footprint: the document remains the
main focus, while the translation help is shown in a compact panel at the
bottom. Rendering is lazy per page, which keeps zooming and scrolling usable on
large multi-page PDFs.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging
import queue
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, scrolledtext, ttk
import webbrowser
import urllib.parse

from PIL import ImageTk

from ..config import AppConfig
from ..models import (
    EN_RU,
    RU_EN,
    ContextTranslationResult,
    SearchHit,
    TranslationDirection,
    WordToken,
)
from ..plugin_loader import PluginLoader
from ..providers.context_providers import (
    LIBRETRANSLATE_DEFAULT_URL,
    ContextTranslationService,
    libretranslate_configuration_diagnostic,
    libretranslate_translate_url,
    normalize_libretranslate_url,
    probe_libretranslate_directions,
)
from ..services.dictionary_service import DictionaryService
from ..services.document_service import DocumentService
from ..services.translation_workflow import TranslationWorkflow, TranslationViewModel
from ..utils.argos_manager import (
    ArgosRuntimeState,
    argos_direction_ready,
    import_argos_model_from_path,
    install_argos_model_for_direction,
    install_argos_runtime,
    list_argos_models,
)
from ..utils.dictionary_catalog import DictionaryPackSpec
from ..utils.dictionary_installer import (
    available_catalog_items,
    import_csv_pack,
    import_freedict_pack,
    install_catalog_pack,
    install_default_pack,
    install_sqlite_pack,
)
from ..utils.settings_store import SettingsStore, UiSettings
from .settings_dialog import SettingsDialog


LOGGER = logging.getLogger(__name__)


@dataclass
class CanvasPageLayout:
    """Placement and canvas item IDs for one logical page."""

    page_index: int
    left: int
    top: int
    width: int
    height: int
    shadow_item: int | None = None
    background_item: int | None = None
    label_item: int | None = None
    image_item: int | None = None

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


@dataclass(frozen=True)
class TreeColumnSpec:
    column_id: str
    min_width: int
    weight: int


class MainWindow:
    """Main application window.

    The class keeps the UI logic together while relying on services for all
    document, dictionary and context-translation operations. That separation
    keeps the click workflow deterministic and unit-test friendly.
    """

    PAGE_MARGIN = 24
    PAGE_GAP = 22
    MIN_ZOOM = 0.5
    MAX_ZOOM = 8.0
    VISIBLE_RENDER_MARGIN_SCREENS = 1.2
    RENDER_STATUS_DELAY_MS = 90
    CONTEXT_RESULT_POLL_MS = 80

    def __init__(
        self,
        root: tk.Tk,
        config: AppConfig,
        plugin_loader: PluginLoader,
        document_service: DocumentService,
        dictionary_service: DictionaryService,
        workflow: TranslationWorkflow,
        settings_store: SettingsStore,
    ) -> None:
        self.root = root
        self.config = config
        self.plugin_loader = plugin_loader
        self.document_service = document_service
        self.dictionary_service = dictionary_service
        self.workflow = workflow
        self.settings_store = settings_store
        self.settings = settings_store.load().normalized()
        self.context_service = ContextTranslationService(self.settings)

        self.current_page_index = 0
        self.current_zoom = 1.20
        self.page_photos: dict[int, ImageTk.PhotoImage] = {}
        self.page_layouts: dict[int, CanvasPageLayout] = {}
        self.current_highlight_token: WordToken | None = None
        self.current_search_hits: list[SearchHit] = []
        self.current_search_index = -1
        self.current_view_model: TranslationViewModel | None = None
        self.search_rect_id: int | None = None
        self.word_rect_id: int | None = None
        self._viewport_update_scheduled = False
        self._visible_render_scheduled = False
        self._last_rendered_zoom: float | None = None
        self._active_context_request_id = 0
        self._context_result_queue: queue.Queue[tuple[int, ContextTranslationResult]] = queue.Queue()
        self._context_poll_scheduled = False
        self._catalog_window: tk.Toplevel | None = None
        self._catalog_tree: ttk.Treeview | None = None
        self._catalog_description_var: tk.StringVar | None = None
        self._catalog_source_var: tk.StringVar | None = None
        self._catalog_specs: dict[str, DictionaryPackSpec] = {}
        self._argos_window: tk.Toplevel | None = None
        self._argos_tree: ttk.Treeview | None = None
        self._argos_status_var: tk.StringVar | None = None
        self._argos_hint_var: tk.StringVar | None = None
        self._argos_runtime_state: ArgosRuntimeState | None = None
        self._settings_dialog: SettingsDialog | None = None

        self._build_window()
        self._schedule_context_result_poll()

    # ------------------------------------------------------------------
    # Window construction and styling
    # ------------------------------------------------------------------
    def _build_window(self) -> None:
        self.root.title("Офлайн переводчик документов — MVP")
        self.root.geometry("1420x940")
        self.root.configure(background="#eef2f7")
        self._configure_styles()

        self._build_menubar()
        self._build_toolbar()
        self._build_content()
        self._build_statusbar()
        self._bind_shortcuts()
        self._update_status("Готово. Откройте PDF, TXT или FB2-файл.")

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        ui = self.settings.ui_font_size
        for font_name in ("TkDefaultFont", "TkTextFont", "TkMenuFont", "TkHeadingFont", "TkCaptionFont"):
            try:
                named_font = tkfont.nametofont(font_name)
                named_font.configure(size=ui)
            except tk.TclError:
                pass

        default_font = tkfont.nametofont("TkDefaultFont")
        heading_font = tkfont.nametofont("TkHeadingFont")
        treeview_rowheight = self._treeview_rowheight(default_font.metrics("linespace"))

        style.configure("App.TFrame", background="#eef2f7")
        style.configure("Toolbar.TFrame", background="#eef2f7")
        style.configure("Surface.TFrame", background="#ffffff")
        style.configure("InfoCard.TFrame", background="#ffffff", relief="flat")
        style.configure("CardTitle.TLabel", background="#ffffff", foreground="#0f172a", font=("TkDefaultFont", ui + 1, "bold"))
        style.configure("Meta.TLabel", background="#ffffff", foreground="#475569", font=("TkDefaultFont", ui - 1))
        style.configure("BestTranslation.TLabel", background="#ffffff", foreground="#0f172a", font=("TkDefaultFont", ui + 3, "bold"))
        style.configure("Context.TLabel", background="#ffffff", foreground="#1e293b", font=("TkDefaultFont", ui))
        style.configure("Muted.TLabel", background="#ffffff", foreground="#64748b", font=("TkDefaultFont", ui - 1))
        style.configure("Status.TFrame", background="#dbe4ef")
        style.configure("Status.TLabel", background="#dbe4ef", foreground="#334155", font=("TkDefaultFont", ui - 1))
        style.configure("Toolbar.TButton", padding=(10, 5))
        style.configure("Catalog.Treeview", font=default_font, rowheight=treeview_rowheight)
        style.configure("Catalog.Treeview.Heading", font=heading_font, padding=(8, 4))

    @staticmethod
    def _treeview_rowheight(linespace: int) -> int:
        return max(24, int(linespace) + 10)

    @staticmethod
    def _responsive_wraplength(width: int, *, padding: int = 48, minimum: int = 320) -> int:
        return max(minimum, max(0, int(width)) - padding)

    @staticmethod
    def _responsive_tree_widths(
        total_width: int,
        *,
        minimums: tuple[int, ...],
        weights: tuple[int, ...],
        reserve: int = 36,
    ) -> tuple[int, ...]:
        if len(minimums) != len(weights):
            raise ValueError("minimums and weights must have identical length")
        if not minimums:
            return ()
        minimum_total = sum(int(value) for value in minimums)
        available = max(minimum_total, int(total_width) - reserve)
        extra = available - minimum_total
        total_weight = max(1, sum(int(weight) for weight in weights))
        widths: list[int] = []
        consumed = 0
        for index, (minimum, weight) in enumerate(zip(minimums, weights)):
            if index == len(minimums) - 1:
                width = available - consumed
            else:
                width = int(minimum) + (extra * int(weight)) // total_weight
            widths.append(max(int(minimum), width))
            consumed += widths[-1]
        return tuple(widths)

    @classmethod
    def _apply_tree_column_layout(
        cls,
        tree: ttk.Treeview,
        specs: tuple[TreeColumnSpec, ...],
        *,
        available_width: int,
    ) -> None:
        widths = cls._responsive_tree_widths(
            available_width,
            minimums=tuple(spec.min_width for spec in specs),
            weights=tuple(spec.weight for spec in specs),
        )
        for spec, width in zip(specs, widths):
            tree.column(spec.column_id, width=width, stretch=True)

    @classmethod
    def _bind_tree_column_layout(
        cls,
        container: tk.Misc,
        tree: ttk.Treeview,
        specs: tuple[TreeColumnSpec, ...],
    ) -> None:
        def on_configure(event: tk.Event | None = None) -> None:
            width = 0
            if event is not None:
                width = int(getattr(event, "width", 0) or 0)
            if width <= 0:
                try:
                    width = container.winfo_width()
                except tk.TclError:
                    width = 0
            if width > 0:
                cls._apply_tree_column_layout(tree, specs, available_width=width)

        container.bind("<Configure>", on_configure)
        container.after_idle(on_configure)

    @classmethod
    def _bind_wraplength_widgets(
        cls,
        container: tk.Misc,
        widgets: tuple[tk.Misc, ...],
        *,
        padding: int = 24,
        minimum: int = 240,
    ) -> None:
        def on_configure(event: tk.Event | None = None) -> None:
            width = 0
            if event is not None:
                width = int(getattr(event, "width", 0) or 0)
            if width <= 0:
                try:
                    width = container.winfo_width()
                except tk.TclError:
                    width = 0
            if width <= 0:
                return
            wraplength = cls._responsive_wraplength(width, padding=padding, minimum=minimum)
            for widget in widgets:
                widget.configure(wraplength=wraplength)

        container.bind("<Configure>", on_configure)
        container.after_idle(on_configure)

    def _build_menubar(self) -> None:
        self.menu_bar = tk.Menu(self.root)
        self.root.configure(menu=self.menu_bar)

        file_menu = tk.Menu(self.menu_bar)
        file_menu.add_command(label="Открыть документ…", command=self.open_document_dialog, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.destroy)
        self.menu_bar.add_cascade(label="Файл", menu=file_menu)

        self.dictionaries_menu = tk.Menu(self.menu_bar)
        self.dictionaries_menu.add_command(label="Каталог словарей…", command=self.show_dictionary_catalog)
        self.dictionaries_menu.add_command(
            label="Установить FreeDict для текущего направления",
            command=self.install_default_dictionary_pack,
        )
        self.dictionaries_menu.add_separator()
        self.dictionaries_menu.add_command(label="Подключить SQLite-словарь…", command=self.install_sqlite_dictionary_pack)
        self.dictionaries_menu.add_command(label="Импортировать CSV-словарь…", command=self.import_csv_dictionary_pack)
        self.dictionaries_menu.add_command(label="Импортировать FreeDict TEI…", command=self.import_freedict_dictionary_pack)
        self.menu_bar.add_cascade(label="Словари", menu=self.dictionaries_menu)

        self.translate_menu = tk.Menu(self.menu_bar)
        direction_menu = tk.Menu(self.translate_menu)
        self.direction_var = tk.StringVar(value=self.settings.direction)
        direction_menu.add_radiobutton(label="EN → RU", value=EN_RU, variable=self.direction_var, command=self.on_direction_menu_change)
        direction_menu.add_radiobutton(label="RU → EN", value=RU_EN, variable=self.direction_var, command=self.on_direction_menu_change)
        self.translate_menu.add_cascade(label="Направление", menu=direction_menu)

        provider_menu = tk.Menu(self.translate_menu)
        self.provider_var = tk.StringVar(value=self.settings.context_provider_id)
        for choice in self.context_service.provider_choices():
            provider_menu.add_radiobutton(
                label=choice.display_name,
                value=choice.provider_id,
                variable=self.provider_var,
                command=self.on_provider_menu_change,
            )
        self.translate_menu.add_cascade(label="Контекстный перевод", menu=provider_menu)
        self.translate_menu.add_command(label="Настройки перевода…", command=self.show_provider_settings_dialog)
        self.translate_menu.add_command(label="Офлайн-модели Argos…", command=self.show_argos_model_manager)
        self.translate_menu.add_command(label="Как установить Argos…", command=self.show_argos_installation_help)
        self.menu_bar.add_cascade(label="Перевод", menu=self.translate_menu)

        settings_menu = tk.Menu(self.menu_bar)
        settings_menu.add_command(label="Открыть настройки…", command=self.show_settings_window)
        settings_menu.add_command(label="Словари", command=lambda: self.show_settings_window("dictionaries"))
        settings_menu.add_command(label="LibreTranslate", command=lambda: self.show_settings_window("libretranslate"))
        settings_menu.add_command(label="Yandex Cloud", command=lambda: self.show_settings_window("yandex"))
        settings_menu.add_command(label="Argos", command=lambda: self.show_settings_window("argos"))
        self.menu_bar.add_cascade(label="Настройки", menu=settings_menu)

        self.dictionary_context_menu = tk.Menu(self.root, tearoff=False)
        self.dictionary_context_menu.add_command(label="Каталог словарей…", command=self.show_dictionary_catalog)
        self.dictionary_context_menu.add_separator()
        self.dictionary_context_menu.add_command(label="Подключить SQLite-словарь…", command=self.install_sqlite_dictionary_pack)
        self.dictionary_context_menu.add_command(label="Импортировать CSV-словарь…", command=self.import_csv_dictionary_pack)
        self.dictionary_context_menu.add_command(label="Импортировать FreeDict TEI…", command=self.import_freedict_dictionary_pack)

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self.root, padding=(12, 10, 12, 4), style="Toolbar.TFrame")
        toolbar.pack(side=tk.TOP, fill=tk.X)
        toolbar.columnconfigure(11, weight=1)

        ttk.Button(toolbar, text="Открыть", command=self.open_document_dialog, style="Toolbar.TButton").grid(row=0, column=0, padx=(0, 6), sticky="w")
        ttk.Button(toolbar, text="◀", command=self.previous_page, width=3).grid(row=0, column=1, sticky="w")
        ttk.Button(toolbar, text="▶", command=self.next_page, width=3).grid(row=0, column=2, padx=(4, 10), sticky="w")

        self.page_label = ttk.Label(toolbar, text="Стр. 0 / 0")
        self.page_label.grid(row=0, column=3, padx=(0, 12), sticky="w")

        ttk.Button(toolbar, text="-", command=lambda: self.change_zoom(-0.1), width=3).grid(row=0, column=4, sticky="w")
        ttk.Button(toolbar, text="+", command=lambda: self.change_zoom(0.1), width=3).grid(row=0, column=5, padx=(4, 10), sticky="w")

        self.zoom_label = ttk.Label(toolbar, text="120%")
        self.zoom_label.grid(row=0, column=6, padx=(0, 12), sticky="w")

        self.direction_button = ttk.Button(toolbar, text=self._direction_display(self.settings.direction), command=self.toggle_direction)
        self.direction_button.grid(row=0, column=7, padx=(0, 12), sticky="w")

        ttk.Button(toolbar, text="Настройки", command=self.show_settings_window).grid(row=0, column=8, padx=(0, 8), sticky="w")
        ttk.Button(toolbar, text="Словари", command=lambda: self.show_settings_window("dictionaries")).grid(row=0, column=9, padx=(0, 12), sticky="w")

        ttk.Label(toolbar, text="Поиск:").grid(row=0, column=10, sticky="w")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var)
        self.search_entry.grid(row=0, column=11, padx=(4, 4), sticky="ew")
        ttk.Button(toolbar, text="Найти", command=self.execute_search).grid(row=0, column=12, sticky="w")
        ttk.Button(toolbar, text="Пред.", command=lambda: self.navigate_search(-1)).grid(row=0, column=13, padx=(4, 0), sticky="w")
        ttk.Button(toolbar, text="След.", command=lambda: self.navigate_search(1)).grid(row=0, column=14, padx=(4, 0), sticky="w")

        self.search_status_label = ttk.Label(toolbar, text="")
        self.search_status_label.grid(row=0, column=15, padx=(10, 0), sticky="w")

    def _build_content(self) -> None:
        body = ttk.Frame(self.root, padding=(12, 4, 12, 8), style="App.TFrame")
        body.pack(fill=tk.BOTH, expand=True)

        viewer_card = ttk.Frame(body, style="Surface.TFrame")
        viewer_card.pack(fill=tk.BOTH, expand=True)

        viewer_frame = ttk.Frame(viewer_card, style="Surface.TFrame")
        viewer_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(viewer_frame, background="#738194", highlightthickness=0, bd=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.yscroll = ttk.Scrollbar(viewer_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.xscroll = ttk.Scrollbar(viewer_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(yscrollcommand=self._on_canvas_yscroll, xscrollcommand=self.xscroll.set)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Enter>", self._bind_canvas_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_canvas_mousewheel)
        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.canvas.bind("<Button-3>", self.show_dictionary_context_menu)

        self.translation_panel = ttk.Frame(body, padding=14, style="InfoCard.TFrame")
        self.translation_panel.pack(fill=tk.X, pady=(10, 0))
        self.translation_panel.bind("<Button-3>", self.show_dictionary_context_menu)
        self.translation_panel.bind("<Configure>", self._on_translation_panel_configure)
        self._build_translation_panel(self.translation_panel)

    def _build_translation_panel(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Справка по слову", style="CardTitle.TLabel").pack(anchor="w")

        self.lookup_meta_var = tk.StringVar(value="Нажмите на слово в документе — здесь появится краткий перевод.")
        self.best_translation_var = tk.StringVar(value="—")
        self.example_var = tk.StringVar(value="Контекстный перевод / пример: —")
        self.alternatives_var = tk.StringVar(value="Варианты: —")
        self.dictionary_footer_var = tk.StringVar(value=self._dictionary_footer_text())

        self.meta_label = ttk.Label(parent, textvariable=self.lookup_meta_var, style="Meta.TLabel", wraplength=1200, justify=tk.LEFT)
        self.meta_label.pack(anchor="w", pady=(6, 6), fill=tk.X)
        self.meta_label.bind("<Button-3>", self.show_dictionary_context_menu)

        self.best_label = ttk.Label(parent, textvariable=self.best_translation_var, style="BestTranslation.TLabel", wraplength=1200, justify=tk.LEFT)
        self.best_label.pack(anchor="w", pady=(0, 6), fill=tk.X)
        self.best_label.bind("<Button-3>", self.show_dictionary_context_menu)

        self.example_label = ttk.Label(parent, textvariable=self.example_var, style="Context.TLabel", wraplength=1200, justify=tk.LEFT)
        self.example_label.pack(anchor="w", pady=(0, 4), fill=tk.X)
        self.example_label.bind("<Button-3>", self.show_dictionary_context_menu)

        self.alternatives_label = ttk.Label(parent, textvariable=self.alternatives_var, style="Muted.TLabel", wraplength=1200, justify=tk.LEFT)
        self.alternatives_label.pack(anchor="w", fill=tk.X)
        self.alternatives_label.bind("<Button-3>", self.show_dictionary_context_menu)

        ttk.Separator(parent).pack(fill=tk.X, pady=(12, 8))
        ttk.Label(parent, textvariable=self.dictionary_footer_var, style="Muted.TLabel").pack(anchor="w")

    def _build_statusbar(self) -> None:
        status_frame = ttk.Frame(self.root, padding=(10, 4), style="Status.TFrame")
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var = tk.StringVar(value="")
        ttk.Label(status_frame, textvariable=self.status_var, style="Status.TLabel").pack(anchor="w")

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-o>", lambda event: self.open_document_dialog())
        self.root.bind("<Control-f>", lambda event: self.search_entry.focus_set())
        self.root.bind("<Prior>", lambda event: self.previous_page())
        self.root.bind("<Next>", lambda event: self.next_page())

    def _schedule_context_result_poll(self) -> None:
        if self._context_poll_scheduled:
            return
        self._context_poll_scheduled = True
        try:
            self.root.after(self.CONTEXT_RESULT_POLL_MS, self._poll_context_results)
        except tk.TclError:
            self._context_poll_scheduled = False

    def _poll_context_results(self) -> None:
        self._context_poll_scheduled = False
        self._drain_context_result_queue()
        try:
            if self.root.winfo_exists():
                self._schedule_context_result_poll()
        except tk.TclError:
            return

    def _drain_context_result_queue(self) -> None:
        while True:
            try:
                request_id, result = self._context_result_queue.get_nowait()
            except queue.Empty:
                break
            self._apply_context_result(request_id, result)

    def _enqueue_context_result(self, request_id: int, result: ContextTranslationResult) -> None:
        self._context_result_queue.put((request_id, result))

    def _cancel_pending_context_translation(self) -> None:
        self._active_context_request_id = self.context_service.next_request_id()

    # ------------------------------------------------------------------
    # Canvas interaction and lazy rendering
    # ------------------------------------------------------------------
    def _bind_canvas_mousewheel(self, _event: tk.Event) -> None:
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self.root.bind_all("<Button-4>", self._on_mousewheel)
        self.root.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_canvas_mousewheel(self, _event: tk.Event) -> None:
        self.root.unbind_all("<MouseWheel>")
        self.root.unbind_all("<Button-4>")
        self.root.unbind_all("<Button-5>")

    def _on_canvas_yscroll(self, first: str, last: str) -> None:
        self.yscroll.set(first, last)
        self._schedule_viewport_update()

    def _on_canvas_configure(self, _event: tk.Event) -> None:
        self._schedule_viewport_update()
        self._schedule_visible_render()

    def _on_translation_panel_configure(self, event: tk.Event) -> None:
        wraplength = self._responsive_wraplength(getattr(event, "width", 0), padding=48, minimum=400)
        for widget in (self.meta_label, self.best_label, self.example_label, self.alternatives_label):
            widget.configure(wraplength=wraplength)

    def _schedule_viewport_update(self) -> None:
        if not self._viewport_update_scheduled:
            self._viewport_update_scheduled = True
            self.root.after_idle(self._update_viewport_page_index)

    def _schedule_visible_render(self) -> None:
        if not self._visible_render_scheduled:
            self._visible_render_scheduled = True
            self.root.after_idle(self._refresh_visible_pages)

    def _update_viewport_page_index(self) -> None:
        self._viewport_update_scheduled = False
        if not self.page_layouts:
            return
        top_y = self.canvas.canvasy(8)
        chosen_layout = self.page_layouts[0]
        for layout in self.page_layouts.values():
            if layout.top <= top_y <= layout.bottom:
                chosen_layout = layout
                break
            if layout.top <= top_y:
                chosen_layout = layout
        self.current_page_index = chosen_layout.page_index
        self.page_label.configure(text=f"Стр. {self.current_page_index + 1} / {self.document_service.page_count()}")
        self._schedule_visible_render()

    def _visible_page_indexes(self) -> list[int]:
        view_height = max(1, self.canvas.winfo_height())
        extra_margin = int(view_height * self.VISIBLE_RENDER_MARGIN_SCREENS)
        top = self.canvas.canvasy(0) - extra_margin
        bottom = self.canvas.canvasy(view_height) + extra_margin
        indexes: list[int] = []
        for page_index, layout in self.page_layouts.items():
            if layout.bottom >= top and layout.top <= bottom:
                indexes.append(page_index)
        return indexes

    def _refresh_visible_pages(self) -> None:
        self._visible_render_scheduled = False
        if self.document_service.current_path is None or not self.page_layouts:
            return

        wanted = set(self._visible_page_indexes())
        for page_index in list(self.page_photos):
            if page_index not in wanted:
                self._unload_page_image(page_index)

        rendered_any = False
        for page_index in sorted(wanted):
            if page_index in self.page_photos:
                continue
            self._render_one_page(page_index)
            rendered_any = True

        if rendered_any:
            self._redraw_overlays()

    def _render_one_page(self, page_index: int) -> None:
        layout = self.page_layouts.get(page_index)
        if layout is None:
            return
        rendered = self.document_service.render_page(page_index, self.current_zoom)
        photo = ImageTk.PhotoImage(rendered.image)
        self.page_photos[page_index] = photo
        if layout.image_item is None:
            layout.image_item = self.canvas.create_image(layout.left, layout.top, image=photo, anchor="nw")
        else:
            self.canvas.itemconfigure(layout.image_item, image=photo)
        self.canvas.tag_raise(layout.label_item)

    def _unload_page_image(self, page_index: int) -> None:
        layout = self.page_layouts.get(page_index)
        if layout is not None and layout.image_item is not None:
            self.canvas.delete(layout.image_item)
            layout.image_item = None
        self.page_photos.pop(page_index, None)

    def _redraw_overlays(self) -> None:
        if self.current_highlight_token is not None:
            self._draw_word_highlight(self.current_highlight_token, scroll_into_view=False)
        if 0 <= self.current_search_index < len(self.current_search_hits):
            self._draw_search_highlight(self.current_search_hits[self.current_search_index], scroll_into_view=False)

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self.document_service.current_path is None:
            return
        direction = self._mousewheel_direction(event)
        if direction == 0:
            return
        ctrl_pressed = bool(getattr(event, "state", 0) & 0x4)
        if ctrl_pressed:
            anchor_canvas = (self.canvas.canvasx(getattr(event, "x", 0)), self.canvas.canvasy(getattr(event, "y", 0)))
            anchor_widget = (getattr(event, "x", 0), getattr(event, "y", 0))
            self.change_zoom(0.1 * direction, anchor_canvas=anchor_canvas, anchor_widget=anchor_widget)
            return
        self.canvas.yview_scroll(-3 * direction, "units")
        self._schedule_viewport_update()

    @staticmethod
    def _mousewheel_direction(event: tk.Event) -> int:
        if getattr(event, "num", None) == 4:
            return 1
        if getattr(event, "num", None) == 5:
            return -1
        raw_delta = int(getattr(event, "delta", 0))
        if raw_delta == 0:
            return 0
        return 1 if raw_delta > 0 else -1

    def _update_status(self, text: str) -> None:
        self.status_var.set(text)

    def _document_filetypes(self) -> list[tuple[str, str]]:
        extensions = self.document_service.supported_extensions()
        supported = " ".join(f"*{extension}" for extension in extensions)
        return [
            ("Поддерживаемые документы", supported),
            ("PDF", "*.pdf"),
            ("Text", "*.txt"),
            ("FB2", "*.fb2"),
            ("Все файлы", "*.*"),
        ]

    # ------------------------------------------------------------------
    # Document opening, scrolling and zooming
    # ------------------------------------------------------------------
    def open_document_dialog(self) -> None:
        path = filedialog.askopenfilename(title="Выберите документ", filetypes=self._document_filetypes())
        if path:
            self.open_document_path(Path(path))

    def open_document_path(self, path: Path) -> None:
        try:
            self.document_service.open_document(path)
            self.current_page_index = 0
            self.current_highlight_token = None
            self.current_search_hits = []
            self.current_search_index = -1
            self.current_view_model = None
            self.search_status_label.configure(text="")
            self.document_service.clear_cache()
            self._clear_panel()
            self.render_document(focus_page=0)
            self._update_status(f"Открыт документ: {path.name}")
        except Exception as exc:  # pragma: no cover - GUI error path only
            LOGGER.exception("Failed to open document %s", path)
            messagebox.showerror("Ошибка открытия", str(exc))

    def render_document(
        self,
        focus_page: int | None = None,
        anchor_doc_point: tuple[int, float, float] | None = None,
        anchor_widget: tuple[float, float] | None = None,
    ) -> None:
        if self.document_service.current_path is None:
            return

        total_pages = self.document_service.page_count()
        self.page_photos.clear()
        self.page_layouts.clear()
        self.canvas.delete("all")
        self.word_rect_id = None
        self.search_rect_id = None

        max_width = 0
        current_top = self.PAGE_MARGIN
        for page_index in range(total_pages):
            width_doc, height_doc = self.document_service.page_dimensions(page_index)
            width = max(1, int(round(width_doc * self.current_zoom)))
            height = max(1, int(round(height_doc * self.current_zoom)))
            left = self.PAGE_MARGIN
            top = current_top
            layout = CanvasPageLayout(page_index=page_index, left=left, top=top, width=width, height=height)
            layout.shadow_item = self.canvas.create_rectangle(left - 3, top - 3, left + width + 3, top + height + 3, fill="#d8e0ea", outline="")
            layout.background_item = self.canvas.create_rectangle(left, top, left + width, top + height, fill="#ffffff", outline="")
            layout.label_item = self.canvas.create_text(left + 10, top - 14, text=f"Стр. {page_index + 1}", fill="#cbd5e1", anchor="w")
            self.page_layouts[page_index] = layout
            current_top += height + self.PAGE_GAP
            max_width = max(max_width, width)

        self.canvas.configure(scrollregion=(0, 0, max_width + self.PAGE_MARGIN * 2, current_top + self.PAGE_MARGIN))
        self.zoom_label.configure(text=f"{int(self.current_zoom * 100)}%")
        self.direction_var.set(self.settings.direction)
        self.direction_button.configure(text=self._direction_display(self.settings.direction))
        self._last_rendered_zoom = self.current_zoom

        if anchor_doc_point is not None and anchor_widget is not None:
            self._scroll_doc_point_to_widget(anchor_doc_point, anchor_widget)
        elif focus_page is not None:
            self.scroll_to_page(focus_page)
        else:
            self._schedule_viewport_update()
            self._schedule_visible_render()

    def scroll_to_page(self, page_index: int) -> None:
        layout = self.page_layouts.get(page_index)
        if layout is None:
            return
        self.current_page_index = page_index
        self.page_label.configure(text=f"Стр. {page_index + 1} / {self.document_service.page_count()}")
        self._set_canvas_view(top=layout.top - 10, left=0)

    def previous_page(self) -> None:
        if self.document_service.current_path is None:
            return
        if self.current_page_index > 0:
            self.scroll_to_page(self.current_page_index - 1)

    def next_page(self) -> None:
        if self.document_service.current_path is None:
            return
        if self.current_page_index + 1 < self.document_service.page_count():
            self.scroll_to_page(self.current_page_index + 1)

    def change_zoom(
        self,
        delta: float,
        anchor_canvas: tuple[float, float] | None = None,
        anchor_widget: tuple[float, float] | None = None,
    ) -> None:
        if self.document_service.current_path is None:
            return
        new_zoom = round(max(self.MIN_ZOOM, min(self.MAX_ZOOM, self.current_zoom + delta)), 2)
        if new_zoom == self.current_zoom:
            return

        anchor_doc_point: tuple[int, float, float] | None = None
        if anchor_canvas is not None:
            layout = self._page_layout_at_canvas_coords(*anchor_canvas)
            if layout is not None:
                page_x = (anchor_canvas[0] - layout.left) / self.current_zoom
                page_y = (anchor_canvas[1] - layout.top) / self.current_zoom
                anchor_doc_point = (layout.page_index, page_x, page_y)

        previous_zoom = self.current_zoom
        self.current_zoom = new_zoom
        self.document_service.clear_cache()
        self.render_document(focus_page=self.current_page_index, anchor_doc_point=anchor_doc_point, anchor_widget=anchor_widget)
        self._update_status(f"Масштаб: {int(self.current_zoom * 100)}% (было {int(previous_zoom * 100)}%)")

    # ------------------------------------------------------------------
    # Click-to-translate workflow
    # ------------------------------------------------------------------
    def on_canvas_click(self, event: tk.Event) -> None:
        if self.document_service.current_path is None:
            return
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        layout = self._page_layout_at_canvas_coords(canvas_x, canvas_y)
        if layout is None:
            return
        page_x = (canvas_x - layout.left) / self.current_zoom
        page_y = (canvas_y - layout.top) / self.current_zoom
        self.process_click_at_page_coords(layout.page_index, page_x, page_y)

    def process_click_at_page_coords(self, page_index: int, page_x: float, page_y: float) -> TranslationViewModel | None:
        view_model = self.workflow.translate_point(page_index, page_x, page_y, direction=self.settings.direction)
        if view_model is None:
            self._update_status("Слово под курсором не найдено.")
            return None
        self.current_page_index = page_index
        self.current_highlight_token = view_model.token
        self.current_view_model = view_model
        self._draw_word_highlight(view_model.token)
        self._populate_panel(view_model)
        self._update_status(f"Выбрано слово: {view_model.token.text}")
        self._start_context_translation(view_model)
        return view_model

    def _page_layout_at_canvas_coords(self, canvas_x: float, canvas_y: float) -> CanvasPageLayout | None:
        for layout in self.page_layouts.values():
            if layout.left <= canvas_x <= layout.right and layout.top <= canvas_y <= layout.bottom:
                return layout
        return None

    def _draw_word_highlight(self, token: WordToken, *, scroll_into_view: bool = True) -> None:
        layout = self.page_layouts.get(token.page_index)
        if layout is None:
            return
        if self.word_rect_id is not None:
            self.canvas.delete(self.word_rect_id)
        x0, y0, x1, y1 = token.rect
        self.word_rect_id = self.canvas.create_rectangle(
            layout.left + x0 * self.current_zoom,
            layout.top + y0 * self.current_zoom,
            layout.left + x1 * self.current_zoom,
            layout.top + y1 * self.current_zoom,
            outline="#f59e0b",
            width=2,
        )
        if scroll_into_view:
            self._scroll_rect_into_view(
                (
                    layout.left + x0 * self.current_zoom,
                    layout.top + y0 * self.current_zoom,
                    layout.left + x1 * self.current_zoom,
                    layout.top + y1 * self.current_zoom,
                )
            )

    def _draw_search_highlight(self, hit: SearchHit, *, scroll_into_view: bool = True) -> None:
        layout = self.page_layouts.get(hit.page_index)
        if layout is None:
            return
        if self.search_rect_id is not None:
            self.canvas.delete(self.search_rect_id)
        x0, y0, x1, y1 = hit.rect
        self.search_rect_id = self.canvas.create_rectangle(
            layout.left + x0 * self.current_zoom,
            layout.top + y0 * self.current_zoom,
            layout.left + x1 * self.current_zoom,
            layout.top + y1 * self.current_zoom,
            outline="#22c55e",
            width=2,
        )
        if scroll_into_view:
            self._scroll_rect_into_view(
                (
                    layout.left + x0 * self.current_zoom,
                    layout.top + y0 * self.current_zoom,
                    layout.left + x1 * self.current_zoom,
                    layout.top + y1 * self.current_zoom,
                )
            )

    def _scroll_rect_into_view(self, rect: tuple[float, float, float, float]) -> None:
        """Best-effort scroll so the highlighted rectangle stays visible."""
        x0, y0, x1, y1 = rect
        scrollregion = self.canvas.cget("scrollregion")
        if not scrollregion:
            return
        sx0, sy0, sx1, sy1 = [float(v) for v in str(scrollregion).split()]
        total_width = max(1.0, sx1 - sx0)
        total_height = max(1.0, sy1 - sy0)
        view_w = max(1, self.canvas.winfo_width())
        view_h = max(1, self.canvas.winfo_height())
        current_left = self.canvas.canvasx(0)
        current_top = self.canvas.canvasy(0)
        current_right = current_left + view_w
        current_bottom = current_top + view_h

        target_left = current_left
        target_top = current_top
        if x0 < current_left:
            target_left = x0 - 20
        elif x1 > current_right:
            target_left = x1 - view_w + 20
        if y0 < current_top:
            target_top = y0 - 20
        elif y1 > current_bottom:
            target_top = y1 - view_h + 20

        target_left = min(max(target_left, sx0), max(sx0, sx1 - view_w))
        target_top = min(max(target_top, sy0), max(sy0, sy1 - view_h))
        self.canvas.xview_moveto((target_left - sx0) / total_width)
        self.canvas.yview_moveto((target_top - sy0) / total_height)
        self._schedule_viewport_update()

    def _scroll_doc_point_to_widget(self, anchor_doc_point: tuple[int, float, float], anchor_widget: tuple[float, float]) -> None:
        layout = self.page_layouts.get(anchor_doc_point[0])
        if layout is None:
            return
        target_canvas_x = layout.left + anchor_doc_point[1] * self.current_zoom
        target_canvas_y = layout.top + anchor_doc_point[2] * self.current_zoom
        self._set_canvas_view(top=target_canvas_y - anchor_widget[1], left=target_canvas_x - anchor_widget[0])

    def _set_canvas_view(self, top: float, left: float) -> None:
        scrollregion = self.canvas.cget("scrollregion")
        if not scrollregion:
            return
        sx0, sy0, sx1, sy1 = [float(v) for v in str(scrollregion).split()]
        total_width = max(1.0, sx1 - sx0)
        total_height = max(1.0, sy1 - sy0)
        view_w = max(1, self.canvas.winfo_width())
        view_h = max(1, self.canvas.winfo_height())
        bounded_left = min(max(left, sx0), max(sx0, sx1 - view_w))
        bounded_top = min(max(top, sy0), max(sy0, sy1 - view_h))
        self.canvas.xview_moveto((bounded_left - sx0) / total_width)
        self.canvas.yview_moveto((bounded_top - sy0) / total_height)
        self._schedule_viewport_update()
        self._schedule_visible_render()

    # ------------------------------------------------------------------
    # Compact translation panel and context provider integration
    # ------------------------------------------------------------------
    def _populate_panel(self, view_model: TranslationViewModel) -> None:
        token = view_model.token
        if view_model.lookup.found and view_model.lookup.entry is not None:
            entry = view_model.lookup.entry
            resolved = entry.headword if entry.headword.lower() != token.text.lower() else token.text
            meta = resolved
            if resolved != token.text:
                meta = f"{token.text} → {resolved}"
            if entry.transcription:
                meta = f"{meta} · /{entry.transcription}/"
            self.lookup_meta_var.set(meta)
            self.best_translation_var.set(entry.best_translation or "—")
            self.example_var.set(self._dictionary_example(entry) or self._provider_idle_text())
            alternatives = ", ".join(entry.alternative_translations[:8]) or "—"
            self.alternatives_var.set(f"Ещё варианты: {alternatives}")
        else:
            self.lookup_meta_var.set(token.text)
            self.best_translation_var.set("Перевод не найден")
            self.example_var.set(self._provider_idle_text())
            forms = ", ".join(view_model.lookup.candidate_forms[:8]) if view_model.lookup.candidate_forms else "—"
            self.alternatives_var.set(f"Проверенные формы: {forms}")

    def _provider_idle_text(self) -> str:
        diagnostic = self.context_service.provider_status(self.settings.direction)
        return self._compact_text(diagnostic.message, limit=260)

    def _dictionary_example(self, entry) -> str:
        if not entry.examples:
            return ""
        src, dst = entry.examples[0]
        if dst:
            return f"Пример: {src} → {dst}"
        return f"Пример: {src}"

    def _clear_panel(self) -> None:
        self._cancel_pending_context_translation()
        self.lookup_meta_var.set("Нажмите на слово в документе — здесь появится краткий перевод.")
        self.best_translation_var.set("—")
        self.example_var.set(self._provider_idle_text())
        self.alternatives_var.set("Варианты: —")
        self._refresh_dictionary_footer()

    def _start_context_translation(self, view_model: TranslationViewModel) -> None:
        context_text = view_model.context.text.strip()
        provider_id = self.context_service.active_provider_id()
        if provider_id == "disabled":
            self._cancel_pending_context_translation()
            self.example_var.set(self._provider_idle_text())
            return
        self.example_var.set(f"{self.context_service.provider_name()}: перевод контекста…")

        def callback(request_id: int, result: ContextTranslationResult) -> None:
            self._enqueue_context_result(request_id, result)

        request_id = self.context_service.next_request_id()
        self._active_context_request_id = request_id
        self.context_service.translate_async(
            context_text,
            self.settings.direction,
            callback,
            request_id=request_id,
        )

    def _apply_context_result(self, request_id: int, result: ContextTranslationResult) -> None:
        if request_id != self._active_context_request_id:
            return
        if result.ok:
            self.example_var.set(self._compact_text(result.text, limit=260))
            return
        message = result.text or result.error or "Контекстный перевод не вернул результат."
        self.example_var.set(self._compact_text(f"{result.provider_name}: {message}", limit=260))

    @staticmethod
    def _compact_text(value: str, *, limit: int = 260) -> str:
        cleaned = " ".join(value.split())
        if len(cleaned) <= limit:
            return cleaned
        return cleaned[: limit - 1].rstrip() + "…"

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------
    def execute_search(self) -> None:
        if self.document_service.current_path is None:
            return
        query = self.search_var.get().strip()
        self.current_search_hits = self.document_service.session.search(query)
        if not self.current_search_hits:
            self.current_search_index = -1
            self.search_status_label.configure(text="Ничего не найдено")
            self._update_status("Поиск: ничего не найдено")
            if self.search_rect_id is not None:
                self.canvas.delete(self.search_rect_id)
                self.search_rect_id = None
            return
        self.current_search_index = 0
        self.search_status_label.configure(text=f"1 / {len(self.current_search_hits)}")
        self._show_search_hit(self.current_search_hits[0])

    def navigate_search(self, direction: int) -> None:
        if not self.current_search_hits:
            return
        self.current_search_index = (self.current_search_index + direction) % len(self.current_search_hits)
        self.search_status_label.configure(text=f"{self.current_search_index + 1} / {len(self.current_search_hits)}")
        self._show_search_hit(self.current_search_hits[self.current_search_index])

    def _show_search_hit(self, hit: SearchHit) -> None:
        self.scroll_to_page(hit.page_index)
        self._draw_search_highlight(hit)
        self._update_status(f"Поиск: {hit.preview}")

    # ------------------------------------------------------------------
    # Dictionary management
    # ------------------------------------------------------------------
    def _dictionary_footer_text(self) -> str:
        return (
            f"Словари: {self.dictionary_service.pack_count()} пак. · "
            f"{self.dictionary_service.entry_count()} статей · направление: {self._direction_display(self.settings.direction)}"
        )

    def _refresh_dictionary_footer(self) -> None:
        self.dictionary_footer_var.set(self._dictionary_footer_text())

    def _reload_dictionary_plugin(self) -> None:
        self.dictionary_service.replace_plugin(self.plugin_loader.create_dictionary_plugin())
        self._refresh_dictionary_footer()

    def _run_dictionary_task(self, action_label: str, task) -> None:
        self.root.configure(cursor="watch")
        self.root.update_idletasks()
        try:
            result_path = task()
            self._reload_dictionary_plugin()
            self._update_status(f"{action_label}: {Path(result_path).name}")
            messagebox.showinfo("Словарь установлен", f"Готово: {result_path}")
        except Exception as exc:  # pragma: no cover - GUI error path only
            LOGGER.exception("Dictionary action failed: %s", action_label)
            messagebox.showerror("Ошибка словаря", str(exc))
        finally:
            self.root.configure(cursor="")
            if self._catalog_window is not None and self._catalog_window.winfo_exists():
                self._populate_dictionary_catalog_tree()

    def install_default_dictionary_pack(self) -> None:
        direction = self.settings.direction
        label = f"Установлен FreeDict {self._direction_display(direction)}"
        self._run_dictionary_task(
            label,
            lambda: install_default_pack(self.config.runtime_dictionary_dir, self.config.runtime_download_dir, direction=direction),
        )

    def install_sqlite_dictionary_pack(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите SQLite-словарь",
            filetypes=[("SQLite", "*.sqlite"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        self._run_dictionary_task(
            "Подключен SQLite-словарь",
            lambda: install_sqlite_pack(Path(path), self.config.runtime_dictionary_dir),
        )

    def import_csv_dictionary_pack(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите CSV-словарь",
            filetypes=[("CSV", "*.csv"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        self._run_dictionary_task(
            "Импортирован CSV-словарь",
            lambda: import_csv_pack(Path(path), self.config.runtime_dictionary_dir, direction=self.settings.direction),
        )

    def import_freedict_dictionary_pack(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите FreeDict TEI",
            filetypes=[("TEI", "*.tei *.xml"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        self._run_dictionary_task(
            "Импортирован FreeDict-словарь",
            lambda: import_freedict_pack(Path(path), self.config.runtime_dictionary_dir, direction=self.settings.direction),
        )

    def show_dictionary_context_menu(self, event: tk.Event) -> None:
        try:
            self.dictionary_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.dictionary_context_menu.grab_release()

    def show_dictionary_catalog(self) -> None:
        if self._catalog_window is not None and self._catalog_window.winfo_exists():
            self._catalog_window.deiconify()
            self._catalog_window.lift()
            self._populate_dictionary_catalog_tree()
            return

        window = tk.Toplevel(self.root)
        window.title("Каталог словарей")
        window.geometry("980x560")
        window.minsize(760, 420)
        window.transient(self.root)
        window.configure(background="#eef2f7")
        window.rowconfigure(0, weight=1)
        window.columnconfigure(0, weight=1)
        self._catalog_window = window
        window.protocol("WM_DELETE_WINDOW", self._close_catalog_window)

        top = ttk.Frame(window, padding=12, style="App.TFrame")
        top.grid(row=0, column=0, sticky="nsew")
        top.rowconfigure(0, weight=1)
        top.columnconfigure(0, weight=1)

        tree_container = ttk.Frame(top, style="App.TFrame")
        tree_container.grid(row=0, column=0, sticky="nsew")
        tree_container.rowconfigure(0, weight=1)
        tree_container.columnconfigure(0, weight=1)

        columns = ("title", "direction", "category", "source")
        tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=10, style="Catalog.Treeview")
        tree.heading("title", text="Пакет")
        tree.heading("direction", text="Направление")
        tree.heading("category", text="Категория")
        tree.heading("source", text="Источник")
        tree.column("title", anchor="w")
        tree.column("direction", anchor="center")
        tree.column("category", anchor="center")
        tree.column("source", anchor="w")
        tree.grid(row=0, column=0, sticky="nsew")
        tree.bind("<<TreeviewSelect>>", self._on_catalog_selection_changed)
        self._catalog_tree = tree

        yscroll = ttk.Scrollbar(tree_container, orient=tk.VERTICAL, command=tree.yview)
        yscroll.grid(row=0, column=1, sticky="ns")
        xscroll = ttk.Scrollbar(tree_container, orient=tk.HORIZONTAL, command=tree.xview)
        xscroll.grid(row=1, column=0, sticky="ew")
        tree.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self._bind_tree_column_layout(
            tree_container,
            tree,
            (
                TreeColumnSpec("title", 240, 30),
                TreeColumnSpec("direction", 120, 12),
                TreeColumnSpec("category", 140, 14),
                TreeColumnSpec("source", 280, 44),
            ),
        )

        bottom = ttk.Frame(top, padding=(0, 10, 0, 0), style="App.TFrame")
        bottom.grid(row=1, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)
        self._catalog_description_var = tk.StringVar(value="Выберите пакет, чтобы увидеть описание и установить его.")
        self._catalog_source_var = tk.StringVar(value="")
        description_label = ttk.Label(bottom, textvariable=self._catalog_description_var, style="Context.TLabel", justify=tk.LEFT)
        description_label.grid(row=0, column=0, sticky="ew")
        source_label = ttk.Label(bottom, textvariable=self._catalog_source_var, style="Muted.TLabel", justify=tk.LEFT)
        source_label.grid(row=1, column=0, sticky="ew", pady=(4, 10))
        self._bind_wraplength_widgets(bottom, (description_label, source_label), padding=20, minimum=260)

        buttons = ttk.Frame(bottom, style="App.TFrame")
        buttons.grid(row=2, column=0, sticky="ew")
        buttons.columnconfigure(3, weight=1)
        ttk.Button(buttons, text="Установить выбранный пакет", command=self.install_selected_catalog_pack).grid(row=0, column=0, sticky="w")
        ttk.Button(buttons, text="Открыть источник", command=self.open_selected_catalog_source).grid(row=0, column=1, padx=(6, 0), sticky="w")
        ttk.Button(buttons, text="Обновить", command=self._populate_dictionary_catalog_tree).grid(row=0, column=2, padx=(6, 0), sticky="w")
        ttk.Button(buttons, text="Закрыть", command=self._close_catalog_window).grid(row=0, column=3, sticky="e")

        self._populate_dictionary_catalog_tree()

    def _close_catalog_window(self) -> None:
        if self._catalog_window is not None and self._catalog_window.winfo_exists():
            self._catalog_window.destroy()
        self._catalog_window = None
        self._catalog_tree = None
        self._catalog_specs = {}

    def _populate_dictionary_catalog_tree(self) -> None:
        if self._catalog_tree is None:
            return
        tree = self._catalog_tree
        for item in tree.get_children():
            tree.delete(item)
        self._catalog_specs = {}
        for spec in available_catalog_items(self.config):
            self._catalog_specs[spec.pack_id] = spec
            source_preview = spec.source
            tree.insert(
                "",
                tk.END,
                iid=spec.pack_id,
                values=(spec.title, spec.direction.upper(), spec.category, source_preview),
            )
        self._set_catalog_details(None)

    def _selected_catalog_spec(self) -> DictionaryPackSpec | None:
        if self._catalog_tree is None:
            return None
        selection = self._catalog_tree.selection()
        if not selection:
            return None
        return self._catalog_specs.get(selection[0])

    def _on_catalog_selection_changed(self, _event: tk.Event | None = None) -> None:
        self._set_catalog_details(self._selected_catalog_spec())

    def _set_catalog_details(self, spec: DictionaryPackSpec | None) -> None:
        if self._catalog_description_var is None or self._catalog_source_var is None:
            return
        if spec is None:
            self._catalog_description_var.set("Выберите пакет, чтобы увидеть описание и установить его.")
            self._catalog_source_var.set("")
            return
        self._catalog_description_var.set(spec.description)
        source_text = spec.source
        if spec.urls:
            source_text = "; ".join(spec.urls)
        self._catalog_source_var.set(f"Источник: {source_text}")

    def install_selected_catalog_pack(self) -> None:
        spec = self._selected_catalog_spec()
        if spec is None:
            messagebox.showinfo("Каталог словарей", "Сначала выберите пакет в списке.")
            return
        self._run_dictionary_task(
            f"Установлен пакет {spec.title}",
            lambda: install_catalog_pack(spec, self.config.runtime_dictionary_dir, self.config.runtime_download_dir),
        )

    def open_selected_catalog_source(self) -> None:
        spec = self._selected_catalog_spec()
        if spec is None:
            return
        url = spec.urls[0] if spec.urls else spec.source
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme.lower() not in {"http", "https"}:
            messagebox.showinfo("Источник словаря", f"Для этого пакета источник локальный или неподдерживаемый: {url}")
            return
        webbrowser.open(url)

    # ------------------------------------------------------------------
    # Argos offline model manager
    # ------------------------------------------------------------------
    def show_argos_model_manager(self) -> None:
        if self._argos_window is not None and self._argos_window.winfo_exists():
            self._argos_window.deiconify()
            self._argos_window.lift()
            self._populate_argos_model_tree(update_index=False)
            return

        window = tk.Toplevel(self.root)
        window.title("Офлайн-модели Argos")
        window.geometry("1040x620")
        window.minsize(820, 480)
        window.transient(self.root)
        window.configure(background="#eef2f7")
        window.rowconfigure(0, weight=1)
        window.columnconfigure(0, weight=1)
        self._argos_window = window
        window.protocol("WM_DELETE_WINDOW", self._close_argos_model_manager)

        top = ttk.Frame(window, padding=12, style="App.TFrame")
        top.grid(row=0, column=0, sticky="nsew")
        top.rowconfigure(1, weight=1)
        top.columnconfigure(0, weight=1)

        intro = (
            "Argos используется только для офлайн-контекстного перевода предложений. "
            "Сначала установите optional dependency argostranslate, затем скачайте модель для EN → RU "
            "или RU → EN прямо из этого окна. Статус «Доступна из сети» означает, что пакет найден в индексе, "
            "но ещё не установлен локально. Если модель уже скачана заранее, можно импортировать локальный .argosmodel файл."
        )
        intro_label = ttk.Label(top, text=intro, style="Context.TLabel", justify=tk.LEFT)
        intro_label.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        tree_container = ttk.Frame(top, style="App.TFrame")
        tree_container.grid(row=1, column=0, sticky="nsew")
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
        self._bind_tree_column_layout(
            tree_container,
            tree,
            (
                TreeColumnSpec("direction", 160, 18),
                TreeColumnSpec("status", 190, 20),
                TreeColumnSpec("version", 120, 12),
                TreeColumnSpec("package", 320, 50),
            ),
        )

        bottom = ttk.Frame(top, padding=(0, 10, 0, 0), style="App.TFrame")
        bottom.grid(row=2, column=0, sticky="ew")
        bottom.columnconfigure(0, weight=1)
        self._argos_status_var = tk.StringVar(value="Выберите направление или используйте текущий перевод EN ↔ RU.")
        self._argos_hint_var = tk.StringVar(value="")
        status_label = ttk.Label(bottom, textvariable=self._argos_status_var, style="Context.TLabel", justify=tk.LEFT)
        status_label.grid(row=0, column=0, sticky="ew")
        hint_label = ttk.Label(bottom, textvariable=self._argos_hint_var, style="Muted.TLabel", justify=tk.LEFT)
        hint_label.grid(row=1, column=0, sticky="ew", pady=(4, 10))
        self._bind_wraplength_widgets(top, (intro_label,), padding=24, minimum=280)
        self._bind_wraplength_widgets(bottom, (status_label, hint_label), padding=20, minimum=260)

        buttons = ttk.Frame(bottom, style="App.TFrame")
        buttons.grid(row=2, column=0, sticky="ew")
        buttons.columnconfigure(6, weight=1)
        ttk.Button(buttons, text="Установить поддержку Argos", command=self.install_argos_runtime_from_gui).grid(row=0, column=0, sticky="w")
        ttk.Button(buttons, text="Обновить список из сети", command=lambda: self._populate_argos_model_tree(update_index=True)).grid(row=0, column=1, padx=(6, 0), sticky="w")
        ttk.Button(buttons, text="Установить выбранную модель", command=self.install_selected_argos_model).grid(row=0, column=2, padx=(6, 0), sticky="w")
        ttk.Button(buttons, text="Импортировать .argosmodel…", command=self.import_argos_model_from_dialog).grid(row=0, column=3, padx=(6, 0), sticky="w")
        ttk.Button(buttons, text="Выбрать Argos", command=self.select_argos_provider).grid(row=0, column=4, padx=(6, 0), sticky="w")
        ttk.Button(buttons, text="Справка", command=self.show_argos_installation_help).grid(row=0, column=5, padx=(6, 0), sticky="w")
        ttk.Button(buttons, text="Закрыть", command=self._close_argos_model_manager).grid(row=0, column=6, sticky="e")

        self._populate_argos_model_tree(update_index=False)

    def _close_argos_model_manager(self) -> None:
        if self._argos_window is not None and self._argos_window.winfo_exists():
            self._argos_window.destroy()
        self._argos_window = None
        self._argos_tree = None
        self._argos_status_var = None
        self._argos_hint_var = None
        self._argos_runtime_state = None

    def _populate_argos_model_tree(self, *, update_index: bool = False) -> None:
        if self._argos_tree is None:
            return
        tree = self._argos_tree
        for item in tree.get_children():
            tree.delete(item)
        self.root.configure(cursor="watch")
        self.root.update_idletasks()
        try:
            state = list_argos_models(update_index=update_index)
            self._argos_runtime_state = state
            for model in state.models:
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
            self._select_current_argos_direction()
            selected = state.for_direction(self.settings.direction)
            if selected is None and state.models:
                selected = state.models[0]
            self._set_argos_details(selected)
            if update_index:
                self._update_status("Argos: список офлайн-моделей обновлён")
        except Exception as exc:  # pragma: no cover - GUI error path only
            LOGGER.exception("Argos model manager refresh failed")
            messagebox.showerror("Argos", str(exc))
        finally:
            self.root.configure(cursor="")

    @staticmethod
    def _argos_model_status_text(model) -> str:
        if model.installed:
            return "Установлена"
        if model.available_for_download:
            return "Доступна из сети"
        return "Нет пакета"

    def _select_current_argos_direction(self) -> None:
        if self._argos_tree is None:
            return
        current_direction = self.settings.direction
        if current_direction in self._argos_tree.get_children(""):
            self._argos_tree.selection_set(current_direction)
            self._argos_tree.focus(current_direction)

    def _selected_argos_direction(self) -> TranslationDirection | None:
        if self._argos_tree is None:
            return None
        selection = self._argos_tree.selection()
        if selection:
            return selection[0]
        return self.settings.direction

    def _on_argos_selection_changed(self, _event: tk.Event | None = None) -> None:
        if self._argos_runtime_state is None:
            return
        direction = self._selected_argos_direction()
        model = self._argos_runtime_state.for_direction(direction) if direction is not None else None
        self._set_argos_details(model)

    def _set_argos_details(self, model) -> None:
        if self._argos_status_var is None or self._argos_hint_var is None:
            return
        if model is None:
            self._argos_status_var.set("Выберите направление, чтобы увидеть состояние модели Argos.")
            self._argos_hint_var.set("")
            return
        prefix = f"{model.display_name}: "
        if model.installed:
            status = prefix + "локальная модель установлена и готова к офлайн-переводу."
        elif model.available_for_download:
            status = prefix + "пакет найден в индексе Argos и доступен для загрузки из сети, но ещё не установлен локально."
        else:
            status = prefix + "локальная модель пока не найдена."
        self._argos_status_var.set(status)

        notes = model.notes
        if self._argos_runtime_state is not None and self._argos_runtime_state.dependency_error:
            notes = self._argos_runtime_state.dependency_error
        elif self._argos_runtime_state is not None and self._argos_runtime_state.index_error and not model.installed:
            notes = self._argos_runtime_state.index_error
        if model.download_url:
            notes = f"{notes} Источник: {model.download_url}".strip()
        self._argos_hint_var.set(notes)

    def _run_argos_task(self, action_label: str, task) -> None:
        self.root.configure(cursor="watch")
        self.root.update_idletasks()
        try:
            result = task()
            self._populate_argos_model_tree(update_index=False)
            self._update_status(result.message or action_label)
            messagebox.showinfo("Argos", result.message)
            if self.context_service.active_provider_id() == "argos" and self.current_view_model is not None:
                self._start_context_translation(self.current_view_model)
        except Exception as exc:  # pragma: no cover - GUI error path only
            LOGGER.exception("Argos action failed: %s", action_label)
            messagebox.showerror("Ошибка Argos", str(exc))
        finally:
            self.root.configure(cursor="")

    def install_argos_runtime_from_gui(self) -> None:
        self._run_argos_task(
            "Поддержка Argos установлена",
            lambda: install_argos_runtime(self.config.project_root / "requirements-optional.txt"),
        )

    def install_selected_argos_model(self) -> None:
        direction = self._selected_argos_direction()
        if direction is None:
            messagebox.showinfo("Argos", "Сначала выберите направление в списке.")
            return
        self._run_argos_task(
            f"Установлена модель Argos {self._direction_display(direction)}",
            lambda: install_argos_model_for_direction(direction),
        )

    def import_argos_model_from_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите локальную модель Argos",
            filetypes=[("Argos model", "*.argosmodel"), ("Все файлы", "*.*")],
        )
        if not path:
            return
        self._run_argos_task(
            "Импортирована локальная модель Argos",
            lambda: import_argos_model_from_path(Path(path)),
        )

    def select_argos_provider(self) -> None:
        self.provider_var.set("argos")
        self.on_provider_menu_change()
    # ------------------------------------------------------------------
    # Direction/provider settings
    # ------------------------------------------------------------------
    def _direction_display(self, direction: TranslationDirection) -> str:
        return "EN → RU" if direction == EN_RU else "RU → EN"

    def toggle_direction(self) -> None:
        self._set_direction(RU_EN if self.settings.direction == EN_RU else EN_RU)

    def on_direction_menu_change(self) -> None:
        self._set_direction(self.direction_var.get())

    def _set_direction(self, direction: TranslationDirection) -> None:
        direction = direction if direction in (EN_RU, RU_EN) else EN_RU
        if direction == self.settings.direction:
            self.direction_button.configure(text=self._direction_display(direction))
            return
        self.settings.direction = direction
        self.settings = self.settings.normalized()
        self.settings_store.save(self.settings)
        self.context_service.update_settings(self.settings)
        self.direction_var.set(self.settings.direction)
        self.direction_button.configure(text=self._direction_display(self.settings.direction))
        self._refresh_dictionary_footer()
        self._cancel_pending_context_translation()
        self._update_status(f"Направление перевода: {self._direction_display(self.settings.direction)}")
        self._retranslate_current_selection()

    def on_provider_menu_change(self) -> None:
        provider_id = self.provider_var.get() or "disabled"
        self.settings.context_provider_id = provider_id
        self.settings = self.settings.normalized()
        self.settings_store.save(self.settings)
        self.context_service.update_settings(self.settings)
        self.provider_var.set(self.settings.context_provider_id)
        self._cancel_pending_context_translation()
        self._update_status(f"Контекстный провайдер: {self.context_service.provider_name()}")
        if self.current_view_model is not None:
            self._populate_panel(self.current_view_model)
            self._start_context_translation(self.current_view_model)
        else:
            self.example_var.set(self._provider_idle_text())

    def show_settings_window(self, tab_key: str = "general") -> None:
        if self._settings_dialog is None or not self._settings_dialog.window.winfo_exists():
            self._settings_dialog = SettingsDialog(self)
        self._settings_dialog.refresh_all()
        self._settings_dialog.focus_tab(tab_key)

    def show_provider_settings_dialog(self) -> None:
        provider_id = self.context_service.active_provider_id()
        tab_map = {
            "libretranslate": "libretranslate",
            "yandex": "yandex",
            "argos": "argos",
        }
        self.show_settings_window(tab_map.get(provider_id, "general"))

    def _probe_libretranslate_settings(self, base_url: str, api_key: str) -> tuple[bool, str]:
        normalized = normalize_libretranslate_url(base_url)
        endpoint = libretranslate_translate_url(normalized)
        results = probe_libretranslate_directions(base_url, api_key, timeout=8)
        lines = [
            f"Сервер: {normalized or '—'}",
            f"Endpoint: {endpoint or '—'}",
        ]
        all_ok = True
        for direction in (EN_RU, RU_EN):
            result = results.get(direction)
            if result is None:
                all_ok = False
                lines.append(f"{self._direction_display(direction)}: ошибка — результат не получен")
                continue
            if result.ok:
                lines.append(
                    f"{self._direction_display(direction)}: OK — {self._compact_text(result.text, limit=120)}"
                )
                continue
            all_ok = False
            message = result.text or result.error or "контекстный перевод не вернул результат"
            lines.append(
                f"{self._direction_display(direction)}: ошибка — {self._compact_text(message, limit=160)}"
            )
        return all_ok, "\n".join(lines)

    def _show_readonly_text_dialog(self, title: str, message: str, *, geometry: str = "860x620") -> None:
        window = tk.Toplevel(self.root)
        window.title(title)
        window.geometry(geometry)
        window.minsize(580, 360)
        window.transient(self.root)
        window.configure(background="#eef2f7")

        frame = ttk.Frame(window, padding=12, style="App.TFrame")
        frame.pack(fill=tk.BOTH, expand=True)

        text_widget = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            font=tkfont.nametofont("TkTextFont"),
            relief="flat",
            borderwidth=0,
            padx=8,
            pady=8,
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert("1.0", message)
        text_widget.configure(state=tk.DISABLED)

        buttons = ttk.Frame(frame, style="App.TFrame")
        buttons.pack(fill=tk.X, pady=(10, 0))

        def copy_text() -> None:
            window.clipboard_clear()
            window.clipboard_append(message)
            self._update_status(f"Содержимое окна «{title}» скопировано в буфер обмена")

        ttk.Button(buttons, text="Скопировать", command=copy_text).pack(side=tk.LEFT)
        ttk.Button(buttons, text="OK", command=window.destroy).pack(side=tk.RIGHT)
        window.bind("<Escape>", lambda _event: window.destroy())
        text_widget.focus_set()

    def show_argos_installation_help(self) -> None:
        direction = self.settings.direction
        from_code = "en" if direction == EN_RU else "ru"
        to_code = "ru" if direction == EN_RU else "en"
        install_command = "source .venv/bin/activate && python -m pip install -r requirements-optional.txt"
        model_command = (
            f"source .venv/bin/activate && PYTHONPATH=src python tools/install_argos_model.py "
            f"--from-lang {from_code} --to-lang {to_code}"
        )
        list_command = "source .venv/bin/activate && PYTHONPATH=src python tools/install_argos_model.py --list"
        help_message = (
            "Argos нужен только для офлайн контекстного перевода предложений.\n\n"
            "Рекомендуемый путь через GUI:\n"
            "1. Установите optional dependency:\n"
            f"   {install_command}\n\n"
            "2. В приложении откройте «Перевод → Офлайн-модели Argos…».\n"
            "3. Нажмите «Обновить список из сети», затем «Установить выбранную модель»\n"
            "   или импортируйте уже скачанный .argosmodel файл.\n"
            "4. Выберите провайдер «Argos (офлайн)».\n\n"
            "CLI-альтернатива для текущего направления:\n"
            f"{model_command}\n\n"
            "Проверка доступных пакетов:\n"
            f"{list_command}\n\n"
            "Подсказка: это окно можно растягивать, а команды — копировать кнопкой снизу."
        )
        self._show_readonly_text_dialog("Установка Argos", help_message)

    def _retranslate_current_selection(self) -> None:
        if self.current_highlight_token is None:
            self.example_var.set(self._provider_idle_text())
            return
        x0, y0, x1, y1 = self.current_highlight_token.rect
        self.process_click_at_page_coords(
            self.current_highlight_token.page_index,
            (x0 + x1) / 2,
            (y0 + y1) / 2,
        )

    # ------------------------------------------------------------------
    # UI font settings
    # ------------------------------------------------------------------
    def change_ui_font_size(self, delta: int) -> None:
        updated = UiSettings(**{**self.settings.__dict__, "ui_font_size": self.settings.ui_font_size + delta}).normalized()
        if updated.ui_font_size == self.settings.ui_font_size:
            return
        self.settings = updated
        self.settings_store.save(self.settings)
        self.context_service.update_settings(self.settings)
        self._configure_styles()
        self.direction_button.configure(text=self._direction_display(self.settings.direction))
        self._update_status(f"Размер интерфейса: {self.settings.ui_font_size} pt")

    def reset_ui_font_size(self) -> None:
        defaults = UiSettings(direction=self.settings.direction, context_provider_id=self.settings.context_provider_id)
        defaults.libretranslate_url = self.settings.libretranslate_url
        defaults.libretranslate_api_key = self.settings.libretranslate_api_key
        defaults.yandex_folder_id = self.settings.yandex_folder_id
        defaults.yandex_api_key = self.settings.yandex_api_key
        defaults.yandex_iam_token = self.settings.yandex_iam_token
        self.settings = defaults.normalized()
        self.settings_store.save(self.settings)
        self.context_service.update_settings(self.settings)
        self._configure_styles()
        self.direction_button.configure(text=self._direction_display(self.settings.direction))
        self._update_status(f"Размер интерфейса сброшен: {self.settings.ui_font_size} pt")
