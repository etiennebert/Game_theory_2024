"""Fig. 3: what the club delivers at convergence across the instrument plane (switching cost 0.1 % of trade).
a  tropical forest kept, b  members at convergence, c  world welfare (decision measure, net of the forest-land wedge term),
   for every simulated combination of footprint surcharge (x) and flat penalty (y), EU alone (circles) or EU + China (squares)
   charging; the dashed line is Brazil's fitted break-even (first-round loss = switching cost), one per seed.
d  the eight largest tropical deforesters: inside (filled) or outside (open) at convergence, same runs.
e  the headline club and coalition with Brazil, the United States (and, when run, the US + China or Indonesia) locked out.
Reads plane_runs_<label>.json, counterfactuals_<label>.json, all_data_<label>.json; writes Fig3_plane.png/.pdf and Fig3_plane_source_data.csv."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))   # the shared modules of the pipeline (paths, figstyle, mapping, v30)
import json, os, csv, math, textwrap
import numpy as np
from figstyle import *
from matplotlib.colors import LinearSegmentedColormap, Normalize, TwoSlopeNorm
from matplotlib.cm import ScalarMappable
from matplotlib.patches import Rectangle
style()
from paths import here, fig as figpath, LABEL
P = json.load(open(here("plane_runs.json")))
E = json.load(open(here("counterfactuals.json")))
D = json.load(open(here("all_data.json")))
BAUR = D["bau"]["bau_trop"]; BAU = D["bau"]["bau_trop_total"]; T_BRA = D["T"]["brasil"]
TOP = sorted(D["top"], key=lambda c: -BAUR[c])
Y_HEAD, X_HEAD = D["headline"]["penalty"], D["headline"]["surcharge"]

# ---- the plane's extent, from the runs (the penalty at 5 % sits above the plane and is footnoted)
XMAX = max(max(p["pha"] for p in P), X_HEAD); XMAX = int(math.ceil(XMAX / 1000.0) * 1000)
YMAX = 2.6 if max(p["tau"] for p in P if p["tau"] <= 3) <= 2.5 else math.ceil(max(p["tau"] for p in P)) + 0.1
SHOWN = [p for p in P if p["tau"] <= YMAX]; OFF = [p for p in P if p["tau"] > YMAX]
def fit(seed):
    Q = [p for p in P if p["seed"] == seed]
    if len(Q) < 3: return None
    X = np.array([[1, p["pha"], p["tau"]] for p in Q]); y = np.array([p["brazil_r1"] for p in Q])
    b = np.linalg.lstsq(X, y, rcond=None)[0]
    return b if b[1] > 0 and b[2] > 0 else None
def front(b): return (T_BRA - b[0]) / b[1], (T_BRA - b[0]) / b[2]      # x- and y-intercepts of the break-even line
B_EU, B_C = fit("EU"), fit("EUChina")
RATE = (B_EU[1] / B_EU[2] * 1000) if B_EU is not None else float("nan")   # points of penalty per 1,000 USD/ha

ROWS_E = [("All free to join", "free"), ("Brazil locked out", "lockBRA"), ("United States locked out", "lockUS"), ("US and China locked out", "lockUS-CN"), ("Indonesia locked out", "lockIDN")]
N_E = [sum(1 for _, suf in ROWS_E if f"{inst} {suf}" in E) for inst in ("pen", "sur")]      # rows of panel e on the disk, per block
RH_E = 4.3
E_TOP, E_H = 161.0, 16.0 + sum(4.2 + n * RH_E + 1.4 for n in N_E if n) + 3.5                  # the panel's height follows its rows
N_FOOT = 3
MM = 1 / 25.4; W, H = 183.0, E_TOP + E_H + 2.9 * N_FOOT + 3.0
BEEF = 8.1 / 4000 * 100   # % tariff on Brazilian beef per 100 USD/ha (AVE 8.1 % at 4,000 USD/ha)
FS_S, FS_M, FS_L = 6.3, 7.0, 8.0
GREEN = "#349130"; BLUE = "#3280de"; ORANGE = "#d0531e"
fig = plt.figure(figsize=(W * MM, H * MM))
def ax_mm(l, t, w, h): return fig.add_axes([l / W, 1 - (t + h) / H, w / W, h / H])
def fx(x): return x / W
def fy(y): return 1 - y / H
def ftext(x, y, s, size=FS_S, color=INK2, ha="left", va="baseline", weight="normal", **kw):
    return fig.text(fx(x), fy(y), s, fontsize=size, color=color, ha=ha, va=va, fontweight=weight, **kw)
def letter(x, y, s, title=None):
    ftext(x, y, s, FS_L, INK, weight="bold")
    if title: ftext(x + 4.2, y, title, FS_M, INK)
def usd(v): return f"{int(round(v)):,}"
def minus(s): return s.replace("-", "−")
XT = list(range(0, XMAX + 1, 2000 if XMAX > 6000 else 1000)); YT = [0, 0.5, 1.0, 1.5, 2.0, 2.5] if YMAX <= 2.7 else list(np.arange(0, YMAX, 1.0))
def plane(ax, small=False):
    ax.set_xlim(-0.04 * XMAX, XMAX * 1.04); ax.set_ylim(-0.04 * YMAX, YMAX)
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_position(("outward", 2.5)); ax.spines[s].set_linewidth(0.6); ax.spines[s].set_color(BASE)
    ax.spines["bottom"].set_bounds(0, XMAX); ax.spines["left"].set_bounds(0, YT[-1])
    ax.tick_params(length=2.0, width=0.6, colors=INK2, labelsize=FS_S if not small else 5.8, pad=1.5)
    xt = XT if not small else [0, XMAX // 2, XMAX]; yt = YT if not small else [0, YT[len(YT) // 2], YT[-1]]
    ax.set_xticks(xt); ax.set_xticklabels([usd(t) for t in xt]); ax.set_yticks(yt); ax.set_yticklabels([f"{t:g}" for t in yt])
    for gx in xt: ax.plot([gx, gx], [0, YT[-1]], color=GRID, linewidth=0.4, zorder=0)
    for gy in yt: ax.plot([0, XMAX], [gy, gy], color=GRID, linewidth=0.4, zorder=0)
    if not small:
        sec = ax.secondary_xaxis("top", functions=(lambda x: x * BEEF / 100, lambda p: p * 100 / BEEF))
        st = list(range(0, int(XMAX * BEEF / 100) + 1, 4)); sec.set_xticks(st); sec.set_xticklabels([str(t) for t in st])
        sec.tick_params(length=2.0, width=0.6, colors=INK2, labelsize=5.8, pad=1.2)
        sec.spines["top"].set_position(("outward", 2.5)); sec.spines["top"].set_linewidth(0.6); sec.spines["top"].set_color(BASE); sec.spines["top"].set_bounds(0, st[-1])
        sec.set_xlabel("same charge as a tariff on Brazilian beef (%)", fontsize=5.8, labelpad=1.5, color=INK2)
    for b in (B_EU, B_C):
        if b is None: continue
        x0, y0 = front(b); ax.plot([0, min(x0, XMAX)], [y0, max(0.0, y0 * (1 - XMAX / x0))], color=BASE, linewidth=0.7, linestyle=(0, (2.5, 1.8)), zorder=1)
def draw_points(ax, value, cmap, norm, s=54):
    for o in sorted(SHOWN, key=lambda o: (o["pha"], o["tau"])):
        mk = "o" if o["seed"] == "EU" else "s"; ss = s if mk == "o" else s * 0.8
        ax.scatter([o["pha"]], [o["tau"]], s=ss * 1.45, marker=mk, color=SURF, edgecolor="none", zorder=4, clip_on=False)
        ax.scatter([o["pha"]], [o["tau"]], s=ss, marker=mk, color=cmap(norm(value(o))), edgecolor=INK2, linewidth=0.5, zorder=5, clip_on=False)
GREEN_CM = LinearSegmentedColormap.from_list("g", ["#eef5ec", "#a5dc9f", "#6dba67", "#349130", "#006500"])
BLUE_CM = LinearSegmentedColormap.from_list("b", ["#eef2f8", "#9ec5f4", "#5598e7", "#2a78d6", "#0d366b"])
DIV_CM = LinearSegmentedColormap.from_list("d", [ORANGE, "#fbcbba", "#f0efec", "#bedaff", BLUE])
wmin = min(o["world"] for o in P) / 1000; wmax = max(o["world"] for o in P) / 1000
WLO = -math.ceil(-wmin) if wmin < 0 else -0.5; WHI = max(0.5, math.ceil(wmax * 2) / 2)

# ---------------- key row ----------------
KY = 3.6
axk = fig.add_axes([fx(2.0), fy(KY + 1.1), 2.4 / W, 2.2 / H]); axk.set_axis_off(); axk.scatter([0.5], [0.5], s=40, color=SURF, edgecolor=INK2, linewidth=0.6); axk.set_xlim(0, 1); axk.set_ylim(0, 1)
ftext(5.4, KY, "EU alone charging", va="center")
axk2 = fig.add_axes([fx(33.0), fy(KY + 1.1), 2.4 / W, 2.2 / H]); axk2.set_axis_off(); axk2.scatter([0.5], [0.5], s=32, marker="s", color=SURF, edgecolor=INK2, linewidth=0.6); axk2.set_xlim(0, 1); axk2.set_ylim(0, 1)
ftext(36.4, KY, "EU + China charging", va="center")
fig.lines.append(plt.Line2D([fx(63.0), fx(68.0)], [fy(KY), fy(KY)], transform=fig.transFigure, color=BASE, linewidth=0.7, linestyle=(0, (2.5, 1.8))))
ftext(69.5, KY, f"Brazil's break-even, fitted on its first-round loss (= switching cost of {T_BRA:.0f} M USD); reference only", va="center")

# ---------------- row 1: outcome planes ----------------
TOP1, PW, PH = 19.0, 50.0, 42.0; XS = [12.0, 70.0, 128.0]
IN = [o for o in SHOWN if o["works"]]; OUT = [o for o in SHOWN if not o["works"]]
def rng(vals, f):
    lo, hi = min(vals), max(vals); return f(lo) if f(lo) == f(hi) else f"{f(lo)}–{f(hi)}"
def rng_signed(vals):
    def f(v): return minus(f"{v:+.1f}")
    lo, hi = min(vals), max(vals); return f"{f(lo)} to {f(hi)}"
specs = [("a", "Tropical forest kept over five years", lambda o: o["forest"], GREEN_CM, Normalize(0, 20), f"Mha (of {BAU:.1f} Mha of business-as-usual clearing)", [0, 5, 10, 15, 20], ["0", "5", "10", "15", "20"],
          rng([o["forest"] for o in IN], lambda v: f"{v:.1f}") + " Mha", ("≤ " + f"{max(o['forest'] for o in OUT):.1f}" + " Mha") if OUT else ""),
         ("b", "Members at convergence", lambda o: o["n"], BLUE_CM, Normalize(0, 42), "regions (of 42)", [0, 10, 20, 30, 40], ["0", "10", "20", "30", "40"],
          rng([o["n"] for o in IN], str) + " regions", (rng([o["n"] for o in OUT], str) + " regions") if OUT else ""),
         ("c", "World welfare change", lambda o: o["world"] / 1000, DIV_CM, TwoSlopeNorm(vcenter=0, vmin=WLO, vmax=WHI), "bn USD per year relative to the EUDR world", None, None,
          rng_signed([o["world"] / 1000 for o in IN]) + " bn", (rng_signed([o["world"] / 1000 for o in OUT]) + " bn") if OUT else "")]
for (let, title, val, cm, norm, unit, ticks, tlabels, lab_in, lab_out), x0 in zip(specs, XS):
    letter(x0 - 10.0, 11.0, let, title)
    ax = ax_mm(x0, TOP1, PW, PH); plane(ax); draw_points(ax, val, cm, norm)
    ax.set_xlabel("Footprint surcharge (USD per hectare deforested)", fontsize=FS_S, labelpad=2.5, color=INK)
    if x0 == XS[0]: ax.set_ylabel("Flat penalty (%)", fontsize=FS_S, labelpad=2.5, color=INK)
    ax.text(XMAX, YMAX * 0.97, "Brazil inside", fontsize=6.0, color=INK2, ha="right", va="top", zorder=6)
    ax.text(XMAX, YMAX * 0.91, lab_in, fontsize=6.0, color=INK, ha="right", va="top", zorder=6)
    if OUT:
        ax.text(XMAX * 0.42, YMAX * 0.40, "Brazil outside", fontsize=6.0, color=INK2, ha="left", va="top", zorder=6)
        ax.text(XMAX * 0.42, YMAX * 0.34, lab_out, fontsize=6.0, color=INK, ha="left", va="top", zorder=6)
    cax = ax_mm(x0 + 12.0, TOP1 + PH + 10.0, PW - 24.0, 1.8)
    if ticks is None: ticks = sorted(set([WLO, 0, WHI] + ([WLO / 2] if WLO < -0.9 else []))); tlabels = [minus(f"{t:g}") for t in ticks]
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cm), cax=cax, orientation="horizontal", ticks=ticks)
    cb.outline.set_visible(False); cax.tick_params(length=2.0, width=0.5, labelsize=5.8, colors=INK2, pad=1.2); cb.set_ticklabels(tlabels)
    cax.set_title(unit, fontsize=5.8, color=INK2, pad=2)

# ---------------- row 2: the eight largest deforesters ----------------
letter(2.0, 86.0, "d", "The eight largest tropical deforesters at convergence: inside (filled) or outside (open)")
MW, MH = 36.0, 22.0; XS2 = [12.0, 55.3, 98.7, 142.0]; YS2 = [91.0, 126.0]
for k, c in enumerate(TOP):
    ax = ax_mm(XS2[k % 4], YS2[k // 4], MW, MH); plane(ax, small=True)
    for o in SHOWN:
        mk = "o" if o["seed"] == "EU" else "s"; inside = c in o["top_in"]
        if inside: ax.scatter([o["pha"]], [o["tau"]], s=22 if mk == "o" else 18, marker=mk, color=GREEN, edgecolor=SURF, linewidth=0.5, zorder=5, clip_on=False)
        else: ax.scatter([o["pha"]], [o["tau"]], s=22 if mk == "o" else 18, marker=mk, facecolor=SURF, edgecolor="#898781", linewidth=0.8, zorder=5, clip_on=False)
    ax.set_title(f"{NAMES[c]}  ·  {BAUR[c]:.1f} Mha", fontsize=FS_S, color=INK, loc="left", pad=3)
    if k % 4 == 0: ax.set_ylabel("Penalty (%)", fontsize=5.8, labelpad=2, color=INK2)
    if k // 4 == 1: ax.set_xlabel("Surcharge (USD per ha deforested)", fontsize=5.8, labelpad=2, color=INK2)

# ---------------- row 3: the thresholds with a region locked out ----------------
letter(2.0, 158.5, "e", "The headline club and coalition when a region refuses to join")
axe = ax_mm(0, E_TOP, W, E_H); axe.set_xlim(0, W); axe.set_ylim(E_H, 0); axe.set_axis_off()
XL, XSTRIP, PITCH, SQ = 12.0, 53.0, 2.55, 2.0
XF0, FSCALE = 82.0, 2.2
XN = 134.0
WMIN_E = min(-0.5, math.floor(min(v["world"] for v in E.values()) / 1000)); WMAX_E = max(0.5, math.ceil(max(v["world"] for v in E.values()) / 1000))
XW0, WSCALE = 146.0, 30.0 / (WMAX_E - WMIN_E)
def xw(v): return XW0 + (v - WMIN_E) * WSCALE
def etext(x, y, s, size=5.8, color=INK2, ha="left", va="center", **kw): axe.text(x, y, s, fontsize=size, color=color, ha=ha, va=va, **kw)
YH = 11.5
for k, c in enumerate(TOP):
    axe.text(XSTRIP + k * PITCH + SQ / 2 + 0.3, YH - 1.2, NAMES[c], fontsize=5.3, color=INK2, ha="left", va="bottom", rotation=55, rotation_mode="anchor")
etext(XF0, YH - 1.0, "Tropical forest kept (Mha)", va="bottom", color=INK)
etext(XN, YH - 1.0, "Members", va="bottom", color=INK, ha="center")
etext(xw(WMIN_E), YH - 1.0, "World welfare (bn USD per year)", va="bottom", color=INK, ha="left")
for t in (0, 5, 10, 15, 20):
    axe.plot([XF0 + t * FSCALE] * 2, [YH + 1.0, YH + 2.0], color=BASE, linewidth=0.5); etext(XF0 + t * FSCALE, YH + 0.6, str(t), size=5.3, ha="center", va="bottom")
wt = sorted(set([WMIN_E, 0, WMAX_E] + [t for t in np.arange(WMIN_E, WMAX_E + 0.01, 1.0)]))
for t in wt:
    axe.plot([xw(t)] * 2, [YH + 1.0, YH + 2.0], color=BASE, linewidth=0.5); etext(xw(t), YH + 0.6, minus(f"{t:g}") if t else "0", size=5.3, ha="center", va="bottom")
axe.plot([XF0, XF0 + 20 * FSCALE], [YH + 2.0, YH + 2.0], color=BASE, linewidth=0.5); axe.plot([xw(WMIN_E), xw(WMAX_E)], [YH + 2.0, YH + 2.0], color=BASE, linewidth=0.5)
blocks = [(f"Flat penalty of {Y_HEAD:g} %", "pen"), (f"Footprint surcharge of {usd(X_HEAD)} USD per hectare", "sur")]
y = YH + 4.5; RH = RH_E; BH = 2.4
for title, inst in blocks:
    etext(XL, y, title, size=FS_S, color=INK, weight="bold"); y += 4.2
    for label, suf in ROWS_E:
        key = f"{inst} {suf}"
        if key not in E: continue
        r = E[key]
        etext(XL + 2.0, y, label, color=INK2)
        for k, c in enumerate(TOP):
            inside = c in r["top_in"]; x = XSTRIP + k * PITCH
            axe.add_patch(Rectangle((x, y - SQ / 2), SQ, SQ, facecolor=GREEN if inside else SURF, edgecolor=GREEN if inside else "#898781", linewidth=0.6))
        for t in (5, 10, 15, 20): axe.plot([XF0 + t * FSCALE] * 2, [y - RH / 2 + 0.3, y + RH / 2 - 0.3], color=GRID, linewidth=0.4, zorder=0)
        axe.plot([xw(0)] * 2, [y - RH / 2 + 0.3, y + RH / 2 - 0.3], color=BASE, linewidth=0.5, zorder=0)
        axe.add_patch(Rectangle((XF0, y - BH / 2), max(r["forest"], 0) * FSCALE, BH, facecolor=GREEN if suf == "free" else "#6dba67", edgecolor="none", zorder=2))
        etext(XF0 + max(r["forest"], 0) * FSCALE + 1.0, y, f"{r['forest']:.1f}", color=INK)
        etext(XN, y, str(r["n"]), color=INK, ha="center")
        w = r["world"] / 1000
        axe.add_patch(Rectangle((xw(min(w, 0)), y - BH / 2), abs(w) * WSCALE, BH, facecolor=BLUE if w >= 0 else ORANGE, edgecolor="none", zorder=2))
        if w >= 0: etext(xw(w) + 1.0, y, minus(f"{w:+.2f}"), color=INK)
        else: etext(xw(w) - 1.0, y, minus(f"{w:+.2f}"), color=INK, ha="right")
        y += RH
    y += 1.4
axe.plot([XF0 + BAU * FSCALE] * 2, [YH + 2.0, y - 2.2], color=INK2, linewidth=0.5, linestyle=(0, (2, 1.5)), zorder=1)
etext(XF0 + BAU * FSCALE, y - 1.6, f"business-as-usual clearing, {BAU:.1f} Mha", size=5.3, ha="center", va="top")

# ---------------- footnotes ----------------
extra = "".join(" The run at %g %% (%d members, %.1f Mha, %s bn USD) lies above the plane." % (o["tau"], o["n"], o["forest"], minus("%+.1f" % (o["world"] / 1000))) for o in OFF)
note = (f"{LABEL} runs. a-c: the dashed lines are Brazil's fitted break-even, EU alone" + (f" ({RATE:.2f} points of penalty per 1,000 USD per hectare)" if RATE == RATE else "") + " and EU + China. d: business-as-usual clearing over five years in each title." + extra +
        " e: a locked-out region is an outsider at every decision. Filled squares: inside at convergence, in the order of d. Welfare on the decision measure (net of the forest-land wedge term).")
lines = textwrap.wrap(note, 163)
if len(lines) > N_FOOT: print(f"  note: the footnote has {len(lines)} lines, {N_FOOT} planned")
for i, line in enumerate(lines): ftext(2.0, H - 1.5 - 2.9 * (len(lines) - 1 - i), line, color=MUTED)   # bottom-anchored, never clipped

fig.savefig(figpath("Fig3_plane.pdf")); fig.savefig(figpath("Fig3_plane.png"), dpi=450)
with open(figpath("Fig3_plane_source_data.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["panel", "seed", "locked_out", "surcharge_usd_per_ha", "penalty_pct", "rounds_to_convergence", "members", "brazil_inside",
                "tropical_forest_kept_Mha", "tropical_leakage_Mha", "world_EV_net_MUSD_per_yr", "world_EV_gross_MUSD_per_yr", "members_EV_MUSD_per_yr", "outsiders_EV_MUSD_per_yr",
                "EU_EV_MUSD_per_yr", "Brazil_EV_MUSD_per_yr", "China_EV_MUSD_per_yr", "US_EV_MUSD_per_yr", "Brazil_first_round_loss_MUSD"] + [f"{NAMES[c]}_inside" for c in TOP])
    for o in sorted(P, key=lambda o: (o["seed"], o["tau"], o["pha"])):
        w.writerow(["a-d", "EU alone" if o["seed"] == "EU" else "EU + China", "", o["pha"], o["tau"], o["rounds"], o["n"], int(o["works"]),
                    round(o["forest"], 3), round(o["leakage"], 3), round(o["world"], 1), "" if o["world_gross"] is None else round(o["world_gross"], 1), round(o["members_ev"], 1), round(o["outsiders_ev"], 1),
                    round(o["eu"], 1), round(o["brasil"], 1), round(o["china"], 1), round(o["us"], 1), round(o["brazil_r1"], 1)] + [int(c in o["top_in"]) for c in TOP])
    for key, r in E.items():
        if r["lock"] == "": continue
        w.writerow(["e", "EU alone", r["lock"], r["pha"], r["tau"], r["rounds"], r["n"], int("brasil" in r["members"]), round(r["forest"], 3), round(r["leakage"], 3), round(r["world"], 1),
                    "" if r["world_gross"] is None else round(r["world_gross"], 1), "", "", round(r["eu"], 1), round(r["brasil"], 1), round(r["china"], 1), round(r["us"], 1), ""] + [int(c in r["top_in"]) for c in TOP])
print("ok", "rate", round(RATE, 3) if RATE == RATE else None)
