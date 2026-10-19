"""The run-level data behind Fig. 3 (the instrument plane), Extended Data Fig. 1 and 2, from all_data_<label>.json (run
extract_all.py first). Writes, next to this script and suffixed with the generation label:
  plane_runs.json       every converged EU-alone and EU + China run at the standard switching cost (0.1 % of trade), no lock-out:
                        surcharge x penalty, members, forest kept and leaked, world / members' / outsiders' welfare (decision
                        measure, and gross = GTAP's EV), EU / Brazil / China / US welfare, Brazil's first-round loss, which of the
                        eight largest deforesters are inside at convergence                               -> fig3_plane.py (a-d)
  top_deforesters.json  the same runs, for each of the eight largest deforesters: first-round loss, switching cost, round of
                        joining, membership and welfare at convergence                                    -> extdata_fig2_deforesters.py
  counterfactuals.json  the headline club and coalition with Brazil, the US, the US + China or Indonesia locked out -> fig3_plane.py (e)
"""
import json
from paths import here
D = json.load(open(here("all_data.json"))); T = D["T"]; TOP = D["top"]; C = D["configs"]

plane, top = [], []
for r in D["runs"]:
    if r["seed"] not in ("EU", "EUChina") or r["lock"] or abs(r["fr"] - 0.001) > 1e-12 or r["fixed"]: continue
    plane.append(dict(seed=r["seed"], pha=r["pha"], tau=r["tau"], tag=r["tag"], rounds=r["last"], n=r["n"], members=r["final_members"], works=r["works"], converged=r["converged"],
                      forest=r["forest"], forest_all=r["forest_all"], leakage=r["leakage"], leakage_all=r["leakage_all"], world=r["world"], world_gross=r["world_gross"],
                      members_ev=r["members_ev"], outsiders_ev=r["outsiders_ev"], eu=r["eu"], brasil=r["brasil"], china=r["china"], us=r["us"],
                      brazil_r1=r["brazil_r1_loss"], top_in=r["top_in"]))
    rec = dict(seed=r["seed"], pha=r["pha"], tau=r["tau"], last=r["last"], works=r["works"])
    for c in TOP:
        rec[c] = dict(r1=round(r["r1"][c], 2), T=round(T[c], 3), joins=r["joins"].get(c), final=c in r["final_members"], dev_final=round(r["ev"][c], 1))
    top.append(rec)
json.dump(plane, open(here("plane_runs.json"), "w"), indent=1)
json.dump(top, open(here("top_deforesters.json"), "w"), indent=1)
print(len(plane), "runs in the plane:", sorted((p["seed"], p["pha"], p["tau"], "ok" if p["works"] else "no") for p in plane))

cf = {}
for inst, key in (("pen", "EU_pen"), ("sur", "EU_sur")):
    for lock, lab in (("", "free"), ("brasil", "lockBRA"), ("us", "lockUS"), ("us-china", "lockUS-CN"), ("indonesia", "lockIDN")):
        k = key if not lock else f"{key}_lock{lock}"
        if k not in C: continue
        s = C[k]
        cf[f"{inst} {lab}"] = dict(label=s["label"], lock=lock, n=s["n"], forest=s["forest"], leakage=s["leakage"], world=s["world"], world_gross=s["world_gross"], top_in=s["top_in"],
                                   members=s["final_members"], rounds=s["last"], eu=s["eu"], us=s["us"], brasil=s["brasil"], china=s["china"], pha=s["pha"], tau=s["tau"])
json.dump(cf, open(here("counterfactuals.json"), "w"), indent=1)
for k, v in cf.items(): print(f"{k:14s} rounds {v['rounds']}  members {v['n']:2d}  forest {v['forest']:5.2f} Mha  world {v['world']:+6.0f}  inside: {', '.join(v['top_in'])}")
