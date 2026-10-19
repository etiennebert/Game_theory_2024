"""The tables of the Results, from all_data_<label>.json (extract_all.py first). Writes Tables_<label>.md (the three tables,
ready to paste) and Table1_<label>.csv, Table2_<label>.csv, Table3_<label>.csv (every number, net and gross) to the figures folder.

Table 1  the club at the lowest working charge for every starting point on the disk (and the headline charges when they differ):
         members, rounds, forest kept inside (members' tropical forest, and all zones) and lost outside (non-members, leakage),
         welfare inside / outside / world on the decision measure (net of the forest-land wedge term), and Brazil / EU / US / China;
         a second block gives the same welfare columns on GTAP's gross EV.
Table 2  the EU-alone thresholds at each switching cost on the disk (penalty and surcharge: highest failing / lowest working).
Table 3  the headline club and coalition with a region locked out (Brazil, the US, US + China, Indonesia), when on the disk.
Every forest number is relative to the EUDR world (Stage B); welfare in USD of 2019 per year."""
import os, sys; sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "common"))   # the shared modules of the pipeline (paths, figstyle, mapping, v30)
import json, csv, os
from paths import here, fig as figpath, LABEL
from figstyle import NAMES
D = json.load(open(here("all_data.json"))); C = D["configs"]; THR = D["thresholds"]; RUNS = {r["tag"]: r for r in D["runs"]}; HL = D["headline"]; TOP = D["top"]
SEEDS = {"EU": "EU", "EUChina": "EU + China", "EUMercosur": "EU + Mercosur", "EUMercosurChina": "EU + Mercosur + China", "EUMercosur5": "EU + Mercosur + Bolivia"}

def m(v, nd=0):   # minus sign, thousands separator
    return (f"{v:+,.{nd}f}" if nd else f"{v:+,.0f}").replace("-", "−")
def bn(v): return m(v / 1000, 2)
def lk(v): return f"{v:,.0f}".replace("-", "\u2212")   # kha, no sign when positive
def charge(pha, tau):
    if pha and tau: return f"{pha:,} USD/ha + {tau:g} %"
    return f"{pha:,} USD/ha" if pha else (f"{tau:g} %" if tau else "none")
def inst_name(pha, tau):
    if pha and tau: return "Surcharge + penalty"
    return "Footprint surcharge" if pha else ("Flat penalty" if tau else "No charge")
def leavers(r):
    """seed members (round 1) that are outside at convergence"""
    mb = r.get("members_by_round")
    if not mb: return []
    return [c for c in mb.get("1", []) if c not in r["final_members"]]
def gross_sums(r):
    g = r.get("ev_gross") or {}
    if not g: return None, None
    return sum(g[c] for c in r["final_members"]), sum(g[c] for c in r["outsiders"])

# ---------------------------------------------------------------- Table 1 rows
rows = []
def add(seed, r, fail, note=""):
    if r is None: return
    if any(x["tag"] == r["tag"] for x in rows): return
    mg, og = gross_sums(r); lv = leavers(r)
    rows.append(dict(seed=SEEDS.get(seed, seed), inst=inst_name(r["pha"], r["tau"]), tag=r["tag"], pha=r["pha"], tau=r["tau"],
                     works=charge(r["pha"], r["tau"]), fails=charge(fail["pha"], fail["tau"]) if fail else None, note=note or (", ".join(NAMES[c] for c in lv) + " leaves" if lv else ""),
                     rounds=r["last"], n=r["n"], brazil_in=r["works"], forest=r["forest"], forest_all=r["forest_all"], leak=1000 * r["leakage"], leak_all=1000 * r["leakage_all"],
                     net=r["net"], net_all=r["net_all"], ev_in=r["members_ev"], ev_out=r["outsiders_ev"], world=r["world"], ev_in_g=mg, ev_out_g=og, world_g=r["world_gross"],
                     brasil=r["brasil"], eu=r["eu"], us=r["us"], china=r["china"],
                     brasil_g=(r.get("ev_gross") or {}).get("brasil"), eu_g=(r.get("ev_gross") or {}).get("eu27"), us_g=(r.get("ev_gross") or {}).get("us"), china_g=(r.get("ev_gross") or {}).get("china")))
def by_tag(tag): return C.get(tag) or RUNS.get(tag)
# EU alone: the headline club and coalition, then the lowest working charge when it differs
for inst, key in (("penalty", "EU_pen"), ("surcharge", "EU_sur")):
    t = THR[f"EU|{inst}"]
    is_min = bool(t["work"] and key in C and C[key]["tag"] == t["work"]["tag"])
    if key in C:
        note = "headline" if is_min else ("headline; works from " + charge(t["work"]["pha"], t["work"]["tau"]) + ", next row" if t["work"] else "headline")
        add("EU", C[key], t["fail"], note)
    if t["work"] and not is_min: add("EU", RUNS.get(t["work"]["tag"]), t["fail"], "lowest working charge")
# the other starting points at the lowest working charge (or no charge)
for seed in ("EUMercosur", "EUChina", "EUMercosurChina", "EUMercosur5"):
    for inst in ("penalty", "surcharge"):
        t = THR.get(f"{seed}|{inst}")
        if t and t["work"]:
            r = RUNS.get(t["work"]["tag"]); r = next((c for c in C.values() if c["tag"] == r["tag"]), r) if r else None
            add(seed, r, t["fail"])
# both instruments (the exchange rate): the penalty at a fixed surcharge
for k, t in sorted(THR.items(), key=lambda kv: -(kv[1].get("pha") or 0)):
    if k.startswith("EU|penalty_at_pha") and t["work"]: add("EU", RUNS.get(t["work"]["tag"]), t["fail"])

# ---------------------------------------------------------------- Table 2: the EU-alone thresholds by switching cost
T_BR = D["T"]["brasil"]
frs = sorted({0.001} | {v["fr"] for k, v in THR.items() if "|fr" in k})
t2 = []
for fr in frs:
    row = dict(fr=fr, T=T_BR * fr / 0.001)
    for inst in ("penalty", "surcharge"):
        t = THR.get(f"EU|{inst}" if fr == 0.001 else f"EU|{inst}|fr{fr:g}".replace("fr0.0005", "fr0.0005"))
        if t is None: t = next((v for k, v in THR.items() if v.get("seed") == "EU" and v["inst"] == inst and abs(v.get("fr", 0.001) - fr) < 1e-12 and "pha" not in v), None)
        f, w = (t or {}).get("fail"), (t or {}).get("work")
        row[inst] = dict(fail=f and (f["tau"] if inst == "penalty" else f["pha"]), work=w and (w["tau"] if inst == "penalty" else w["pha"]),
                         n=w and w["n"], forest=w and w["forest"], n_f=f and f["n"], forest_f=f and f["forest"])
    t2.append(row)

# ---------------------------------------------------------------- Table 3: lock-outs
t3 = []
for inst, key in (("penalty", "EU_pen"), ("surcharge", "EU_sur")):
    for lock, lab in (("", "nobody"), ("brasil", "Brazil"), ("us", "United States"), ("us-china", "United States and China"), ("indonesia", "Indonesia")):
        k = key if not lock else f"{key}_lock{lock}"
        if k not in C: continue
        r = C[k]; t3.append(dict(inst=charge(r["pha"], r["tau"]), lock=lab, rounds=r["last"], n=r["n"], forest=r["forest"], leak=1000 * r["leakage"], world=r["world"], world_g=r["world_gross"],
                                 brasil=r["brasil"], eu=r["eu"], us=r["us"], china=r["china"], out=[NAMES[c] for c in TOP if c not in r["final_members"]], tag=r["tag"]))

# ---------------------------------------------------------------- write
L = []
L.append(f"# Tables of the Results, {LABEL} runs\n")
L.append("Forest relative to the EUDR world (Stage B), five years; welfare = equivalent variation per year in USD of 2019, on the decision measure (net of the forest-land wedge term) unless marked gross. Switching cost 0.1 % of trade.\n")
L.append("## Table 1 | The Forest Club at convergence, by starting coalition and instrument\n")
L.append("| Starting coalition | Instrument | Charge that works (highest that fails) | Rounds | Members | Forest kept inside: tropical (all zones), Mha | Forest lost outside: tropical (all zones), kha | Welfare inside / outside / world, bn USD per yr | Brazil / EU / US / China, M USD per yr |")
L.append("|---|---|---|---|---|---|---|---|---|")
for r in rows:
    wf = r["works"] + (f" (fails at {r['fails']})" if r["fails"] else " (no failing run below yet)" if r["inst"] != "No charge" else "")
    note = f"; {r['note']}" if r["note"] else ""
    L.append(f"| {r['seed']} | {r['inst']} | {wf}{note} | {r['rounds']} | {r['n']}{'' if r['brazil_in'] else ' (Brazil outside)'} | {r['forest']:.1f} ({r['forest_all']:.1f}) | {lk(r['leak'])} ({lk(r['leak_all'])}) | "
             f"{bn(r['ev_in'])} / {bn(r['ev_out'])} / {bn(r['world'])} | {m(r['brasil'])} / {m(r['eu'])} / {m(r['us'])} / {m(r['china'])} |")
L.append("\nInside = members at convergence, outside = non-members. Forest kept and lost relative to the EUDR world over five years; a negative loss outside means the non-members cleared less than in the EUDR world. "
         "The same rows on GTAP's gross equivalent variation (before the wedge term):\n")
L.append("| Starting coalition | Charge | Welfare inside / outside / world, gross, bn USD per yr | Brazil / EU / US / China, gross, M USD per yr |")
L.append("|---|---|---|---|")
for r in rows:
    if r["world_g"] is None: continue
    L.append(f"| {r['seed']} | {r['works']} | {bn(r['ev_in_g'])} / {bn(r['ev_out_g'])} / {bn(r['world_g'])} | {m(r['brasil_g'])} / {m(r['eu_g'])} / {m(r['us_g'])} / {m(r['china_g'])} |")
L.append("\n## Table 2 | The EU-alone thresholds by switching cost\n")
L.append("| Switching cost (Brazil's, M USD per yr) | Penalty: fails / works | Members, Mha kept (at the working charge) | Surcharge, USD/ha: fails / works | Members, Mha kept |")
L.append("|---|---|---|---|---|")
for r in t2:
    p, s = r["penalty"], r["surcharge"]
    fmtp = lambda v: "–" if v is None else f"{v:g} %"; fmts = lambda v: "–" if v is None else f"{v:,}"
    nf = lambda x: ("\u2013" if x["n"] is None else str(x["n"])) + ", " + ("\u2013" if x["forest"] is None else f"{x['forest']:.1f}")
    L.append(f"| {100 * r['fr']:g} % of trade ({r['T']:.0f}) | {fmtp(p['fail'])} / {fmtp(p['work'])} | {nf(p)} | {fmts(s['fail'])} / {fmts(s['work'])} | {nf(s)} |")
if t3:
    L.append("\n## Table 3 | The headline club and coalition with a region locked out\n")
    L.append("| Instrument | Locked out | Rounds | Members | Forest kept inside, tropical, Mha | Lost outside, kha | World welfare, bn USD per yr (gross) | Brazil / EU / US / China, M USD per yr | Of the eight largest deforesters, outside at convergence |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for r in t3:
        L.append(f"| {r['inst']} | {r['lock']} | {r['rounds']} | {r['n']} | {r['forest']:.1f} | {lk(r['leak'])} | {bn(r['world'])} ({bn(r['world_g']) if r['world_g'] is not None else '–'}) | "
                 f"{m(r['brasil'])} / {m(r['eu'])} / {m(r['us'])} / {m(r['china'])} | {', '.join(r['out']) or 'none'} |")
open(figpath(f"Tables_{LABEL}.md"), "w").write("\n".join(L) + "\n")
with open(figpath(f"Table1_{LABEL}.csv"), "w", newline="") as f:
    w = csv.writer(f); keys = ["seed", "inst", "works", "fails", "note", "tag", "pha", "tau", "rounds", "n", "brazil_in", "forest", "forest_all", "leak", "leak_all", "net", "net_all",
                               "ev_in", "ev_out", "world", "ev_in_g", "ev_out_g", "world_g", "brasil", "eu", "us", "china", "brasil_g", "eu_g", "us_g", "china_g"]
    w.writerow(["starting_coalition", "instrument", "charge_works", "charge_fails", "note", "tag", "surcharge_usd_per_ha", "penalty_pct", "rounds", "members", "brazil_inside",
                "forest_kept_inside_tropical_Mha", "forest_kept_inside_all_zones_Mha", "forest_lost_outside_tropical_kha", "forest_lost_outside_all_zones_kha", "net_forest_tropical_Mha", "net_forest_all_zones_Mha",
                "EV_net_inside_MUSD", "EV_net_outside_MUSD", "EV_net_world_MUSD", "EV_gross_inside_MUSD", "EV_gross_outside_MUSD", "EV_gross_world_MUSD",
                "Brazil_net_MUSD", "EU_net_MUSD", "US_net_MUSD", "China_net_MUSD", "Brazil_gross_MUSD", "EU_gross_MUSD", "US_gross_MUSD", "China_gross_MUSD"])
    for r in rows: w.writerow([round(r[k], 3) if isinstance(r[k], float) else r[k] for k in keys])
with open(figpath(f"Table2_{LABEL}.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["switching_cost_share_of_trade", "brazil_switching_cost_MUSD", "penalty_fails_pct", "penalty_works_pct", "members_at_working_penalty", "forest_Mha_at_working_penalty", "members_at_failing_penalty", "forest_Mha_at_failing_penalty",
                                   "surcharge_fails_usd_per_ha", "surcharge_works_usd_per_ha", "members_at_working_surcharge", "forest_Mha_at_working_surcharge", "members_at_failing_surcharge", "forest_Mha_at_failing_surcharge"])
    for r in t2:
        p, s = r["penalty"], r["surcharge"]; rd = lambda v: "" if v is None else (round(v, 3) if isinstance(v, float) else v)
        w.writerow([r["fr"], round(r["T"], 1), rd(p["fail"]), rd(p["work"]), rd(p["n"]), rd(p["forest"]), rd(p["n_f"]), rd(p["forest_f"]), rd(s["fail"]), rd(s["work"]), rd(s["n"]), rd(s["forest"]), rd(s["n_f"]), rd(s["forest_f"])])
with open(figpath(f"Table3_{LABEL}.csv"), "w", newline="") as f:
    w = csv.writer(f); w.writerow(["instrument", "locked_out", "tag", "rounds", "members", "forest_kept_inside_tropical_Mha", "forest_lost_outside_tropical_kha", "EV_net_world_MUSD", "EV_gross_world_MUSD", "Brazil_net_MUSD", "EU_net_MUSD", "US_net_MUSD", "China_net_MUSD", "largest_deforesters_outside"])
    for r in t3: w.writerow([r["inst"], r["lock"], r["tag"], r["rounds"], r["n"], round(r["forest"], 3), round(r["leak"], 1), round(r["world"], 1), "" if r["world_g"] is None else round(r["world_g"], 1), round(r["brasil"], 1), round(r["eu"], 1), round(r["us"], 1), round(r["china"], 1), "; ".join(r["out"])])
print("ok:", len(rows), "rows in Table 1,", len(t2), "in Table 2,", len(t3), "in Table 3 ->", figpath(f"Tables_{LABEL}.md"))
