"""Tkinter main window for the offline PDF word translator MVP."""
from __future__ import annotations

from pathlib import Path
import logging
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import ImageTk

from ..config import AppConfig
from ..models import SearchHit, WordToken
from ..services.dictionary_service import DictionaryService
from ..services.document_service import DocumentService
from ..services.translation_workflow import TranslationWorkflow, TranslationViewModel


LOGGER = logging.getLogger(__name__)


class MainWindow:
    """Main application window.

    The class keeps the UI logic together while relying on services for all
    document and dictionary operations. That separation makes the click workflow
    easy to test outside the GUI.
    """

    def __init__(
        self,
        root: tk.Tk,
        config: AppConfig,
        document_service: DocumentService,
        dictionary_service: DictionaryService,
        workflow: TranslationWorkflow,
    ) -> None:
        self.root = root
        self.config = config
        self.document_service = document_service
        self.dictionary_service = dictionary_service
        self.workflow = workflow

        self.current_page_index = 0
        self.current_zoom = 1.20
        self.current_photo = None
        self.current_highlight_token: WordToken | None = None
        self.current_search_hits: list[SearchHit] = []
        self.current_search_index = -1
        self.search_rect_id: int | None = None
        self.word_rect_id: int | None = None

        self._build_window()

    def _build_window(self) -> None:
        self.root.title("Офлайн переводчик PDF — MVP")
        self.root.geometry("1400x920")
        self.root.configure(background="#eef2f7")
        self._configure_styles()

        self._build_toolbar()
        self._build_content()
        self._build_statusbar()
        self._bind_shortcuts()
        self._update_status("Готово. Откройте PDF-файл.")

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("App.TFrame", background="#eef2f7")
        style.configure("Toolbar.TFrame", background="#eef2f7")
        style.configure("Surface.TFrame", background="#ffffff")
        style.configure("InfoCard.TFrame", background="#ffffff", relief="flat")
        style.configure("CardTitle.TLabel", background="#ffffff", foreground="#0f172a", font=("TkDefaultFont", 12, "bold"))
        style.configure("Meta.TLabel", background="#ffffff", foreground="#475569", font=("TkDefaultFont", 10))
        style.configure("BestTranslation.TLabel", background="#ffffff", foreground="#0f172a", font=("TkDefaultFont", 16, "bold"))
        style.configure("Context.TLabel", background="#ffffff", foreground="#1e293b", font=("TkDefaultFont", 10))
        style.configure("Muted.TLabel", background="#ffffff", foreground="#64748b", font=("TkDefaultFont", 10))
        style.configure("Status.TFrame", background="#e2e8f0")
        style.configure("Status.TLabel", background="#e2e8f0", foreground="#334155")
        style.configure("Toolbar.TButton", padding=(10, 5))

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self.root, padding=(12, 10, 12, 4), style="Toolbar.TFrame")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(toolbar, text="Открыть PDF", command=self.open_document_dialog, style="Toolbar.TButton").pack(side=tk.LEFT, padx=(0, 6))
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

        self.canvas = tk.Canvas(viewer_frame, background="#5b6472", highlightthickness=0, bd=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll = ttk.Scrollbar(viewer_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll = ttk.Scrollbar(viewer_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<Enter>", self._bind_canvas_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_canvas_mousewheel)

        info_card = ttk.Frame(body, padding=14, style="InfoCard.TFrame")
        info_card.pack(fill=tk.X, pady=(10, 0))
        self._build_translation_panel(info_card)

    def _build_translation_panel(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Подсказка по слову", style="CardTitle.TLabel").pack(anchor="w")

        self.lookup_meta_var = tk.StringVar(value="Нажмите на слово в документе — здесь появится краткий перевод.")
        self.best_translation_var = tk.StringVar(value="—")
        self.example_var = tk.StringVar(value="Пример: —")
        self.alternatives_var = tk.StringVar(value="Варианты: —")
        self.dictionary_footer_var = tk.StringVar(
            value=f"Словари: {self.dictionary_service.pack_count()} пак. · {self.dictionary_service.entry_count()} статей"
        )

        self.meta_label = ttk.Label(parent, textvariable=self.lookup_meta_var, style="Meta.TLabel", wraplength=1200, justify=tk.LEFT)
        self.meta_label.pack(anchor="w", pady=(6, 6), fill=tk.X)

        self.best_label = ttk.Label(parent, textvariable=self.best_translation_var, style="BestTranslation.TLabel", wraplength=1200, justify=tk.LEFT)
        self.best_label.pack(anchor="w", pady=(0, 6), fill=tk.X)

        self.example_label = ttk.Label(parent, textvariable=self.example_var, style="Context.TLabel", wraplength=1200, justify=tk.LEFT)
        self.example_label.pack(anchor="w", pady=(0, 4), fill=tk.X)

        self.alternatives_label = ttk.Label(parent, textvariable=self.alternatives_var, style="Muted.TLabel", wraplength=1200, justify=tk.LEFT)
        self.alternatives_label.pack(anchor="w", fill=tk.X)

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

    def _on_mousewheel(self, event: tk.Event) -> None:
        if self.document_service.current_path is None:
            return
        if getattr(event, "num", None) == 4:
            delta = -4
        elif getattr(event, "num", None) == 5:
            delta = 4
        else:
            raw_delta = int(getattr(event, "delta", 0))
            if raw_delta == 0:
                return
            delta = -1 * max(1, abs(raw_delta) // 120) if raw_delta > 0 else max(1, abs(raw_delta) // 120)
        self.canvas.yview_scroll(delta, "units")

    def _update_status(self, text: str) -> None:
        self.status_var.set(text)

    def open_document_dialog(self) -> None:
        path = filedialog.askopenfilename(
            title="Выберите PDF-файл",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
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
            self._clear_panel()
            self.show_page(self.current_page_index)
            self._update_status(f"Открыт документ: {path.name}")
        except Exception as exc:  # pragma: no cover - GUI error path only
            LOGGER.exception("Failed to open document %s", path)
            messagebox.showerror("Ошибка открытия", str(exc))

    def show_page(self, page_index: int) -> None:
        rendered = self.document_service.render_page(page_index, self.current_zoom)
        self.current_page_index = page_index
        self.current_photo = ImageTk.PhotoImage(rendered.image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, image=self.current_photo, anchor="nw")
        self.canvas.configure(scrollregion=(0, 0, rendered.image.width, rendered.image.height))
        self.page_label.configure(text=f"Стр. {page_index + 1} / {self.document_service.page_count()}")
        self.zoom_label.configure(text=f"{int(self.current_zoom * 100)}%")
        self.word_rect_id = None
        self.search_rect_id = None
        if self.current_highlight_token and self.current_highlight_token.page_index == page_index:
            self._draw_word_highlight(self.current_highlight_token)
        if 0 <= self.current_search_index < len(self.current_search_hits):
            hit = self.current_search_hits[self.current_search_index]
            if hit.page_index == page_index:
                self._draw_search_highlight(hit)
        self.root.after(25, lambda: self.document_service.prewarm_neighbors(page_index, self.current_zoom))

    def previous_page(self) -> None:
        if self.document_service.current_path is None:
            return
        if self.current_page_index > 0:
            self.show_page(self.current_page_index - 1)

    def next_page(self) -> None:
        if self.document_service.current_path is None:
            return
        if self.current_page_index + 1 < self.document_service.page_count():
            self.show_page(self.current_page_index + 1)

    def change_zoom(self, delta: float) -> None:
        if self.document_service.current_path is None:
            return
        new_zoom = round(max(0.6, min(2.5, self.current_zoom + delta)), 2)
        if new_zoom == self.current_zoom:
            return
        self.current_zoom = new_zoom
        self.show_page(self.current_page_index)

    def on_canvas_click(self, event: tk.Event) -> None:
        if self.document_service.current_path is None:
            return
        canvas_x = self.canvas.canvasx(event.x)
        canvas_y = self.canvas.canvasy(event.y)
        page_x = canvas_x / self.current_zoom
        page_y = canvas_y / self.current_zoom
        self.process_click_at_page_coords(page_x, page_y)

    def process_click_at_page_coords(self, page_x: float, page_y: float) -> TranslationViewModel | None:
        view_model = self.workflow.translate_point(self.current_page_index, page_x, page_y)
        if view_model is None:
            self._update_status("Слово под курсором не найдено.")
            return None
        self.current_highlight_token = view_model.token
        self._draw_word_highlight(view_model.token)
        self._populate_panel(view_model)
        self._update_status(f"Выбрано слово: {view_model.token.text}")
        return view_model

    def _draw_word_highlight(self, token: WordToken) -> None:
        if self.word_rect_id is not None:
            self.canvas.delete(self.word_rect_id)
        x0, y0, x1, y1 = token.rect
        self.word_rect_id = self.canvas.create_rectangle(
            x0 * self.current_zoom,
            y0 * self.current_zoom,
            x1 * self.current_zoom,
            y1 * self.current_zoom,
            outline="#f59e0b",
            width=2,
        )
        self._scroll_rect_into_view((x0 * self.current_zoom, y0 * self.current_zoom, x1 * self.current_zoom, y1 * self.current_zoom))

    def _draw_search_highlight(self, hit: SearchHit) -> None:
        if self.search_rect_id is not None:
            self.canvas.delete(self.search_rect_id)
        x0, y0, x1, y1 = hit.rect
        self.search_rect_id = self.canvas.create_rectangle(
            x0 * self.current_zoom,
            y0 * self.current_zoom,
            x1 * self.current_zoom,
            y1 * self.current_zoom,
            outline="#22c55e",
            width=2,
        )
        self._scroll_rect_into_view((x0 * self.current_zoom, y0 * self.current_zoom, x1 * self.current_zoom, y1 * self.current_zoom))

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
            self.example_var.set(f"Пример: {view_model.context.text or self._dictionary_example(entry) or '—'}")
            alternatives = ", ".join(entry.alternative_translations[:8]) or "—"
            self.alternatives_var.set(f"Варианты: {alternatives}")
        else:
            self.lookup_meta_var.set(token.text)
            self.best_translation_var.set("Перевод не найден в установленных словарях")
            self.example_var.set(f"Пример: {view_model.context.text or '—'}")
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
        if hit.page_index != self.current_page_index:
            self.show_page(hit.page_index)
        self._draw_search_highlight(hit)
        self._update_status(f"Поиск: {hit.preview}")
