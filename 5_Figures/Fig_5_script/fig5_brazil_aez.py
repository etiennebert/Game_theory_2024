"""Fig. 5: Brazil inside the club - where its agriculture goes when the forest stays (EU alone, the headline penalty club at
convergence; the surcharge coalition gives the same picture and is in the source data; FOREST_CLUB_FIG5=surcharge draws it).
a  Brazil's agro-ecological zones (GTAP-AEZ: thermal zone x length of growing period) and the forest each keeps.
b  Land use at the club equilibrium relative to the baseline (the EUDR world: business-as-usual clearing, Stage A, then the
   EUDR, Stage B), by zone: land covers (forest, pasture, cropland) and harvested area by crop; colour = % of the baseline
   level, number = change in thousand hectares.
c  National output of the land-based products, % relative to the baseline.
Reads brazil_aez_<label>.csv (extract_brazil_aez.R) and brazil_aez.geojson (build_brazil_aez_map.py).
"""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))   # the shared modules of the pipeline (paths, figstyle, mapping, v30)
import csv, os, json
import numpy as np, pandas as pd, geopandas as gpd
from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.patches import Rectangle, Patch
from figstyle import *
from paths import here, fig as figpath, LABEL
import warnings; warnings.filterwarnings("ignore")
style()
INST = os.environ.get("FOREST_CLUB_FIG5", "penalty")
d = pd.read_csv(here("brazil_aez.csv"))
if INST not in set(d.instrument): INST = sorted(set(d.instrument))[0]; print("  Fig. 5 drawn for the", INST, "run (the other is not on the disk)")
d["club_vs_bau_kha"] = d["club_change_kha"] - d["stageB_change_kha"]                              # club relative to the EUDR world (both solved from the Stage A data)
d["bau_level_kha"] = d["level_2019_kha"] + d["stageA_change_kha"] + d["stageB_change_kha"]        # the baseline level: 2019 + BAU clearing + the EUDR's effect
RUNS = {l.split()[0]: l.split()[1] for l in open(here("brazil_runs.txt")) if l.strip()}
CHARGE = {"penalty": "flat penalty", "surcharge": "footprint surcharge"}[INST]
s = d[(d.instrument == INST) & (d.aez != "national")]
nat = d[(d.instrument == INST) & (d.aez == "national")].set_index("item")
AEZ = ["aez2", "aez3", "aez4", "aez5", "aez6", "aez12"]
AEZLAB = {"aez2": "AEZ 2\ndry\nsemi-arid", "aez3": "AEZ 3\nmoist\nsemi-arid", "aez4": "AEZ 4\nsub-humid", "aez5": "AEZ 5\nhumid",
          "aez6": "AEZ 6\nyear-round\nhumid", "aez12": "AEZ 12\ntemperate,\nyear-round"}
ZNAME = {2: "Dry semi-arid tropics", 3: "Moist semi-arid tropics", 4: "Sub-humid tropics", 5: "Humid tropics", 6: "Year-round humid tropics", 12: "Temperate, year-round"}
ROWS = [("forestland", "Forest", None), ("pastureland", "Pasture (cattle, dairy)", "qo_ruminant"), ("cropland", "Cropland", None),
        ("osd", "Soybeans, other oilseeds", "qo_osd"), ("gro", "Maize, other grains", "qo_gro"), ("c_b", "Sugar cane", "qo_c_b"),
        ("wht", "Wheat", "qo_wht"), ("pdr", "Rice", "qo_pdr"), ("v_f", "Vegetables, fruit", "qo_v_f"), ("pfb", "Cotton, other fibres", "qo_pfb"),
        ("ocr", "Coffee, cocoa, other crops", "qo_ocr")]
def cell(item, aez):
    if aez == "brasil":
        r = s[s.item == item]; return r["club_vs_bau_kha"].sum(), r["bau_level_kha"].sum()
    r = s[(s.item == item) & (s.aez == aez)].iloc[0]; return r["club_vs_bau_kha"], r["bau_level_kha"]
def pct(v, lvl): return 100 * v / lvl if lvl > 0 else np.nan
def out_pct(key):
    if key is None: return np.nan
    b, c = nat.loc[key, "stageB_change_kha"], nat.loc[key, "club_change_kha"]; return 100 * ((1 + c / 100) / (1 + b / 100) - 1)
def minus(t): return t.replace("-", "−")

MM = 1 / 25.4; W, H = 183.0, 96.0
FS_S, FS_M, FS_L = 6.3, 7.0, 8.0
fig = plt.figure(figsize=(W * MM, H * MM))
def ax_mm(l, t, w, h): return fig.add_axes([l / W, 1 - (t + h) / H, w / W, h / H])
def fx(x): return x / W
def fy(y): return 1 - y / H
def ftext(x, y, t, size=FS_S, color=INK2, ha="left", va="baseline", weight="normal", **kw):
    return fig.text(fx(x), fy(y), t, fontsize=size, color=color, ha=ha, va=va, fontweight=weight, **kw)
def letter(x, y, s_, title=None):
    ftext(x, y, s_, FS_L, INK, weight="bold")
    if title: ftext(x + 4.2, y, title, FS_M, INK)

# ---------------- a: the zones ----------------
ZC = {1: "#f7efd9", 2: "#efe0b4", 3: "#dcd48f", 4: "#b3cd85", 5: "#78b07a", 6: "#3b8a5e", 11: "#bfd0e6", 12: "#8fadd0"}
letter(2.0, 5.5, "a", "Brazil's agro-ecological zones")
g = gpd.read_file(here("brazil_aez.geojson")).to_crs("+proj=aea +lat_1=-5 +lat_2=-30 +lat_0=-15 +lon_0=-54")
axm = ax_mm(2.0, 8.0, 50.0, 50.0); axm.set_axis_off()
for _, r in g.iterrows(): gpd.GeoSeries([r.geometry]).plot(ax=axm, color=ZC.get(int(r.aez), "#eeeeee"), edgecolor=SURF, linewidth=0.3)
kept = {a: s[(s.item == "forestland") & (s.aez == a)]["club_vs_bau_kha"].iloc[0] / 1000 for a in ["aez4", "aez5", "aez6", "aez12"]}
KEPT_ALL = s[s.item == "forestland"]["club_vs_bau_kha"].sum() / 1000
from pyproj import Transformer
tr = Transformer.from_crs("EPSG:4326", g.crs, always_xy=True)
pos = {6: (-62, -4), 5: (-54.5, -13.5), 4: (-45.5, -12.5), 3: (-42.5, -5.5), 2: (-40.5, -10.2), 12: (-53.0, -29.5)}
for k, (lo, la) in pos.items():
    x, y = tr.transform(lo, la)
    axm.text(x, y, str(k), fontsize=7.5 if k != 2 else 5.8, color=SURF if k in (6, 5, 12) else INK, ha="center", va="center", weight="bold")
minx, miny, maxx, maxy = g.total_bounds; axm.set_xlim(minx - 3e4, maxx + 3e4); axm.set_ylim(miny - 3e4, maxy + 3e4); axm.set_aspect("equal")
axl = ax_mm(2.0, 59.0, 50.0, 24.0); axl.set_xlim(0, 50); axl.set_ylim(24, 0); axl.set_axis_off()
for i, k in enumerate([6, 5, 4, 3, 2, 12]):
    y = 1.0 + i * 3.4
    axl.add_patch(Rectangle((0.5, y), 2.6, 2.6, facecolor=ZC[k], edgecolor="none"))
    axl.text(4.2, y + 1.3, f"AEZ {k}", fontsize=FS_S, color=INK, ha="left", va="center", weight="bold")
    axl.text(13.0, y + 1.3, ZNAME[k], fontsize=5.8, color=INK2, ha="left", va="center")
    kv = kept.get(f"aez{k}")
    if kv: axl.text(50.0, y + 1.3, f"{kv:.1f} Mha kept" if kv >= 0.3 else f"{kv:.2f} Mha kept", fontsize=5.8, color=INK, ha="right", va="center")
import textwrap
for i, line in enumerate(textwrap.wrap(f"Kept: the clearing the baseline (the EUDR world) makes in five years, {KEPT_ALL:.1f} Mha in all. Zones: GTAP-AEZ, thermal zone \u00d7 length of growing period, from FAO GAEZ v4.", 58)):
    ftext(2.0, 84.5 + 2.7 * i, line, 5.6, MUTED)

# ---------------- b: the heatmap ----------------
letter(56.0, 5.5, "b", f"Land use at the club equilibrium ({CHARGE}) relative to the baseline")
X0, Y0 = 82.0, 21.0; CW, RH = 11.5, 5.0; COLS = AEZ + ["brasil"]
DIV = LinearSegmentedColormap.from_list("d", ["#d0531e", "#fbcbba", "#f0efec", "#bedaff", "#3280de"]); norm = TwoSlopeNorm(vcenter=0, vmin=-12, vmax=12)
axh = ax_mm(0, 0, W, H); axh.set_xlim(0, W); axh.set_ylim(H, 0); axh.set_axis_off(); axh.set_zorder(-1)
# column headers
for j, c in enumerate(COLS):
    x = X0 + j * CW + CW / 2
    if c == "brasil": axh.text(x, Y0 - 1.2, "Brazil", fontsize=FS_S, color=INK, ha="center", va="bottom", weight="bold")
    else: axh.text(x, Y0 - 1.2, AEZLAB[c], fontsize=5.6, color=INK, ha="center", va="bottom", linespacing=1.1)
axh.plot([X0, X0 + 5 * CW - 0.4], [Y0 - 10.4] * 2, color=BASE, linewidth=0.5); axh.text(X0 + 2.5 * CW, Y0 - 11.0, "tropical zones", fontsize=5.6, color=INK2, ha="center", va="bottom")
grid = {}
for i, (item, label, qo) in enumerate(ROWS):
    y = Y0 + i * RH
    axh.text(X0 - 1.5, y + RH / 2, label, fontsize=FS_S, color=INK if item in ("forestland", "pastureland", "cropland") else INK2, ha="right", va="center")
    for j, c in enumerate(COLS):
        v, lvl = cell(item, c); p = pct(v, lvl); grid[(item, c)] = (v, lvl, p)
        from matplotlib.colors import to_rgba
        face = DIV(norm(p)) if not np.isnan(p) else to_rgba(NEUTRAL)
        axh.add_patch(Rectangle((X0 + j * CW, y), CW - 0.4, RH - 0.4, facecolor=face, edgecolor="none"))
        lum = 0.299 * face[0] + 0.587 * face[1] + 0.114 * face[2]
        txt = "" if abs(v) < 0.5 else minus(f"{v:+,.0f}")
        axh.text(X0 + j * CW + CW / 2 - 0.2, y + RH / 2 - 0.2, txt, fontsize=5.8, color=SURF if lum < 0.55 else INK, ha="center", va="center")
    if item == "cropland": axh.plot([X0 - 26, X0 + len(COLS) * CW - 0.4], [y + RH + 0.3] * 2, color=BASE, linewidth=0.5)
# colour key
ck = ax_mm(X0, Y0 + len(ROWS) * RH + 3.5, 34.0, 1.8)
from matplotlib.cm import ScalarMappable
cb = fig.colorbar(ScalarMappable(norm=norm, cmap=DIV), cax=ck, orientation="horizontal", ticks=[-12, -6, 0, 6, 12])
cb.outline.set_visible(False); ck.tick_params(length=2.0, width=0.5, labelsize=5.8, colors=INK2, pad=1.2); cb.set_ticklabels(["−12", "−6", "0", "+6", "+12"])
ck.set_title("colour: % of the baseline level (EUDR world)", fontsize=5.8, color=INK2, pad=2)
ftext(X0 + 40.0, Y0 + len(ROWS) * RH + 5.5, "numbers: change in thousand hectares", 5.8, INK2, va="center")

# ---------------- c: national output ----------------
XC = X0 + len(COLS) * CW + 3.0; CWID = 15.0
letter(XC - 1.5, 5.5, "c", "Output")
axh.text(XC + CWID / 2, Y0 - 1.2, "Brazil, % vs\nthe baseline", fontsize=5.6, color=INK, ha="center", va="bottom", linespacing=1.1)
zero = XC + CWID * 0.75; scale = CWID * 0.7 / 3.5   # mm per % ; range -3.5 .. +1
axh.plot([zero] * 2, [Y0 - 0.5, Y0 + len(ROWS) * RH - 0.2], color=BASE, linewidth=0.5)
for i, (item, label, qo) in enumerate(ROWS):
    y = Y0 + i * RH; o = out_pct(qo)
    if np.isnan(o): continue
    x0, x1 = sorted([zero, zero + o * scale])
    axh.add_patch(Rectangle((x0, y + 0.9), x1 - x0, RH - 2.2, facecolor="#d0531e" if o < 0 else "#3280de", edgecolor="none"))
    axh.text((x0 - 0.8) if o < 0 else (x1 + 0.8), y + RH / 2 - 0.2, minus(f"{o:+.1f}"), fontsize=5.6, color=INK2, ha="right" if o < 0 else "left", va="center")

#ftext(56.0, H - 2.0, f"{LABEL} runs \u00b7 {RUNS.get(INST, '')}", 5.0, MUTED)   # no run-tag stamp in the published figure
fig.savefig(figpath("Fig5_brazil_aez.pdf")); fig.savefig(figpath("Fig5_brazil_aez.png"), dpi=450)
# source data: both instruments, every cell
with open(figpath("Fig5_source_data.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["instrument", "run", "item", "label", "zone", "level_2019_kha", "stageA_bau_clearing_change_kha", "stageB_eudr_change_kha", "baseline_level_kha", "club_change_from_stageA_kha", "club_vs_baseline_kha", "club_vs_baseline_pct"])
    for inst in sorted(set(d.instrument)):
        ss = d[(d.instrument == inst) & (d.aez != "national")]
        for item, label, qo in ROWS:
            for c in AEZ + ["aez1", "aez10", "aez11"]:
                r = ss[(ss.item == item) & (ss.aez == c)]
                if len(r) == 0: continue
                r = r.iloc[0]; w.writerow([inst, RUNS.get(inst, ""), item, label, c, round(r.level_2019_kha, 1), round(r.stageA_change_kha, 1), round(r.stageB_change_kha, 2), round(r.bau_level_kha, 1), round(r.club_change_kha, 1), round(r.club_vs_bau_kha, 1), round(pct(r.club_vs_bau_kha, r.bau_level_kha), 2)])
            r = ss[ss.item == item]; w.writerow([inst, RUNS.get(inst, ""), item, label, "brasil", round(r.level_2019_kha.sum(), 1), round(r.stageA_change_kha.sum(), 1), round(r.stageB_change_kha.sum(), 2), round(r.bau_level_kha.sum(), 1), round(r.club_change_kha.sum(), 1), round(r.club_vs_bau_kha.sum(), 1), round(pct(r.club_vs_bau_kha.sum(), r.bau_level_kha.sum()), 2)])
        nn = d[(d.instrument == inst) & (d.aez == "national")]
        for _, r in nn.iterrows(): w.writerow([inst, RUNS.get(inst, ""), r["item"], "output, % change (not kha)", "national", "", round(r.stageA_change_kha, 3), round(r.stageB_change_kha, 3), "", round(r.club_change_kha, 3), "", round(100 * ((1 + r.club_change_kha / 100) / (1 + r.stageB_change_kha / 100) - 1), 2)])
print("ok")
