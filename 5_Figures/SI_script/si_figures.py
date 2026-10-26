"""Supplementary figures and tables of one generation of runs (paths.VERSION; SI sections 6.2, 6.4 and 7).
Reads data_<label>/*.csv (si_extract.R: forest change of the baseline, welfare decomposition, sectoral supply, Brazil's commodities),
all_data_<label>.json and the result csv files; writes Fig_S7 (baseline forest change), Fig_S9 (sectoral supply responses), Fig_S10
(members by round, every run), Fig_S11 (welfare of members and outsiders by round, every run) and Tables S9-S12 as markdown."""
import json, csv, math, os, sys
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_HERE, "..", "common"))   # the shared modules of the pipeline (paths, figstyle, v30)
import numpy as np, matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from figstyle import style, clean, NAMES, INK, INK2, MUTED, GRID, BASE, SURF, GREENS, ORANGES, BLUES, DARK, LIGHT, NEUTRAL
style()
from paths import here, LABEL, VERSION, out_dir
import v30
DATA = os.path.join(_HERE, f"data_{LABEL.lower()}")   # the csv files written by si_extract.R for this generation (V32: data\)
if not os.path.isdir(DATA): DATA = os.path.join(_HERE, "data")
OUT = out_dir()                       # SI_Output\
D = json.load(open(here("all_data.json"))); C = D["configs"]; T = D["T"]; BAU = D["bau"]
MM = 1 / 25.4
def rd(path): return list(csv.DictReader(open(path)))
def fmt(v, d=0): return f"{v:,.{d}f}".replace("-", "−")
def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=400); fig.savefig(os.path.join(OUT, name + ".pdf")); plt.close(fig); print("wrote", name)

# ------------------------------------------------------------------ Fig. S7: forest change of the baseline by region and climate zone
rows = rd(os.path.join(DATA, "si_forest_baseline.csv"))
regs = sorted({r["region"] for r in rows}, key=lambda r: -sum(float(x["stageA"]) for x in rows if x["region"] == r))   # largest clearing at the top
regs = [r for r in regs if abs(sum(float(x["stageA"]) for x in rows if x["region"] == r)) > 5 or abs(sum(float(x["stageB"]) for x in rows if x["region"] == r)) > 1]
ZC = {"tropical": GREENS[4], "temperate": GREENS[2], "boreal": GREENS[0]}
fig = plt.figure(figsize=(183 * MM, 150 * MM))
ax1 = fig.add_axes([0.17, 0.09, 0.48, 0.86]); ax2 = fig.add_axes([0.72, 0.09, 0.26, 0.86])
y = np.arange(len(regs))
totA = sum(float(x["stageA"]) for x in rows) / 1000; totB = sum(float(x["stageB"]) for x in rows)
mn = lambda v, u: f"{v:+.1f} {u}".replace("-", "−")
for ax, col, title, unit in ((ax1, "stageA", f"a  Stage A: business-as-usual clearing, relative to 2019 (world {mn(totA, 'Mha')})", "Mha"), (ax2, "stageB", f"b  Stage B: the EUDR, relative to Stage A\n(world {mn(totB, 'kha')})", "kha")):
    left_pos = np.zeros(len(regs)); left_neg = np.zeros(len(regs))
    for z in ("tropical", "temperate", "boreal"):
        v = np.array([next(float(x[col]) for x in rows if x["region"] == r and x["zone"] == z) for r in regs]) / (1000 if unit == "Mha" else 1)
        pos = np.where(v > 0, v, 0); neg = np.where(v < 0, v, 0)
        ax.barh(y, pos, left=left_pos, color=ZC[z], height=0.72, edgecolor="none"); ax.barh(y, neg, left=left_neg, color=ZC[z], height=0.72, edgecolor="none")
        left_pos += pos; left_neg += neg
    ax.axvline(0, color=INK2, linewidth=0.6); clean(ax, y=False); ax.set_yticks(y); ax.set_ylim(-0.6, len(regs) - 0.4)
    ax.set_yticklabels([NAMES[r] for r in regs] if ax is ax1 else [""] * len(regs), fontsize=6.3); ax.tick_params(axis="y", length=0)
    ax.set_title(title, loc="left", fontsize=7, color=INK, pad=4); ax.set_xlabel(f"Forest cover change over five years ({unit})", fontsize=7, labelpad=2)
ax1.legend(handles=[Patch(color=ZC[z], label=z.capitalize() + " AEZs") for z in ZC], loc="lower left", frameon=False, fontsize=6.3)
save(fig, "Fig_S7_baseline_forest")

# ------------------------------------------------------------------ Fig. S9: sectoral supply responses at the club equilibrium
PROD = ["angola", "argentina", "bolivia", "brasil", "colombia", "ghana", "ivorycoast", "indonesia", "malasya", "paraguay", "peru", "drc"]   # list_producer_countries of the game script
LAND = ["pdr", "wht", "gro", "v_f", "osd", "c_b", "pfb", "ocr", "ruminant", "rmk", "wol", "ruminantmeat", "dairy", "vegoil", "pcr", "sgr", "lea", "forest"]
sup = rd(os.path.join(DATA, "si_supply_club.csv"))
fig, axs = plt.subplots(1, 2, figsize=(183 * MM, 84 * MM), sharey=True); plt.subplots_adjust(left=0.08, right=0.99, bottom=0.22, top=0.9, wspace=0.08)
for ax, group, title in ((axs[0], PROD, "a  The twelve producer regions of the game script"), (axs[1], [r for r in NAMES if r not in PROD], "b  The thirty other regions")):
    for r in sup:
        if r["region"] not in group or float(r["vom_musd"]) <= 0: continue
        land = r["sector"].lower() in LAND
        ax.scatter(float(r["vom_musd"]), float(r["qo_pct"]), s=7 if land else 4, color=GREENS[4] if land else LIGHT, alpha=0.9 if land else 0.8, linewidth=0, zorder=3 if land else 2)
    ax.set_xscale("log"); ax.set_xlim(5, 5e6); ax.axhline(0, color=INK2, linewidth=0.5); clean(ax)
    ax.set_title(title, loc="left", fontsize=7, pad=4); ax.set_xlabel("Value of output in the base data (M USD, log scale)", fontsize=7, labelpad=2)
    ax.set_ylim(-10, 10)
axs[0].set_ylabel("Change in output at the club equilibrium (%)", fontsize=7)
for sec, lab_, dx, dy in (("forest", "Brazil, forestry", 4, 2), ("osd", "Brazil, oilseeds", 4, -7), ("ruminantmeat", "Brazil, beef", 4, 3)):
    r = next(r for r in sup if r["region"] == "brasil" and r["sector"].lower() == sec)
    axs[0].annotate(lab_, (float(r["vom_musd"]), float(r["qo_pct"])), xytext=(dx, dy), textcoords="offset points", fontsize=5.5, color=INK2)
big = sorted([r for r in sup if abs(float(r["qo_pct"])) > 6], key=lambda r: -abs(float(r["qo_pct"])))[:6]
for r in big: print("  off scale:", r["region"], r["sector"], round(float(r["qo_pct"]), 1), round(float(r["vom_musd"])))
axs[0].legend(handles=[Line2D([0], [0], marker="o", color="none", markerfacecolor=GREENS[4], markersize=4, label="Land-based sectors (the 17 charged commodities and forestry)"),
                       Line2D([0], [0], marker="o", color="none", markerfacecolor=LIGHT, markersize=3.5, label="Other sectors")], loc="upper left", frameon=False, fontsize=6)
off = sorted([r for r in sup if abs(float(r["qo_pct"])) > 10 and float(r["vom_musd"]) > 0], key=lambda r: -abs(float(r["qo_pct"])))
SN = {"forest": "forestry", "lum": "wood products", "wol": "wool"}
off_txt = f"{len(off)} points, " + "; ".join(f"{NAMES[r['region']]} {SN.get(r['sector'].lower(), r['sector'])} {float(r['qo_pct']):+.0f} %" for r in off[:6]).replace("-", "−") + (f" and {len(off) - 6} others between 10 and {abs(float(off[6]['qo_pct'])):.0f} %" if len(off) > 6 else "")
import textwrap as _tw
for i_, line in enumerate(_tw.wrap(f"{LABEL} runs · penalty club 1.5 % at convergence, relative to the EUDR world · beyond ±10 % (the held forest returns to timber production): {off_txt}", 190)):
    fig.text(0.01, 0.045 - 0.03 * i_, line, fontsize=5.4, color=MUTED)
save(fig, "Fig_S9_supply_responses")

# ------------------------------------------------------------------ every run: members and welfare by round (Figs S10, S11)
gdp = v30.read_gdp(); metas = v30.all_runs(pin="all", eudr="keep"); Tt = v30.read_thresholds(metas[0]["tag"])
S = [v30.run_stats(m["tag"], gdp, Tt, m) for m in metas]
def inst_lab(s):
    parts = []
    if s["pha"] > 0: parts.append(f"{s['pha']:,} USD/ha")
    if s["tau"] > 0: parts.append(f"{s['tau']:g} %")
    return " + ".join(parts) if parts else "no charge"
SEEDL = {"EU": "EU", "EUChina": "EU + China", "EUMercosur": "EU + Mercosur", "EUMercosurChina": "EU + Mercosur + China", "EUMercosur5": "EU + Mercosur-5"}
def title_of(s):
    t = f"{SEEDL[s['seed']]}, {inst_lab(s)}"; q = []
    if s["lock"]: q.append({"brasil": "Brazil", "us": "US", "us-china": "US + China", "indonesia": "Indonesia"}[s["lock"]] + " locked out")
    if abs(s["fr"] - 0.001) > 1e-12: q.append(f"switching cost {100 * s['fr']:g} % of trade")
    return t + ("\n" + ", ".join(q) if q else "\n")
order = sorted(S, key=lambda s: (["EU", "EUChina", "EUMercosur", "EUMercosurChina", "EUMercosur5"].index(s["seed"]), s["lock"] != "", s["lock"], s["fr"] != 0.001, s["fr"], s["pha"] > 0 and s["tau"] > 0, s["pha"], s["tau"]))
trop = {r for r, v in BAU["bau_trop"].items() if v >= 0.1}
nc = 5; nr = math.ceil(len(order) / nc)
fig, axs = plt.subplots(nr, nc, figsize=(183 * MM, (22 * nr + 16) * MM)); plt.subplots_adjust(left=0.05, right=0.99, bottom=0.055, top=0.965, wspace=0.28, hspace=1.0)
for i, s in enumerate(order):
    ax = axs[i // nc][i % nc]; mb0 = s["members_by_round"]; mb = {str(k): v for k, v in mb0.items()}; R = list(range(s["last"] + 1))
    nt = [sum(1 for c in mb[str(k)] if c in trop) for k in R]; no = [len(mb[str(k)]) - nt[k] for k in R]
    ax.bar(R, nt, color=DARK, width=0.75); ax.bar(R, no, bottom=nt, color=LIGHT, width=0.75)
    ax.set_ylim(0, 42); ax.set_xlim(-0.7, 14.7); ax.set_xticks([0, 5, 10]); ax.set_yticks([0, 20, 40]); clean(ax, x=False)
    ax.set_title(title_of(s), fontsize=5.6, loc="left", pad=2, color=INK)
    ax.text(0.98, 0.95, f"{s['n']} · {s['forest']:.1f} Mha" + ("" if s["converged"] else " · cap"), transform=ax.transAxes, ha="right", va="top", fontsize=5.4, color=INK2 if s["works"] else ORANGES[2])
    ax.tick_params(labelsize=5.4, length=2)
for j in range(len(order), nr * nc): axs[j // nc][j % nc].set_axis_off()
fig.text(0.01, 0.018, f"{LABEL} runs · bars: tropical forest regions (dark) and other regions (light) inside the club after each round (round 0 = the EUDR world, the seed alone); the label gives the members at", fontsize=5.6, color=MUTED)
fig.text(0.01, 0.005, "convergence and the tropical forest they keep, in orange when the club does not form (Brazil outside at convergence, or 'cap': the 15-round cap reached without convergence)", fontsize=5.6, color=MUTED)
save(fig, "Fig_S10_members_by_round")

fig, axs = plt.subplots(nr, nc, figsize=(183 * MM, (22 * nr + 16) * MM)); plt.subplots_adjust(left=0.06, right=0.99, bottom=0.055, top=0.965, wspace=0.32, hspace=1.0)
for i, s in enumerate(order):
    ax = axs[i // nc][i % nc]; mb0 = s["members_by_round"]; mb = {str(k): v for k, v in mb0.items()}; ep = s["ev_path"]; R = list(range(s["last"] + 1))
    mem = [sum(ep[c][k] - ep[c][0] for c in mb[str(k)]) / 1000 for k in R]; out = [sum(ep[c][k] - ep[c][0] for c in ep if c not in mb[str(k)]) / 1000 for k in R]
    ax.plot(R, mem, color=GREENS[4], linewidth=1.0, marker="o", markersize=1.8); ax.plot(R, out, color=ORANGES[2], linewidth=1.0, marker="o", markersize=1.8)
    ax.plot(R, [m + o for m, o in zip(mem, out)], color=INK2, linewidth=0.7, linestyle=(0, (2, 1.5)))
    ax.axhline(0, color=BASE, linewidth=0.5); ax.set_xlim(-0.7, 14.7); ax.set_xticks([0, 5, 10]); ax.set_ylim(-4.2, 1.8); ax.set_yticks([-4, -2, 0]); clean(ax, x=False)
    ax.set_title(title_of(s), fontsize=5.6, loc="left", pad=2, color=INK); ax.tick_params(labelsize=5.4, length=2)
for j in range(len(order), nr * nc): axs[j // nc][j % nc].set_axis_off()
fig.text(0.01, 0.018, f"{LABEL} runs · welfare relative to the EUDR world (bn USD per year, on the decision measure): the sum over the members (green), over the non-members (orange) and the world (dashed)", fontsize=5.6, color=MUTED)
fig.text(0.01, 0.005, "after each round, with the membership of that round", fontsize=5.6, color=MUTED)
save(fig, "Fig_S11_welfare_by_round")

# ------------------------------------------------------------------ Table S9: every run
L = []
L.append("| Seed | Locked out | Switching cost, % of trade | Charge | Rounds | Members (Brazil) | Forest kept inside, tropical (all zones), Mha | Lost outside, tropical (all zones), Mha | World welfare, net (gross), M USD/yr |")
L.append("|---|---|---|---|---|---|---|---|---|")
for s in order:
    L.append(f"| {SEEDL[s['seed']]} | {({'brasil': 'Brazil', 'us': 'United States', 'us-china': 'US and China', 'indonesia': 'Indonesia'}.get(s['lock'], '–'))} | {100 * s['fr']:g} | {inst_lab(s)} | "
             f"{s['last']}{'' if s['converged'] else ' (cap)'} | {s['n']} ({'in' if 'brasil' in s['final_members'] else 'out'}) | {s['forest']:.2f} ({s['forest_all']:.2f}) | {fmt(s['leakage'], 2)} ({fmt(s['leakage_all'], 2)}) | {fmt(s['world'])} ({fmt(s['world_gross']) if s['world_gross'] is not None else '–'}) |")
open(os.path.join(OUT, "Table_S9_runs.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

# ------------------------------------------------------------------ Table S10: the one-deviation tests
L = ["| Coalition tested (run) | Members | Would leave (no switching cost) | Would join (no switching cost) | Would move, switching cost counted | Transfer that retains the leavers, M USD/yr | What the members who prefer the club could pay, M USD/yr | Duty raised by the charge, M USD/yr |", "|---|---|---|---|---|---|---|---|"]
import glob, re
for key in ("EU_pen", "EU_sur", "EUC_pen_1.12", "EUM_0"):
    if key not in D["stability"] or key not in C: continue
    c = C[key]; rows = D["stability"][key]
    leave0 = [t["region"] for t in rows if t["status"] == "member" and t["gain"] > 0]; join0 = [t["region"] for t in rows if t["status"] == "outsider" and t["gain"] > 0]
    move = [t["region"] for t in rows if t["gain"] - t["threshold"] > 0]
    f = [p for p in glob.glob(os.path.join(v30.DB, f"Stability_*{VERSION}.txt")) if f"pha{c['pha']}_tau{c['tau']:g}" in os.path.basename(p)]
    f = sorted(f, key=lambda p: -os.path.getsize(p))   # the full test first (a one-region supplement such as the Japan file is smaller)
    txt = open(f[0]).read() if f else ""
    m = re.search(r"transfers to keep the leavers \(\$M/yr\): (\S+) \| what the members who prefer S could pay: (\S+) \| duty raised by the charge in S: (\S+)", txt)
    tr, pay, duty = (m.group(1), m.group(2), m.group(3)) if m else ("", "", "")
    nm = lambda L_: ", ".join(NAMES[r] for r in L_) if L_ else "nobody"
    L.append(f"| {c['label']} | {c['n']} | {nm(leave0)} | {nm(join0)} | {nm(move)} | {tr} | {pay} | {duty} |")
open(os.path.join(OUT, "Table_S10_stability.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

# ------------------------------------------------------------------ Table S11: welfare decomposition, club and coalition, all regions
dc = {r["region"]: r for r in rd(os.path.join(DATA, "si_welfare_decomp_club.csv"))}; ds = {r["region"]: r for r in rd(os.path.join(DATA, "si_welfare_decomp_coalition.csv"))}
L = ["| Region | Club: EV gross | Wedge term | EV, decision measure | Allocative efficiency | Technical change | Terms of trade | Investment–savings | Coalition: EV, decision measure | Terms of trade |", "|---|---|---|---|---|---|---|---|---|---|"]
regs_all = sorted(dc, key=lambda r: -float(dc[r]["ev_net"]))
for r in regs_all:
    a = dc[r]; b = ds[r]
    L.append(f"| {NAMES[r]}{' (out)' if r not in C['EU_pen']['final_members'] else ''} | {fmt(float(a['ev_gross']))} | {fmt(float(a['wedge']))} | {fmt(float(a['ev_net']))} | {fmt(float(a['alloc']))} | {fmt(float(a['tech']))} | {fmt(float(a['tot']))} | {fmt(float(a['pinv']))} | {fmt(float(b['ev_net']))}{' (out)' if r not in C['EU_sur']['final_members'] else ''} | {fmt(float(b['tot']))} |")
w = lambda d, k: sum(float(x[k]) for x in d.values())
L.append(f"| **World** | {fmt(w(dc, 'ev_gross'))} | {fmt(w(dc, 'wedge'))} | {fmt(w(dc, 'ev_net'))} | {fmt(w(dc, 'alloc'))} | {fmt(w(dc, 'tech'))} | {fmt(w(dc, 'tot'))} | {fmt(w(dc, 'pinv'))} | {fmt(w(ds, 'ev_net'))} | {fmt(w(ds, 'tot'))} |")
open(os.path.join(OUT, "Table_S11_welfare_decomposition.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

# ------------------------------------------------------------------ Table S12: Brazil's commodities at the two equilibria
bc = {r["item"]: r for r in rd(os.path.join(DATA, "si_brazil_club.csv"))}; bs = {r["item"]: r for r in rd(os.path.join(DATA, "si_brazil_coalition.csv"))}
CN = {"pdr": "Paddy rice", "wht": "Wheat", "gro": "Other grains", "v_f": "Vegetables, fruit", "osd": "Oilseeds", "c_b": "Sugar crops", "pfb": "Plant fibres", "ocr": "Other crops", "ruminant": "Cattle", "rmk": "Raw milk", "wol": "Wool", "ruminantmeat": "Beef", "dairy": "Dairy", "vegoil": "Vegetable oils", "pcr": "Processed rice", "sgr": "Sugar", "lea": "Leather"}
L = ["| Commodity | Output in 2019 (M USD) | Club: output (%) | Exports (%) | Export price (%) | Coalition: output (%) | Exports (%) | Export price (%) |", "|---|---|---|---|---|---|---|---|"]
for k in CN:
    a = bc[k]; b = bs[k]
    L.append(f"| {CN[k]} | {fmt(float(a['vom_musd']))} | {fmt(float(a['qo']), 2)} | {fmt(float(a['qxw']), 2)} | {fmt(float(a['pxw']), 2)} | {fmt(float(b['qo']), 2)} | {fmt(float(b['qxw']), 2)} | {fmt(float(b['pxw']), 2)} |")
rc = rd(os.path.join(DATA, "si_brazil_rents_club.csv"))
rent = lambda v, z: next((float(x["change_pct"]) for x in rc if x["var"] == v and x["aez"] == z), float("nan"))
L.append("")
L.append("Land rents at the club equilibrium (%, zones with cover): cropland " + ", ".join(f"AEZ {z[3:]} {fmt(rent('pecroplnd', z), 1)}" for z in ("aez2", "aez3", "aez4", "aez5", "aez6", "aez12")) + "; pasture " + ", ".join(f"AEZ {z[3:]} {fmt(rent('pegrazlnd', z), 1)}" for z in ("aez4", "aez5", "aez6", "aez12")) + "; forest " + ", ".join(f"AEZ {z[3:]} {fmt(rent('peforslnd', z), 1)}" for z in ("aez4", "aez5", "aez6", "aez12")) + ".")
open(os.path.join(OUT, "Table_S12_brazil.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
wp = rd(os.path.join(DATA, "si_world_prices_club.csv")); print("world prices (club):", {r["item"]: round(float(r["pw_pct"]), 2) for r in wp if r["item"].lower() in LAND})
print("done")
