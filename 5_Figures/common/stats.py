"""stats_<label>.json and a printed digest of every run of the generation (paths.VERSION) the Results quote: members, rounds, forest kept and leaked (tropical
and all forest), welfare by region in M USD and in % of GDP, real GDP, the join/leave sequence, the eight largest
deforesters' first-round loss against their switching cost. Reads all_data_<label>.json (extract_all.py first) and 4_DB.
Add a (label, tag) pair to EXTRA to get the numbers of any other run."""
import json, os, sys
from paths import here, LABEL
import v30
from figstyle import NAMES

D = json.load(open(here("all_data.json"))); gdp = D["gdp"]; T = D["T"]; base = D["bau"]
EXTRA = {}   # e.g. {"penalty 2.5 (plane)": v30.tag_of(0, 2.5)}
runs = {}
for key in ("EU_pen_below", "EU_pen", "EU_sur_below", "EU_sur", "EUC_pen", "EUC_sur", "EUM_0", "EUMC_0", "EU_pen_lockbrasil", "EU_pen_lockus", "EU_sur_lockbrasil", "EU_sur_lockus"):
    if key in D["configs"]: runs[D["configs"][key]["label"]] = D["configs"][key]["tag"]
for k, v in D["thresholds"].items():   # every bracket-closing run of the searches (seeds, exchange rate, switching cost)
    for side in ("fail", "work"):
        r = v[side]
        if r and r["tag"] not in runs.values(): runs[f"{k} · {side}s at {r['tau'] if v['inst'] == 'penalty' else r['pha']}"] = r["tag"]
runs.update(EXTRA)

def fmt(v): return f"{v:+,.0f}".replace("-", "−")
out = {}
for name, tag in runs.items():
    if not os.path.exists(v30.csv_path(tag)): print("missing:", tag); continue
    s = v30.run_stats(tag, gdp, T)
    mem, outs = s["final_members"], s["outsiders"]
    print("=" * 100)
    print(f"{name}  [{tag}]")
    print(f"  {s['outcome']} | members {s['n']} | rounds {s['last']} | forest kept {s['forest']:.2f} Mha tropical ({s['forest_all']:.2f} all forest) of "
          f"{base['bau_trop_total']:.2f} ({base['bau_all_total']:.2f}) BAU | leakage {s['leakage']:.3f} Mha tropical ({s['leakage_all']:.3f} all) = "
          f"{100 * s['leakage'] / s['forest'] if s['forest'] else float('nan'):.1f}% of kept | net {s['net']:.2f} ({s['net_all']:.2f})")
    print(f"  world EV {fmt(s['world'])} M USD/yr | members {fmt(s['members_ev'])} | outsiders {fmt(s['outsiders_ev'])} | "
          f"EU {fmt(s['eu'])} | Brazil {fmt(s['brasil'])} ({s['ev_pct']['brasil']:+.3f}% GDP) | China {fmt(s['china'])} | US {fmt(s['us'])}")
    print("  outsiders:", " ".join(outs) if outs else "none", f"| their BAU tropical clearing {sum(base['bau_trop'][c] for c in outs):.2f} Mha")
    print("  members EV (M USD, % GDP):", ", ".join(f"{c} {fmt(s['ev'][c])} ({s['ev_pct'][c]:+.3f}%)" for c in sorted(mem, key=lambda c: s["ev"][c])))
    print("  outsiders EV:", ", ".join(f"{c} {fmt(s['ev'][c])} ({s['ev_pct'][c]:+.3f}%)" for c in sorted(outs, key=lambda c: s["ev"][c])))
    print("  leakage by outsider (kha, tropical / all):", ", ".join(f"{c} {1000 * s['leak'][c]:+.0f}/{1000 * s['leak_all'][c]:+.0f}" for c in sorted(outs, key=lambda c: -s["leak_all"][c]) if abs(s["leak_all"][c]) > 0.001))
    print("  members' temperate + boreal change (kha):", ", ".join(f"{c} {1000 * (s['dtemp'][c] + s['dbor'][c]):+.0f}" for c in sorted(mem, key=lambda c: -(s["dtemp"][c] + s["dbor"][c])) if abs(s["dtemp"][c] + s["dbor"][c]) > 0.001)[:400])
    print("  real GDP change of members (pp), lowest:", ", ".join(f"{c} {s['gdp_pct'][c]:+.4f}" for c in sorted(mem, key=lambda c: s["gdp_pct"][c])[:5]))
    Ts = s.get("T", T)   # the switching cost at this run's share of trade
    print("  first-round loss / switching cost, largest deforesters:", ", ".join(f"{c} {s['r1'][c]:.0f}/{Ts[c]:.0f} = {s['r1'][c] / Ts[c]:.2f}" for c in v30.TOP))
    print("  charge alone (round 1, before anyone joins): outsiders' tropical forest change", f"{1000 * s['charge_alone'].get('trop', 0):+.0f} kha, all forest {1000 * sum(s['charge_alone'].values()):+.0f} kha")
    prev = set()
    for i, m in s["members_by_round"].items():
        cur = set(m); print(f"   round {i}: n={len(cur)} +{' '.join(sorted(cur - prev))} -{' '.join(sorted(prev - cur))}"); prev = cur
    out[name] = {k: v for k, v in s.items() if k not in ("ev_path", "members_by_round")}
json.dump(out, open(here("stats.json"), "w"), indent=1)
print("\nEUDR alone (Stage B):", f"tropical {1000 * base['eudr_trop_total']:+.1f} kha, all forest {1000 * base['eudr_all_total']:+.1f} kha, world EV {fmt(base['eudr_world'])} M USD/yr;",
      "by region (kha tropical):", ", ".join(f"{c} {1000 * v:+.1f}" for c, v in sorted(base["eudr_trop"].items(), key=lambda x: -abs(x[1])) if abs(v) > 0.0005))
