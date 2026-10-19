"""Replay the headline runs under the geopolitical schedules and re-read the one-deviation tests with the new thresholds."""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from replay import replay, thresholds_trade, SUFFIX, DB, load_run
geo = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "geo_schedule.json"))); g = geo["g"]
trade = thresholds_trade()
FLOOR = 2.0
sched = {"trade (0.1 %)": trade,
         "geo symmetric": {r: (max(FLOOR, t[0] * g[r]), max(FLOOR, t[1] * g[r])) for r, t in trade.items()},
         "geo asymmetric": {r: (max(FLOOR, t[0] / g[r]), max(FLOOR, t[1] * g[r])) for r, t in trade.items()}}
RUNS = [("pha0_tau1.5charged", "club 1.5 %"), ("pha0_tau1.25charged", "club 1.25 %"), ("pha0_tau1charged", "club 1.0 %"),
        ("pha4000_tau0", "coalition 4,000"), ("pha2000_tau0", "coalition 2,000"), ("pha1500_tau0", "coalition 1,500"),
        ("pha3500_tau0", "coalition 3,500"), ("pha3000_tau0", "coalition 3,000")]
def path_actual(tag):
    its, ev, club = load_run(tag); return {k: {r for r in club[k] if club[k][r]} for k in its}
for tag, name in RUNS:
    full = tag + SUFFIX
    try: actual = path_actual(full)
    except FileNotFoundError: print(name, "missing"); continue
    last = max(actual)
    print(f"\n=== {name}: {len(actual[last])} members at convergence (iteration {last})")
    for sname, thr in sched.items():
        path, dec, kdiv, extra, missing = replay(full, thr)
        if kdiv is None:
            print(f"  {sname:15s}: identical path through convergence")
        else:
            # the decisions at iteration kdiv-1 that differ
            diff = [d for d in dec if d[0] == kdiv - 1 and d[1] in set(extra) | set(missing)]
            txt = "; ".join(f"{d[1]} ({d[2]}) measure {d[3]:.1f} vs threshold {d[4]:.1f} -> {d[6]}" for d in diff)
            print(f"  {sname:15s}: diverges at iteration {kdiv}: replay adds {extra}, drops {missing} | {txt}")
# the one-deviation tests: gains from the Stability files against the thresholds
print("\n=== one-deviation tests (gain from moving vs threshold)")
files = [f for f in os.listdir(DB) if f.startswith("Stability_") and f.endswith("_v32.txt")]
for f in sorted(files):
    txt = open(os.path.join(DB, f)).read()
    seed = re.search(r"seed(Smin\w+?)_fixed", f).group(1)
    charge = re.search(r"forest_(pha\d+_tau[\d.]+(?:charged)?)", f).group(1)
    # parse the table: region status ... gain_from_moving threshold
    lines = txt.split("\n")
    hdr_i = next(i for i, l in enumerate(lines) if l.strip().startswith("region"))
    hdr = lines[hdr_i].split()
    rows = []
    for l in lines[hdr_i + 1:]:
        p = l.split()
        if len(p) < len(hdr) or p[0] == "eu27": continue
        d = dict(zip(hdr, p)); rows.append(d)
    out = []
    for d in rows:
        r = d["region"]; gain = float(d["gain_from_moving"]); st = d["status"]
        verdict = {}
        for sname, thr in sched.items():
            t = thr[r][0] if st == "member" else thr[r][1]
            verdict[sname] = gain > t
        if gain > 0:
            out.append(f"{r} ({'leaves' if st == 'member' else 'joins'}) gain {gain:.1f}: " + ", ".join(f"{k}: {'moves' if v else 'stays'} (thr {sched[k][r][0 if st == 'member' else 1]:.1f})" for k, v in verdict.items()))
    print(f"\n{charge} {seed}:")
    for o in out: print("   ", o)
