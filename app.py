import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch

RED = "#ff3030"    # Main positive output (B+)
LRED = "#ff4747"   # Internal positive / series links
BLK = "#111111"    # Negative output (B-)


def draw_wiring(S, P):
    """Draw P parallel strings, each containing S cells in series."""
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

    xlim = (-1.0, XR + 2.8)
    ylim = (y_bus_bot - 1.8, y_bus_top + 1.8)

    fig, ax = plt.subplots(figsize=(max(7, P * 1.1), max(5, S * 0.9)))
    fig.subplots_adjust(left=0.02, right=0.98, top=0.98, bottom=0.02)

    def line(xs, ys, color, lw, **kw):
        ax.plot(xs, ys, color=color, lw=lw, zorder=1, **kw)

    def dot(x, y, color):
        ax.plot(x, y, "o", color=color, ms=8, zorder=4)

    def txt(x, y, label, fs, **kw):
        ax.text(x, y, label, fontsize=fs, **kw)

    for p in range(P):
        x = p * (CW + GAP)
        xm = x + CW / 2

        for j in range(S):
            y0 = j * PITCH
            box = FancyBboxPatch(
                (x, y0), CW, H,
                boxstyle="round,pad=0,rounding_size=0.2",
                fc="white", ec=BLK, lw=2.2, zorder=2
            )
            ax.add_patch(box)
            ax.add_patch(Rectangle(
                (xm - 0.2, y0 + H), 0.4, NUB,
                fc=BLK, ec=BLK, lw=0, zorder=2
            ))
            txt(xm, y0 + H - 0.55, "+", 17, ha="center",
                va="center", weight="bold", zorder=3)
            txt(xm, y0 + 0.55, "−", 17, ha="center",
                va="center", weight="bold", zorder=3)
            txt(xm, y0 + H / 2, f"S{j + 1}", 8,
                ha="center", va="center", color="#888888", zorder=3)

        line([xm, xm], [0, y_bus_bot], BLK, 3)
        line([xm, xm], [y_top_cell + NUB, y_bus_top], RED, 3)

        for j in range(S - 1):
            ya = j * PITCH + H + NUB
            yb = (j + 1) * PITCH
            line([xm, xm], [ya, yb], LRED, 3)

    # Parallel links between the series strings and balance taps
    for j in range(S - 1):
        yj = j * PITCH + H + NUB + (JG - NUB) / 2
        line([xc0, xc1], [yj, yj], LRED, 4, solid_capstyle="round")
        line([xc1, XR], [yj, yj], LRED, 4, solid_capstyle="round")
        dot(XR, yj, LRED)
        txt(XR + 0.3, yj, f"B{j + 1}", 10, ha="left",
            va="center", color="#e06666", weight="bold")

    line([xc0, XR], [y_bus_bot, y_bus_bot], BLK, 4,
         solid_capstyle="round")
    line([xc0, XR], [y_bus_top, y_bus_top], RED, 4,
         solid_capstyle="round")
    dot(XR, y_bus_bot, BLK)
    dot(XR, y_bus_top, RED)
    txt(XR + 0.3, y_bus_top, "B+", 10, ha="left",
        va="center", color=RED, weight="bold")
    txt(XR + 0.3, y_bus_bot, "B-", 10, ha="left",
        va="center", color=BLK, weight="bold")

    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.set_aspect("auto")
    ax.axis("off")
    return fig


st.set_page_config(
    page_title="Battery Pack Visualizer",
    page_icon="🔋",
    layout="wide"
)

st.title("🔋 Battery Pack Visualizer")
st.caption(
    "Configure a series-parallel battery pack, view its wiring diagram, "
    "and estimate its electrical specifications."
)

with st.sidebar:
    st.header("Battery Configuration")
    S = st.number_input("Series cells (S)", min_value=1, max_value=40,
                        value=3, step=1)
    P = st.number_input("Parallel strings (P)", min_value=1, max_value=40,
                        value=2, step=1)

    st.subheader("Cell and Load Specifications")
    v = st.number_input("Cell voltage (V)", min_value=0.01,
                        value=3.7, step=0.1, format="%.2f")
    mah = st.number_input("Cell capacity (mAh)", min_value=1.0,
                          value=2500.0, step=100.0)
    c = st.number_input("Maximum discharge rate (C)", min_value=0.01,
                        value=10.0, step=0.5, format="%.2f")
    load = st.number_input("Load current (A)", min_value=0.0,
                           value=5.0, step=0.5, format="%.2f")
    cycles = st.number_input("Rated cycle life (cycles)", min_value=1,
                             value=500, step=100)

    st.caption("S and P are whole numbers. Cell capacity and discharge rate must be positive.")

if S * P > 200:
    st.error("The diagram is limited to 200 cells to keep the browser responsive. Reduce S or P.")
    st.stop()

# Core calculations, consistent with the desktop version
volts = S * v
ah = P * mah / 1000
wh = volts * ah
max_a = ah * c
per_cell = load / P
cell_c = per_cell / (mah / 1000)
overload = load > max_a
runtime_min = (ah / load * 60) if load > 0 else None
life_kwh = wh * cycles / 1000

left, right = st.columns([1.65, 1], gap="large")

with left:
    st.subheader(f"Wiring Diagram: {S}S{P}P")
    st.caption(f"{S * P} cells total · Red = positive · Black = negative · B1, B2, etc. = balance taps")
    fig = draw_wiring(int(S), int(P))
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

with right:
    st.subheader("Pack Summary")
    st.metric("Configuration", f"{S}S{P}P", f"{S * P} cells")
    st.metric("Output voltage", f"{volts:.2f} V")
    st.metric("Pack capacity", f"{ah:.2f} Ah")
    st.metric("Energy", f"{wh:.2f} Wh")

    st.subheader("Current and Load")
    st.metric("Load current", f"{load:.2f} A")
    st.metric("Maximum theoretical current", f"{max_a:.2f} A")
    st.metric("Current per cell", f"{per_cell:.2f} A", f"{cell_c:.2f}C per cell")

    if overload:
        st.error("OVERLOAD: entered load exceeds the calculated maximum discharge current.")
    else:
        st.success("OK: entered load is within the calculated maximum discharge current.")

    st.subheader("Runtime and Cycle Life")
    if runtime_min is None:
        st.metric("Estimated runtime", "N/A", help="Enter a load current greater than zero.")
    else:
        st.metric("Estimated runtime", f"{runtime_min:.1f} min")
    st.metric("Rated cycle life", f"{int(cycles):,} cycles")
    st.metric("Estimated lifetime energy", f"~{life_kwh:.2f} kWh")

st.divider()
st.subheader("Calculation Notes")
st.markdown(
    """
    - **Pack voltage** = series count × cell voltage
    - **Pack capacity** = parallel count × cell capacity
    - **Energy** = pack voltage × pack capacity
    - **Maximum theoretical current** = pack capacity (Ah) × cell discharge rate (C)
    - **Current per cell** = load current ÷ parallel count
    - **Estimated runtime** = pack capacity ÷ load current × 60
    - **Lifetime energy** = energy per full pack cycle × rated cycle life
    """
)
st.warning(
    "These are ideal estimates, not live measurements. Actual runtime and safe current "
    "depend on the specific cells, temperature, wiring, protection circuitry, load behavior, "
    "and manufacturer ratings. The cycle-life and lifetime-energy figures use your entered "
    "rated cycle life and do not predict actual battery aging."
)
