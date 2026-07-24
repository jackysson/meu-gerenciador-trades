import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import csv
from datetime import datetime
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import matplotlib.gridspec as gridspec
import numpy as np

# ──────────────────────────────────────────────
# CONSTANTES E CONFIGURAÇÕES
# ──────────────────────────────────────────────
APP_TITLE = "Gerenciador de Trades Pro"
DATE_FMT = "%Y-%m-%d %H:%M:%S"
DISPLAY_FMT = "%Y-%m-%d %H:%M:%S"
INITIAL_CAPITAL_DEFAULT = 20.0

TRADE_FIELDS = [
    "data_abertura", "ativo", "bilhete", "tipo", "volume",
    "preco_entrada", "sl", "tp", "data_fechamento",
    "preco_fechamento", "lucro", "mudanca_pct", "observacao"
]
DEPOSIT_FIELDS = ["data", "valor", "descricao"]

# Paleta de Cores (Tema Dark)
C = {
    "bg":         "#0d1117",   # Fundo geral
    "bg2":        "#161b22",   # Painéis
    "bg3":        "#21262d",   # Cards / Inputs
    "border":     "#30363d",   # Bordas
    "accent":     "#58a6ff",   # Azul destaque
    "green":      "#3fb950",   # Verde lucro
    "red":        "#f85149",   # Vermelho prejuízo
    "warn":       "#d29922",   # Amarelo alerta
    "text":       "#e6edf3",   # Texto principal
    "text2":      "#8b949e",   # Texto secundário
}

# ──────────────────────────────────────────────
# UTILITÁRIOS
# ──────────────────────────────────────────────
def parse_float(v):
    if v is None or v == "": return None
    try: return float(str(v).replace(",", "."))
    except: return None

def fmt_money(v):
    if v is None: return "0,00"
    return f"{v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_pct(v):
    if v is None: return "0,00%"
    return f"{v * 100:.2f}%"

def parse_dt(s):
    if not s: return None
    for fmt in [DISPLAY_FMT, DATE_FMT, "%Y.%m.%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y"]:
        try: return datetime.strptime(s, fmt)
        except: pass
    return None

def dt_to_str(dt):
    return dt.strftime(DISPLAY_FMT) if isinstance(dt, datetime) else ""

# ──────────────────────────────────────────────
# CLASSE PRINCIPAL
# ──────────────────────────────────────────────
class TradeManagerApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1400x850")
        self.configure(bg=C["bg"])

        self.initial_capital = INITIAL_CAPITAL_DEFAULT
        self.trades = []
        self.deposits = []
        self.filepath = None
        self.current_edit_trade_index = None
        self.current_edit_deposit_index = None

        self._apply_style()
        self._build_ui()
        self._refresh_all()

    def _apply_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure(".", background=C["bg"], foreground=C["text"], font=("Segoe UI", 10))
        style.configure("TFrame", background=C["bg"])
        style.configure("TLabel", background=C["bg"], foreground=C["text"])
        
        # Notebook (Abas)
        style.configure("TNotebook", background=C["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=C["bg2"], foreground=C["text2"], padding=[15, 5])
        style.map("TNotebook.Tab", background=[("selected", C["bg3"])], foreground=[("selected", C["accent"])])

        # Treeview (Tabelas)
        style.configure("Treeview", background=C["bg2"], foreground=C["text"], fieldbackground=C["bg2"], rowheight=28)
        style.configure("Treeview.Heading", background=C["bg3"], foreground=C["accent"], font=("Segoe UI", 10, "bold"))
        style.map("Treeview", background=[("selected", C["accent"])], foreground=[("selected", "#000")])

        # Botões
        style.configure("TButton", padding=5)
        style.configure("Accent.TButton", background=C["accent"], foreground="black")
        style.configure("Danger.TButton", background=C["red"], foreground="white")

    def _build_ui(self):
        # Header com Stats Rápidas
        header = tk.Frame(self, bg=C["bg2"], height=100)
        header.pack(fill=tk.X, padx=10, pady=10)
        
        self.stat_labels = {}
        stats = ["Equity", "Lucro Total", "Win Rate", "Trades"]
        for i, s in enumerate(stats):
            f = tk.Frame(header, bg=C["bg3"], highlightbackground=C["border"], highlightthickness=1)
            f.place(relx=i*0.25, rely=0.1, relwidth=0.23, relheight=0.8)
            tk.Label(f, text=s, bg=C["bg3"], fg=C["text2"], font=("Segoe UI", 9)).pack(pady=5)
            lbl = tk.Label(f, text="---", bg=C["bg3"], fg=C["accent"], font=("Segoe UI", 14, "bold"))
            lbl.pack()
            self.stat_labels[s] = lbl

        # Notebook Principal
        nb = ttk.Notebook(self)
        nb.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # ABA 1: TRADES
        page_trades = ttk.Frame(nb)
        nb.add(page_trades, text="  Lista de Trades  ")
        
        paned = ttk.Panedwindow(page_trades, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)

        # Tabela
        tree_frame = ttk.Frame(paned)
        paned.add(tree_frame, weight=4)
        
        toolbar = tk.Frame(tree_frame, bg=C["bg"])
        toolbar.pack(fill=tk.X, pady=5)
        ttk.Button(toolbar, text="+ Novo Trade", command=self._form_new_trade).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Excluir", command=self._delete_selected_trade).pack(side=tk.LEFT, padx=5)

        self.tree = ttk.Treeview(tree_frame, columns=TRADE_FIELDS, show="headings")
        for c in TRADE_FIELDS:
            self.tree.heading(c, text=c.replace("_", " ").title())
            self.tree.column(c, width=100, anchor="center")
        
        self.tree.tag_configure("win", foreground=C["green"])
        self.tree.tag_configure("loss", foreground=C["red"])
        self.tree.pack(fill=tk.BOTH, expand=True)
        self.tree.bind("<<TreeviewSelect>>", lambda e: self._load_trade_to_form())

        # Formulário lateral
        form_frame = tk.Frame(paned, bg=C["bg2"], padx=15, pady=15)
        paned.add(form_frame, weight=1)
        tk.Label(form_frame, text="DETALHES DO TRADE", bg=C["bg2"], fg=C["accent"], font=("Segoe UI", 11, "bold")).pack(pady=10)
        
        self.trade_vars = {k: tk.StringVar() for k in TRADE_FIELDS}
        for k in TRADE_FIELDS:
            tk.Label(form_frame, text=k.replace("_", " ").title(), bg=C["bg2"], fg=C["text2"], font=("Segoe UI", 8)).pack(anchor="w")
            tk.Entry(form_frame, textvariable=self.trade_vars[k], bg=C["bg3"], fg="white", insertbackground="white", relief="flat").pack(fill="x", pady=2)
        
        ttk.Button(form_frame, text="SALVAR ALTERAÇÕES", command=self._save_trade_from_form).pack(fill="x", pady=20)

        # ABA 2: DASHBOARD
        self.page_dash = ttk.Frame(nb)
        nb.add(self.page_dash, text="  Dashboard Visual  ")
        self.fig = Figure(figsize=(10, 6), facecolor=C["bg"])
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.page_dash)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    # ──────────────────────────────────────────────
    # LÓGICA E GRÁFICOS
    # ──────────────────────────────────────────────
    def _refresh_all(self):
        # Atualiza Tabela
        for i in self.tree.get_children(): self.tree.delete(i)
        total_profit = 0
        wins = 0
        for idx, t in enumerate(self.trades):
            lucro = parse_float(t.get("lucro")) or 0
            total_profit += lucro
            tag = "win" if lucro > 0 else "loss" if lucro < 0 else ""
            if lucro > 0: wins += 1
            self.tree.insert("", "end", iid=str(idx), values=[t.get(k, "") for k in TRADE_FIELDS], tags=(tag,))

        # Atualiza Stats no Header
        equity = self.initial_capital + total_profit
        self.stat_labels["Equity"].config(text=f"$ {fmt_money(equity)}")
        self.stat_labels["Lucro Total"].config(text=f"$ {fmt_money(total_profit)}", fg=C["green"] if total_profit >= 0 else C["red"])
        wr = (wins / len(self.trades) * 100) if self.trades else 0
        self.stat_labels["Win Rate"].config(text=f"{wr:.1f}%")
        self.stat_labels["Trades"].config(text=str(len(self.trades)))

        self._update_charts()

    def _update_charts(self):
        self.fig.clear()
        if not self.trades: return
        
        gs = gridspec.GridSpec(1, 2, figure=self.fig)
        
        # 1. Curva de Equity
        ax1 = self.fig.add_subplot(gs[0, 0])
        ax1.set_facecolor(C["bg"])
        profits = [parse_float(t.get("lucro")) or 0 for t in self.trades]
        equity_curve = np.cumsum([self.initial_capital] + profits)
        ax1.plot(equity_curve, color=C["accent"], marker='o', linewidth=2)
        ax1.set_title("Evolução do Patrimônio", color="white", fontsize=10)
        ax1.grid(color=C["border"], linestyle='--', alpha=0.5)
        ax1.tick_params(colors=C["text2"])

        # 2. Distribuição Win/Loss
        ax2 = self.fig.add_subplot(gs[0, 1])
        ax2.set_facecolor(C["bg"])
        wins = sum(1 for p in profits if p > 0)
        losses = sum(1 for p in profits if p < 0)
        ax2.pie([wins, losses], labels=["Wins", "Losses"], colors=[C["green"], C["red"]], autopct='%1.1f%%', textprops={'color':"w"})
        ax2.set_title("Win Rate Real", color="white", fontsize=10)

        self.fig.tight_layout()
        self.canvas.draw()

    # ──────────────────────────────────────────────
    # HANDLERS
    # ──────────────────────────────────────────────
    def _form_new_trade(self):
        for v in self.trade_vars.values(): v.set("")
        self.current_edit_trade_index = None

    def _load_trade_to_form(self):
        sel = self.tree.selection()
        if not sel: return
        idx = int(sel[0])
        self.current_edit_trade_index = idx
        t = self.trades[idx]
        for k in TRADE_FIELDS: self.trade_vars[k].set(t.get(k, ""))

    def _save_trade_from_form(self):
        t = {k: self.trade_vars[k].get() for k in TRADE_FIELDS}
        if self.current_edit_trade_index is None:
            self.trades.append(t)
        else:
            self.trades[self.current_edit_trade_index] = t
        self._refresh_all()
        messagebox.showinfo("Sucesso", "Trade salvo com sucesso!")

    def _delete_selected_trade(self):
        sel = self.tree.selection()
        if not sel: return
        if messagebox.askyesno("Confirmar", "Excluir trade selecionado?"):
            self.trades.pop(int(sel[0]))
            self._refresh_all()

if __name__ == "__main__":
    app = TradeManagerApp()
    app.mainloop()
