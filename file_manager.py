"""
╔══════════════════════════════════════════════════╗
║       ФАЙЛОВИЙ МЕНЕДЖЕР  — Dark Edition          ║
║  Запуск:  python file_manager.py                 ║
║  Залежності: тільки стандартна бібліотека Python ║
╚══════════════════════════════════════════════════╝
"""

import os, shutil, stat, time, threading, subprocess, platform
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

# ──────────────────────────────────────────────────────────────────────────────
#  ПАЛІТРА КОЛЬОРІВ  (темна тема у стилі VS Code / Midnight)
# ──────────────────────────────────────────────────────────────────────────────
C = {
    "bg":          "#1e1e2e",   # основний фон
    "bg2":         "#181825",   # фон сайдбару / панелей
    "bg3":         "#313244",   # фон заголовків, hover
    "bg4":         "#45475a",   # роздільники, рамки
    "accent":      "#cba6f7",   # фіолетовий акцент (Mauve)
    "accent2":     "#89b4fa",   # блакитний акцент (Blue)
    "accent3":     "#a6e3a1",   # зелений (Green)
    "accent4":     "#f38ba8",   # червоний (Red)
    "accent5":     "#fab387",   # персиковий (Peach)
    "accent6":     "#f9e2af",   # жовтий (Yellow)
    "text":        "#cdd6f4",   # основний текст
    "text2":       "#a6adc8",   # вторинний текст
    "text3":       "#585b70",   # підказки / приховане
    "sel":         "#45475a",   # фон виділення
    "sel_fg":      "#cba6f7",   # текст виділення
    "toolbar":     "#24273a",   # тулбар
    "statusbar":   "#11111b",   # статусбар
    "entry_bg":    "#313244",   # фон поля введення
    "entry_bd":    "#585b70",   # рамка поля введення
    "btn_bg":      "#313244",
    "btn_hover":   "#45475a",
    "btn_press":   "#585b70",
}

# ──────────────────────────────────────────────────────────────────────────────
#  УТИЛІТИ
# ──────────────────────────────────────────────────────────────────────────────

def fmt_size(n: int) -> str:
    for u in ("Б", "КБ", "МБ", "ГБ", "ТБ"):
        if n < 1024:
            return f"{n} {u}" if u == "Б" else f"{n:.1f} {u}"
        n /= 1024
    return f"{n:.1f} ПБ"

def fmt_time(ts: float) -> str:
    return time.strftime("%d.%m.%Y  %H:%M", time.localtime(ts))

def open_native(path: str):
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception as e:
        messagebox.showerror("Помилка", str(e))

# ──────────────────────────────────────────────────────────────────────────────
#  СТИЛІЗАЦІЯ TTK
# ──────────────────────────────────────────────────────────────────────────────

def apply_theme(root: tk.Tk):
    style = ttk.Style(root)
    style.theme_use("default")

    # загальний фон
    style.configure(".",
        background=C["bg"], foreground=C["text"],
        font=("Segoe UI", 10), borderwidth=0, relief="flat"
    )

    # Treeview (список файлів)
    style.configure("Files.Treeview",
        background=C["bg"], foreground=C["text"],
        fieldbackground=C["bg"],
        rowheight=26,
        borderwidth=0,
        font=("Segoe UI", 10),
    )
    style.map("Files.Treeview",
        background=[("selected", C["sel"])],
        foreground=[("selected", C["accent"])],
    )
    style.configure("Files.Treeview.Heading",
        background=C["bg2"], foreground=C["text2"],
        relief="flat", borderwidth=0,
        font=("Segoe UI", 9, "bold"),
        padding=(8, 6),
    )
    style.map("Files.Treeview.Heading",
        background=[("active", C["bg3"])],
        foreground=[("active", C["accent"])],
    )

    # Treeview (дерево папок)
    style.configure("Nav.Treeview",
        background=C["bg2"], foreground=C["text2"],
        fieldbackground=C["bg2"],
        rowheight=28,
        borderwidth=0,
        font=("Segoe UI", 10),
        indent=16,
    )
    style.map("Nav.Treeview",
        background=[("selected", C["accent"])],
        foreground=[("selected", C["bg"])],
    )

    # Scrollbar
    style.configure("Dark.Vertical.TScrollbar",
        background=C["bg3"], troughcolor=C["bg2"],
        arrowcolor=C["text3"], borderwidth=0, width=8,
    )
    style.configure("Dark.Horizontal.TScrollbar",
        background=C["bg3"], troughcolor=C["bg2"],
        arrowcolor=C["text3"], borderwidth=0, width=8,
    )
    style.map("Dark.Vertical.TScrollbar",
        background=[("active", C["bg4"])],
    )
    style.map("Dark.Horizontal.TScrollbar",
        background=[("active", C["bg4"])],
    )

    # PanedWindow
    style.configure("TPanedwindow", background=C["bg4"])

# ──────────────────────────────────────────────────────────────────────────────
#  ІКОНКИ (емодзі → рядки)
# ──────────────────────────────────────────────────────────────────────────────

EXT_ICONS = {
    ".py":"🐍", ".js":"📜", ".ts":"📜", ".html":"🌐", ".css":"🎨",
    ".json":"📋", ".xml":"📋", ".yaml":"📋", ".yml":"📋",
    ".md":"📝", ".txt":"📝", ".rst":"📝", ".log":"📝",
    ".pdf":"📄", ".doc":"📄", ".docx":"📄", ".odt":"📄",
    ".xls":"📊", ".xlsx":"📊", ".csv":"📊",
    ".ppt":"📊", ".pptx":"📊",
    ".jpg":"🖼", ".jpeg":"🖼", ".png":"🖼", ".gif":"🖼",
    ".svg":"🖼", ".ico":"🖼", ".webp":"🖼", ".bmp":"🖼",
    ".mp3":"🎵", ".flac":"🎵", ".wav":"🎵", ".ogg":"🎵", ".aac":"🎵",
    ".mp4":"🎬", ".mkv":"🎬", ".avi":"🎬", ".mov":"🎬", ".webm":"🎬",
    ".zip":"📦", ".tar":"📦", ".gz":"📦", ".7z":"📦", ".rar":"📦", ".bz2":"📦",
    ".exe":"⚙", ".msi":"⚙", ".sh":"⚙", ".bat":"⚙", ".cmd":"⚙",
    ".iso":"💿", ".img":"💿",
    ".db":"🗄", ".sqlite":"🗄", ".sql":"🗄",
    ".c":"🔧", ".cpp":"🔧", ".h":"🔧", ".rs":"🔧", ".go":"🔧", ".java":"☕",
}

# кольори тегів у списку файлів
TAG_COLORS = {
    "dir":    C["accent2"],
    "exec":   C["accent3"],
    "link":   C["accent"],
    "hidden": C["text3"],
    "img":    C["accent6"],
    "audio":  C["accent3"],
    "video":  C["accent5"],
    "arch":   C["accent4"],
    "code":   C["accent"],
}

def get_icon(name: str, is_dir: bool) -> str:
    if is_dir:
        return "📁"
    return EXT_ICONS.get(Path(name).suffix.lower(), "📄")

def get_tag(name: str, is_dir: bool, is_link: bool, executable: bool) -> str:
    if name.startswith("."):
        return "hidden"
    if is_link:
        return "link"
    if is_dir:
        return "dir"
    ext = Path(name).suffix.lower()
    if ext in (".jpg",".jpeg",".png",".gif",".svg",".webp",".bmp",".ico"):
        return "img"
    if ext in (".mp3",".flac",".wav",".ogg",".aac"):
        return "audio"
    if ext in (".mp4",".mkv",".avi",".mov",".webm"):
        return "video"
    if ext in (".zip",".tar",".gz",".7z",".rar",".bz2",".iso"):
        return "arch"
    if ext in (".py",".js",".ts",".html",".css",".c",".cpp",".rs",".go",".java"):
        return "code"
    if executable:
        return "exec"
    return ""

# ──────────────────────────────────────────────────────────────────────────────
#  КНОПКА З HOVER-ЕФЕКТОМ
# ──────────────────────────────────────────────────────────────────────────────

class DarkButton(tk.Label):
    """Красива кнопка на основі Label — підтримує hover і натискання."""
    def __init__(self, parent, text, command=None, width=None,
                 font=("Segoe UI", 11), padx=10, pady=6, tooltip="", **kw):
        super().__init__(parent,
            text=text, font=font,
            bg=C["btn_bg"], fg=C["text"],
            cursor="hand2", padx=padx, pady=pady,
            relief="flat", bd=0,
            **({} if width is None else {"width": width}),
            **kw,
        )
        self._cmd = command
        self.bind("<Enter>",    lambda e: self.config(bg=C["btn_hover"], fg=C["accent"]))
        self.bind("<Leave>",    lambda e: self.config(bg=C["btn_bg"],    fg=C["text"]))
        self.bind("<Button-1>", self._press)
        self.bind("<ButtonRelease-1>", self._release)
        if tooltip:
            self._tip = tooltip
            self.bind("<Enter>", self._show_tip, add="+")
            self.bind("<Leave>", self._hide_tip, add="+")

    def _press(self, e):
        self.config(bg=C["btn_press"])

    def _release(self, e):
        self.config(bg=C["btn_hover"])
        if self._cmd:
            self._cmd()

    def _show_tip(self, e):
        x, y = self.winfo_rootx() + 10, self.winfo_rooty() + self.winfo_height() + 4
        self._tip_win = tk.Toplevel(self)
        self._tip_win.wm_overrideredirect(True)
        self._tip_win.wm_geometry(f"+{x}+{y}")
        tk.Label(self._tip_win, text=self._tip,
                 bg=C["bg3"], fg=C["text"], font=("Segoe UI", 9),
                 padx=6, pady=3, relief="flat").pack()

    def _hide_tip(self, e):
        if hasattr(self, "_tip_win"):
            self._tip_win.destroy()

# ──────────────────────────────────────────────────────────────────────────────
#  ГОЛОВНЕ ВІКНО
# ──────────────────────────────────────────────────────────────────────────────

class FileManager(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("  Файловий менеджер")
        self.geometry("1200x720")
        self.minsize(900, 520)
        self.configure(bg=C["bg"])

        # ── Іконка вікна (генеруємо програмно) ──
        try:
            icon = tk.PhotoImage(width=32, height=32)
            icon.put(C["accent"], to=(0, 0, 31, 31))
            self.iconphoto(True, icon)
        except Exception:
            pass

        # стан
        self.current_path = tk.StringVar(value=str(Path.home()))
        self.history: list[str] = [str(Path.home())]
        self.hist_idx: int = 0
        self.clipboard: dict | None = None
        self.sort_col: str = "name"
        self.sort_rev: bool = False
        self.show_hidden = tk.BooleanVar(value=False)
        self.search_var  = tk.StringVar()

        apply_theme(self)
        self._build_ui()
        self._bind_keys()
        self.refresh()

    # ── ПОБУДОВА UI ─────────────────────────────────────────────────────────

    def _build_ui(self):
        self._build_titlebar()
        self._build_toolbar()
        self._build_body()
        self._build_statusbar()

    # ── Декоративний заголовок ───────────────────────────────────────────────

    def _build_titlebar(self):
        bar = tk.Frame(self, bg=C["bg2"], height=4)
        bar.pack(fill=tk.X)
        # кольорова смуга-акцент зверху
        stripe = tk.Frame(self, bg=C["accent"], height=3)
        stripe.pack(fill=tk.X)

    # ── Тулбар ──────────────────────────────────────────────────────────────

    def _build_toolbar(self):
        tb = tk.Frame(self, bg=C["toolbar"], pady=4)
        tb.pack(fill=tk.X)

        nav_frame = tk.Frame(tb, bg=C["toolbar"])
        nav_frame.pack(side=tk.LEFT, padx=(8, 4))

        btns = [
            ("◀", self.go_back,    "Назад  (Alt+←)"),
            ("▶", self.go_forward, "Вперед (Alt+→)"),
            ("↑", self.go_up,      "Вгору  (Backspace)"),
            ("⌂", self.go_home,    "Домівка"),
            ("⟳", self.refresh,    "Оновити (F5)"),
        ]
        for txt, cmd, tip in btns:
            DarkButton(nav_frame, txt, command=cmd, tooltip=tip,
                       font=("Segoe UI", 12), padx=9, pady=3).pack(side=tk.LEFT, padx=1)

        # separator
        tk.Frame(tb, bg=C["bg4"], width=1).pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)

        # actions
        act_frame = tk.Frame(tb, bg=C["toolbar"])
        act_frame.pack(side=tk.LEFT)
        actions = [
            ("📁+", self.new_folder, "Нова папка (Ctrl+D)"),
            ("📄+", self.new_file,   "Новий файл (Ctrl+N)"),
            ("✂",  self.cut_items,  "Вирізати (Ctrl+X)"),
            ("⎘",  self.copy_items, "Копіювати (Ctrl+C)"),
            ("⎗",  self.paste_items,"Вставити (Ctrl+V)"),
            ("🗑",  self.delete_items,"Видалити (Del)"),
        ]
        for txt, cmd, tip in actions:
            DarkButton(act_frame, txt, command=cmd, tooltip=tip,
                       font=("Segoe UI", 11), padx=8, pady=3).pack(side=tk.LEFT, padx=1)

        tk.Frame(tb, bg=C["bg4"], width=1).pack(side=tk.LEFT, fill=tk.Y, padx=6, pady=4)

        # рядок шляху
        path_frame = tk.Frame(tb, bg=C["entry_bg"],
                              highlightthickness=1, highlightbackground=C["entry_bd"])
        path_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8), pady=2)

        tk.Label(path_frame, text=" 📂 ", bg=C["entry_bg"],
                 fg=C["accent2"], font=("Segoe UI", 11)).pack(side=tk.LEFT)

        self.path_entry = tk.Entry(path_frame,
            textvariable=self.current_path,
            font=("Consolas", 10), bg=C["entry_bg"], fg=C["text"],
            insertbackground=C["accent"], relief="flat", bd=0,
        )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6), ipady=4)
        self.path_entry.bind("<Return>", lambda e: self.navigate(self.current_path.get()))

        # пошук
        search_frame = tk.Frame(tb, bg=C["entry_bg"],
                                highlightthickness=1, highlightbackground=C["entry_bd"])
        search_frame.pack(side=tk.LEFT, padx=(0, 10), pady=2)

        tk.Label(search_frame, text=" 🔍 ", bg=C["entry_bg"],
                 fg=C["text2"], font=("Segoe UI", 10)).pack(side=tk.LEFT)

        self.search_entry = tk.Entry(search_frame,
            textvariable=self.search_var,
            font=("Segoe UI", 10), bg=C["entry_bg"], fg=C["text"],
            insertbackground=C["accent"], relief="flat", bd=0, width=18,
        )
        self.search_entry.pack(side=tk.LEFT, padx=(0, 6), ipady=4)
        self.search_var.trace_add("write", lambda *_: self.refresh())

        # placeholder
        self.search_entry.insert(0, "Пошук…")
        self.search_entry.config(fg=C["text3"])
        self.search_entry.bind("<FocusIn>",  self._search_focus_in)
        self.search_entry.bind("<FocusOut>", self._search_focus_out)

    def _search_focus_in(self, e):
        if self.search_entry.get() == "Пошук…":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg=C["text"])

    def _search_focus_out(self, e):
        if not self.search_entry.get():
            self.search_entry.insert(0, "Пошук…")
            self.search_entry.config(fg=C["text3"])

    # ── Основна область ─────────────────────────────────────────────────────

    def _build_body(self):
        paned = tk.PanedWindow(self, orient=tk.HORIZONTAL,
                               sashwidth=4, sashrelief="flat",
                               bg=C["bg4"], bd=0)
        paned.pack(fill=tk.BOTH, expand=True)

        # ── Сайдбар ─────────────────────────────────────────────────────────
        sidebar = tk.Frame(paned, bg=C["bg2"], width=230)
        paned.add(sidebar, minsize=160)

        # Заголовок сайдбару
        tk.Frame(sidebar, bg=C["accent"], height=2).pack(fill=tk.X)
        tk.Label(sidebar, text="  НАВІГАЦІЯ",
                 bg=C["bg2"], fg=C["text3"],
                 font=("Segoe UI", 8, "bold"), anchor=tk.W,
                 padx=10, pady=6).pack(fill=tk.X)

        self.nav_tree = ttk.Treeview(sidebar, style="Nav.Treeview",
                                     show="tree", selectmode="browse")
        sb_nav = ttk.Scrollbar(sidebar, style="Dark.Vertical.TScrollbar",
                               orient=tk.VERTICAL, command=self.nav_tree.yview)
        self.nav_tree.configure(yscrollcommand=sb_nav.set)
        sb_nav.pack(side=tk.RIGHT, fill=tk.Y)
        self.nav_tree.pack(fill=tk.BOTH, expand=True)

        self.nav_tree.bind("<<TreeviewSelect>>", self._on_nav_select)
        self.nav_tree.bind("<<TreeviewOpen>>",   self._on_nav_open)
        self._populate_nav()

        # ── Права панель ────────────────────────────────────────────────────
        right = tk.Frame(paned, bg=C["bg"])
        paned.add(right, minsize=500)

        # заголовок колонок через Frame (замість стандартного heading)
        self.col_header = tk.Frame(right, bg=C["bg2"])
        self.col_header.pack(fill=tk.X)
        self._build_col_headers()

        # Treeview файлів
        list_frame = tk.Frame(right, bg=C["bg"])
        list_frame.pack(fill=tk.BOTH, expand=True)

        cols = ("name", "size", "modified", "type", "permissions")
        self.file_list = ttk.Treeview(list_frame, style="Files.Treeview",
                                      columns=cols, show="headings",
                                      selectmode="extended")
        col_cfg = {
            "name":        ("Назва",  320, tk.W),
            "size":        ("Розмір", 90,  tk.E),
            "modified":    ("Змінено",150, tk.W),
            "type":        ("Тип",    110, tk.W),
            "permissions": ("Права",  90,  tk.W),
        }
        for col, (lbl, w, anc) in col_cfg.items():
            self.file_list.heading(col, text=lbl, command=lambda c=col: self._sort_by(c))
            self.file_list.column(col, width=w, anchor=anc, minwidth=50)

        sb_x = ttk.Scrollbar(list_frame, style="Dark.Horizontal.TScrollbar",
                              orient=tk.HORIZONTAL, command=self.file_list.xview)
        sb_y = ttk.Scrollbar(list_frame, style="Dark.Vertical.TScrollbar",
                              orient=tk.VERTICAL, command=self.file_list.yview)
        self.file_list.configure(xscrollcommand=sb_x.set, yscrollcommand=sb_y.set)
        sb_y.pack(side=tk.RIGHT, fill=tk.Y)
        sb_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.file_list.pack(fill=tk.BOTH, expand=True)

        # теги
        for tag, color in TAG_COLORS.items():
            self.file_list.tag_configure(tag, foreground=color)

        # чергування рядків
        self.file_list.tag_configure("odd",  background=C["bg"])
        self.file_list.tag_configure("even", background="#242436")

        self.file_list.bind("<Double-1>",         self._on_dbl_click)
        self.file_list.bind("<Return>",           self._on_dbl_click)
        self.file_list.bind("<Button-3>",         self._on_right_click)
        self.file_list.bind("<<TreeviewSelect>>", self._update_status)

        self._build_ctx_menu()

    def _build_col_headers(self):
        """Власні заголовки колонок."""
        headers = [
            ("Назва",   320, "name"),
            ("Розмір",   90, "size"),
            ("Змінено", 150, "modified"),
            ("Тип",     110, "type"),
            ("Права",    90, "permissions"),
        ]
        for lbl, w, col in headers:
            btn = tk.Label(self.col_header, text=f"  {lbl}",
                           bg=C["bg2"], fg=C["text2"],
                           font=("Segoe UI", 9, "bold"),
                           anchor=tk.W, width=w//8, pady=6, cursor="hand2")
            btn.pack(side=tk.LEFT)
            btn.bind("<Button-1>", lambda e, c=col: self._sort_by(c))
            btn.bind("<Enter>", lambda e, b=btn: b.config(fg=C["accent"]))
            btn.bind("<Leave>", lambda e, b=btn: b.config(fg=C["text2"]))

        tk.Frame(self.col_header, bg=C["accent2"], height=1).pack(fill=tk.X, side=tk.BOTTOM)

    def _build_ctx_menu(self):
        self.ctx = tk.Menu(self, tearoff=0,
                           bg=C["bg3"], fg=C["text"],
                           activebackground=C["accent"],
                           activeforeground=C["bg"],
                           font=("Segoe UI", 10),
                           bd=0, relief="flat")
        items = [
            ("  📂  Відкрити",              self._open_selected),
            None,
            ("  ✂    Вирізати    Ctrl+X",   self.cut_items),
            ("  ⎘    Копіювати  Ctrl+C",    self.copy_items),
            ("  ⎗    Вставити   Ctrl+V",    self.paste_items),
            None,
            ("  ✏️   Перейменувати  F2",     self.rename_item),
            ("  🗑    Видалити      Del",    self.delete_items),
            None,
            ("  📁+  Нова папка",           self.new_folder),
            ("  📄+  Новий файл",           self.new_file),
            None,
            ("  ℹ️   Властивості  Alt+Enter", self.show_properties),
        ]
        for item in items:
            if item is None:
                self.ctx.add_separator()
            else:
                self.ctx.add_command(label=item[0], command=item[1])

    # ── Статусбар ────────────────────────────────────────────────────────────

    def _build_statusbar(self):
        sb = tk.Frame(self, bg=C["statusbar"], pady=4)
        sb.pack(fill=tk.X, side=tk.BOTTOM)

        # кольорова смуга знизу
        tk.Frame(self, bg=C["accent2"], height=2).pack(fill=tk.X, side=tk.BOTTOM)

        self.status_left  = tk.Label(sb, text="", bg=C["statusbar"],
                                     fg=C["text2"], font=("Segoe UI", 9), anchor=tk.W)
        self.status_mid   = tk.Label(sb, text="", bg=C["statusbar"],
                                     fg=C["accent"], font=("Segoe UI", 9))
        self.status_right = tk.Label(sb, text="", bg=C["statusbar"],
                                     fg=C["text3"], font=("Segoe UI", 9), anchor=tk.E)

        self.status_left .pack(side=tk.LEFT,  padx=12)
        self.status_mid  .pack(side=tk.LEFT)
        self.status_right.pack(side=tk.RIGHT, padx=12)

    def _bind_keys(self):
        self.bind("<Control-c>",    lambda e: self.copy_items())
        self.bind("<Control-x>",    lambda e: self.cut_items())
        self.bind("<Control-v>",    lambda e: self.paste_items())
        self.bind("<Control-a>",    lambda e: self.select_all())
        self.bind("<Control-d>",    lambda e: self.new_folder())
        self.bind("<Control-n>",    lambda e: self.new_file())
        self.bind("<Control-f>",    lambda e: self.focus_search())
        self.bind("<Delete>",       lambda e: self.delete_items())
        self.bind("<F2>",           lambda e: self.rename_item())
        self.bind("<F5>",           lambda e: self.refresh())
        self.bind("<Alt-Return>",   lambda e: self.show_properties())
        self.bind("<BackSpace>",    lambda e: self.go_up())
        self.bind("<Alt-Left>",     lambda e: self.go_back())
        self.bind("<Alt-Right>",    lambda e: self.go_forward())

    # ── Дерево навігації ─────────────────────────────────────────────────────

    def _populate_nav(self):
        self.nav_tree.delete(*self.nav_tree.get_children())

        quick = [
            ("  🏠  Домівка",       str(Path.home())),
            ("  🖥  Робочий стіл",  str(Path.home() / "Desktop")),
            ("  📁  Документи",     str(Path.home() / "Documents")),
            ("  ⬇  Завантаження",  str(Path.home() / "Downloads")),
            ("  🖼  Зображення",    str(Path.home() / "Pictures")),
            ("  🎵  Музика",        str(Path.home() / "Music")),
            ("  🎬  Відео",         str(Path.home() / "Videos")),
        ]
        for lbl, path in quick:
            if os.path.exists(path):
                self.nav_tree.insert("", tk.END, iid=path, text=lbl, values=[path])

        # роздільник
        self.nav_tree.insert("", tk.END, iid="__div1__",
                             text="  ─────────────────", tags=("sep",))

        if platform.system() == "Windows":
            import string
            for d in string.ascii_uppercase:
                dp = f"{d}:\\"
                if os.path.exists(dp):
                    n = self.nav_tree.insert("", tk.END, iid=dp,
                                             text=f"  💾  {dp}", values=[dp])
                    self.nav_tree.insert(n, tk.END, text="")
        else:
            n = self.nav_tree.insert("", tk.END, iid="/",
                                     text="  🖥  / (корінь)", values=["/"])
            self.nav_tree.insert(n, tk.END, text="")

        self.nav_tree.tag_configure("sep", foreground=C["text3"])

    def _on_nav_open(self, event):
        node = self.nav_tree.focus()
        vals = self.nav_tree.item(node, "values")
        if not vals:
            return
        path = vals[0]
        children = self.nav_tree.get_children(node)
        if len(children) == 1 and self.nav_tree.item(children[0], "text") == "":
            self.nav_tree.delete(children[0])
            try:
                for e in sorted(os.scandir(path), key=lambda x: x.name.lower()):
                    if e.is_dir():
                        ch = self.nav_tree.insert(node, tk.END, iid=e.path,
                                                  text=f"  📁  {e.name}", values=[e.path])
                        self.nav_tree.insert(ch, tk.END, text="")
            except PermissionError:
                pass

    def _on_nav_select(self, event):
        node = self.nav_tree.focus()
        vals = self.nav_tree.item(node, "values")
        if vals and not vals[0].startswith("__"):
            self.navigate(vals[0])

    # ── Навігація ────────────────────────────────────────────────────────────

    def navigate(self, path: str, push: bool = True):
        path = os.path.normpath(path)
        if not os.path.isdir(path):
            messagebox.showerror("Помилка", f"Папку не знайдено:\n{path}")
            return
        if push:
            self.history = self.history[:self.hist_idx + 1]
            self.history.append(path)
            self.hist_idx = len(self.history) - 1
        self.current_path.set(path)
        self.refresh()

    def go_back(self):
        if self.hist_idx > 0:
            self.hist_idx -= 1
            self.navigate(self.history[self.hist_idx], push=False)

    def go_forward(self):
        if self.hist_idx < len(self.history) - 1:
            self.hist_idx += 1
            self.navigate(self.history[self.hist_idx], push=False)

    def go_up(self):
        self.navigate(str(Path(self.current_path.get()).parent))

    def go_home(self):
        self.navigate(str(Path.home()))

    # ── Відображення ─────────────────────────────────────────────────────────

    def refresh(self):
        path    = self.current_path.get()
        query   = self.search_var.get().strip().lower()
        if query == "пошук…":
            query = ""
        hidden  = self.show_hidden.get()

        self.file_list.delete(*self.file_list.get_children())

        try:
            entries = list(os.scandir(path))
        except PermissionError:
            self._set_status("❌ Немає доступу", "", "")
            return
        except FileNotFoundError:
            self._set_status("❌ Папку не знайдено", "", "")
            return

        if not hidden:
            entries = [e for e in entries if not e.name.startswith(".")]
        if query:
            entries = [e for e in entries if query in e.name.lower()]

        # сортування
        rev = self.sort_rev
        if self.sort_col == "name":
            entries.sort(key=lambda e: (not e.is_dir(), e.name.lower()), reverse=rev)
        elif self.sort_col == "size":
            entries.sort(key=lambda e: (not e.is_dir(),
                e.stat().st_size if e.is_file() else 0), reverse=rev)
        elif self.sort_col == "modified":
            entries.sort(key=lambda e: e.stat().st_mtime, reverse=rev)
        elif self.sort_col == "type":
            entries.sort(key=lambda e: Path(e.name).suffix.lower(), reverse=rev)

        total_sz = 0
        n_dirs = n_files = 0

        for idx, e in enumerate(entries):
            try:
                st = e.stat(follow_symlinks=False)
            except OSError:
                continue

            is_dir  = e.is_dir(follow_symlinks=True)
            is_link = e.is_symlink()
            is_exec = os.access(e.path, os.X_OK) and not is_dir

            if is_dir:
                n_dirs += 1
            else:
                n_files += 1
                total_sz += st.st_size

            size   = ""    if is_dir else fmt_size(st.st_size)
            mod    = fmt_time(st.st_mtime)
            ftype  = "Папка" if is_dir else (Path(e.name).suffix.upper().lstrip(".") or "Файл")
            icon   = get_icon(e.name, is_dir)
            perms  = stat.filemode(st.st_mode)
            tag    = get_tag(e.name, is_dir, is_link, is_exec)

            row_tag = "even" if idx % 2 == 0 else "odd"
            tags = (tag, row_tag) if tag else (row_tag,)

            self.file_list.insert("", tk.END, iid=e.path,
                values=(f"  {icon}  {e.name}", size, f"  {mod}", ftype, perms),
                tags=tags,
            )

        # статус
        parts = []
        if n_dirs:
            parts.append(f"📁 {n_dirs} папок")
        if n_files:
            parts.append(f"📄 {n_files} файлів")
        if total_sz:
            parts.append(f"({fmt_size(total_sz)})")

        sel_txt = ""
        sel = self.file_list.selection()
        if sel:
            sel_txt = f"  ✔ Вибрано: {len(sel)}"

        self._set_status("  " + "   ".join(parts), sel_txt, "")
        self._update_disk(path)

    def _set_status(self, left: str, mid: str, right: str):
        self.status_left .config(text=left)
        self.status_mid  .config(text=mid)
        self.status_right.config(text=right)

    def _update_disk(self, path: str):
        try:
            u = shutil.disk_usage(path)
            pct  = 100 * u.used // u.total
            bar  = "█" * (pct // 10) + "░" * (10 - pct // 10)
            self.status_right.config(
                text=f"{bar}  {fmt_size(u.free)} вільно / {fmt_size(u.total)}   "
            )
        except Exception:
            pass

    def _update_status(self, event=None):
        sel = self.file_list.selection()
        if sel:
            self.status_mid.config(text=f"  ✔ Вибрано: {len(sel)}")

    def _sort_by(self, col: str):
        if self.sort_col == col:
            self.sort_rev = not self.sort_rev
        else:
            self.sort_col = col
            self.sort_rev = False
        self.refresh()

    # ── Дії ─────────────────────────────────────────────────────────────────

    def _selected_paths(self) -> list[str]:
        return list(self.file_list.selection())

    def _open_selected(self):
        for p in self._selected_paths():
            if os.path.isdir(p):
                self.navigate(p)
            else:
                open_native(p)

    def _on_dbl_click(self, e=None):
        self._open_selected()

    def _on_right_click(self, event):
        row = self.file_list.identify_row(event.y)
        if row and row not in self.file_list.selection():
            self.file_list.selection_set(row)
        self.ctx.tk_popup(event.x_root, event.y_root)

    def select_all(self):
        self.file_list.selection_set(*self.file_list.get_children())

    def new_folder(self):
        name = self._ask_string("Нова папка", "Введіть назву папки:")
        if name:
            try:
                os.makedirs(os.path.join(self.current_path.get(), name), exist_ok=True)
                self.refresh()
            except Exception as e:
                messagebox.showerror("Помилка", str(e))

    def new_file(self):
        name = self._ask_string("Новий файл", "Введіть назву файлу:")
        if name:
            try:
                Path(os.path.join(self.current_path.get(), name)).touch()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Помилка", str(e))

    def rename_item(self):
        sel = self._selected_paths()
        if len(sel) != 1:
            messagebox.showinfo("Перейменування", "Виберіть рівно один елемент.")
            return
        old = sel[0]
        new_name = self._ask_string("Перейменувати", "Нова назва:",
                                    init=os.path.basename(old))
        if new_name:
            try:
                os.rename(old, os.path.join(os.path.dirname(old), new_name))
                self.refresh()
            except Exception as e:
                messagebox.showerror("Помилка", str(e))

    def delete_items(self):
        sel = self._selected_paths()
        if not sel:
            return
        names = "\n".join(f"  • {os.path.basename(p)}" for p in sel[:8])
        if len(sel) > 8:
            names += f"\n  … та ще {len(sel)-8}"
        if not messagebox.askyesno("Підтвердити видалення",
                                   f"Видалити {len(sel)} елемент(ів)?\n\n{names}",
                                   icon="warning"):
            return
        errors = []
        for p in sel:
            try:
                shutil.rmtree(p) if (os.path.isdir(p) and not os.path.islink(p)) else os.remove(p)
            except Exception as e:
                errors.append(f"{os.path.basename(p)}: {e}")
        if errors:
            messagebox.showerror("Помилки", "\n".join(errors))
        self.refresh()

    def copy_items(self):
        sel = self._selected_paths()
        if sel:
            self.clipboard = {"op": "copy", "paths": sel}
            self._set_status(f"  ⎘  Скопійовано: {len(sel)} елемент(ів)", "", "")

    def cut_items(self):
        sel = self._selected_paths()
        if sel:
            self.clipboard = {"op": "cut", "paths": sel}
            self._set_status(f"  ✂  Вирізано: {len(sel)} елемент(ів)", "", "")

    def paste_items(self):
        if not self.clipboard:
            return
        dest_dir = self.current_path.get()
        errors = []
        for src in self.clipboard["paths"]:
            name = os.path.basename(src)
            dest = os.path.join(dest_dir, name)
            c = 1
            while os.path.exists(dest):
                s, e = Path(name).stem, Path(name).suffix
                dest = os.path.join(dest_dir, f"{s}_копія{c}{e}")
                c += 1
            try:
                shutil.copytree(src, dest) if os.path.isdir(src) else shutil.copy2(src, dest)
                if self.clipboard["op"] == "cut":
                    shutil.rmtree(src) if os.path.isdir(src) else os.remove(src)
            except Exception as ex:
                errors.append(f"{name}: {ex}")
        if self.clipboard["op"] == "cut":
            self.clipboard = None
        if errors:
            messagebox.showerror("Помилки вставки", "\n".join(errors))
        self.refresh()

    def focus_search(self):
        self.search_entry.focus_set()
        if self.search_entry.get() == "Пошук…":
            self._search_focus_in(None)

    def open_in_explorer(self):
        sel = self._selected_paths()
        path = (sel[0] if sel and os.path.isdir(sel[0])
                else os.path.dirname(sel[0]) if sel
                else self.current_path.get())
        open_native(path)

    # ── Властивості ─────────────────────────────────────────────────────────

    def show_properties(self):
        sel = self._selected_paths()
        path = sel[0] if len(sel) == 1 else self.current_path.get()
        PropertiesDialog(self, path)

    # ── Утиліта: красивий діалог введення ────────────────────────────────────

    def _ask_string(self, title: str, prompt: str, init: str = "") -> str | None:
        return simpledialog.askstring(title, prompt, initialvalue=init, parent=self)

    @staticmethod
    def _dir_size(path: str) -> int:
        total = 0
        try:
            for e in os.scandir(path):
                total += e.stat().st_size if e.is_file() else FileManager._dir_size(e.path)
        except PermissionError:
            pass
        return total


# ──────────────────────────────────────────────────────────────────────────────
#  ВІКНО ВЛАСТИВОСТЕЙ
# ──────────────────────────────────────────────────────────────────────────────

class PropertiesDialog:
    def __init__(self, master, path: str):
        self.win = tk.Toplevel(master)
        self.win.title("Властивості")
        self.win.geometry("440x400")
        self.win.resizable(False, False)
        self.win.configure(bg=C["bg"])
        self.win.grab_set()

        # Заголовок
        header = tk.Frame(self.win, bg=C["bg2"], pady=14)
        header.pack(fill=tk.X)
        tk.Frame(header, bg=C["accent"], height=3).pack(fill=tk.X, side=tk.TOP)

        icon = get_icon(os.path.basename(path), os.path.isdir(path))
        tk.Label(header, text=icon, font=("Segoe UI", 28),
                 bg=C["bg2"], fg=C["accent"]).pack()
        tk.Label(header, text=os.path.basename(path),
                 font=("Segoe UI", 12, "bold"),
                 bg=C["bg2"], fg=C["text"]).pack()
        tk.Label(header, text=os.path.dirname(path),
                 font=("Segoe UI", 8),
                 bg=C["bg2"], fg=C["text3"]).pack()

        # Тіло
        body = tk.Frame(self.win, bg=C["bg"], padx=20, pady=12)
        body.pack(fill=tk.BOTH, expand=True)

        try:
            st = os.stat(path)
        except Exception as e:
            tk.Label(body, text=str(e), bg=C["bg"], fg=C["accent4"]).pack()
            return

        is_dir = os.path.isdir(path)
        rows = [
            ("Тип",      "Папка" if is_dir else (Path(path).suffix.upper().lstrip(".") or "Файл")),
            ("Розмір",   "обчислення…" if is_dir else fmt_size(st.st_size)),
            ("Змінено",  fmt_time(st.st_mtime)),
            ("Створено", fmt_time(st.st_ctime)),
            ("Доступ",   fmt_time(st.st_atime)),
            ("Права",    stat.filemode(st.st_mode)),
            ("Inode",    str(st.st_ino)),
        ]

        self.size_lbl = None
        for lbl, val in rows:
            row = tk.Frame(body, bg=C["bg"])
            row.pack(fill=tk.X, pady=3)
            tk.Label(row, text=lbl, width=10, anchor=tk.E,
                     bg=C["bg"], fg=C["text3"],
                     font=("Segoe UI", 9)).pack(side=tk.LEFT)
            tk.Frame(row, bg=C["bg4"], width=1).pack(side=tk.LEFT, fill=tk.Y, padx=8)
            l = tk.Label(row, text=val, anchor=tk.W,
                         bg=C["bg"], fg=C["text"],
                         font=("Consolas", 9))
            l.pack(side=tk.LEFT)
            if lbl == "Розмір" and is_dir:
                self.size_lbl = l
                threading.Thread(target=self._calc_size,
                                 args=(path,), daemon=True).start()

        # кнопка
        tk.Frame(self.win, bg=C["bg4"], height=1).pack(fill=tk.X)
        DarkButton(self.win, "  Закрити  ", command=self.win.destroy,
                   font=("Segoe UI", 10), padx=20, pady=8).pack(pady=10)

    def _calc_size(self, path: str):
        size = FileManager._dir_size(path)
        if self.size_lbl:
            self.size_lbl.config(text=fmt_size(size))


# ──────────────────────────────────────────────────────────────────────────────
#  ЗАПУСК
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = FileManager()
    app.mainloop()
