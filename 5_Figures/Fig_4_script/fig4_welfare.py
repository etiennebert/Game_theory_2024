"""Fig. 4 - who gains and who pays. a: maps of the welfare change at convergence (% of GDP) for the headline club and coalition;
b: the welfare change by region (M USD per year) for every starting point on the disk (EU alone x 2 instruments, EU + China x 2,
EU + Mercosur, EU + Mercosur + China); c: the one-deviation stability test of the headline club and coalition (gain from switching
status alone, net of the switching cost). Everything comes from all_data_<label>.json: the configurations, their labels and member
counts, the world welfare in the titles, and the regions annotated in c (every region whose deviation pays)."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))   # the shared modules of the pipeline (paths, figstyle, mapping, v30)
import json, csv, math
from matplotlib.patches import Rectangle
from figstyle import *
style()
from paths import here, fig as figpath, LABEL
d = json.load(open(here("all_data.json"))); C = d["configs"]; gdp = d["gdp"]; SEEDS = d["seeds"]
A = C["EU_pen"] if "EU_pen" in C else C[next(iter(C))]
trop = [c for c, v in sorted(d["bau"]["bau_trop"].items(), key=lambda x: -x[1]) if v >= 0.1]      # tropical forest regions: >= 0.1 Mha of BAU clearing
other = sorted([c for c in A["ev"] if c not in trop], key=lambda c: -gdp[c])
EDGES = [-math.inf, -0.05, -0.01, -0.002, 0.002, 0.01, 0.05, math.inf]
COLS7 = [ORANGES[2], ORANGES[1], ORANGES[0], NEUTRAL, BLUES[0], BLUES[1], BLUES[2]]
def binc(v):
    for i in range(7):
        if EDGES[i] <= v < EDGES[i + 1]: return i
    return 6
fmt = lambda v: f"{v:+,.0f}".replace("-", "−")
def inst(c, short=False):
    """'penalty 1.5%' / 'surcharge 4,000 USD/ha' / 'no charge' from a config's charge"""
    if c["pha"] > 0 and c["tau"] > 0: return f"surcharge {c['pha']:,}/ha + penalty {c['tau']:g}%" if short else f"surcharge {c['pha']:,} USD/ha + penalty {c['tau']:g}%"
    if c["pha"] > 0: return f"surcharge\n{c['pha']:,}/ha" if short else f"Footprint surcharge {c['pha']:,} USD/ha"
    if c["tau"] > 0: return f"penalty\n{c['tau']:g}%" if short else f"Flat penalty {c['tau']:g}%"
    return "no charge" if short else "No charge"
mm = 1 / 25.4
fig = plt.figure(figsize=(183 * mm, 235 * mm))

# ---------- a: maps of welfare change (% of GDP), headline club and coalition ----------
maps = [k for k in ("EU_pen", "EU_sur") if k in C]
for j, k in enumerate(maps):
    ax = fig.add_axes([0.005 + 0.5 * j, 0.80, 0.49, 0.175])
    draw_map_div(ax, C[k]["ev_pct"], set(C[k]["final_members"]), EDGES[1:-1], COLS7)
    ax.set_title(f"{inst(C[k])}  ·  world {C[k]['world'] / 1000:+.2f} bn USD/yr".replace("-", "−"), loc="left", fontsize=7, pad=2, x=0.03)
    if j == 0: panel(ax, "a", x=0.0, y=1.06)
handles = [Patch(facecolor=c, edgecolor=GRID if c == NEUTRAL else c, linewidth=0.4) for c in COLS7] + [Patch(facecolor="none", edgecolor="#9a9891", hatch="//////", linewidth=0.4)]
labels = ["< −0.05", "−0.05 to −0.01", "−0.01 to −0.002", "±0.002", "0.002 to 0.01", "0.01 to 0.05", "> 0.05", "non-member"]
fig.legend(handles, labels, loc="center", bbox_to_anchor=(0.5, 0.787), ncol=8, frameon=False, fontsize=5.9, handlelength=1.3, columnspacing=1.0,
           handletextpad=0.4, labelcolor=INK2, title="Welfare change at convergence relative to the baseline (% of GDP)", title_fontsize=6.2)

# ---------- b: grid, starting points x regions ----------
cols = []
for k in ("EU_pen", "EU_sur", "EUC_pen", "EUC_sur", "EUM_0", "EUMC_0"):
    if k not in C: print("  panel b: config", k, "not on the disk, column skipped"); continue
    seed = {"EU": "EU alone", "EUChina": "EU + China", "EUMercosur": "EU +\nMercosur", "EUMercosurChina": "EU + Mercosur\n+ China"}.get(C[k]["seed"], SEEDS.get(C[k]["seed"], C[k]["seed"]))
    cols.append((k, f"{seed}\n{inst(C[k], short=True)}"))
rows = ["#Tropical forest regions"] + trop + ["#Other regions"] + other
axm = fig.add_axes([0.20, 0.05, 0.44, 0.655]); n = len(rows)
for i, c in enumerate(rows):
    if c.startswith("#"):
        axm.text(-0.06, i + 0.62, c[1:], ha="right", va="center", fontsize=6.2, fontweight="bold", color=INK); continue
    for j, (k, lab) in enumerate(cols):
        r = C[k]; b = binc(r["ev_pct"][c]); mem = c in r["final_members"]
        axm.add_patch(Rectangle((j, i), 1, 1, facecolor=COLS7[b], edgecolor=SURF, linewidth=0.8))
        axm.text(j + 0.5, i + 0.53, fmt(r["ev"][c]), ha="center", va="center", fontsize=5.2, color=SURF if b in (0, 6) else INK,
                 fontweight="bold" if mem else "normal", zorder=5)
        if mem: axm.plot(j + 0.12, i + 0.5, marker="o", markersize=1.8, color=SURF if b in (0, 6) else INK, zorder=4)
axm.set_xlim(0, len(cols)); axm.set_ylim(n, 0)
tick_rows = [i for i, c in enumerate(rows) if not c.startswith("#")]
axm.set_yticks([i + 0.5 for i in tick_rows]); axm.set_yticklabels([NAMES[rows[i]] for i in tick_rows], fontsize=5.8)
axm.set_xticks([j + 0.5 for j in range(len(cols))]); axm.set_xticklabels([l for _, l in cols], fontsize=5.8, linespacing=1.1)
axm.xaxis.tick_top(); axm.tick_params(length=0, pad=2)
for s in axm.spines.values(): s.set_visible(False)
sep = rows.index("#Other regions"); axm.axhline(sep, color=INK2, linewidth=0.6)
panel(axm, "b", x=-0.43, y=1.075)
axm.text(0.0, -0.012, "M USD per year; colour as in a; bold with a dot = member at convergence", transform=axm.transAxes, fontsize=5.9, color=INK2, va="top")

# ---------- c: one-deviation stability, same rows ----------
axs = fig.add_axes([0.685, 0.05, 0.295, 0.655])
stab = [(k, mk, fc, ec) for k, mk, fc, ec in [("EU_pen", "o", INK, SURF), ("EU_sur", "o", SURF, INK)] if k in d["stability"]]
nets = [t["gain"] - t["threshold"] for k, *_ in stab for t in d["stability"][k]]
XMAX = max(430, math.ceil((max(nets) if nets else 0) / 50) * 50 + 420)   # room for the switchers' labels
axs.set_ylim(n, 0); axs.set_xlim(-1000, XMAX); CLIP = -960
axs.axvspan(-1000, 0, color="#f5f4f0", zorder=0); axs.axvline(0, color=INK2, linewidth=0.8)
for i in tick_rows: axs.axhline(i + 0.5, color=GRID, linewidth=0.4, zorder=0.5)
axs.axhline(sep, color=INK2, linewidth=0.6)
ridx = {c: i for i, c in enumerate(rows)}
clipped, switchers = {}, []
for k, mk, fc, ec in stab:
    for t in d["stability"][k]:
        if t["region"] not in ridx: continue
        i = ridx[t["region"]]; net = t["gain"] - t["threshold"]; short = "penalty" if k == "EU_pen" else "surcharge"
        if net < CLIP:
            axs.scatter([CLIP], [i + 0.5], s=14, marker="<", facecolor=fc, edgecolor=ec, linewidth=0.7, zorder=4)
            clipped.setdefault(i, []).append(fmt(net) + f" ({short})"); continue
        axs.scatter([net], [i + 0.5], s=12, marker=mk, facecolor=fc, edgecolor=ec, linewidth=0.7, zorder=4)
        if t["status"] == "outsider": axs.scatter([net], [i + 0.5], s=40, marker="s", facecolor="none", edgecolor=MUTED, linewidth=0.5, zorder=3)
        if net > 0: switchers.append((i, net, t["region"], short, t["status"]))
for i, labs in clipped.items():
    axs.text(CLIP + 40, i + 0.5, ", ".join(labs), fontsize=5.2, color=INK2, va="center", ha="left")
ticks = [-1000, -750, -500, -250, 0] + [x for x in (250, 500, 750, 1000) if x <= XMAX]
axs.set_yticks([]); axs.set_xticks(ticks); axs.set_xticklabels(["< −1,000"] + [fmt(x).replace("+", "") if x else "0" for x in ticks[1:]])
for s in ("top", "right", "left"): axs.spines[s].set_visible(False)
axs.set_xlabel("Gain from switching status alone,\nnet of the switching cost (M USD per year)")
axs.text(-980, 0.4, "no profitable deviation", fontsize=5.9, color=INK2, va="top")
axs.text(30, 0.4, "would\nswitch", fontsize=5.9, color=INK2, va="top")
# annotate every region whose deviation pays (the switchers), with the instrument when both are tested
for i, net, reg, short, status in sorted(switchers):
    axs.text(net + 0.055 * XMAX, i + 0.5, f"{NAMES[reg]} {fmt(net)}", fontsize=5.4, color=INK2, va="center", ha="left")   # the marker says which instrument
panel(axs, "c", x=-0.05, y=1.075)
leg_h = [Line2D([0], [0], color="none", marker=mk, markersize=3.6, markerfacecolor=fc, markeredgecolor=ec) for k, mk, fc, ec in stab]
leg_l = [f"{'Penalty club' if k == 'EU_pen' else 'Surcharge coalition'} ({C[k]['n']} members)" for k, *_ in stab]
leg_h.append(Line2D([0], [0], color="none", marker="s", markersize=5.5, markerfacecolor="none", markeredgecolor=MUTED)); leg_l.append("Non-member tested for joining")
axs.legend(leg_h, leg_l, loc="lower left", bbox_to_anchor=(-0.05, 1.0), frameon=False, fontsize=5.8, handletextpad=0.3, labelcolor=INK2, ncol=1, borderaxespad=0)
fig.text(0.012, 0.005, f"{LABEL} runs", fontsize=5, color=MUTED, ha="left", va="bottom")

for ext in ("pdf", "png"): fig.savefig(figpath(f"Fig4_welfare.{ext}"), dpi=450 if ext == "png" else None)
with open(figpath("Fig4_source_data.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["panel", "configuration", "tag", "region", "member", "EV_net_MUSD_per_year", "EV_gross_MUSD_per_year", "EV_net_pct_GDP",
                                   "stability_status", "stability_gain_from_moving_MUSD", "switching_cost_MUSD"])
    for k, lab in cols:
        r = C[k]; st = {t["region"]: t for t in d["stability"].get(k, [])}
        for c in trop + other:
            t = st.get(c); w.writerow(["a/b/c" if k in maps else "b", lab.replace("\n", " "), r["tag"], NAMES[c], c in r["final_members"], round(r["ev"][c], 1),
                                       round(r["ev_gross"][c], 1) if r.get("ev_gross") else "", round(r["ev_pct"][c], 4),
                                       t["status"] if t else "", round(t["gain"], 1) if t else "", round(t["threshold"], 1) if t else ""])
print("ok", [k for k, _ in cols], "switchers:", [(NAMES[r], round(v)) for _, v, r, *_ in switchers])
