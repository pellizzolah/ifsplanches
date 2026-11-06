import tkinter as tk
from tkinter import ttk
import sqlite3
import os
import shutil
from datetime import datetime

DB = "ifsp_lanches.db"
BACKUP_DIR = "backups"
MAX_BACKUPS = 10

# ---------- NOVA PALETA ----------
BG_BASE      = "#101820"
BG_GRAD_TOP  = (16, 24, 32)
BG_GRAD_BOT  = (10, 16, 26)
CARD         = "#1a2430"
CARD_LIGHT   = "#243240"
CARD_HOVER   = "#2e3e50"
CARD_BORDER  = "#354a5f"

PRIMARY      = "#ff6b5b"
PRIMARY_H    = "#ff8b7e"
ACCENT       = "#4ecdc4"
ACCENT_H     = "#6ee0d8"
GOLD         = "#ffd166"
GOLD_H       = "#ffe08a"
SKY          = "#7ec8e3"
SKY_H        = "#a4dcef"
VIOLET       = "#b392f0"
VIOLET_H     = "#c9adf7"
GREEN        = "#95e06c"
GREEN_H      = "#b0ec8f"
DANGER       = "#f25f5c"
DANGER_H     = "#ff7d7a"

TEXT         = "#f4f7fa"
TEXT_MUTED   = "#8fa3b8"
TEXT_DIM     = "#5d7085"

F_HERO   = ("Segoe UI", 26, "bold")
F_TITLE  = ("Segoe UI", 22, "bold")
F_H2     = ("Segoe UI", 14, "bold")
F_H3     = ("Segoe UI", 12, "bold")
F_BODY   = ("Segoe UI", 10)
F_SMALL  = ("Segoe UI", 9)
F_TINY   = ("Segoe UI", 8)
F_BTN    = ("Segoe UI", 10, "bold")
F_EMOJI_XL = ("Segoe UI Emoji", 48)
F_EMOJI_L  = ("Segoe UI Emoji", 24)
F_EMOJI_S  = ("Segoe UI Emoji", 13)


def conectar():
    conn = sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.commit()
    return conn


def init_db():
    conn = conectar()
    try:
        conn.execute("""CREATE TABLE IF NOT EXISTS lanches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            estoque INTEGER NOT NULL DEFAULT 0,
            consumo_diario REAL NOT NULL DEFAULT 0
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS demandas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lanche_id INTEGER NOT NULL,
            quantidade INTEGER NOT NULL,
            data TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pendente',
            FOREIGN KEY (lanche_id) REFERENCES lanches(id) ON DELETE CASCADE
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS consumo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            lanche_id INTEGER NOT NULL,
            data TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            FOREIGN KEY (lanche_id) REFERENCES lanches(id) ON DELETE CASCADE
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_dem_lanche ON demandas(lanche_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_cons_lanche ON consumo(lanche_id, data)")
        conn.commit()
    finally:
        conn.close()


def fazer_backup():
    try:
        if not os.path.exists(DB):
            return
        os.makedirs(BACKUP_DIR, exist_ok=True)
        nome = f"backup_{datetime.now():%Y%m%d_%H%M%S}.db"
        shutil.copy(DB, os.path.join(BACKUP_DIR, nome))
        backups = sorted(
            [f for f in os.listdir(BACKUP_DIR) if f.startswith("backup_")],
            reverse=True)
        for antigo in backups[MAX_BACKUPS:]:
            try:
                os.remove(os.path.join(BACKUP_DIR, antigo))
            except OSError:
                pass
    except Exception:
        pass


def consumo_efetivo(conn, lanche_id, consumo_manual):
    try:
        row = conn.execute(
            "SELECT AVG(quantidade) FROM consumo "
            "WHERE lanche_id=? AND data >= date('now','-7 days')",
            (lanche_id,)).fetchone()
        if row and row[0] is not None:
            return float(row[0]), True
    except sqlite3.Error:
        pass
    return float(consumo_manual), False


def center(window, w, h):
    window.update_idletasks()
    x = (window.winfo_screenwidth() - w) // 2
    y = (window.winfo_screenheight() - h) // 2 - 20
    window.geometry(f"{w}x{h}+{x}+{y}")


def fade_in(window, duration=220, steps=18):
    try:
        window.attributes("-alpha", 0.0)
    except tk.TclError:
        return
    delay = max(1, duration // steps)

    def step(i=0):
        if i > steps or not window.winfo_exists():
            return
        try:
            window.attributes("-alpha", min(1.0, i / steps))
            window.after(delay, step, i + 1)
        except tk.TclError:
            pass
    step()


def draw_gradient(canvas, w, h, steps=50):
    for i in range(steps):
        t = i / steps
        r = int(BG_GRAD_TOP[0] + (BG_GRAD_BOT[0] - BG_GRAD_TOP[0]) * t)
        g = int(BG_GRAD_TOP[1] + (BG_GRAD_BOT[1] - BG_GRAD_TOP[1]) * t)
        b = int(BG_GRAD_TOP[2] + (BG_GRAD_BOT[2] - BG_GRAD_TOP[2]) * t)
        canvas.create_rectangle(0, (h / steps) * i, w, (h / steps) * (i + 1),
                                fill=f"#{r:02x}{g:02x}{b:02x}", outline="")


class PillButton(tk.Label):
    def __init__(self, parent, text, command=None, base=ACCENT, hover=ACCENT_H,
                 fg="#101820", font=F_BTN, padx=22, pady=10, **kw):
        super().__init__(parent, text=text, bg=base, fg=fg, font=font,
                         padx=padx, pady=pady, cursor="hand2", **kw)
        self._base = base
        self._hover = hover
        self._cmd = command
        self.bind("<Enter>", lambda e: self.config(bg=self._hover))
        self.bind("<Leave>", lambda e: self.config(bg=self._base))
        self.bind("<Button-1>", self._click)

    def _click(self, _):
        if self._cmd:
            self._cmd()


class NeonEntry(tk.Frame):
    def __init__(self, parent, label, show=None, width=30, bg=CARD):
        super().__init__(parent, bg=bg)
        tk.Label(self, text=label, bg=bg, fg=TEXT_MUTED,
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(0, 6))
        self._wrap = tk.Frame(self, bg=CARD_LIGHT,
                              highlightbackground=CARD_BORDER, highlightthickness=1)
        self._wrap.pack(fill="x")
        self.entry = tk.Entry(self._wrap, bg=CARD_LIGHT, fg=TEXT,
                              insertbackground=ACCENT, relief="flat", bd=0,
                              font=("Segoe UI", 11), show=show, width=width)
        self.entry.pack(fill="x", padx=14, pady=11)
        self.entry.bind("<FocusIn>",
                        lambda e: self._wrap.config(highlightbackground=ACCENT,
                                                    highlightthickness=2))
        self.entry.bind("<FocusOut>",
                        lambda e: self._wrap.config(highlightbackground=CARD_BORDER,
                                                    highlightthickness=1))

    def get(self):
        return self.entry.get()

    def focus(self):
        self.entry.focus()


class Confirm(tk.Toplevel):
    def __init__(self, parent, msg, title="Confirmação"):
        super().__init__(parent)
        self.result = False
        self.title(title)
        self.configure(bg=CARD)
        self.resizable(False, False)
        self.transient(parent)

        w, h = 440, 230
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        card = tk.Frame(self, bg=CARD, padx=30, pady=26,
                        highlightbackground=CARD_BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        tk.Label(card, text="⚠️  " + title, bg=CARD, fg=GOLD,
                 font=("Segoe UI", 13, "bold")).pack(anchor="w")
        tk.Label(card, text=msg, bg=CARD, fg=TEXT, font=F_BODY,
                 wraplength=360, justify="left").pack(anchor="w", pady=(12, 0))

        btns = tk.Frame(card, bg=CARD)
        btns.pack(fill="x", pady=(22, 0))
        PillButton(btns, "Cancelar", command=self._cancel,
                   base=CARD_LIGHT, hover=CARD_HOVER, fg=TEXT).pack(side="left")
        PillButton(btns, "Confirmar", command=self._ok,
                   base=PRIMARY, hover=PRIMARY_H, fg="white").pack(side="right")

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        self.bind("<Escape>", lambda e: self._cancel())
        self.bind("<Return>", lambda e: self._ok())
        self.after(50, self._grab)

    def _grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass

    def _ok(self):
        self.result = True
        self.destroy()

    def _cancel(self):
        self.result = False
        self.destroy()


class Toast:
    def __init__(self, parent, msg, color=GREEN):
        try:
            if not parent.winfo_exists():
                return
            parent.update_idletasks()
        except tk.TclError:
            return

        self.top = tk.Toplevel(parent)
        self.top.overrideredirect(True)
        try:
            self.top.attributes("-topmost", True)
        except tk.TclError:
            pass

        wrap = tk.Frame(self.top, bg=color, padx=22, pady=14)
        wrap.pack()
        tk.Label(wrap, text=msg, bg=color, fg="#101820", font=F_BTN).pack()

        self.top.update_idletasks()
        w, h = self.top.winfo_reqwidth(), self.top.winfo_reqheight()
        px = parent.winfo_x() + parent.winfo_width() - w - 30
        py = parent.winfo_y() + parent.winfo_height() - h - 30
        self.top.geometry(f"{w}x{h}+{max(0, px)}+{max(0, py)}")

        try:
            self.top.attributes("-alpha", 1.0)
        except tk.TclError:
            pass

        self.top.after(2200, self._destroy)

    def _destroy(self):
        try:
            if self.top.winfo_exists():
                self.top.destroy()
        except tk.TclError:
            pass


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("IFSP Lanches")
        self.root.configure(bg=BG_BASE)
        self.root.resizable(False, False)

        W, H = 460, 580
        center(self.root, W, H)

        canvas = tk.Canvas(root, bg=BG_BASE, highlightthickness=0)
        canvas.place(x=0, y=0, relwidth=1, relheight=1)
        draw_gradient(canvas, self.root.winfo_screenwidth(),
                      self.root.winfo_screenheight())

        # Bolhas decorativas
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        canvas.create_oval(-100, -150, 260, 200, fill="#1a2430", outline="")
        canvas.create_oval(sw - 200, sh - 260, sw + 200, sh + 100,
                           fill="#1e2b3a", outline="")

        card = tk.Frame(root, bg=CARD, padx=44, pady=40,
                        highlightbackground=CARD_BORDER, highlightthickness=1)
        card.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(card, text="🍔", bg=CARD, fg=PRIMARY,
                 font=F_EMOJI_XL).pack(pady=(0, 10))

        tk.Label(card, text="IFSP Lanches", bg=CARD, fg=TEXT,
                 font=F_HERO).pack()
        tk.Label(card, text="controle de estoque", bg=CARD, fg=TEXT_MUTED,
                 font=F_BODY).pack(pady=(4, 30))

        self.user = NeonEntry(card, "USUÁRIO")
        self.user.pack(fill="x", pady=(0, 16))
        self.pwd = NeonEntry(card, "SENHA", show="•")
        self.pwd.pack(fill="x", pady=(0, 10))

        self.erro_lbl = tk.Label(card, text="", bg=CARD, fg=DANGER, font=F_SMALL)
        self.erro_lbl.pack(pady=(0, 10))

        PillButton(card, "Entrar", command=self.login,
                   base=PRIMARY, hover=PRIMARY_H, fg="white",
                   padx=20, pady=13,
                   font=("Segoe UI", 11, "bold")).pack(fill="x")

        self.user.entry.bind("<Return>", lambda e: self.pwd.focus())
        self.pwd.entry.bind("<Return>", lambda e: self.login())
        self.root.after(280, self.user.focus)
        fade_in(self.root)

    def login(self):
        if self.user.get().strip() == "admin" and self.pwd.get() == "123":
            self.root.destroy()
            main_root = tk.Tk()
            MainApp(main_root)
            main_root.mainloop()
        else:
            self.erro_lbl.config(text="✗  Usuário ou senha incorretos")


class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IFSP Lanches")
        self.root.configure(bg=BG_BASE)
        center(self.root, 1240, 800)
        self.root.minsize(1080, 720)

        fazer_backup()

        self._active_menu = None
        self._config_styles()
        self._build()
        self.refresh()
        self.root.after(600, self.verificar_alertas)
        self.root.protocol("WM_DELETE_WINDOW", self._fechar_app)
        fade_in(self.root)

    def _fechar_app(self):
        fazer_backup()
        self.root.destroy()

    def _config_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Neon.Treeview",
                        background=CARD, foreground=TEXT,
                        fieldbackground=CARD, rowheight=44,
                        borderwidth=0, font=("Segoe UI", 10))
        style.configure("Neon.Treeview.Heading",
                        background=BG_BASE, foreground=ACCENT,
                        font=("Segoe UI", 9, "bold"),
                        borderwidth=0, relief="flat", padding=16)
        style.map("Neon.Treeview.Heading", background=[("active", CARD_HOVER)])
        style.map("Neon.Treeview",
                  background=[("selected", ACCENT)],
                  foreground=[("selected", "#101820")])

    def _build(self):
        self._build_sidebar()

        right = tk.Frame(self.root, bg=BG_BASE)
        right.pack(side="left", fill="both", expand=True)

        self._build_topbar(right)

        body = tk.Frame(right, bg=BG_BASE)
        body.pack(fill="both", expand=True, padx=32, pady=(20, 24))

        header = tk.Frame(body, bg=BG_BASE)
        header.pack(fill="x", pady=(0, 18))
        self.header_title = tk.Label(header, text="", bg=BG_BASE, fg=TEXT,
                                     font=F_TITLE)
        self.header_title.pack(side="left")
        self.header_sub = tk.Label(header, text="", bg=BG_BASE, fg=TEXT_MUTED,
                                   font=F_SMALL)
        self.header_sub.pack(side="left", padx=14, pady=(10, 0))

        self.card_container = tk.Frame(body, bg=BG_BASE)
        self.card_container.pack(fill="both", expand=True)

        self.view_estoque = tk.Frame(self.card_container, bg=BG_BASE)
        self.view_demandas = tk.Frame(self.card_container, bg=BG_BASE)
        self.view_consumo = tk.Frame(self.card_container, bg=BG_BASE)
        self.view_resumo = tk.Frame(self.card_container, bg=BG_BASE)

        self._build_estoque_view()
        self._build_demandas_view()
        self._build_consumo_view()
        self._build_resumo_view()
        self.show_estoque()

    def _build_sidebar(self):
        sidebar = tk.Frame(self.root, bg=CARD, width=200)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Frame(sidebar, bg=PRIMARY, height=4).pack(fill="x")

        logo = tk.Frame(sidebar, bg=CARD)
        logo.pack(fill="x", pady=(30, 6), padx=22)
        tk.Label(logo, text="🍔", bg=CARD, fg=PRIMARY,
                 font=F_EMOJI_L).pack(side="left")
        info = tk.Frame(logo, bg=CARD)
        info.pack(side="left", padx=10)
        tk.Label(info, text="IFSP", bg=CARD, fg=PRIMARY,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(info, text="Lanches", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 11)).pack(anchor="w")

        tk.Frame(sidebar, bg=CARD_BORDER, height=1).pack(fill="x", padx=20, pady=(24, 20))

        self.menu_buttons = {}
        self._nav(sidebar, "estoque", "📦  Estoque", self.show_estoque)
        self._nav(sidebar, "demandas", "📋  Demandas", self.show_demandas)
        self._nav(sidebar, "consumo", "📊  Consumo", self.show_consumo)
        self._nav(sidebar, "resumo", "📈  Resumo", self.show_resumo)

        tk.Frame(sidebar, bg=CARD).pack(fill="both", expand=True)

        tk.Frame(sidebar, bg=CARD_BORDER, height=1).pack(fill="x", padx=20, pady=(10, 14))

        adm = tk.Frame(sidebar, bg=CARD)
        adm.pack(fill="x", padx=22, pady=(0, 10))
        tk.Label(adm, text="👤", bg=CARD, fg=ACCENT,
                 font=F_EMOJI_S).pack(side="left")
        ai = tk.Frame(adm, bg=CARD)
        ai.pack(side="left", padx=8)
        tk.Label(ai, text="admin", bg=CARD, fg=TEXT,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(ai, text="● online", bg=CARD, fg=GREEN,
                 font=("Segoe UI", 8)).pack(anchor="w")

        PillButton(sidebar, "ℹ  Sobre", command=self.abrir_sobre,
                   base=CARD_LIGHT, hover=CARD_HOVER, fg=TEXT_MUTED,
                   padx=12, pady=9,
                   font=("Segoe UI", 9, "bold")).pack(fill="x", padx=20, pady=(0, 6))

        PillButton(sidebar, "Sair", command=self.logout,
                   base=CARD_LIGHT, hover="#3b1a1a", fg=DANGER,
                   padx=12, pady=10,
                   font=("Segoe UI", 10, "bold")).pack(fill="x", padx=20, pady=(0, 22))

    def _nav(self, parent, key, text, cmd):
        btn = tk.Label(parent, text=text, bg=CARD, fg=TEXT_MUTED, font=F_BTN,
                       cursor="hand2", anchor="w", padx=22, pady=14)
        btn.pack(fill="x", padx=14, pady=3)
        btn._key = key
        btn.bind("<Button-1>", lambda e: (cmd(), self._highlight(key)))
        btn.bind("<Enter>", lambda e: self._hover(key, True))
        btn.bind("<Leave>", lambda e: self._hover(key, False))
        self.menu_buttons[key] = btn

    def _hover(self, key, entering):
        if key == self._active_menu:
            return
        self.menu_buttons[key].config(bg=CARD_HOVER if entering else CARD)

    def _highlight(self, key):
        self._active_menu = key
        for k, b in self.menu_buttons.items():
            if k == key:
                b.config(bg=CARD_LIGHT, fg=PRIMARY)
            else:
                b.config(bg=CARD, fg=TEXT_MUTED)

    def _build_topbar(self, parent):
        bar = tk.Frame(parent, bg=CARD, height=52)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        tk.Label(bar, text="Painel administrativo", bg=CARD, fg=TEXT_MUTED,
                 font=("Segoe UI", 9, "bold")).pack(side="left", padx=24)

        right = tk.Frame(bar, bg=CARD)
        right.pack(side="right", padx=20)
        tk.Label(right, text=datetime.now().strftime("%d/%m/%Y  ·  %H:%M"),
                 bg=CARD, fg=TEXT_DIM, font=F_SMALL).pack(side="left")

        tk.Frame(parent, bg=CARD_BORDER, height=1).pack(fill="x")

    def _actions_bar(self, parent):
        bar = tk.Frame(parent, bg=BG_BASE)
        bar.pack(fill="x", pady=(0, 18))
        return bar

    def _build_estoque_view(self):
        v = self.view_estoque

        # Cartões de resumo
        stats = tk.Frame(v, bg=BG_BASE)
        stats.pack(fill="x", pady=(0, 18))
        self.stat_total = self._stat_card(stats, "TOTAL", "0", ACCENT, "📦")
        self.stat_criticos = self._stat_card(stats, "CRÍTICOS", "0", DANGER, "⚠")
        self.stat_pendentes = self._stat_card(stats, "PENDENTES", "0", GOLD, "📋")
        self.stat_unidades = self._stat_card(stats, "UNIDADES", "0", GREEN, "🍔")

        bar = self._actions_bar(v)
        PillButton(bar, "＋  Novo lanche", command=self.add_lanche,
                   base=PRIMARY, hover=PRIMARY_H, fg="white",
                   padx=22, pady=11).pack(side="left", padx=(0, 8))

        secondary = tk.Frame(bar, bg=CARD, highlightbackground=CARD_BORDER,
                             highlightthickness=1)
        secondary.pack(side="left")
        for i, (txt, cmd, c, h) in enumerate([
            ("✎  Editar", self.edit_lanche, GOLD, GOLD_H),
            ("✕  Excluir", self.del_lanche, DANGER, DANGER_H),
            ("📩  Solicitar", self.solicitar_demanda, VIOLET, VIOLET_H),
        ]):
            b = tk.Label(secondary, text=txt, bg=CARD, fg=c,
                         font=("Segoe UI", 9, "bold"),
                         cursor="hand2", padx=16, pady=11)
            b.pack(side="left")
            b.bind("<Enter>", lambda e, w=b, hh=h: w.config(bg=hh, fg="#101820"))
            b.bind("<Leave>", lambda e, w=b, cc=c: w.config(bg=CARD, fg=cc))
            b.bind("<Button-1>", lambda e, cc=cmd: cc())
            if i < 2:
                tk.Frame(secondary, bg=CARD_BORDER, width=1).pack(side="left", fill="y")

        PillButton(bar, "⟳", command=self.refresh,
                   base=CARD_LIGHT, hover=CARD_HOVER, fg=TEXT_MUTED,
                   padx=14, pady=11).pack(side="right")

        wrap = tk.Frame(v, bg=CARD, highlightbackground=CARD_BORDER,
                        highlightthickness=1)
        wrap.pack(fill="both", expand=True)

        cols = ("id", "nome", "estoque", "consumo", "dias", "status")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings",
                                 style="Neon.Treeview")
        headers = {"id": "ID", "nome": "LANCHE", "estoque": "ESTOQUE",
                   "consumo": "CONSUMO/DIA", "dias": "DURAÇÃO", "status": "STATUS"}
        widths = {"id": 60, "nome": 260, "estoque": 110,
                  "consumo": 140, "dias": 160, "status": 180}
        for c in cols:
            self.tree.heading(c, text=headers[c])
            self.tree.column(c, width=widths[c],
                             anchor="w" if c == "nome" else "center")

        self.tree.tag_configure("critico", background="#3a1e22", foreground="#ffb3b0")
        self.tree.tag_configure("atencao", background="#3a2f18", foreground=GOLD)
        self.tree.tag_configure("ok",      background="#1c3324", foreground=GREEN)

        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree.pack(fill="both", expand=True, padx=1, pady=1)

    def _stat_card(self, parent, label, valor, cor, icone):
        c = tk.Frame(parent, bg=CARD, highlightbackground=CARD_BORDER,
                     highlightthickness=1)
        c.pack(side="left", fill="x", expand=True, padx=(0, 12))

        inner = tk.Frame(c, bg=CARD, padx=18, pady=14)
        inner.pack(fill="both", expand=True)

        tk.Label(inner, text=icone, bg=CARD, fg=cor,
                 font=F_EMOJI_L).pack(side="left")
        txt = tk.Frame(inner, bg=CARD)
        txt.pack(side="left", padx=12)
        tk.Label(txt, text=label, bg=CARD, fg=TEXT_MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w")
        lbl = tk.Label(txt, text=valor, bg=CARD, fg=cor,
                       font=("Segoe UI", 16, "bold"))
        lbl.pack(anchor="w")
        return lbl

    def _build_demandas_view(self):
        v = self.view_demandas
        bar = self._actions_bar(v)
        PillButton(bar, "✓  Marcar atendida", command=self.atender_demanda,
                   base=GREEN, hover=GREEN_H, fg="#101820",
                   padx=22, pady=11).pack(side="left", padx=(0, 8))
        PillButton(bar, "✕  Excluir", command=self.del_demanda,
                   base=DANGER, hover=DANGER_H, fg="white",
                   padx=18, pady=11).pack(side="left", padx=(0, 8))
        PillButton(bar, "⟳", command=self.refresh,
                   base=CARD_LIGHT, hover=CARD_HOVER, fg=TEXT_MUTED,
                   padx=14, pady=11).pack(side="right")

        wrap = tk.Frame(v, bg=CARD, highlightbackground=CARD_BORDER,
                        highlightthickness=1)
        wrap.pack(fill="both", expand=True)

        cols = ("id", "lanche", "quantidade", "data", "status")
        self.tree_dem = ttk.Treeview(wrap, columns=cols, show="headings",
                                     style="Neon.Treeview")
        headers = {"id": "ID", "lanche": "LANCHE", "quantidade": "QUANTIDADE",
                   "data": "DATA", "status": "STATUS"}
        widths = {"id": 60, "lanche": 280, "quantidade": 140, "data": 200, "status": 140}
        for c in cols:
            self.tree_dem.heading(c, text=headers[c])
            self.tree_dem.column(c, width=widths[c],
                                 anchor="w" if c == "lanche" else "center")

        self.tree_dem.tag_configure("atendida", background="#1c3324", foreground=GREEN)
        self.tree_dem.tag_configure("pendente", background="#3a2f18", foreground=GOLD)

        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree_dem.yview)
        self.tree_dem.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree_dem.pack(fill="both", expand=True, padx=1, pady=1)

    def _build_consumo_view(self):
        v = self.view_consumo
        bar = self._actions_bar(v)
        PillButton(bar, "＋  Registrar consumo", command=self.registrar_consumo,
                   base=ACCENT, hover=ACCENT_H, fg="#101820",
                   padx=22, pady=11).pack(side="left", padx=(0, 8))
        PillButton(bar, "✕  Excluir", command=self.del_consumo,
                   base=DANGER, hover=DANGER_H, fg="white",
                   padx=18, pady=11).pack(side="left", padx=(0, 8))
        PillButton(bar, "⟳", command=self.refresh_consumo,
                   base=CARD_LIGHT, hover=CARD_HOVER, fg=TEXT_MUTED,
                   padx=14, pady=11).pack(side="right")

        tk.Label(v, text="A média dos últimos 7 dias substitui o consumo manual no cálculo de duração.",
                 bg=BG_BASE, fg=TEXT_MUTED, font=F_SMALL, anchor="w").pack(fill="x", pady=(0, 12))

        wrap = tk.Frame(v, bg=CARD, highlightbackground=CARD_BORDER,
                        highlightthickness=1)
        wrap.pack(fill="both", expand=True)

        cols = ("id", "lanche", "data", "quantidade")
        self.tree_cons = ttk.Treeview(wrap, columns=cols, show="headings",
                                      style="Neon.Treeview")
        headers = {"id": "ID", "lanche": "LANCHE", "data": "DATA",
                   "quantidade": "QUANTIDADE"}
        widths = {"id": 60, "lanche": 300, "data": 220, "quantidade": 160}
        for c in cols:
            self.tree_cons.heading(c, text=headers[c])
            self.tree_cons.column(c, width=widths[c],
                                  anchor="w" if c == "lanche" else "center")

        self.tree_cons.tag_configure("hoje", background="#1c3324", foreground=GREEN)

        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree_cons.yview)
        self.tree_cons.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.tree_cons.pack(fill="both", expand=True, padx=1, pady=1)

    def _build_resumo_view(self):
        v = self.view_resumo
        bar = self._actions_bar(v)
        PillButton(bar, "⟳  Atualizar", command=self.refresh_resumo,
                   base=CARD_LIGHT, hover=CARD_HOVER, fg=TEXT_MUTED,
                   padx=18, pady=11).pack(side="right")

        wrap = tk.Frame(v, bg=CARD, highlightbackground=CARD_BORDER,
                        highlightthickness=1)
        wrap.pack(fill="both", expand=True)

        self.resumo_canvas = tk.Canvas(wrap, bg=CARD, highlightthickness=0)
        self.resumo_canvas.pack(fill="both", expand=True, padx=18, pady=18)

    def _hide_all(self):
        for view in (self.view_estoque, self.view_demandas,
                     self.view_consumo, self.view_resumo):
            view.pack_forget()

    def show_estoque(self):
        self._hide_all()
        self.view_estoque.pack(fill="both", expand=True)
        self.header_title.config(text="Estoque")
        self._update_subtitle()

    def show_demandas(self):
        self._hide_all()
        self.view_demandas.pack(fill="both", expand=True)
        self.header_title.config(text="Demandas")
        self.header_sub.config(text="Pedidos de reposição")

    def show_consumo(self):
        self._hide_all()
        self.view_consumo.pack(fill="both", expand=True)
        self.header_title.config(text="Consumo diário")
        self.header_sub.config(text="Registre as saídas reais do dia")
        self.refresh_consumo()

    def show_resumo(self):
        self._hide_all()
        self.view_resumo.pack(fill="both", expand=True)
        self.header_title.config(text="Resumo visual")
        self.header_sub.config(text="Estoque atual por lanche")
        self.refresh_resumo()

    def _update_subtitle(self):
        try:
            conn = conectar()
            n = conn.execute("SELECT COUNT(*) FROM lanches").fetchone()[0]
            conn.close()
            self.header_sub.config(text=f"{n} lanche(s) cadastrado(s)")
        except sqlite3.Error:
            pass

    def _update_stats(self):
        try:
            conn = conectar()
            rows = conn.execute(
                "SELECT id, estoque, consumo_diario FROM lanches").fetchall()
            criticos = 0
            unidades = 0
            for id_, est, cons_manual in rows:
                cons, _ = consumo_efetivo(conn, id_, cons_manual)
                unidades += est
                if cons > 0 and (est == 0 or est / cons <= 3):
                    criticos += 1
            pendentes = conn.execute(
                "SELECT COUNT(*) FROM demandas WHERE status='Pendente'"
            ).fetchone()[0]
            conn.close()
            self.stat_total.config(text=str(len(rows)))
            self.stat_criticos.config(text=str(criticos))
            self.stat_pendentes.config(text=str(pendentes))
            self.stat_unidades.config(text=str(unidades))
        except sqlite3.Error:
            pass

    def refresh(self):
        if not hasattr(self, "tree"):
            return
        for i in self.tree.get_children():
            self.tree.delete(i)

        try:
            conn = conectar()
            rows = conn.execute(
                "SELECT id, nome, estoque, consumo_diario FROM lanches ORDER BY nome"
            ).fetchall()
            dados = []
            for id_, nome, est, cons_manual in rows:
                cons, veio = consumo_efetivo(conn, id_, cons_manual)
                dados.append((id_, nome, est, cons, veio))
            conn.close()
        except sqlite3.Error as e:
            Toast(self.root, f"Erro: {e}", DANGER)
            return

        for id_, nome, est, cons, veio in dados:
            if cons > 0:
                dias = est / cons
                dias_str = f"{int(dias)} dias" if dias == int(dias) else f"{dias:.1f} dias"
                if est == 0:
                    status, tag = "SEM ESTOQUE", "critico"
                elif dias <= 3:
                    status, tag = "CRÍTICO", "critico"
                elif dias <= 7:
                    status, tag = "ATENÇÃO", "atencao"
                else:
                    status, tag = "OK", "ok"
            else:
                dias_str = "∞"
                status, tag = "OK", "ok"

            cons_str = f"{cons:.2f}" + (" *" if veio else "")
            self.tree.insert("", "end",
                             values=(id_, nome, est, cons_str, dias_str, status),
                             tags=(tag,))

        self.refresh_demandas()
        self._update_subtitle()
        self._update_stats()

    def refresh_demandas(self):
        if not hasattr(self, "tree_dem"):
            return
        for i in self.tree_dem.get_children():
            self.tree_dem.delete(i)
        try:
            conn = conectar()
            rows = conn.execute("""SELECT d.id, l.nome, d.quantidade, d.data, d.status
                                   FROM demandas d
                                   JOIN lanches l ON l.id = d.lanche_id
                                   ORDER BY d.id DESC""").fetchall()
            conn.close()
        except sqlite3.Error:
            return
        for r in rows:
            atendida = r[4] == "Atendida"
            self.tree_dem.insert("", "end",
                                 values=(r[0], r[1], r[2], r[3],
                                         "Atendida" if atendida else "Pendente"),
                                 tags=("atendida" if atendida else "pendente",))

    def refresh_consumo(self):
        if not hasattr(self, "tree_cons"):
            return
        for i in self.tree_cons.get_children():
            self.tree_cons.delete(i)
        try:
            conn = conectar()
            rows = conn.execute("""SELECT c.id, l.nome, c.data, c.quantidade
                                   FROM consumo c
                                   JOIN lanches l ON l.id = c.lanche_id
                                   ORDER BY c.data DESC, c.id DESC""").fetchall()
            conn.close()
        except sqlite3.Error:
            return
        hoje = datetime.now().strftime("%d/%m/%Y")
        for r in rows:
            tag = ("hoje",) if r[2].startswith(hoje) else ()
            self.tree_cons.insert("", "end", values=r, tags=tag)

    def refresh_resumo(self):
        if not hasattr(self, "resumo_canvas"):
            return
        c = self.resumo_canvas
        c.delete("all")
        c.update_idletasks()
        try:
            conn = conectar()
            rows = conn.execute(
                "SELECT id, nome, estoque, consumo_diario FROM lanches ORDER BY nome"
            ).fetchall()
            dados = []
            for id_, nome, est, cons_manual in rows:
                cons, _ = consumo_efetivo(conn, id_, cons_manual)
                dados.append((nome, est, cons))
            conn.close()
        except sqlite3.Error:
            return
        if not dados:
            c.create_text(20, 20, anchor="nw", text="Nenhum lanche cadastrado.",
                          fill=TEXT_MUTED, font=F_BODY)
            return
        max_est = max((e for _, e, _ in dados), default=1) or 1
        bar_x0 = 220
        bar_w = max(200, c.winfo_width() - bar_x0 - 160)
        row_h = 50
        y = 10
        for nome, est, cons in dados:
            if cons > 0:
                dias = est / cons
                if est == 0 or dias <= 3:
                    cor = DANGER
                elif dias <= 7:
                    cor = GOLD
                else:
                    cor = GREEN
            else:
                cor = SKY
            c.create_text(10, y + 16, anchor="nw", text=nome,
                          fill=TEXT, font=("Segoe UI", 10, "bold"))
            c.create_rectangle(bar_x0, y + 8, bar_x0 + bar_w, y + 32,
                               fill=CARD_LIGHT, outline=CARD_BORDER)
            larg = int(bar_w * (est / max_est if max_est > 0 else 0))
            if larg > 0:
                c.create_rectangle(bar_x0, y + 8, bar_x0 + larg, y + 32,
                                   fill=cor, outline="")
            texto = f"{est} un."
            if cons > 0:
                texto += f" · {dias:.1f} dias"
            c.create_text(bar_x0 + bar_w + 12, y + 16, anchor="nw",
                          text=texto, fill=TEXT_MUTED, font=F_SMALL)
            y += row_h
        c.configure(scrollregion=(0, 0, bar_x0 + bar_w + 160, y + 10))

    def verificar_alertas(self):
        try:
            conn = conectar()
            rows = conn.execute(
                "SELECT id, nome, estoque, consumo_diario FROM lanches").fetchall()
            criticos = []
            for id_, nome, est, cons_manual in rows:
                cons, _ = consumo_efetivo(conn, id_, cons_manual)
                if cons > 0 and (est == 0 or est / cons <= 3):
                    criticos.append(f"• {nome}  ({est / cons:.1f} dias)")
            conn.close()
        except sqlite3.Error:
            return
        if criticos:
            AlertDialog(self.root, criticos)

    def get_selecionado(self):
        sel = self.tree.selection()
        if not sel:
            Toast(self.root, "Selecione um lanche", GOLD)
            return None
        return self.tree.item(sel[0])["values"]

    def add_lanche(self):
        dlg = LancheDialog(self.root, "Novo lanche")
        self.root.wait_window(dlg)
        if not dlg.result:
            return
        try:
            conn = conectar()
            conn.execute(
                "INSERT INTO lanches (nome, estoque, consumo_diario) VALUES (?, ?, ?)",
                dlg.result)
            conn.commit()
            conn.close()
            Toast(self.root, "Lanche adicionado", GREEN)
            self.refresh()
        except sqlite3.IntegrityError:
            Toast(self.root, "Nome já existe", DANGER)
        except sqlite3.Error as e:
            Toast(self.root, f"Erro: {e}", DANGER)

    def edit_lanche(self):
        v = self.get_selecionado()
        if not v:
            return
        try:
            dados = (str(v[1]), int(v[2]), float(str(v[3]).replace(" *", "")))
        except (ValueError, TypeError):
            Toast(self.root, "Dados inválidos", DANGER)
            return
        dlg = LancheDialog(self.root, "Editar lanche", dados)
        self.root.wait_window(dlg)
        if not dlg.result:
            return
        try:
            conn = conectar()
            conn.execute(
                "UPDATE lanches SET nome=?, estoque=?, consumo_diario=? WHERE id=?",
                (*dlg.result, v[0]))
            conn.commit()
            conn.close()
            Toast(self.root, "Lanche atualizado", GREEN)
            self.refresh()
        except sqlite3.IntegrityError:
            Toast(self.root, "Nome já existe", DANGER)
        except sqlite3.Error as e:
            Toast(self.root, f"Erro: {e}", DANGER)

    def del_lanche(self):
        v = self.get_selecionado()
        if not v:
            return
        dlg = Confirm(self.root, f"Excluir '{v[1]}' e todas as demandas e consumos?")
        self.root.wait_window(dlg)
        if not dlg.result:
            return
        try:
            conn = conectar()
            conn.execute("DELETE FROM demandas WHERE lanche_id=?", (v[0],))
            conn.execute("DELETE FROM consumo WHERE lanche_id=?", (v[0],))
            cur = conn.execute("DELETE FROM lanches WHERE id=?", (v[0],))
            conn.commit()
            ok = cur.rowcount > 0
            conn.close()
            Toast(self.root,
                  f"'{v[1]}' excluído" if ok else "Lanche já não existia",
                  GREEN if ok else GOLD)
            self.refresh()
        except sqlite3.Error as e:
            Toast(self.root, f"Erro: {e}", DANGER)

    def solicitar_demanda(self):
        v = self.get_selecionado()
        if not v:
            return
        dlg = QuantidadeDialog(self.root, v[1])
        self.root.wait_window(dlg)
        if not dlg.result:
            return
        try:
            conn = conectar()
            conn.execute(
                "INSERT INTO demandas (lanche_id, quantidade, data, status) VALUES (?, ?, ?, ?)",
                (v[0], dlg.result, datetime.now().strftime("%d/%m/%Y %H:%M"), "Pendente"))
            conn.commit()
            conn.close()
            Toast(self.root, "Demanda registrada", GREEN)
            self.refresh_demandas()
            self._update_stats()
        except sqlite3.Error as e:
            Toast(self.root, f"Erro: {e}", DANGER)

    def atender_demanda(self):
        sel = self.tree_dem.selection()
        if not sel:
            Toast(self.root, "Selecione uma demanda", GOLD)
            return
        v = self.tree_dem.item(sel[0])["values"]
        if "Atendida" in str(v[4]):
            Toast(self.root, "Já foi atendida", GOLD)
            return
        dlg = Confirm(self.root,
                      f"Atender {v[2]} un. de '{v[1]}'?\nAdicionará ao estoque.")
        self.root.wait_window(dlg)
        if not dlg.result:
            return
        try:
            conn = conectar()
            row = conn.execute("SELECT id FROM lanches WHERE nome=?", (v[1],)).fetchone()
            if not row:
                conn.execute("DELETE FROM demandas WHERE id=?", (v[0],))
                conn.commit()
                conn.close()
                Toast(self.root, "Lanche não existe mais", DANGER)
                self.refresh()
                return
            conn.execute("UPDATE lanches SET estoque = estoque + ? WHERE id=?",
                         (v[2], row[0]))
            conn.execute("UPDATE demandas SET status='Atendida' WHERE id=?", (v[0],))
            conn.commit()
            conn.close()
            Toast(self.root, "Demanda atendida", GREEN)
            self.refresh()
        except sqlite3.Error as e:
            Toast(self.root, f"Erro: {e}", DANGER)

    def del_demanda(self):
        sel = self.tree_dem.selection()
        if not sel:
            return
        v = self.tree_dem.item(sel[0])["values"]
        dlg = Confirm(self.root, "Excluir essa demanda?")
        self.root.wait_window(dlg)
        if not dlg.result:
            return
        try:
            conn = conectar()
            conn.execute("DELETE FROM demandas WHERE id=?", (v[0],))
            conn.commit()
            conn.close()
            Toast(self.root, "Demanda excluída", GREEN)
            self.refresh_demandas()
            self._update_stats()
        except sqlite3.Error as e:
            Toast(self.root, f"Erro: {e}", DANGER)

    def registrar_consumo(self):
        try:
            conn = conectar()
            lanches = conn.execute("SELECT id, nome FROM lanches ORDER BY nome").fetchall()
            conn.close()
        except sqlite3.Error as e:
            Toast(self.root, f"Erro: {e}", DANGER)
            return
        if not lanches:
            Toast(self.root, "Cadastre um lanche antes", GOLD)
            return
        dlg = ConsumoDialog(self.root, lanches)
        self.root.wait_window(dlg)
        if not dlg.result:
            return
        lanche_id, qtd = dlg.result
        try:
            conn = conectar()
            conn.execute(
                "INSERT INTO consumo (lanche_id, data, quantidade) VALUES (?, ?, ?)",
                (lanche_id, datetime.now().strftime("%d/%m/%Y"), qtd))
            conn.execute("UPDATE lanches SET estoque = MAX(0, estoque - ?) WHERE id=?",
                         (qtd, lanche_id))
            conn.commit()
            conn.close()
            Toast(self.root, "Consumo registrado", GREEN)
            self.refresh()
        except sqlite3.Error as e:
            Toast(self.root, f"Erro: {e}", DANGER)

    def del_consumo(self):
        sel = self.tree_cons.selection()
        if not sel:
            Toast(self.root, "Selecione um registro", GOLD)
            return
        v = self.tree_cons.item(sel[0])["values"]
        dlg = Confirm(self.root,
                      f"Excluir registro de '{v[1]}' ({v[3]} un.)?\n"
                      f"O estoque NÃO será reajustado.")
        self.root.wait_window(dlg)
        if not dlg.result:
            return
        try:
            conn = conectar()
            conn.execute("DELETE FROM consumo WHERE id=?", (v[0],))
            conn.commit()
            conn.close()
            Toast(self.root, "Registro excluído", GREEN)
            self.refresh_consumo()
        except sqlite3.Error as e:
            Toast(self.root, f"Erro: {e}", DANGER)

    def abrir_sobre(self):
        dlg = SobreDialog(self.root)
        self.root.wait_window(dlg)

    def logout(self):
        dlg = Confirm(self.root, "Deseja sair do sistema?")
        self.root.wait_window(dlg)
        if dlg.result:
            fazer_backup()
            self.root.destroy()
            start()


class LancheDialog(tk.Toplevel):
    def __init__(self, parent, title, dados=None):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.configure(bg=CARD)
        self.resizable(False, False)
        self.transient(parent)

        w, h = 440, 500
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        card = tk.Frame(self, bg=CARD, padx=32, pady=28,
                        highlightbackground=CARD_BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        tk.Label(card, text=title, bg=CARD, fg=TEXT, font=F_H2).pack(anchor="w", pady=(0, 22))

        self.nome = NeonEntry(card, "NOME DO LANCHE")
        self.nome.pack(fill="x", pady=(0, 16))
        self.estoque = NeonEntry(card, "ESTOQUE ATUAL (UNIDADES)")
        self.estoque.pack(fill="x", pady=(0, 16))
        self.consumo = NeonEntry(card, "CONSUMO DIÁRIO MANUAL (UNID./DIA)")
        self.consumo.pack(fill="x", pady=(0, 8))

        if dados:
            self.nome.entry.insert(0, str(dados[0]))
            self.estoque.entry.insert(0, str(dados[1]))
            self.consumo.entry.insert(0, str(dados[2]))

        btns = tk.Frame(card, bg=CARD)
        btns.pack(fill="x", pady=(22, 0))
        PillButton(btns, "Cancelar", command=self.destroy,
                   base=CARD_LIGHT, hover=CARD_HOVER, fg=TEXT).pack(side="left")
        PillButton(btns, "Salvar", command=self.salvar,
                   base=PRIMARY, hover=PRIMARY_H, fg="white").pack(side="right")

        self.after(50, self._grab)
        self.after(200, self.nome.focus)

    def _grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass

    def salvar(self):
        try:
            nome = self.nome.get().strip()
            est = int(self.estoque.get())
            cons = float(self.consumo.get().replace(",", "."))
            if not nome:
                raise ValueError("Nome vazio")
            if est < 0 or cons < 0:
                raise ValueError("Negativos não permitidos")
            self.result = (nome, est, cons)
            self.destroy()
        except ValueError as e:
            Toast(self, f"Valor inválido: {e}", DANGER)


class QuantidadeDialog(tk.Toplevel):
    def __init__(self, parent, nome_lanche):
        super().__init__(parent)
        self.result = None
        self.title("Solicitar demanda")
        self.configure(bg=CARD)
        self.resizable(False, False)
        self.transient(parent)

        w, h = 410, 310
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        card = tk.Frame(self, bg=CARD, padx=32, pady=28,
                        highlightbackground=CARD_BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        tk.Label(card, text="Solicitar demanda", bg=CARD, fg=TEXT, font=F_H2).pack(anchor="w")
        tk.Label(card, text=f"Lanche: {nome_lanche}", bg=CARD, fg=TEXT_MUTED,
                 font=F_BODY).pack(anchor="w", pady=(4, 20))

        self.qtd = NeonEntry(card, "QUANTIDADE A SOLICITAR")
        self.qtd.pack(fill="x", pady=(0, 8))

        btns = tk.Frame(card, bg=CARD)
        btns.pack(fill="x", pady=(20, 0))
        PillButton(btns, "Cancelar", command=self.destroy,
                   base=CARD_LIGHT, hover=CARD_HOVER, fg=TEXT).pack(side="left")
        PillButton(btns, "Solicitar", command=self.ok,
                   base=VIOLET, hover=VIOLET_H, fg="white").pack(side="right")

        self.after(50, self._grab)
        self.after(200, self.qtd.focus)

    def _grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass

    def ok(self):
        try:
            n = int(self.qtd.get())
            if n <= 0:
                raise ValueError()
            self.result = n
            self.destroy()
        except ValueError:
            Toast(self, "Digite um inteiro maior que zero", DANGER)


class ConsumoDialog(tk.Toplevel):
    def __init__(self, parent, lanches):
        super().__init__(parent)
        self.result = None
        self._lanches = lanches
        self.title("Registrar consumo")
        self.configure(bg=CARD)
        self.resizable(False, False)
        self.transient(parent)

        w, h = 440, 380
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        card = tk.Frame(self, bg=CARD, padx=32, pady=28,
                        highlightbackground=CARD_BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        tk.Label(card, text="Registrar consumo", bg=CARD, fg=TEXT, font=F_H2).pack(anchor="w")
        tk.Label(card, text="O estoque será reduzido automaticamente.",
                 bg=CARD, fg=TEXT_MUTED, font=F_SMALL).pack(anchor="w", pady=(2, 20))

        tk.Label(card, text="LANCHE", bg=CARD, fg=TEXT_MUTED,
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(0, 6))

        self.combo_var = tk.StringVar()
        nomes = [n for _, n in lanches]
        self.combo_var.set(nomes[0])
        style = ttk.Style()
        style.configure("Neon.TCombobox",
                        fieldbackground=CARD_LIGHT, background=CARD_LIGHT,
                        foreground=TEXT, arrowcolor=ACCENT,
                        borderwidth=0, relief="flat")
        combo = ttk.Combobox(card, textvariable=self.combo_var, values=nomes,
                             state="readonly", font=("Segoe UI", 11),
                             style="Neon.TCombobox")
        combo.pack(fill="x", ipady=6, pady=(0, 16))

        self.qtd = NeonEntry(card, "QUANTIDADE CONSUMIDA")
        self.qtd.pack(fill="x", pady=(0, 8))

        btns = tk.Frame(card, bg=CARD)
        btns.pack(fill="x", pady=(20, 0))
        PillButton(btns, "Cancelar", command=self.destroy,
                   base=CARD_LIGHT, hover=CARD_HOVER, fg=TEXT).pack(side="left")
        PillButton(btns, "Registrar", command=self.ok,
                   base=ACCENT, hover=ACCENT_H, fg="#101820").pack(side="right")

        self.after(50, self._grab)
        self.after(200, self.qtd.focus)

    def _grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass

    def ok(self):
        try:
            nome = self.combo_var.get()
            lanche_id = next(i for i, n in self._lanches if n == nome)
            qtd = int(self.qtd.get())
            if qtd <= 0:
                raise ValueError()
            self.result = (lanche_id, qtd)
            self.destroy()
        except (ValueError, StopIteration):
            Toast(self, "Digite um inteiro maior que zero", DANGER)


class AlertDialog(tk.Toplevel):
    def __init__(self, parent, criticos):
        super().__init__(parent)
        self.title("Alerta de estoque")
        self.configure(bg=CARD)
        self.resizable(False, False)
        self.transient(parent)

        w, h = 500, 400
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        card = tk.Frame(self, bg=CARD, padx=30, pady=28,
                        highlightbackground=CARD_BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        row = tk.Frame(card, bg=CARD)
        row.pack(fill="x")
        tk.Label(row, text="⚡", bg=CARD, fg=GOLD,
                 font=("Segoe UI Emoji", 28)).pack(side="left")
        tk.Label(row, text="  Estoque baixo", bg=CARD, fg=TEXT,
                 font=F_H2).pack(side="left", pady=(4, 0))

        tk.Label(card, text="Os seguintes lanches precisam de reposição:",
                 bg=CARD, fg=TEXT_MUTED, font=F_BODY, anchor="w").pack(fill="x", pady=(14, 12))

        box = tk.Frame(card, bg=CARD_LIGHT, padx=16, pady=12,
                       highlightbackground=CARD_BORDER, highlightthickness=1)
        box.pack(fill="both", expand=True)
        for c in criticos:
            tk.Label(box, text=c, bg=CARD_LIGHT, fg=GOLD_H,
                     font=F_BODY, anchor="w").pack(fill="x", pady=3)

        PillButton(card, "Entendi", command=self.destroy,
                   base=PRIMARY, hover=PRIMARY_H, fg="white").pack(pady=(18, 0))

        self.after(50, self._grab)

    def _grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass


class SobreDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Sobre")
        self.configure(bg=CARD)
        self.resizable(False, False)
        self.transient(parent)

        w, h = 580, 720
        parent.update_idletasks()
        x = parent.winfo_x() + (parent.winfo_width() - w) // 2
        y = parent.winfo_y() + (parent.winfo_height() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

        card = tk.Frame(self, bg=CARD, padx=34, pady=28,
                        highlightbackground=CARD_BORDER, highlightthickness=1)
        card.pack(fill="both", expand=True, padx=14, pady=14)

        tk.Label(card, text="🍔", bg=CARD, fg=PRIMARY,
                 font=("Segoe UI Emoji", 42)).pack(pady=(0, 2))
        tk.Label(card, text="IFSP Lanches", bg=CARD, fg=TEXT,
                 font=F_HERO).pack()
        tk.Label(card, text="Sistema de gerenciamento de estoque",
                 bg=CARD, fg=TEXT_MUTED, font=F_BODY).pack(pady=(2, 16))

        tk.Frame(card, bg=CARD_BORDER, height=1).pack(fill="x", pady=(0, 16))

        tk.Label(card, text="SOBRE O PROGRAMA", bg=CARD, fg=ACCENT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tk.Label(card,
                 text="Aplicação desktop desenvolvida em Python para "
                      "controlar o estoque de lanches escolares. Permite "
                      "cadastrar lanches, acompanhar o consumo diário e "
                      "calcular em quantos dias o estoque atual irá durar, "
                      "facilitando o planejamento de novas demandas.",
                 bg=CARD, fg=TEXT, font=F_BODY, wraplength=490,
                 justify="left").pack(anchor="w", pady=(6, 16))

        tk.Label(card, text="DESENVOLVEDORES", bg=CARD, fg=ACCENT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")

        devs = tk.Frame(card, bg=CARD)
        devs.pack(fill="x", pady=(8, 16))

        for nome, inicial, cor in [
            ("Leandro Pellizzola", "L", PRIMARY),
            ("Davi Ribeiro",       "D", VIOLET),
            ("Matheus Augusto",    "M", ACCENT),
        ]:
            linha = tk.Frame(devs, bg=CARD_LIGHT, padx=14, pady=10,
                             highlightbackground=CARD_BORDER, highlightthickness=1)
            linha.pack(fill="x", pady=3)

            av = tk.Frame(linha, bg=cor, width=38, height=38)
            av.pack(side="left")
            av.pack_propagate(False)
            tk.Label(av, text=inicial, bg=cor, fg="#101820",
                     font=("Segoe UI", 16, "bold")).pack(expand=True)

            tk.Label(linha, text=nome, bg=CARD_LIGHT, fg=TEXT,
                     font=("Segoe UI", 11, "bold")).pack(side="left", padx=12)

        tk.Label(card, text="TECNOLOGIAS", bg=CARD, fg=ACCENT,
                 font=("Segoe UI", 9, "bold")).pack(anchor="w")
        tags = tk.Frame(card, bg=CARD)
        tags.pack(anchor="w", pady=(6, 16))
        for t in ("Python", "Tkinter", "SQLite"):
            tk.Label(tags, text=t, bg=CARD_LIGHT, fg=SKY_H,
                     font=("Segoe UI", 8, "bold"),
                     padx=12, pady=5).pack(side="left", padx=(0, 6))

        PillButton(card, "Fechar", command=self.destroy,
                   base=PRIMARY, hover=PRIMARY_H, fg="white",
                   padx=30, pady=11).pack(fill="x")

        self.after(50, self._grab)
        self.bind("<Escape>", lambda e: self.destroy())

    def _grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except tk.TclError:
            pass


def start():
    init_db()
    root = tk.Tk()
    LoginWindow(root)
    root.mainloop()


if __name__ == "__main__":
    start()