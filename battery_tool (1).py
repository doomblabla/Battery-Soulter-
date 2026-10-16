import customtkinter as ctk
from matplotlib.figure import Figure
from matplotlib.patches import Rectangle, FancyBboxPatch
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

RED = "#ff3030"    # actual output (B+)
LRED = "#ff4747"   # internal positive / series links
BLK = "#111111"    # GND (B-)

REF_PPU = 70       # pixels per data unit at "normal" look


def draw_wiring(S, P):
    """P columns (parallel), each column = S cells stacked in series."""
    CW, GAP, H, NUB = 1.0, 1.0, 2.4, 0.2
    JG = 1.4
    PITCH = H + JG
    OUT = 0.9

    xc0 = CW / 2
    xc1 = xc0 + (P - 1) * (CW + GAP)
    XR = xc1 + CW / 2 + 2.5
    y_top_cell = (S - 1) * PITCH + H
    y_bus_top = y_top_cell + NUB + OUT
    y_bus_bot = -OUT

    xlim = (-1.0, XR + 1.5)
    ylim = (y_bus_bot - 1.8, y_bus_top + 1.8)

    fig = Figure(figsize=(8, 7))
    fig.subplots_adjust(0, 0, 1, 1)
    ax = fig.add_subplot(111)
    items = []

    def line(xs, ys, color, lw, **kw):
        ln, = ax.plot(xs, ys, color=color, lw=lw, zorder=1, **kw)
        items.append((ln, "lw", lw))

    def dot(x, y, color):
        ln, = ax.plot(x, y, "o", color=color, ms=16, zorder=4)
        items.append((ln, "ms", 16))

    def txt(x, y, s, fs, **kw):
        t = ax.text(x, y, s, fontsize=fs, **kw)
        items.append((t, "fs", fs))

    for p in range(P):
        x = p * (CW + GAP)
        xm = x + CW / 2
        for j in range(S):
            y0 = j * PITCH
            box = FancyBboxPatch(
                (x, y0), CW, H, boxstyle="round,pad=0,rounding_size=0.2",
                fc="white", ec=BLK, lw=3, zorder=2)
            ax.add_patch(box)
            items.append((box, "lw", 3))
            ax.add_patch(Rectangle((xm - 0.2, y0 + H), 0.4, NUB,
                                   fc=BLK, ec=BLK, lw=0, zorder=2))
            txt(xm, y0 + H - 0.55, "+", 20, ha="center", va="center",
                weight="bold", zorder=3)
            txt(xm, y0 + 0.55, "\u2212", 20, ha="center", va="center",
                weight="bold", zorder=3)
            txt(xm, y0 + H / 2, f"S{j+1}", 8, ha="center", va="center",
                color="#888888", zorder=3)

        line([xm, xm], [0, y_bus_bot], BLK, 4)
        line([xm, xm], [y_top_cell + NUB, y_bus_top], RED, 4)
        for j in range(S - 1):
            ya = j * PITCH + H + NUB
            yb = (j + 1) * PITCH
            line([xm, xm], [ya, yb], LRED, 4)

    for j in range(S - 1):
        yj = j * PITCH + H + NUB + (JG - NUB) / 2
        line([xc0, xc1], [yj] * 2, LRED, 5, solid_capstyle="round")
        # balance lead papunta sa kanan, kapantay ng B+ at B-
        line([xc1, XR], [yj] * 2, LRED, 5, solid_capstyle="round")
        dot(XR, yj, LRED)
        txt(XR + 0.35, yj, f"B{j+1}", 12, ha="left", va="center",
            color="#e06666", weight="bold")

    line([xc0, XR], [y_bus_bot] * 2, BLK, 5, solid_capstyle="round")
    line([xc0, XR], [y_bus_top] * 2, RED, 5, solid_capstyle="round")
    dot(XR, y_bus_bot, BLK)
    dot(XR, y_bus_top, RED)
    txt(XR + 0.35, y_bus_top, "B+", 12, ha="left", va="center",
        color=RED, weight="bold")
    txt(XR + 0.35, y_bus_bot, "B-", 12, ha="left", va="center",
        color=BLK, weight="bold")

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("auto")      # view is computed manually (see App.apply_view)
    ax.axis("off")
    fig.home = (xlim, ylim)
    return fig, items


ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Battery Pack Visualizer")
        self.geometry("1350x760")
        self.canvas = None
        self.ax = None
        self.fig = None
        self.items = []
        self.home = None
        self.pan = None
        self.fitted = True
        self.ppu = 1.0
        self.cx = self.cy = 0.0

        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        self.build_left()
        self.build_center()
        self.build_right()

        self.bind("<Return>", lambda e: self.create())

    # ---------- LEFT: inputs ----------
    def build_left(self):
        left = ctk.CTkScrollableFrame(self, width=240)
        left.grid(row=0, column=0, sticky="ns", padx=(10, 5), pady=10)

        ctk.CTkLabel(left, text="INPUT",
                     font=("Arial", 20, "bold")).pack(pady=(10, 8))

        self.main = {}
        for label, ph in [("Series (S)", "e.g. 3"),
                          ("Parallel (P)", "e.g. 2")]:
            ctk.CTkLabel(left, text=label).pack(anchor="w", padx=10)
            e = ctk.CTkEntry(left, placeholder_text=ph)
            e.pack(padx=10, pady=(0, 8), fill="x")
            self.main[label] = e

        ctk.CTkButton(left, text="Create", height=40,
                      font=("Arial", 15, "bold"),
                      command=self.create).pack(padx=10, pady=8, fill="x")

        self.msg = ctk.CTkLabel(left, text="", text_color="#ff6b6b",
                                wraplength=200, justify="left")
        self.msg.pack(padx=10)

        ctk.CTkLabel(left, text="Cell & load specs",
                     font=("Arial", 13, "bold")).pack(pady=(8, 4))
        self.extra = {}
        for label, default in [("Cell voltage (V)", "3.7"),
                               ("Capacity (mAh)", "2500"),
                               ("Max discharge (C)", "10"),
                               ("Load current (A)", "5"),
                               ("Rated cycle life", "500")]:
            ctk.CTkLabel(left, text=label).pack(anchor="w", padx=10)
            e = ctk.CTkEntry(left)
            e.insert(0, default)
            e.pack(padx=10, pady=(0, 5), fill="x")
            self.extra[label] = e

    # ---------- CENTER: visual ----------
    def build_center(self):
        self.view = ctk.CTkFrame(self)
        self.view.grid(row=0, column=1, sticky="nsew", padx=5, pady=10)
        self.hint = ctk.CTkLabel(
            self.view, text="Ilagay ang S at P, tapos pindutin ang Create",
            font=("Arial", 16))
        self.hint.place(relx=0.5, rely=0.5, anchor="center")
        self.tip = ctk.CTkLabel(
            self.view,
            text="Scroll = zoom  |  Drag = pan  |  Double-click = reset",
            font=("Arial", 11), text_color="#9aa0a6")

    # ---------- RIGHT: outputs ----------
    def build_right(self):
        right = ctk.CTkScrollableFrame(self, width=240)
        right.grid(row=0, column=2, sticky="ns", padx=(5, 10), pady=10)

        ctk.CTkLabel(right, text="OUTPUT",
                     font=("Arial", 20, "bold")).pack(pady=(10, 8))

        self.pack_label = ctk.CTkLabel(right, text="-",
                                       font=("Arial", 13, "bold"))
        self.pack_label.pack(pady=(0, 8))

        self.out = {}
        for key, title in [("volt", "Output voltage"),
                           ("load", "Output current (load)"),
                           ("status", "Status"),
                           ("maxa", "Max output current"),
                           ("percell", "Current per cell"),
                           ("cap", "Capacity"),
                           ("energy", "Energy"),
                           ("runtime", "Runtime (ideal)"),
                           ("cycles", "Rated cycles"),
                           ("life", "Lifetime energy")]:
            self.add_row(right, key, title)

    def add_row(self, parent, key, title):
        ctk.CTkLabel(parent, text=title).pack(anchor="w", padx=10)
        lbl = ctk.CTkLabel(parent, text="-", font=("Arial", 14, "bold"))
        lbl.pack(anchor="w", padx=10, pady=(0, 5))
        self.out[key] = lbl

    # ---------- view / zoom / pan ----------
    def fit_ppu(self):
        w, h = self.fig.bbox.width, self.fig.bbox.height
        (x0, x1), (y0, y1) = self.home
        return min(w / (x1 - x0), h / (y1 - y0))

    def rescale(self):
        s = min(self.ppu / REF_PPU, 2.5)
        for art, kind, base in self.items:
            if kind == "lw":
                art.set_linewidth(max(base * s, 0.3))
            elif kind == "ms":
                art.set_markersize(max(base * s, 2))
            else:
                fs = base * s
                art.set_visible(fs >= 3.5)
                art.set_fontsize(max(fs, 1))

    def apply_view(self):
        if self.fig is None:
            return
        w, h = self.fig.bbox.width, self.fig.bbox.height
        if w <= 1 or h <= 1:
            return
        if self.fitted:
            (x0, x1), (y0, y1) = self.home
            self.ppu = self.fit_ppu()
            self.cx, self.cy = (x0 + x1) / 2, (y0 + y1) / 2
        self.ax.set_xlim(self.cx - w / 2 / self.ppu,
                         self.cx + w / 2 / self.ppu)
        self.ax.set_ylim(self.cy - h / 2 / self.ppu,
                         self.cy + h / 2 / self.ppu)
        self.rescale()
        self.canvas.draw_idle()

    def on_resize(self, ev):
        self.apply_view()

    def on_scroll(self, ev):
        if ev.x is None or self.fig is None:
            return
        f = 1.25 if ev.button == "up" else 0.8
        w, h = self.fig.bbox.width, self.fig.bbox.height
        fit = self.fit_ppu()
        new = min(max(self.ppu * f, fit * 0.5), fit * 400)
        # keep the point under the mouse fixed
        mx, my = ev.x - w / 2, ev.y - h / 2
        xd = self.cx + mx / self.ppu
        yd = self.cy + my / self.ppu
        self.ppu = new
        self.cx = xd - mx / new
        self.cy = yd - my / new
        self.fitted = False
        self.apply_view()

    def on_press(self, ev):
        if ev.dblclick:
            self.fitted = True
            self.apply_view()
            return
        if ev.button == 1 and ev.x is not None:
            self.pan = (ev.x, ev.y)

    def on_move(self, ev):
        if self.pan is None or ev.x is None:
            return
        dx, dy = ev.x - self.pan[0], ev.y - self.pan[1]
        self.cx -= dx / self.ppu
        self.cy -= dy / self.ppu
        self.pan = (ev.x, ev.y)
        self.fitted = False
        self.apply_view()

    def on_release(self, ev):
        self.pan = None

    # ---------- logic ----------
    def create(self):
        try:
            S = int(self.main["Series (S)"].get())
            P = int(self.main["Parallel (P)"].get())
            v = float(self.extra["Cell voltage (V)"].get())
            mah = float(self.extra["Capacity (mAh)"].get())
            c = float(self.extra["Max discharge (C)"].get())
            load = float(self.extra["Load current (A)"].get())
            cycles = int(float(self.extra["Rated cycle life"].get()))
            if S < 1 or P < 1 or min(v, mah, c, cycles) <= 0 or load < 0:
                raise ValueError
        except ValueError:
            self.msg.configure(
                text="Mali ang input.\nWhole numbers ang S at P (1 pataas).")
            return
        self.msg.configure(text="")

        try:
            fig, items = draw_wiring(S, P)
            if self.canvas:
                self.canvas.get_tk_widget().destroy()
            self.fig, self.items = fig, items
            self.ax = fig.axes[0]
            self.home = fig.home
            self.pan = None
            self.fitted = True
            self.canvas = FigureCanvasTkAgg(fig, master=self.view)
            self.hint.place_forget()
            self.tip.pack(side="bottom", pady=2)
            self.canvas.get_tk_widget().pack(fill="both", expand=True)
            self.canvas.mpl_connect("scroll_event", self.on_scroll)
            self.canvas.mpl_connect("button_press_event", self.on_press)
            self.canvas.mpl_connect("motion_notify_event", self.on_move)
            self.canvas.mpl_connect("button_release_event", self.on_release)
            self.canvas.mpl_connect("resize_event", self.on_resize)
            self.update_idletasks()
            self.apply_view()
            self.canvas.draw()
        except Exception as ex:
            self.msg.configure(text=f"Drawing error:\n{ex!r}")
            return

        volts = S * v
        ah = P * mah / 1000
        wh = volts * ah
        max_a = ah * c
        per_cell = load / P
        cell_c = per_cell / (mah / 1000)
        overload = load > max_a
        runtime_min = (ah / load * 60) if load > 0 else float("inf")
        life_kwh = wh * cycles / 1000

        self.pack_label.configure(text=f"{S}S{P}P  ({S*P} cells)")
        self.out["volt"].configure(text=f"{volts:.1f} V")
        self.out["load"].configure(text=f"{load:.1f} A")
        self.out["status"].configure(
            text="OVERLOAD!" if overload else "OK",
            text_color="#ff4d4d" if overload else "#4cd964")
        self.out["maxa"].configure(text=f"{max_a:.0f} A")
        self.out["percell"].configure(
            text=f"{per_cell:.2f} A ({cell_c:.1f}C)")
        self.out["cap"].configure(text=f"{ah:.1f} Ah")
        self.out["energy"].configure(text=f"{wh:.1f} Wh")
        self.out["runtime"].configure(
            text="-" if load == 0 else f"{runtime_min:.0f} min")
        self.out["cycles"].configure(text=f"{cycles} cycles")
        self.out["life"].configure(text=f"~{life_kwh:.1f} kWh")


App().mainloop()