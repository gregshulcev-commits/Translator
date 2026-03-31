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
        self.current_zoom = 1.25
        self.current_photo = None
        self.current_highlight_token: WordToken | None = None
        self.current_search_hits: list[SearchHit] = []
        self.current_search_index = -1
        self.search_rect_id: int | None = None
        self.word_rect_id: int | None = None

        self._build_window()

    def _build_window(self) -> None:
        self.root.title("Офлайн переводчик PDF — MVP")
        self.root.geometry("1400x900")

        self._build_toolbar()
        self._build_content()
        self._build_statusbar()
        self._bind_shortcuts()
        self._update_status("Готово. Откройте PDF-файл.")

    def _build_toolbar(self) -> None:
        toolbar = ttk.Frame(self.root, padding=6)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        ttk.Button(toolbar, text="Открыть PDF", command=self.open_document_dialog).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(toolbar, text="◀", command=self.previous_page).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="▶", command=self.next_page).pack(side=tk.LEFT, padx=(4, 10))

        self.page_label = ttk.Label(toolbar, text="Стр. 0 / 0")
        self.page_label.pack(side=tk.LEFT, padx=(0, 12))

        ttk.Button(toolbar, text="-", command=lambda: self.change_zoom(-0.1)).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="+", command=lambda: self.change_zoom(0.1)).pack(side=tk.LEFT, padx=(4, 10))

        self.zoom_label = ttk.Label(toolbar, text="125%")
        self.zoom_label.pack(side=tk.LEFT, padx=(0, 16))

        ttk.Label(toolbar, text="Поиск:").pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=28)
        self.search_entry.pack(side=tk.LEFT, padx=(4, 4))
        ttk.Button(toolbar, text="Найти", command=self.execute_search).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Пред.", command=lambda: self.navigate_search(-1)).pack(side=tk.LEFT, padx=(4, 0))
        ttk.Button(toolbar, text="След.", command=lambda: self.navigate_search(1)).pack(side=tk.LEFT, padx=(4, 0))

        self.search_status_label = ttk.Label(toolbar, text="")
        self.search_status_label.pack(side=tk.LEFT, padx=(10, 0))

    def _build_content(self) -> None:
        paned = ttk.Panedwindow(self.root, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        viewer_frame = ttk.Frame(paned)
        paned.add(viewer_frame, weight=4)

        panel_frame = ttk.Frame(paned, padding=10, width=360)
        paned.add(panel_frame, weight=1)

        self.canvas = tk.Canvas(viewer_frame, background="#606060", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        yscroll = ttk.Scrollbar(viewer_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)
        xscroll = ttk.Scrollbar(viewer_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        xscroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.configure(yscrollcommand=yscroll.set, xscrollcommand=xscroll.set)
        self.canvas.bind("<Button-1>", self.on_canvas_click)

        self._build_translation_panel(panel_frame)

    def _build_translation_panel(self, parent: ttk.Frame) -> None:
        ttk.Label(parent, text="Перевод", font=("TkDefaultFont", 12, "bold")).pack(anchor="w")

        self.source_word_var = tk.StringVar(value="—")
        self.headword_var = tk.StringVar(value="—")
        self.transcription_var = tk.StringVar(value="—")
        self.best_translation_var = tk.StringVar(value="—")

        for label_text, variable in (
            ("Выбранное слово", self.source_word_var),
            ("Словарная форма", self.headword_var),
            ("Транскрипция", self.transcription_var),
            ("Лучший перевод", self.best_translation_var),
        ):
            block = ttk.Frame(parent)
            block.pack(fill=tk.X, pady=(10, 0), anchor="w")
            ttk.Label(block, text=label_text, font=("TkDefaultFont", 9, "bold")).pack(anchor="w")
            ttk.Label(block, textvariable=variable, wraplength=320, justify=tk.LEFT).pack(anchor="w")

        self.alternatives_text = self._make_readonly_text(parent, "Альтернативы")
        self.context_text = self._make_readonly_text(parent, "Контекст из документа")
        self.dictionary_examples_text = self._make_readonly_text(parent, "Примеры из словаря")
        self.notes_text = self._make_readonly_text(parent, "Примечания")

        stats_frame = ttk.Frame(parent)
        stats_frame.pack(fill=tk.X, pady=(12, 0))
        self.dictionary_stats_var = tk.StringVar(value=f"Записей в словаре: {self.dictionary_service.entry_count()}")
        ttk.Label(stats_frame, textvariable=self.dictionary_stats_var).pack(anchor="w")

    def _make_readonly_text(self, parent: ttk.Frame, title: str) -> tk.Text:
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=False, pady=(10, 0))
        ttk.Label(frame, text=title, font=("TkDefaultFont", 9, "bold")).pack(anchor="w")
        text = tk.Text(frame, height=5, wrap=tk.WORD)
        text.pack(fill=tk.X, expand=False)
        text.configure(state=tk.DISABLED)
        return text

    def _build_statusbar(self) -> None:
        status_frame = ttk.Frame(self.root, padding=(6, 2))
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var = tk.StringVar(value="")
        ttk.Label(status_frame, textvariable=self.status_var).pack(anchor="w")

    def _bind_shortcuts(self) -> None:
        self.root.bind("<Control-o>", lambda event: self.open_document_dialog())
        self.root.bind("<Control-f>", lambda event: self.search_entry.focus_set())
        self.root.bind("<Prior>", lambda event: self.previous_page())
        self.root.bind("<Next>", lambda event: self.next_page())

    def _set_readonly_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state=tk.NORMAL)
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value)
        widget.configure(state=tk.DISABLED)

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
            outline="#ffcc00",
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
            outline="#33dd88",
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
        self.source_word_var.set(view_model.token.text)
        if view_model.lookup.found and view_model.lookup.entry is not None:
            entry = view_model.lookup.entry
            self.headword_var.set(entry.headword)
            self.transcription_var.set(entry.transcription or "—")
            self.best_translation_var.set(entry.best_translation or "—")
            self._set_readonly_text(
                self.alternatives_text,
                "\n".join(f"• {item}" for item in entry.alternative_translations) or "—",
            )
            dict_examples = "\n\n".join(f"EN: {src}\nRU: {dst}" for src, dst in entry.examples) or "—"
            self._set_readonly_text(self.dictionary_examples_text, dict_examples)
            self._set_readonly_text(self.notes_text, entry.notes or f"Стратегия поиска: {view_model.lookup.strategy}")
        else:
            self.headword_var.set("—")
            self.transcription_var.set("—")
            self.best_translation_var.set("Слово не найдено в стартовом словаре")
            forms = ", ".join(view_model.lookup.candidate_forms) if view_model.lookup.candidate_forms else "—"
            self._set_readonly_text(self.alternatives_text, f"Проверенные формы: {forms}")
            self._set_readonly_text(self.dictionary_examples_text, "—")
            self._set_readonly_text(self.notes_text, "Добавьте более полный словарь через импорт CSV/SQLite.")
        self._set_readonly_text(self.context_text, view_model.context.text or "—")

    def _clear_panel(self) -> None:
        self.source_word_var.set("—")
        self.headword_var.set("—")
        self.transcription_var.set("—")
        self.best_translation_var.set("—")
        for widget in (
            self.alternatives_text,
            self.context_text,
            self.dictionary_examples_text,
            self.notes_text,
        ):
            self._set_readonly_text(widget, "—")

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
