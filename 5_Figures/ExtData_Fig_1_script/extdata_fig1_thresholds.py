"""Extended Data Fig. 1 - what it takes for the EU alone to start the Forest Club: Brazil's first-round loss against the charge,
the switching cost as the rule, and the club just below and just above each threshold.

a  Brazil's first-round loss (M USD per year) against the flat penalty (left) and the footprint surcharge (right), every EU-alone
   run on the disk with one instrument; the loss does not depend on the switching cost, so runs at every switching cost pool on
   one curve. Brazil's switching cost at each share of trade simulated is a rule; on each rule the observed switch - the highest
   failing and the lowest working charge - is a thick segment (open = no club, filled = the club forms with Brazil inside).
b  Members at convergence just below and just above each threshold, and the number of regions joining.
c  Tropical forest kept over five years, same rows.
Everything comes from all_data_<label>.json: the switching costs present, the brackets, the EU + China rows. A threshold with
only one side on the disk (no failing run yet) is drawn with that side alone. Writes ExtData_Fig1_thresholds.png/.pdf and
ExtData_Fig1_source_data.csv."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))   # the shared modules of the pipeline (paths, figstyle, mapping, v30)
import json, csv, math
import numpy as np
from figstyle import *
style()
from paths import here, fig as figpath, LABEL
D = json.load(open(here("all_data.json"))); C = D["configs"]; T = D["T"]; N_REG = len(T)
BAU = sum(v for v in D["bau"]["bau_trop"].values() if v > 0); EUDR = D["bau"]["eudr_trop_total"]

# ------------------------------------------------------------------ data
def inst_of(r):
    if r["pha"] > 0 and r["tau"] == 0: return "surcharge"
    if r["tau"] > 0 and r["pha"] == 0: return "penalty"
    return "combined" if r["pha"] > 0 else "none"
RUNS = [dict(r, inst=inst_of(r), x=(r["tau"] if inst_of(r) == "penalty" else r["pha"])) for r in D["runs"] if r["seed"] == "EU" and not r["lock"] and not r["fixed"]]
FR = sorted({r["fr"] for r in RUNS}); FRLAB = {fr: f"{100 * fr:g}" for fr in FR}
TB = {fr: T["brasil"] * fr / 0.001 for fr in FR}                      # Brazil's switching cost (M USD per year) at each share of trade
def bracket(runs, inst, fr=None):
    rs = sorted([r for r in runs if r["inst"] == inst and (fr is None or abs(r["fr"] - fr) < 1e-12)], key=lambda r: r["x"])
    fails = [r for r in rs if not r["works"] and r["converged"]]; works = [r for r in rs if r["works"]]   # a run at the round cap is neither
    f = max(fails, key=lambda r: r["x"]) if fails else None; w = min(works, key=lambda r: r["x"]) if works else None
    if f and w and f["x"] > w["x"]: print(f"  WARNING: non-monotone outcome for {inst} at fr {fr}: fails at {f['x']} above a working {w['x']}")
    return f, w
BRK = {(i, fr): bracket(RUNS, i, fr) for i in ("penalty", "surcharge") for fr in FR}
RUNS_C = [dict(r, inst=inst_of(r), x=(r["tau"] if inst_of(r) == "penalty" else r["pha"])) for r in D["runs"] if r["seed"] == "EUChina" and not r["lock"] and not r["fixed"] and abs(r["fr"] - 0.001) < 1e-12]
BRK_C = {i: bracket(RUNS_C, i) for i in ("penalty", "surcharge")}
r1 = {k: sorted({(r["x"], round(r["brazil_r1_loss"], 3)) for r in RUNS if r["inst"] == k}) for k in ("penalty", "surcharge")}
for k in r1:   # the loss is independent of the switching cost: one value per charge
    xs = [x for x, _ in r1[k]]
    if len(xs) != len(set(xs)): print(f"  WARNING: Brazil's first-round loss differs across switching costs at the same {k}:", [(x, y) for x, y in r1[k] if xs.count(x) > 1])
CASES = [("Flat penalty, EU alone", None, None)] + [(FRLAB[fr], BRK[("penalty", fr)], fr) for fr in FR if any(BRK[("penalty", fr)])]
CASES += [("Footprint surcharge, EU alone", None, None)] + [(FRLAB[fr], BRK[("surcharge", fr)], fr) for fr in FR if any(BRK[("surcharge", fr)])]
if any(any(v) for v in BRK_C.values()):
    CASES.append(("EU + China charging, 0.1%", None, None))
    for i in ("penalty", "surcharge"):
        if any(BRK_C[i]): CASES.append(("0.1", BRK_C[i], "C"))
MAX_FAIL = max([r["forest"] for r in RUNS + RUNS_C if not r["works"] and r["converged"]] + [0.0])
UNSETTLED = [r for r in RUNS + RUNS_C if not r["converged"] and r["inst"] in ("penalty", "surcharge")]   # reached the round cap: shown in a, footnoted
XP = min(3.0, max(x for x, _ in r1["penalty"])) if r1["penalty"] else 2.0; XS = max([x for x, _ in r1["surcharge"]] + [4000])
off_p = [(x, y) for x, y in r1["penalty"] if x > XP + 1e-9]           # penalties beyond the axis (5 %): footnoted

# ------------------------------------------------------------------ canvas and helpers
import textwrap
dag = ""
if UNSETTLED:
    dag = " † " + "; ".join(f"{'EU alone' if u['seed'] == 'EU' else 'EU + China'}, {u['x']:g}{'%' if u['inst'] == 'penalty' else ' USD/ha'} at {100 * u['fr']:g}% of trade: the round cap ({u['last']} rounds) was reached with {u['n']} members and Brazil {'inside' if 'brasil' in u['final_members'] else 'outside'}, no settled club" for u in UNSETTLED) + "."
FOOT = textwrap.wrap(f"Forest kept relative to the EUDR world (Stage B); the EUDR alone keeps {EUDR:.3f} Mha of the {BAU:.1f} Mha of business-as-usual tropical clearing.{dag}", 168)
MM = 1 / 25.4; W = 183.0; ROW = 4.2; C_TOP = 80.0; H = C_TOP + ROW * len(CASES) + 12.5 + 2.9 * len(FOOT)
COL = dict(zip(FR, (BLUE3 if len(FR) <= 3 else ["#9cc3f0", "#4a8de0", "#1a4f9c", "#061a36"])[:len(FR)])); COL1 = COL.get(0.001, BLUE3[1]); ORANGE = "#eb6834"; GREEN = "#349130"   # four costs (the 1 % bracket): a four-step ramp
FS_S, FS_M, FS_L = 6.3, 7.0, 8.0
fig = plt.figure(figsize=(W * MM, H * MM))
def ax_mm(l, t, w, h): return fig.add_axes([l / W, 1 - (t + h) / H, w / W, h / H])
def fx(x): return x / W
def fy(y): return 1 - y / H
def ftext(x, y, s, size=FS_S, color=INK2, ha="left", va="baseline", weight="normal", **kw):
    return fig.text(fx(x), fy(y), s, fontsize=size, color=color, ha=ha, va=va, fontweight=weight, **kw)
def letter(x, y, s, title=None):
    ftext(x, y, s, FS_L, INK, weight="bold")
    if title: ftext(x + 4.2, y, title, FS_M, INK)
def spines(ax, offset=2.0):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_position(("outward", offset)); ax.spines[s].set_linewidth(0.6); ax.spines[s].set_color(BASE)
    ax.tick_params(length=2.2, width=0.6, colors=INK2, labelsize=FS_S, pad=1.8)
def marker(ax, x, y, col, works, s=20, z=6, clip=False):
    if works: ax.scatter([x], [y], s=s, color=col, edgecolor=SURF, linewidth=0.5, zorder=z, clip_on=clip)
    else: ax.scatter([x], [y], s=s, facecolor=SURF, edgecolor=col, linewidth=1.0, zorder=z, clip_on=clip)
def usd(v): return f"{int(round(v)):,}"

# ============================ key (one row) ============================
KY = 3.6
def key_marker(x, works):
    axk = fig.add_axes([fx(x - 1.1), fy(KY + 1.1), 2.2 / W, 2.2 / H]); axk.set_axis_off(); axk.set_xlim(0, 1); axk.set_ylim(0, 1)
    marker(axk, 0.5, 0.5, INK2, works, s=20)
key_marker(2.9, False); ftext(4.9, KY, "No club (Brazil stays out)", va="center")
key_marker(34.5, True); ftext(36.5, KY, "Club forms (Brazil joins)", va="center")
hdr = "Switching cost, % of trade (Brazil, M USD per year):" if len(FR) <= 3 else "Switching cost, % of trade (Brazil, M USD/yr):"
ftext(63.5, KY, hdr, va="center")
x0 = 63.5 + 1.05 * len(hdr) + 2.5 if len(FR) > 3 else 121.6
cw, gap = (1.05, 2.0) if len(FR) > 3 else (1.12, 3.0)
for fr in FR:
    fig.lines.append(plt.Line2D([fx(x0), fx(x0 + 4.0)], [fy(KY), fy(KY)], transform=fig.transFigure, color=COL[fr], linewidth=3.0, solid_capstyle="butt"))
    lab = f"{FRLAB[fr]}% ({TB[fr]:.0f})"; ftext(x0 + 4.8, KY, lab, va="center"); x0 += 4.8 + cw * len(lab) + gap

# ============================ a: Brazil's first-round loss ============================
letter(2.0, 11.0, "a", "Brazil's first-round loss, EU alone charging: the switching cost decides under the penalty, the surcharge recruits Brazil below it")
YMAX = max([y for k in r1 for x, y in r1[k] if (k == "surcharge" or x <= XP + 1e-9)] + list(TB.values()) + [100]); YTOP = math.ceil(YMAX / 50) * 50 + 20
pticks = [t / 2 for t in range(0, int(XP * 2) + 1)]
# log axes when a bracket lies beyond the linear planes (the 1 % of trade bracket, 27 Oct 2026: penalties above 3 %, surcharges above 12,000 USD/ha); EDF1_LOG=1|0 forces
LOG = {"1": True, "0": False}.get(os.environ.get("EDF1_LOG", "auto"), any(r["x"] > 3.0 for i, fr in BRK if i == "penalty" for r in BRK[(i, fr)] if r) or any(r["x"] > 12000 for i, fr in BRK if i == "surcharge" for r in BRK[(i, fr)] if r))
if LOG:
    XP = max([x for x, _ in r1["penalty"]] + [3.0]); off_p = []
    def _lim(vals, lo, cands): hi = max(vals); return lo, next((c for c in cands if c >= hi * 1.15), hi * 1.3)
    PX = _lim([x for x, _ in r1["penalty"]], 0.2, [3, 5, 10, 20, 30, 50]); SX = _lim([x for x, _ in r1["surcharge"]], 200, [5000, 10000, 20000, 50000, 100000, 200000])
    YL = (max(5.0, min(min(y for k in r1 for _, y in r1[k]), min(TB.values())) / 1.5), max(max(y for k in r1 for _, y in r1[k]), max(TB.values())) * 1.6)
    LT = {"penalty": [t for t in (0.25, 0.5, 1, 2, 5, 10, 20, 50) if PX[0] <= t <= PX[1]], "surcharge": [t for t in (250, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000) if SX[0] <= t <= SX[1]]}
    YLT = [t for t in (5, 10, 20, 50, 100, 200, 500, 1000, 2000) if YL[0] <= t <= YL[1]]
for i, (inst, left, xmax, ticks, tlab, xlab) in enumerate((("penalty", 14.0, XP, pticks, [f"{t:g}" for t in pticks], "Flat penalty (%)"),
        ("surcharge", 106.0, XS, list(range(0, int(XS) + 1, 1000 if XS <= 6000 else 2000)), None, "Footprint surcharge (USD per hectare)"))):
    if tlab is None: tlab = [usd(t) for t in ticks]
    axb = ax_mm(left, 15.0, 73.0, 40.0)
    if LOG:
        lo, hi = PX if inst == "penalty" else SX; ticks = LT[inst]; tlab = [f"{t:g}" if inst == "penalty" else usd(t) for t in ticks]
        axb.set_xscale("log"); axb.set_yscale("log"); axb.set_xlim(lo, hi); axb.set_ylim(*YL); spines(axb)
        axb.spines["bottom"].set_bounds(lo, hi); axb.spines["left"].set_bounds(*YL)
        axb.set_xticks(ticks); axb.set_xticklabels(tlab); axb.set_yticks(YLT); axb.set_yticklabels([str(t) for t in YLT])
        axb.xaxis.set_minor_locator(plt.NullLocator()); axb.yaxis.set_minor_locator(plt.NullLocator()); xmax = hi
    else:
        axb.set_xlim(-0.02 * xmax, xmax * 1.03); axb.set_ylim(-45, YTOP); spines(axb)
        axb.spines["bottom"].set_bounds(0, xmax); axb.spines["left"].set_bounds(-40, YTOP - 20)
        axb.set_xticks(ticks); axb.set_xticklabels(tlab); axb.set_yticks(list(range(0, YTOP - 19, 50)))
        axb.axhline(0, color=BASE, linewidth=0.5, zorder=1)
    for fr in FR:
        axb.axhline(TB[fr], color=COL[fr], linewidth=0.75, zorder=2)
        f, w = BRK[(inst, fr)]
        if f and w: axb.plot([f["x"], w["x"]], [TB[fr]] * 2, color=COL[fr], linewidth=3.0, solid_capstyle="butt", zorder=4)   # the bracket, on the rule
        if f: marker(axb, f["x"], f["brazil_r1_loss"], COL[fr], False, s=20, z=5)   # the runs themselves sit on the curve, at Brazil's actual first-round loss
        if w: marker(axb, w["x"], w["brazil_r1_loss"], COL[fr], True, s=20, z=5)
    for u in [u for u in UNSETTLED if u["inst"] == inst and u["seed"] == "EU" and u["x"] <= xmax + 1e-9]:
        axb.scatter([u["x"]], [u["brazil_r1_loss"]], s=20, facecolor=NEUTRAL, edgecolor=COL[u["fr"]], linewidth=1.0, zorder=5, clip_on=False)
        axb.text(u["x"], u["brazil_r1_loss"] * (1.12 if LOG else 1) + (0 if LOG else 9), "†", fontsize=FS_S, color=COL[u["fr"]], ha="center", va="bottom")
    pts = [(x, y) for x, y in r1[inst] if x <= xmax + 1e-9 and (not LOG or (x > 0 and y > 0))]
    if pts:
        x, y = zip(*pts); axb.plot(x, y, color=INK2, linewidth=1.0, zorder=3); axb.scatter(x, y, s=6, color=INK2, zorder=3)
    axb.set_xlabel(xlab + (" (log scale)" if LOG else ""), fontsize=FS_M, labelpad=2, color=INK)
    if i == 0:
        axb.set_ylabel("Brazil's first-round loss\n(M USD per year" + (", log scale)" if LOG else ")"), fontsize=FS_M, labelpad=3, color=INK)
        if off_p: axb.text(0.02 * xmax, YTOP - 28, "off scale: " + ", ".join(f"{x:g}% → {y:.0f}" for x, y in off_p), fontsize=FS_S, color=MUTED, va="top")
    else:
        if LOG: axb.text(0.02, 0.84, "Open and filled points: the highest failing and\nthe lowest working charge at each switching cost\n(b, c), at Brazil's loss in that run; the bar on\nthe rule is the bracket", fontsize=FS_S, color=MUTED, va="top", ha="left", linespacing=1.15, transform=axb.transAxes)
        else: axb.text(0.02, 0.97, "Open and filled points: the highest failing and the lowest working\ncharge at each switching cost (b, c), at Brazil's loss in that run;\nthe bar on the rule is the bracket", fontsize=FS_S, color=MUTED, va="top", ha="left", linespacing=1.15, transform=axb.transAxes)

# ============================ b, c: what changes when Brazil joins ============================
n_rows = len(CASES); C_H = ROW * n_rows
letter(2.0, C_TOP - 9.5, "b", "What changes when Brazil joins")
letter(121.0, C_TOP - 9.5, "c")
def row_y(i): return C_TOP + ROW * (i + 0.5)
ftext(2.0, C_TOP - 4.0, "Switching cost", color=MUTED); ftext(2.0, C_TOP - 1.4, "(% of trade)", color=MUTED)
ftext(18.8, C_TOP - 4.0, "Charge", color=MUTED); ftext(18.8, C_TOP - 1.4, "no club → club", color=MUTED)
ftext(110.0, C_TOP - 4.0, "Regions", color=MUTED, ha="right"); ftext(110.0, C_TOP - 1.4, "joining", color=MUTED, ha="right")
def xtxt(r, pct): return "–" if r is None else (f"{r['x']:.2f}" if pct else usd(r["x"]))
for i, (lab, br, fr) in enumerate(CASES):
    if br is None:
        ftext(2.0, row_y(i), lab, color=INK, va="center"); continue
    f, w = br; pct = (w or f)["x"] < 50
    ftext(2.0, row_y(i), lab, va="center")
    b_txt = xtxt(w, pct) + ("%" if pct else " USD/ha") if w else "–"
    ftext(26.0, row_y(i), xtxt(f, pct), ha="right", va="center"); ftext(27.7, row_y(i), "→", ha="center", va="center"); ftext(29.4, row_y(i), b_txt, va="center")
axc = ax_mm(48.0, C_TOP, 56.0, C_H); axc.set_xlim(-1, N_REG + 1); axc.set_ylim(n_rows, 0); spines(axc)
axc.spines["left"].set_visible(False); axc.set_yticks([]); axc.spines["bottom"].set_bounds(0, N_REG)
axc.set_xticks(list(range(0, N_REG + 1, 10))); axc.grid(axis="x", color=GRID, linewidth=0.4); axc.set_axisbelow(True)
axc.set_xlabel(f"Members at convergence (of {N_REG} regions)", fontsize=FS_M, labelpad=2, color=INK)
FX = math.ceil(BAU / 5) * 5 + 1.5
axd = ax_mm(123.0, C_TOP, 56.0, C_H); axd.set_xlim(-0.5, FX); axd.set_ylim(n_rows, 0); spines(axd)
axd.spines["left"].set_visible(False); axd.set_yticks([]); axd.spines["bottom"].set_bounds(0, FX - 1.5)
axd.set_xticks(list(range(0, int(FX - 1.5) + 1, 5)))
for gx in range(0, int(FX - 1.5), 5): axd.axvline(gx, color=GRID, linewidth=0.4, zorder=0)
axd.set_xlabel("Tropical forest kept over five years (Mha)", fontsize=FS_M, labelpad=2, color=INK)
if MAX_FAIL > 0: axd.axvspan(0, MAX_FAIL, color=NEUTRAL, zorder=0)
axd.axvline(BAU, color=MUTED, linewidth=0.5, zorder=1)
def d_x(v): return 123.0 + 56.0 * (v + 0.5) / (FX + 0.5)
if MAX_FAIL > 0: ftext(d_x(0), C_TOP - 4.0, f"≤ {MAX_FAIL:.1f} Mha", color=MUTED); ftext(d_x(0), C_TOP - 1.4, "without Brazil", color=MUTED)
ftext(d_x(BAU), C_TOP - 4.0, "Business-as-usual", color=MUTED, ha="right"); ftext(d_x(BAU), C_TOP - 1.4, f"clearing, {BAU:.1f} Mha", color=MUTED, ha="right")
for i, (lab, br, fr) in enumerate(CASES):
    if br is None: continue
    f, w = br; col = ORANGE if fr == "C" else COL[fr]; yy = i + 0.5
    if f and w:
        axc.plot([f["n"], w["n"]], [yy, yy], color=BASE, linewidth=1.5, solid_capstyle="butt", zorder=3)
        axd.plot([max(f["forest"], 0.0), w["forest"]], [yy, yy], color=BASE, linewidth=1.5, solid_capstyle="butt", zorder=3)
        ftext(110.0, row_y(i), f"+{w['n'] - f['n']}", FS_M, INK, ha="right", va="center", weight="bold")
    if f: marker(axc, f["n"], yy, col, False, s=25, z=5, clip=True); marker(axd, max(f["forest"], 0.0), yy, GREEN, False, s=25, z=5, clip=True)
    if w: marker(axc, w["n"], yy, col, True, s=25, z=5, clip=True); marker(axd, w["forest"], yy, GREEN, True, s=25, z=5, clip=True)
for i, line in enumerate(FOOT): ftext(2.0, H - 2.5 - 2.9 * (len(FOOT) - 1 - i), line, color=MUTED)

fig.savefig(figpath("ExtData_Fig1_thresholds.pdf"))
fig.savefig(figpath("ExtData_Fig1_thresholds.png"), dpi=450)
from PIL import Image
im = Image.open(figpath("ExtData_Fig1_thresholds.png")).convert("RGB"); im.save(figpath("ExtData_Fig1_thresholds.png"), dpi=(450, 450))

# ------------------------------------------------------------------ source data
with open(figpath("ExtData_Fig1_source_data.csv"), "w", newline="", encoding="utf-8") as fh:
    w_ = csv.writer(fh)
    w_.writerow(["panel", "series", "tag", "surcharge_USD_per_ha", "penalty_pct", "switching_cost_share_of_trade", "brazil_switching_cost_MUSD", "brazil_first_round_loss_MUSD",
                 "club_forms_brazil_inside", "members_at_convergence", "tropical_forest_kept_Mha_5yr", "rounds", "note"])
    for r in sorted(RUNS + RUNS_C, key=lambda r: (r["seed"], r["fr"], r["pha"], r["tau"])):
        w_.writerow(["a/b/c" if r["inst"] != "combined" else "-", ("EU alone" if r["seed"] == "EU" else "EU + China") + f", {r['inst']}", r["tag"], r["pha"], r["tau"], r["fr"], round(T["brasil"] * r["fr"] / 0.001, 1),
                     round(r["brazil_r1_loss"], 1), r["works"], r["n"], round(max(r["forest"], 0), 3), r["last"], "both instruments: Fig. 3 only" if r["inst"] == "combined" else ("round cap reached, not settled" if not r["converged"] else ("off scale in a" if r["inst"] == "penalty" and r["x"] > XP + 1e-9 else ""))])
    for lab, br, fr in CASES:
        if br is None: continue
        f, w = br; share = 0.001 if fr == "C" else fr; x = (w or f)
        w_.writerow(["b/c", ("EU + China, " if fr == "C" else "EU alone, ") + ("penalty" if x["x"] < 50 else "surcharge"), "", "", "", share, round(TB.get(share, T["brasil"]), 1), "", "",
                     f"{f['n'] if f else '-'} -> {w['n'] if w else '-'}", f"{max(f['forest'], 0) if f else '-'} -> {w['forest'] if w else '-'}", "", f"charge {f['x'] if f else '-'} -> {w['x'] if w else '-'}"])
print("ok", {k: (v[0] and v[0]["x"], v[1] and v[1]["x"]) for k, v in BRK.items()}, "EU+China", {k: (v[0] and v[0]["x"], v[1] and v[1]["x"]) for k, v in BRK_C.items()}, "max fail", round(MAX_FAIL, 2))
