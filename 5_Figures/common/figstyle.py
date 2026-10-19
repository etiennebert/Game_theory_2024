import matplotlib as mpl, matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
import geopandas as gpd, pandas as pd, numpy as np
from mapping import regions_gdf
INK, INK2, MUTED, GRID, BASE, SURF = "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7", "#ffffff"
OUTSIDE, MEMBER0 = "#ecebe6", "#d9e6d7"       # non-member fill; member with no clearing to forgo
GREENS = ['#d5f1d2', '#a5dc9f', '#6dba67', '#349130', '#006500', '#004000']
ORANGES = ['#fbcbba', '#ef8d69', '#d0531e']; BLUES = ['#bedaff', '#71adfb', '#3280de']; NEUTRAL = "#f0efec"
DARK, LIGHT = "#4b4a47", "#c9c8c1"           # producers / other regions
BLUE3 = ["#6da7ec", "#256abf", "#0d366b"]    # switching-cost ordinal ramp (validated)
def style():
    mpl.rcParams.update({"font.family": "Liberation Sans", "font.size": 7, "axes.labelsize": 7, "axes.titlesize": 7.5,
        "xtick.labelsize": 6.3, "ytick.labelsize": 6.3, "axes.edgecolor": BASE, "axes.linewidth": 0.6, "xtick.color": INK2, "ytick.color": INK2,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5, "axes.labelcolor": INK, "text.color": INK,
        "pdf.fonttype": 42, "svg.fonttype": "none", "savefig.facecolor": SURF, "figure.facecolor": SURF, "hatch.linewidth": 0.5, "legend.fontsize": 6.2})
def clean(ax, x=True, y=True):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    if y: ax.grid(axis="y", color=GRID, linewidth=0.5)
    if x: ax.grid(axis="x", color=GRID, linewidth=0.5)
    ax.set_axisbelow(True)
NAMES = {"brasil": "Brazil", "drc": "DRC", "seasia": "South-East Asia", "bolivia": "Bolivia", "ivorycoast": "Ivory Coast", "indonesia": "Indonesia",
 "colombia": "Colombia", "nigeria": "Nigeria", "cafr": "Central Africa", "india": "India", "peru": "Peru", "ghana": "Ghana", "malasya": "Malaysia",
 "latinamer": "Rest of Latin America", "mexico": "Mexico", "myanmar": "Myanmar", "angola": "Angola", "eafr": "Eastern Africa", "madagascar": "Madagascar",
 "wafr": "Western Africa", "paraguay": "Paraguay", "safr": "Southern Africa", "mozambique": "Mozambique", "venezuela": "Venezuela", "eu27": "EU",
 "us": "United States", "china": "China", "japan": "Japan", "uk": "United Kingdom", "mena": "Middle East", "canada": "Canada", "russia": "Russia",
 "korea": "Korea", "oceania": "Oceania", "efta": "EFTA", "southasia": "South Asia", "nafr": "North Africa", "argentina": "Argentina",
 "restofworld": "Rest of world", "newzealand": "New Zealand", "eastasia": "Rest of East Asia", "uruguay": "Uruguay"}
def panel(ax, letter, x=-0.06, y=1.04):
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=8.5, fontweight="bold", va="bottom", ha="left")
def draw_map(ax, values, members, bins, colors, member_zero=MEMBER0, edge=SURF):
    """values: dict region -> value (colour by bins); members: set of regions; others grey."""
    g, _ = regions_gdf()
    def col(r):
        if r not in members: return OUTSIDE
        v = values.get(r, 0.0)
        if v <= bins[0]: return member_zero
        for i in range(len(bins) - 1):
            if bins[i] < v <= bins[i + 1]: return colors[i]
        return colors[-1]
    g = g.copy(); g["c"] = g["region"].map(col)
    g.plot(ax=ax, color=g["c"], edgecolor=edge, linewidth=0.25)
    ax.set_axis_off(); ax.set_xlim(-1.7e7, 1.7e7); ax.set_ylim(-6.0e6, 8.7e6)
def draw_map_div(ax, values, members, bins, colors, edge=SURF, hatch_out=False):
    g, _ = regions_gdf()
    def col(r):
        v = values.get(r, 0.0)
        for i in range(len(bins) - 1):
            if bins[i] <= v < bins[i + 1]: return colors[i]
        return colors[-1] if v >= bins[-1] else colors[0]
    g = g.copy(); g["c"] = g["region"].map(col); g["m"] = g["region"].isin(members)
    g.plot(ax=ax, color=g["c"], edgecolor=edge, linewidth=0.25)
    out = g[~g["m"]]
    if len(out): out.plot(ax=ax, facecolor="none", edgecolor="#9a9891", linewidth=0.0, hatch="//////", alpha=0.55)
    ax.set_axis_off(); ax.set_xlim(-1.7e7, 1.7e7); ax.set_ylim(-6.0e6, 8.7e6)
