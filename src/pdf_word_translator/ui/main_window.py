"""Tkinter main window for the offline document word translator MVP."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import logging
import tkinter as tk
import tkinter.font as tkfont
from tkinter import filedialog, messagebox, ttk
from PIL import ImageTk

from ..config import AppConfig
from ..models import SearchHit, WordToken
from ..plugin_loader import PluginLoader
from ..services.dictionary_service import DictionaryService
from ..services.document_service import DocumentService
from ..services.translation_workflow import TranslationWorkflow, TranslationViewModel
from ..utils.dictionary_installer import (
    import_csv_pack,
    import_freedict_pack,
    install_default_pack,
    install_sqlite_pack,
)
from ..utils.settings_store import SettingsStore, UiSettings


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class CanvasPageLayout:
    """Placement of one rendered page inside the scrolling canvas."""

    page_index: int
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height


class MainWindow:
    """Main application window.

    The class keeps the UI logic together while relying on services for all
    document and dictionary operations. That separation makes the click workflow
    easy to test outside the GUI.
    """

    PAGE_MARGIN = 24
    PAGE_GAP = 22
    MIN_ZOOM = 0.5
    MAX_ZOOM = 6.0

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

        self.current_page_index = 0
        self.current_zoom = 1.20
        self.page_photos: list[ImageTk.PhotoImage] = []
        self.page_layouts: dict[int, CanvasPageLayout] = {}
        self.current_highlight_token: WordToken | None = None
        self.current_search_hits: list[SearchHit] = []
        self.current_search_index = -1
        self.search_rect_id: int | None = None
        self.word_rect_id: int | None = None
        self._viewport_update_scheduled = False

        self._build_window()

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

    def _build_menubar(self) -> None:
        menu = tk.Menu(self.root)
        self.root.configure(menu=menu)

        file_menu = tk.Menu(menu)
        file_menu.add_command(label="Открыть документ…", command=self.open_document_dialog, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.root.destroy)
        menu.add_cascade(label="Файл", menu=file_menu)

        dictionaries_menu = tk.Menu(menu)
        dictionaries_menu.add_command(label="Скачать общий FreeDict EN→RU", command=self.install_default_dictionary_pack)
        dictionaries_menu.add_separator()
        dictionaries_menu.add_command(label="Подключить SQLite-словарь…", command=self.install_sqlite_dictionary_pack)
        dictionaries_menu.add_command(label="Импортировать CSV-словарь…", command=self.import_csv_dictionary_pack)
        dictionaries_menu.add_command(label="Импортировать FreeDict TEI…", command=self.import_freedict_dictionary_pack)
        menu.add_cascade(label="Словари", menu=dictionaries_menu)

        view_menu = tk.Menu(menu)
        view_menu.add_command(label="Интерфейс крупнее", command=lambda: self.change_ui_font_size(1))
        view_menu.add_command(label="Интерфейс мельче", command=lambda: self.change_ui_font_size(-1))
        view_menu.add_command(label="Сбросить размер интерфейса", command=self.reset_ui_font_size)
        menu.add_cascade(label="Вид", menu=view_menu)

        self.dictionary_context_menu = tk.Menu(self.root, tearoff=False)
        self.dictionary_context_menu.add_command(label="Скачать общий FreeDict EN→RU", command=self.install_default_dictionary_pack)
        self.dictionary_context_menu.add_command(label="Подключить SQLite-словарь…", command=self.install_sqlite_dictionary_pack)
        self.dictionary_context_menu.add_command(label="Импортировать CSV-словарь…", command=self.import_csv_dictionary_pack)
        self.dictionary_context_menu.add_command(label="Импортировать FreeDict TEI…", command=self.import_freedict_dictionary_pack)

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self.root, padding=(12, 10, 12, 4), style="Toolbar.TFrame")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(toolbar, text="Открыть", command=self.open_document_dialog, style="Toolbar.TButton").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="◀", command=self.previous_page, width=3).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="▶", command=self.next_page, width=3).pack(side=tk.LEFT, padx=(4, 10))

        self.page_label = ttk.Label(toolbar, text="Стр. 0 / 0")
        self.page_label.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Button(toolbar, text="-", command=lambda: self.change_zoom(-0.1), width=3).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="+", command=lambda: self.change_zoom(0.1), width=3).pack(side=tk.LEFT, padx=(4, 10))

        self.zoom_label = ttk.Label(toolbar, text="120%")
        self.zoom_label.pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(toolbar, text="Поиск:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(4, 4))
        ttk.Button(toolbar, text="Найти", command=self.execute_search).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Пред.", command=lambda: self.navigate_search(-1)).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Button(toolbar, text="След.", command=lambda: self.navigate_search(1)).pack(side=tk.LEFT, padx=(4, 0))

        self.search_status_label = ttk.Label(toolbar, text="")
        self.search_status_label.pack(side=tk.LEFT, padx=(10, 0))

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
        self._build_translation_panel(self.translation_panel)

    def _build_translation_panel(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Справка по слову", style="CardTitle.TLabel").pack(anchor="w")

        self.lookup_meta_var = tk.StringVar(value="Нажмите на слово в документе — здесь появится краткий перевод.")
        self.best_translation_var = tk.StringVar(value="—")
        self.example_var = tk.StringVar(value="Пример: —")
        self.alternatives_var = tk.StringVar(value="Варианты: —")
        self.dictionary_footer_var = tk.StringVar(
            value=f"Словари: {self.dictionary_service.pack_count()} пак. · {self.dictionary_service.entry_count()} статей"
        )

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
        if not self._viewport_update_scheduled:
            self._viewport_update_scheduled = True
            self.root.after_idle(self._update_viewport_page_index)

    def _on_canvas_configure(self, _event: tk.Event) -> None:
        wraplength = max(400, self.canvas.winfo_width() - 48)
        for widget in (self.meta_label, self.best_label, self.example_label, self.alternatives_label):
            widget.configure(wraplength=wraplength)
        self._schedule_viewport_update()

    def _schedule_viewport_update(self) -> None:
        if not self._viewport_update_scheduled:
            self._viewport_update_scheduled = True
            self.root.after_idle(self._update_viewport_page_index)

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

    def open_document_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите документ",
            filetypes=self._document_filetypes(),
        )
        if path:
            self.open_document_path(Path(path))

    def open_document_path(self, path: Path) -> None:
        try:
            self.document_service.open_document(path)
            self.current_page_index = 0
            self.current_highlight_token = None
            self.current_search_hits = []
            self.current_search_index = -1
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
            rendered = self.document_service.render_page(page_index, self.current_zoom)
            photo = ImageTk.PhotoImage(rendered.image)
            self.page_photos.append(photo)

            left = self.PAGE_MARGIN
            top = current_top
            width = rendered.image.width
            height = rendered.image.height
            self.page_layouts[page_index] = CanvasPageLayout(page_index=page_index, left=left, top=top, width=width, height=height)

            self.canvas.create_rectangle(left - 3, top - 3, left + width + 3, top + height + 3, fill="#d8e0ea", outline="")
            self.canvas.create_image(left, top, image=photo, anchor="nw")
            self.canvas.create_text(left + 10, top - 14, text=f"Стр. {page_index + 1}", fill="#cbd5e1", anchor="w")

            current_top += height + self.PAGE_GAP
            max_width = max(max_width, width)

        self.canvas.configure(scrollregion=(0, 0, max_width + self.PAGE_MARGIN * 2, current_top + self.PAGE_MARGIN))
        self.zoom_label.configure(text=f"{int(self.current_zoom * 100)}%")

        if self.current_highlight_token is not None:
            self._draw_word_highlight(self.current_highlight_token)
        if 0 <= self.current_search_index < len(self.current_search_hits):
            self._draw_search_highlight(self.current_search_hits[self.current_search_index])

        if anchor_doc_point is not None and anchor_widget is not None:
            self._scroll_doc_point_to_widget(anchor_doc_point, anchor_widget)
        elif focus_page is not None:
            self.scroll_to_page(focus_page)
        else:
            self._schedule_viewport_update()

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

        self.current_zoom = new_zoom
        self.document_service.clear_cache()
        self.render_document(focus_page=self.current_page_index, anchor_doc_point=anchor_doc_point, anchor_widget=anchor_widget)

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
        view_model = self.workflow.translate_point(page_index, page_x, page_y)
        if view_model is None:
            self._update_status("Слово под курсором не найдено.")
            return None
        self.current_page_index = page_index
        self.current_highlight_token = view_model.token
        self._draw_word_highlight(view_model.token)
        self._populate_panel(view_model)
        self._update_status(f"Выбрано слово: {view_model.token.text}")
        return view_model

    def _page_layout_at_canvas_coords(self, canvas_x: float, canvas_y: float) -> CanvasPageLayout | None:
        for layout in self.page_layouts.values():
            if layout.left <= canvas_x <= layout.right and layout.top <= canvas_y <= layout.bottom:
                return layout
        return None

    def _draw_word_highlight(self, token: WordToken) -> None:
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
        self._scroll_rect_into_view(
            (
                layout.left + x0 * self.current_zoom,
                layout.top + y0 * self.current_zoom,
                layout.left + x1 * self.current_zoom,
                layout.top + y1 * self.current_zoom,
            )
        )

    def _draw_search_highlight(self, hit: SearchHit) -> None:
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
            example_text = self._dictionary_example(entry) or view_model.context.text or "—"
            self.example_var.set(example_text)
            alternatives = ", ".join(entry.alternative_translations[:8]) or "—"
            self.alternatives_var.set(f"Ещё варианты: {alternatives}")
        else:
            self.lookup_meta_var.set(token.text)
            self.best_translation_var.set("Перевод не найден")
            self.example_var.set(view_model.context.text or "—")
            forms = ", ".join(view_model.lookup.candidate_forms[:8]) if view_model.lookup.candidate_forms else "—"
            self.alternatives_var.set(f"Проверенные формы: {forms}")

    def _dictionary_example(self, entry) -> str:
        if not entry.examples:
            return ""
        src, dst = entry.examples[0]
        if dst:
            return f"{src} → {dst}"
        return src

    def _clear_panel(self) -> None:
        self.lookup_meta_var.set("Нажмите на слово в документе — здесь появится краткий перевод.")
        self.best_translation_var.set("—")
        self.example_var.set("Пример: —")
        self.alternatives_var.set("Варианты: —")
        self._refresh_dictionary_footer()

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

    def _refresh_dictionary_footer(self) -> None:
        self.dictionary_footer_var.set(
            f"Словари: {self.dictionary_service.pack_count()} пак. · {self.dictionary_service.entry_count()} статей"
        )

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

    def install_default_dictionary_pack(self) -> None:
        self._run_dictionary_task(
            "Установлен общий словарь",
            lambda: install_default_pack(self.config.runtime_dictionary_dir, self.config.runtime_download_dir),
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
            lambda: import_csv_pack(Path(path), self.config.runtime_dictionary_dir),
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
            lambda: import_freedict_pack(Path(path), self.config.runtime_dictionary_dir),
        )

    def show_dictionary_context_menu(self, event: tk.Event) -> None:
        try:
            self.dictionary_context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.dictionary_context_menu.grab_release()

    def change_ui_font_size(self, delta: int) -> None:
        updated = UiSettings(ui_font_size=self.settings.ui_font_size + delta).normalized()
        if updated.ui_font_size == self.settings.ui_font_size:
            return
        self.settings = updated
        self.settings_store.save(self.settings)
        self._configure_styles()
        self._update_status(f"Размер интерфейса: {self.settings.ui_font_size} pt")

    def reset_ui_font_size(self) -> None:
        self.settings = UiSettings().normalized()
        self.settings_store.save(self.settings)
        self._configure_styles()
        self._update_status(f"Размер интерфейса сброшен: {self.settings.ui_font_size} pt")
