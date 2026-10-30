"""Extended Data Fig. 2 - where the largest tropical deforesters stand when the EU alone charges (switching cost 0.1 % of trade).
a  First-round loss of the eight largest deforesters at the headline charges (the club's penalty and the coalition's surcharge,
   all_data["headline"]), as a multiple of each region's switching cost (1 = the region would switch on its own first-round loss).
b  Round in which each region joins, in every EU-alone run at 0.1 % on the disk (surcharge alone, penalty alone, both), and
   whether it is a member at convergence.
Reads top_deforesters_<label>.json and all_data_<label>.json (extract_all.py, extract_plane.py)."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))   # the shared modules of the pipeline (paths, figstyle, mapping, v30)
import json, csv
from figstyle import *
from matplotlib.patches import Rectangle
style()
from paths import here, fig as figpath, LABEL
R = json.load(open(here("top_deforesters.json"))); D = json.load(open(here("all_data.json")))
BAU = D["bau"]["bau_trop"]; HL = D["headline"]
TOP = sorted(D["top"], key=lambda c: -BAU[c]); T = {c: D["T"][c] for c in TOP}; n = len(TOP)
EU = [r for r in R if r["seed"] == "EU"]
def run(pha, tau):
    m = [r for r in EU if r["pha"] == pha and abs(r["tau"] - tau) < 1e-9]; return m[0] if m else None
COLS = [("surcharge", sorted([(r["pha"], r["tau"]) for r in EU if r["tau"] == 0 and r["pha"] > 0])),
        ("penalty", sorted([(r["pha"], r["tau"]) for r in EU if r["pha"] == 0 and r["tau"] > 0], key=lambda x: x[1])),
        ("both", sorted([(r["pha"], r["tau"]) for r in EU if r["pha"] > 0 and r["tau"] > 0]))]
COLS = [(k, v) for k, v in COLS if v]; ncols = sum(len(v) for _, v in COLS)
HEAD = [(HL["surcharge"], 0, "#4a3aa7", -0.17, f"Surcharge {HL['surcharge']:,} USD/ha"), (0, HL["penalty"], "#1baf7a", 0.17, f"Penalty {HL['penalty']:g}%")]
HEAD = [h for h in HEAD if run(h[0], h[1])]
MM = 1 / 25.4; W, H = 183.0, 92.0
FS_S, FS_M, FS_L = 6.3, 7.0, 8.0
fig = plt.figure(figsize=(W * MM, H * MM))
def ax_mm(l, t, w, h): return fig.add_axes([l / W, 1 - (t + h) / H, w / W, h / H])
def fx(x): return x / W
def fy(y): return 1 - y / H
def ftext(x, y, s, size=FS_S, color=INK2, ha="left", va="baseline", weight="normal", **kw):
    return fig.text(fx(x), fy(y), s, fontsize=size, color=color, ha=ha, va=va, fontweight=weight, **kw)
def spines(ax):
    for s in ("top", "right"): ax.spines[s].set_visible(False)
    for s in ("left", "bottom"): ax.spines[s].set_position(("outward", 2)); ax.spines[s].set_linewidth(0.6); ax.spines[s].set_color(BASE)
    ax.tick_params(length=2.2, width=0.6, colors=INK2, labelsize=FS_S, pad=1.8)
ROW = 5.0; TOPY = 24.0
# row labels (shared by a and b)
ftext(2.0, 11.0, "a", FS_L, INK, weight="bold"); ftext(6.2, 11.0, "First-round loss at the headline charges, as a multiple of the switching cost", FS_M, INK)
ftext(2.0, 21.6, "Region", color=MUTED); ftext(28.0, 19.2, "Clearing", color=MUTED, ha="right"); ftext(45.5, 19.2, "Switching", color=MUTED, ha="right")
ftext(28.0, 21.6, "Mha, 5 yr", color=MUTED, ha="right"); ftext(45.5, 21.6, "cost, M USD", color=MUTED, ha="right")
for i, c in enumerate(TOP):
    y = TOPY + ROW * (i + 0.5)
    ftext(2.0, y, NAMES[c], color=INK, va="center"); ftext(28.0, y, f"{BAU[c]:.1f}", ha="right", va="center"); ftext(45.5, y, f"{T[c]:.0f}" if T[c] >= 10 else f"{T[c]:.1f}", ha="right", va="center")
# ---- a: ratio at the headline charges
axa = ax_mm(51.0, TOPY, 43.0, ROW * n); axa.set_ylim(n, 0); spines(axa); axa.spines["left"].set_visible(False); axa.set_yticks([])
axa.set_xscale("symlog", linthresh=1.0, linscale=0.9); axa.set_xlim(-15, 15)
axa.set_xticks([-10, -1, 0, 1, 10]); axa.set_xticklabels(["−10", "−1", "0", "1", "10"])
for gx in (-10, -1, 0, 10): axa.axvline(gx, color=GRID, linewidth=0.4, zorder=0)
axa.axvline(1, color=INK2, linewidth=0.7, zorder=2)
axa.text(1.15, -0.2, "= switching cost", fontsize=FS_S, color=INK2, ha="left", va="bottom")
axa.axvspan(1, 15, color=NEUTRAL, zorder=0)
for i, c in enumerate(TOP):
    for pha, tau, col, off, lab in HEAD:
        rec = run(pha, tau)[c]; v = max(min(rec["r1"] / T[c], 14.5), -14.5); y = i + 0.5 + off
        axa.plot([0, v], [y, y], color=col, linewidth=2.2, solid_capstyle="butt", zorder=3)
        if rec["joins"] == 2: axa.scatter([v], [y], s=14, color=col, edgecolor=SURF, linewidth=0.5, zorder=5)
axa.set_xlabel("First-round loss / switching cost (symmetric log scale)", fontsize=FS_M, color=INK, labelpad=2)
axa.legend([Line2D([0], [0], color=col, linewidth=2.2) for _, _, col, _, _ in HEAD] + [Line2D([0], [0], color="none", marker="o", markersize=3.6, markerfacecolor=INK2, markeredgecolor=SURF)],
           [lab for *_, lab in HEAD] + ["Joins in round 2, on its own first-round loss"],
           loc="upper left", bbox_to_anchor=(-1.02, -0.30), frameon=False, fontsize=FS_S, handlelength=1.6, labelcolor=INK2, borderaxespad=0, ncol=1)
# ---- b: joining round grid
BX = 101.0; GAP = 1.6; CW = min(6.4, (W - BX - 3.0 - GAP * (len(COLS) - 1)) / ncols)
ftext(BX - 2.0, 11.0, "b", FS_L, INK, weight="bold"); ftext(BX + 2.2, 11.0, "Round in which each region joins (EU alone charging, 0.1%)", FS_M, INK)
axb = ax_mm(BX, TOPY, CW * ncols + GAP * (len(COLS) - 1), ROW * n); axb.set_axis_off()
axb.set_xlim(0, ncols + (len(COLS) - 1) * (GAP / CW)); axb.set_ylim(n, 0)
RAMP = ["#b7d3f6", "#9ec5f4", "#6da7ec", "#5598e7", "#2a78d6", "#1c5cab", "#104281", "#0d366b"]
xpos = 0.0; col_x = {}
for g, (name, cols) in enumerate(COLS):
    for pha, tau in cols:
        rec = run(pha, tau); col_x[(pha, tau)] = xpos; works = rec["works"]
        lab = (f"{pha / 1000:g}k" if name == "surcharge" else f"{tau:g}%" if name == "penalty" else f"{pha / 1000:g}k\n{tau:g}")   # "2k / 0.5": the surcharge in thousands, the penalty in %
        fig.text(fx(BX + (xpos + 0.5) * CW), fy(TOPY - 1.4), lab, fontsize=5.0 if CW < 6 else 5.6, color=INK if works else MUTED, ha="center", va="bottom", linespacing=1.05)
        for i, c in enumerate(TOP):
            r = rec[c]; jr = r["joins"]
            if jr is None: axb.add_patch(Rectangle((xpos, i), 1, 1, facecolor="#f5f4f0", edgecolor=SURF, linewidth=0.8))
            else:
                axb.add_patch(Rectangle((xpos, i), 1, 1, facecolor=RAMP[min(jr, 8) - 1], edgecolor=SURF, linewidth=0.8))
                axb.text(xpos + 0.5, i + 0.55, str(jr), fontsize=FS_S, color=SURF if jr >= 5 else INK, ha="center", va="center")
                if not r["final"]: axb.add_patch(Rectangle((xpos + 0.12, i + 0.12), 0.76, 0.76, facecolor="none", edgecolor="#e34948", linewidth=0.9))
        xpos += 1
    xpos += GAP / CW
for g, (name, cols) in enumerate(COLS):
    x0 = col_x[cols[0]]; x1 = col_x[cols[-1]] + 1
    fig.text(fx(BX + (x0 + x1) / 2 * CW), fy(TOPY - 7.6), {"surcharge": "Surcharge (k USD/ha)", "penalty": "Penalty", "both": "Surcharge (k USD/ha)\n+ penalty (%)"}[name], fontsize=FS_S, color=INK2, ha="center", va="bottom")
# legend for b
ly = TOPY + ROW * n + 4.5
ftext(BX, ly, "Round in which the region joins:  2", color=INK2)
for k in range(8):
    fig.patches.append(Rectangle((fx(BX + 40.5 + k * 3.4), fy(ly + 0.9)), 3.0 / W, 2.2 / H, transform=fig.transFigure, facecolor=RAMP[k], edgecolor=SURF, linewidth=0.4))
ftext(BX + 40.5 + 8 * 3.4 + 0.8, ly, "8 or later", color=INK2)
fig.patches.append(Rectangle((fx(BX), fy(ly + 4.6 + 0.9)), 3.0 / W, 2.2 / H, transform=fig.transFigure, facecolor="#f5f4f0", edgecolor=GRID, linewidth=0.4))
ftext(BX + 4.0, ly + 4.6, "never joins", color=INK2)
fig.patches.append(Rectangle((fx(BX + 22), fy(ly + 4.6 + 0.9)), 3.0 / W, 2.2 / H, transform=fig.transFigure, facecolor="none", edgecolor="#e34948", linewidth=0.9))
ftext(BX + 26.0, ly + 4.6, "joins, then leaves before convergence", color=INK2)
ftext(BX, ly + 8.4, "Column headers in black: the club forms (Brazil inside); grey: it does not", color=MUTED)
#ftext(2.0, H - 2.5, f"{LABEL} runs", color=MUTED)
fig.savefig(figpath("ExtData_Fig2_largest_deforesters.pdf")); fig.savefig(figpath("ExtData_Fig2_largest_deforesters.png"), dpi=450)
with open(figpath("ExtData_Fig2_source_data.csv"), "w", newline="", encoding="utf-8") as fh:   # one row per run x region
    w = csv.writer(fh); w.writerow(["seed", "tag", "surcharge_usd_per_ha", "penalty_pct", "rounds_to_convergence", "club_forms_brazil_inside", "region", "first_round_loss_MUSD", "switching_cost_MUSD", "joins_in_round", "inside_at_convergence", "EV_net_at_convergence_MUSD_per_yr"])
    for r in sorted(R, key=lambda r: (r["seed"], r["tau"], r["pha"])):
        for c in TOP: w.writerow([r["seed"], r.get("tag", ""), r["pha"], r["tau"], r["last"], r["works"], NAMES[c], r[c]["r1"], r[c]["T"], r[c]["joins"] if r[c]["joins"] is not None else "never", int(r[c]["final"]), r[c]["dev_final"]])
print("ok", ncols, "columns, cell", round(CW, 2), "mm; headline:", [lab for *_, lab in HEAD])
