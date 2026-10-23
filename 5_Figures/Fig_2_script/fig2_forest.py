"""Fig. 2: the forest, when the EU alone charges (V30: the game from the business-as-usual world, EUDR kept on outsiders).
a  maps: forest kept by members (green) and forest lost by outsiders (orange, leakage) at the headline penalty and
   surcharge, five-year change relative to the EUDR world, all forest zones, in Mha with the SAME class breaks on both sides,
   so that the colour intensity of a loss outside can be compared with that of a gain inside (most losses fall in the lightest class)
b  number of members round by round, four starting points (EU alone x two instruments, EU + China, EU + Mercosur)
c  tropical forest kept by member region at convergence, every configuration on the disk
d  forest lost outside the club (leakage) by outsider region, same configurations, tropical (dot) and all forest (ring)
Reads all_data.json; writes Fig2_forest.png/.pdf and Fig2_source_data.csv."""

import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))   # the shared modules of the pipeline (paths, figstyle, mapping, v30)
import json, csv
from figstyle import *
style()
from paths import here, fig as figpath
d = json.load(open(here("all_data.json"))); C = d["configs"]; base = d["bau"]
BAU = base["bau_trop_total"]; BAU_ALL = base["bau_all_total"]
TROP = [c for c, v in sorted(base["bau_trop"].items(), key=lambda x: -x[1]) if v >= 0.1]   # tropical forest regions: >= 0.1 Mha of BAU clearing
ORDER = [("EU_pen", "EU alone · penalty"), ("EU_sur", "EU alone · surcharge"), ("EUC_pen", "EU + China · penalty"), ("EUC_sur", "EU + China · surcharge"),
         ("EUM_0", "EU + Mercosur · no charge"), ("EUMC_0", "EU + Mercosur + China · no charge")]
rows = [(k, C[k]["label"]) for k, _ in ORDER if k in C]
mm = 1 / 25.4
fig = plt.figure(figsize=(183 * mm, 212 * mm))
def short(k):
    r = C[k]; return f"{r['forest_all']:.1f} Mha kept, {r['leakage_all']:.2f} Mha lost outside"

# ---------- a: maps ----------
BRK = [0.001, 0.1, 0.5, 1.0, 3.0, 1e9]                                     # one set of class breaks, Mha, for both sides
KC = GREENS[1:]                                                             # kept by members, all zones
LC = ["#fbcbba", "#f5a07e", "#e9743f", "#c04d14", "#86300a"]                # lost by non-members, all zones (same breaks)
def cls(v):
    """class index 0-4 of a change of v Mha, or None below 1 kha"""
    if v < BRK[0]: return None
    for i in range(len(BRK) - 1):
        if BRK[i] <= v < BRK[i + 1]: return i
    return len(BRK) - 2
def draw_kept_lost(ax, r):
    g, _ = regions_gdf(); mem = set(r["final_members"])
    def col(reg):
        if reg in mem:
            i = cls(r["kept_all"].get(reg, 0.0)); return MEMBER0 if i is None else KC[i]
        i = cls(r["leak_all"].get(reg, 0.0)); return OUTSIDE if i is None else LC[i]
    g = g.copy(); g["c"] = g["region"].map(col); g.plot(ax=ax, color=g["c"], edgecolor=SURF, linewidth=0.25)
    ax.set_axis_off(); ax.set_xlim(-1.7e7, 1.7e7); ax.set_ylim(-6.0e6, 8.7e6)
for j, k in enumerate(["EU_pen", "EU_sur"]):
    if k not in C: continue
    ax = fig.add_axes([0.005 + 0.5 * j, 0.745, 0.49, 0.235]); r = C[k]
    draw_kept_lost(ax, r)
    ax.set_title(f"{(lambda t: t[:1].upper() + t[1:])(r['label'].replace('EU alone · ', ''))}  ·  {r['n']} members  ·  {short(k)}", loc="left", fontsize=6.2, pad=2, x=0.035)
    if j == 0: panel(ax, "a", x=0.0, y=1.06)
lab = [f"{BRK[i]:g}–{BRK[i+1]:g}" if i < 4 else f"> {BRK[4]:g}" for i in range(5)]
items = [(MEMBER0, "Member, < 0.001")] + [(KC[i], lab[i]) for i in range(5)] + [(OUTSIDE, "Non-member, < 0.001")] + [(LC[i], lab[i]) for i in range(5)]
handles = [Patch(facecolor=c, edgecolor=GRID if c in (OUTSIDE, MEMBER0) else c, linewidth=0.4) for c, _ in items]
fig.legend(handles, [l for _, l in items], loc="center", bbox_to_anchor=(0.5, 0.728), ncol=12, frameon=False, fontsize=5.6, handlelength=1.2,
           columnspacing=0.7, handletextpad=0.35, labelcolor=INK2,
           title="Five-year change relative to the EUDR world, all forest zones, Mha:  forest kept by members (green)  ·  forest lost by non-members (orange), same classes", title_fontsize=6.2)

# ---------- b: members round by round ----------
confs = [k for k in ("EU_pen", "EU_sur", "EUC_pen", "EUM_0") if k in C]
for j, k in enumerate(confs):
    ax = fig.add_axes([0.075 + 0.235 * j, 0.465, 0.205, 0.20]); r = C[k]; last = r["last"]
    mbr = d["configs"][k].get("members_by_round") or {}
    if not mbr:   # members by round were slimmed out of the json for the run list but kept for configs
        raise SystemExit("members_by_round missing from configs")
    rounds = list(range(1, last + 1))
    tro = [len([c for c in mbr[str(i)] if c in TROP]) for i in rounds]
    oth = [len(mbr[str(i)]) - t for i, t in zip(rounds, tro)]
    ax.bar(rounds, tro, width=0.66, color=DARK, edgecolor=SURF, linewidth=0.7, zorder=3)
    ax.bar(rounds, oth, width=0.66, bottom=tro, color=LIGHT, edgecolor=SURF, linewidth=0.7, zorder=3)
    for x, t, o in zip(rounds, tro, oth): ax.text(x, t + o + 0.8, f"{t+o}", ha="center", va="bottom", fontsize=5.6, color=INK2)
    xmax = max(8, last); ax.set_xlim(0.4, xmax + 0.6); ax.set_xticks(range(1, xmax + 1)); ax.set_ylim(0, 44); ax.set_yticks([0, 10, 20, 30, 40]); clean(ax, x=False)
    ax.set_title(r["label"].replace(" · ", ", "), loc="left", fontsize=6.4, pad=3)
    if j == 0: ax.set_ylabel("Members (of 42 regions)")
    else: ax.tick_params(labelleft=False)
    ax.set_xlabel("Round")
    jb = r["joins"].get("brasil")
    if jb and jb >= 2 and "brasil" not in mbr["1"]:
        ax.annotate("Brazil\njoins", xy=(jb, len(mbr[str(jb)]) + 3.5), xytext=(jb + 0.2, 36), fontsize=5.6, color=INK2, ha="left", va="center",
                    arrowprops=dict(arrowstyle="-", color=MUTED, linewidth=0.5, shrinkA=1, shrinkB=1))
    if j == 0: panel(ax, "b", x=-0.30, y=1.06)
fig.legend([Patch(facecolor=DARK), Patch(facecolor=LIGHT)], ["Tropical forest regions (≥ 0.1 Mha of business-as-usual clearing)", "Other regions (importers, incl. the EU)"],
           loc="upper left", bbox_to_anchor=(0.07, 0.712), ncol=2, frameon=False, fontsize=6.0, handlelength=1.2, columnspacing=2.0, labelcolor=INK2)

# ---------- c: forest kept by member region ----------
SEG = ["brasil", "drc", "seasia", "bolivia", "ivorycoast", "indonesia", "nigeria"]
SEGC = dict(zip(SEG, ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7"])); OTHER = "#9b9a94"
axc = fig.add_axes([0.215, 0.115, 0.40, 0.27])
for i, (k, lab) in enumerate(rows):
    r = C[k]; mem = set(r["final_members"]); left = 0
    for c in SEG:
        v = r["kept"].get(c, 0) if c in mem else 0
        if v > 0.005:
            axc.barh(i, v, left=left, height=0.6, color=SEGC[c], edgecolor=SURF, linewidth=0.8, zorder=3)
            if c == "brasil": axc.text(left + v / 2, i, f"Brazil {v:.1f}", ha="center", va="center", fontsize=5.8, color=SURF, zorder=4)
            left += v
    oth = sum(v for c, v in r["kept"].items() if c not in SEG and v > 0)
    if oth > 0.005: axc.barh(i, oth, left=left, height=0.6, color=OTHER, edgecolor=SURF, linewidth=0.8, zorder=3); left += oth
    axc.text(left + 0.3, i, f"{left:.1f} Mha ({100*left/BAU:.0f}%)", ha="left", va="center", fontsize=6, color=INK, zorder=5, bbox=dict(facecolor=SURF, edgecolor="none", pad=0.5))
axc.axvline(BAU, color=INK2, linewidth=0.7, zorder=2)
axc.text(BAU - 0.2, -0.75, f"All tropical business-as-usual clearing: {BAU:.1f} Mha", ha="right", va="bottom", fontsize=5.8, color=INK2)
axc.set_yticks(range(len(rows))); axc.set_yticklabels([l for _, l in rows], fontsize=6.3); axc.invert_yaxis(); axc.set_ylim(len(rows) - 0.4, -1.0)
axc.set_xlim(0, 24); axc.set_xticks([0, 5, 10, 15, 20]); clean(axc, y=False); axc.spines["left"].set_visible(False); axc.tick_params(axis="y", length=0)
axc.set_xlabel("Tropical forest kept by members at convergence (Mha, five years)")
panel(axc, "c", x=-0.52, y=1.0)
axc.legend([Patch(facecolor=SEGC[c]) for c in SEG] + [Patch(facecolor=OTHER)], [NAMES[c] for c in SEG] + ["Other members"], loc="upper left",
           bbox_to_anchor=(-0.52, -0.23), ncol=8, frameon=False, fontsize=5.8, handlelength=1.1, columnspacing=0.9, handletextpad=0.4, labelcolor=INK2)

# ---------- d: leakage by outsider region ----------
axd = fig.add_axes([0.70, 0.115, 0.27, 0.27], sharey=axc)
import math
_vmax = max(max(C[k]["leakage_all"], max(list(C[k]["leak_all"].values()) + [0])) for k, _ in rows)
XMAX = math.ceil(_vmax / 0.25) * 0.25 + 0.05
axd.axvline(0, color=BASE, linewidth=0.8, zorder=1)
for i, (k, lab) in enumerate(rows):
    r = C[k]; outs = r["outsiders"]
    pts = sorted(((r["leak"][c], r["leak_all"][c], c) for c in outs), key=lambda x: -x[1])
    for n_, (vt, va, c) in enumerate(pts):
        if max(abs(vt), abs(va)) < 0.001: continue
        off = (-0.14, 0.0, 0.14)[n_ % 3]
        axd.scatter([min(va, XMAX - 0.005)], [i + off], s=16, facecolor="none", edgecolor=INK2, linewidth=0.6, zorder=4, clip_on=False)
        axd.scatter([min(vt, XMAX - 0.005)], [i + off], s=9, color=INK2, edgecolor=SURF, linewidth=0.4, zorder=5, clip_on=False)
        if n_ < 2 and va >= 0.06 * XMAX: axd.text(min(va, XMAX - 0.005) + 0.015 * XMAX, i + off, NAMES[c], ha="left", va="center", fontsize=5.3, color=INK2, zorder=6)
    axd.plot([r["leakage"]] * 2, [i - 0.3, i + 0.3], color="#e9743f", linewidth=1.8, solid_capstyle="round", zorder=3)
    axd.plot([r["leakage_all"]] * 2, [i - 0.3, i + 0.3], color="#e9743f", linewidth=0.8, linestyle=(0, (1.5, 1.2)), zorder=3)
_step = 0.5 if XMAX > 1.2 else 0.25 if XMAX > 0.7 else 0.1
axd.set_xlim(-0.07 * XMAX, XMAX); _ticks = [round(_step * t, 2) for t in range(int(XMAX / _step) + 1)]; axd.set_xticks(_ticks); axd.set_xticklabels([f"{t:g}" for t in _ticks]); clean(axd, y=False); axd.spines["left"].set_visible(False); axd.tick_params(axis="y", length=0, labelleft=False)
axd.set_xlabel("Forest lost outside the club, five years\nrelative to the EUDR world (Mha)")
panel(axd, "d", x=-0.05, y=1.0)
axd.legend([Line2D([0], [0], color="none", marker="o", markersize=3.0, markerfacecolor=INK2, markeredgecolor=SURF),
            Line2D([0], [0], color="none", marker="o", markersize=4.0, markerfacecolor="none", markeredgecolor=INK2),
            Line2D([0], [0], color="#e9743f", linewidth=1.8), Line2D([0], [0], color="#e9743f", linewidth=0.8, linestyle=(0, (1.5, 1.2)))],
           ["Non-member, tropical", "Non-member, all zones", "Total, tropical", "Total, all zones"],
           loc="upper left", bbox_to_anchor=(-0.05, -0.23), frameon=False, fontsize=5.6, handlelength=1.4, labelcolor=INK2, ncol=2, columnspacing=0.8, handletextpad=0.5)

for ext in ("pdf", "png"): fig.savefig(figpath(f"Fig2_forest.{ext}"), dpi=450 if ext == "png" else None)
with open(figpath("Fig2_source_data.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["panel", "configuration", "item", "value", "unit"])
    for k, lab in rows:
        r = C[k]; mbr = r["members_by_round"]
        for c in sorted(r["final_members"]): w.writerow(["c", lab, NAMES.get(c, c), round(r["kept"].get(c, 0), 4), "Mha tropical forest kept over 5 yr vs the EUDR world (member)"])
        for c in sorted(r["final_members"]): w.writerow(["a", lab, NAMES.get(c, c), round(r["kept_all"].get(c, 0), 4), "Mha all forest kept over 5 yr (member)"])
        for i in range(1, r["last"] + 1):
            m = mbr[str(i)]; w.writerow(["b", lab, f"round {i}", f"{len([c for c in m if c in TROP])} tropical + {len([c for c in m if c not in TROP])} other", "members"])
        for c in sorted(r["outsiders"], key=lambda c: -r["leak_all"][c]):
            w.writerow(["a/d", lab, NAMES.get(c, c), round(1000 * r["leak"][c], 2), "kha tropical forest lost over 5 yr vs the EUDR world (non-member)"])
            w.writerow(["a/d", lab, NAMES.get(c, c), round(1000 * r["leak_all"][c], 2), "kha all forest lost (non-member)"])
        w.writerow(["d", lab, "all non-members", round(1000 * r["leakage"], 2), "kha tropical"]); w.writerow(["d", lab, "all non-members", round(1000 * r["leakage_all"], 2), "kha all zones"])
print("ok")
