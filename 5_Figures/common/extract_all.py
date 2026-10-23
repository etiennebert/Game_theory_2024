"""all_data_<label>.json: everything the figures, tables and the Results quote, read once from the model folder (paths.REPO)
for the generation of runs paths.VERSION (V32 by default; `python make_all.py --version _wnet` for the V31 runs).

  bau, eudr        Stage A clearing and Stage B (EUDR alone) effect by region (Mha) and the EUDR's welfare effect
  thresholds       for each seed and instrument, the highest failing and the lowest working charge among the runs on the disk
                   (EU alone, EU + China, EU + Mercosur, EU + Mercosur + China; the penalty at a fixed surcharge = the exchange
                   rate; the switching cost halved and doubled)
  configs          the runs the text and figures quote, keyed by role: EU_pen / EU_sur (the headline EU-alone club and coalition,
                   HEADLINE below: the values every other block of the programme uses), EU_pen_min / EU_sur_min (the lowest
                   working charge when it differs from the headline), EU_pen_below / EU_sur_below (the highest failing charge),
                   EUC_pen, EUC_sur, EUM_0, EUMC_0, EUM5_0 (the other seeds), the lock-outs (EU_pen_lockbrasil, EU_sur_lockus,
                   EU_pen_lockus-china, ...), the higher penalties (EU_pen_2.5, EU_pen_5), the plane point (EU_sur_6000);
                   each with members by round, forest kept and leaked by region (tropical and all forest), welfare by region on
                   the decision measure (net of the wedge term) and gross (GTAP's EV), the first-round losses, the joining
                   rounds, the real GDP change
  runs             every dynamic run of this generation on the disk, one summary each (the plane, the cliff figure)
  stability        the one-deviation tables, keyed like configs (matched on the seed, the charge and the final coalition of the tested run)
  gdp, T           GDP (M USD, 2019) and the switching costs at 0.1 % of trade (M USD per year)
Also writes brazil_runs_<label>.txt (the run folders and solution files extract_brazil_aez.R reads).
Missing runs are reported, never invented: a config whose run is not on the disk is absent from the json."""
import json, os, glob, re
from paths import here, LABEL, VERSION
import v30

HEADLINE = {"_wnet_v33": {"penalty": 1.25, "surcharge": 4000}}.get(VERSION, {"penalty": 1.5, "surcharge": 4000})   # the EU-alone values the programme is built on (Run_V32_all.R: Y and X);
# V33 (21 Oct 2026): Y = 1.25 % (the lowest working penalty), X = 4,000 USD/ha; the 2,500 coalition (lowest working surcharge) is EU_sur_min with its own lock-outs

gdp = v30.read_gdp()
metas = v30.all_runs(pin="all", eudr="keep")
if not metas: raise SystemExit(f"no run with the suffix '{VERSION}' (generation {LABEL}) found in 4_DB")
T = v30.read_thresholds(next((m["tag"] for m in metas if abs(m.get("fr", 0.001) - 0.001) < 1e-12), metas[0]["tag"]))   # a run at 0.1 % of trade (the first run is a fr0.0005 one once the brackets are in)
S = [v30.run_stats(m["tag"], gdp, T, m) for m in metas]
print(len(S), f"{LABEL} runs (pin all, EUDR kept on outsiders, suffix '{VERSION}')")
for s in sorted(S, key=lambda s: (s["seed"], s["lock"], s["fr"], s["pha"], s["tau"])):
    print(f"  {s['seed']:16s} lock={s['lock'] or '-':10s} fr={s['fr']:<6g} pha={s['pha']:5d} tau={s['tau']:<5g} {'WORKS' if s['works'] else 'fails':5s} n={s['n']:2d} rounds={s['last']:2d} "
          f"kept={s['forest']:6.2f} leak={s['leakage']:6.3f}/{s['leakage_all']:6.3f} world={s['world']:+6.0f} (gross {s['world_gross'] if s['world_gross'] is None else round(s['world_gross']):>5}) brasil={s['brasil']:+5.0f}  {s['outcome']}")

base = v30.read_baseline()
SEEDS = {"EU": "EU alone", "EUChina": "EU + China", "EUMercosur": "EU + Mercosur", "EUMercosurChina": "EU + Mercosur + China", "EUMercosur5": "EU + Mercosur-5"}
def brief(r): return None if r is None else dict(tag=r["tag"], pha=r["pha"], tau=r["tau"], n=r["n"], forest=r["forest"], leakage=r["leakage"], leakage_all=r["leakage_all"], world=r["world"], world_gross=r["world_gross"], works=r["works"])
thr = {}
for seed in SEEDS:
    for inst in ("penalty", "surcharge"):
        f, w = v30.brackets(S, seed, inst)
        thr[f"{seed}|{inst}"] = dict(seed=seed, inst=inst, fail=brief(f), work=brief(w))
for s in S:   # the exchange rate: the penalty at a fixed surcharge
    if s["seed"] == "EU" and not s["lock"] and s["pha"] > 0 and s["tau"] > 0 and abs(s["fr"] - 0.001) < 1e-12:
        key = f"EU|penalty_at_pha{s['pha']}"
        if key not in thr:
            f, w = v30.brackets(S, "EU", "penalty", pha=s["pha"]); thr[key] = dict(seed="EU", inst="penalty", pha=s["pha"], fail=brief(f), work=brief(w))
for fr in sorted({s["fr"] for s in S} - {0.001}):   # the switching cost halved and doubled
    for inst in ("penalty", "surcharge"):
        f, w = v30.brackets(S, "EU", inst, fr=fr); thr[f"EU|{inst}|fr{v30.fmt_num(fr)}"] = dict(seed="EU", inst=inst, fr=fr, fail=brief(f), work=brief(w))
for k, v in thr.items():
    if v["fail"] or v["work"]:
        x = lambda r: (r["tau"] if v["inst"] == "penalty" else r["pha"]) if r else "-"
        print(f"  {k:32s} fails at {x(v['fail'])}  works at {x(v['work'])}")

# ---- the configurations quoted in the text
def find(seed, pha, tau, lock="", fr=0.001):
    for s in S:
        if s["seed"] == seed and s["lock"] == lock and abs(s["fr"] - fr) < 1e-12 and s["pha"] == pha and abs(s["tau"] - tau) < 1e-9: return s
    return None
configs = {}
def add(key, label, s):
    if s is None: print("  config", key, "not on the disk yet"); return
    configs[key] = dict(s, label=label)
Y, X = HEADLINE["penalty"], HEADLINE["surcharge"]
add("EU_pen", f"EU alone · penalty {Y:g}%", find("EU", 0, Y))
add("EU_sur", f"EU alone · surcharge {X:,} USD/ha", find("EU", X, 0))
if "EU_pen" in configs and not configs["EU_pen"]["works"]: print("  WARNING: the headline penalty club does not form in this generation")
if "EU_sur" in configs and not configs["EU_sur"]["works"]: print("  WARNING: the headline surcharge coalition does not form in this generation")
w = thr["EU|penalty"]["work"]
if w and abs(w["tau"] - Y) > 1e-9: add("EU_pen_min", f"EU alone · penalty {w['tau']:g}% (lowest working)", find("EU", 0, w["tau"]))
w = thr["EU|surcharge"]["work"]
if w and w["pha"] != X: add("EU_sur_min", f"EU alone · surcharge {w['pha']:,} USD/ha (lowest working)", find("EU", w["pha"], 0))
if thr["EU|penalty"]["fail"]: add("EU_pen_below", f"EU alone · penalty {thr['EU|penalty']['fail']['tau']:g}% (no club)", find("EU", 0, thr["EU|penalty"]["fail"]["tau"]))
if thr["EU|surcharge"]["fail"]: add("EU_sur_below", f"EU alone · surcharge {thr['EU|surcharge']['fail']['pha']:,} USD/ha (no club)", find("EU", thr["EU|surcharge"]["fail"]["pha"], 0))
w = thr["EUChina|penalty"]["work"]; add("EUC_pen", f"EU + China · penalty {w['tau']:g}%" if w else "", find("EUChina", 0, w["tau"]) if w else None)
w = thr["EUChina|surcharge"]["work"]; add("EUC_sur", f"EU + China · surcharge {w['pha']:,} USD/ha" if w else "", find("EUChina", w["pha"], 0) if w else None)
for seed, key, lab in (("EUMercosur", "EUM_0", "EU + Mercosur"), ("EUMercosurChina", "EUMC_0", "EU + Mercosur + China"), ("EUMercosur5", "EUM5_0", "EU + Mercosur-5")):
    s0 = find(seed, 0, 0)
    if s0: add(key, f"{lab} · no charge", s0)
    else:
        w = thr[f"{seed}|penalty"]["work"] or thr[f"{seed}|surcharge"]["work"]
        if w: add(key, f"{lab} · " + (f"penalty {w['tau']:g}%" if w["pha"] == 0 else f"surcharge {w['pha']:,} USD/ha"), find(seed, w["pha"], w["tau"]))
for lock, lab in (("brasil", "Brazil locked out"), ("us", "United States locked out"), ("us-china", "US and China locked out"), ("indonesia", "Indonesia locked out")):
    add(f"EU_pen_lock{lock}", f"EU alone · penalty {Y:g}% · {lab}", find("EU", 0, Y, lock=lock))
    add(f"EU_sur_lock{lock}", f"EU alone · surcharge {X:,} USD/ha · {lab}", find("EU", X, 0, lock=lock))
    if "EU_sur_min" in configs and find("EU", configs["EU_sur_min"]["pha"], 0, lock=lock) is not None:   # V33: the lock-outs of the lowest working surcharge (2,500) as well
        add(f"EU_sur_min_lock{lock}", f"EU alone · surcharge {configs['EU_sur_min']['pha']:,} USD/ha · {lab}", find("EU", configs["EU_sur_min"]["pha"], 0, lock=lock))
for tau in (2.5, 5.0):
    add(f"EU_pen_{tau:g}", f"EU alone · penalty {tau:g}%", find("EU", 0, tau))
add("EU_sur_6000", "EU alone · surcharge 6,000 USD/ha", find("EU", 6000, 0))

# ---- consistency: a member's forest kept is its business-as-usual clearing net of the EUDR's own effect on it (every cell held)
for key in ("EU_pen", "EU_sur"):
    if key in configs:
        c = configs[key]; expect = sum(base["bau_trop"][r] - base["eudr_trop"][r] for r in c["final_members"])
        print(f"  check {key}: members' tropical BAU clearing net of the EUDR effect {expect:.3f} Mha vs kept {c['forest']:.3f} Mha (difference {c['forest'] - expect:+.4f})")

# ---- stability tables: every Stability_*.txt of this generation, matched to a config on its final coalition
stab = {}
def final_set(path):
    for line in open(path).read().splitlines():
        m = re.match(r"final coalition S \(\d+\): (.*)$", line.strip())
        if m: return set(m.group(1).split())
    return set()
sfiles = sorted(glob.glob(os.path.join(v30.DB, f"Stability_Friction_forest_*_fixed_*{VERSION}.txt")), key=os.path.getmtime)
sfiles = [f for f in sfiles if f.endswith(VERSION + ".txt")]
# the seed named in the file (seedSmin<name>_fixed) says which starting point the tested coalition came from; two configs
# can end on the same coalition (the club at 1.5 % and the EU + China club at 1.12 % both converge to 35 members in V32)
FAMILY = {"club": "EU", "coalition": "EU", "mercosur": "EUMercosur", "euchinaclub": "EUChina", "mercosurchina": "EUMercosurChina"}
def file_seed(path):   # seedSmin<name>_fixed: the name starts with the family (clubY, coalitionX, mercosur0, euchinaclub112, clubYjapan ...)
    m = re.search(r"seedSmin([A-Za-z0-9.]+)_fixed", os.path.basename(path)); name = (m.group(1) if m else "").lower()
    return next((v for k, v in sorted(FAMILY.items(), key=lambda kv: -len(kv[0])) if name.startswith(k)), None)
def file_charge(path):
    m = re.search(r"pha([0-9.]+)_tau([0-9.]+)", os.path.basename(path)); return (float(m.group(1)), float(m.group(2))) if m else None
ABBR = {"EU": "EU", "EUChina": "EUC", "EUMercosur": "EUM", "EUMercosurChina": "EUMC", "EUMercosur5": "EUM5"}
for f in sfiles:
    S_f = final_set(f); seed_f = file_seed(f); charge_f = file_charge(f)
    # the run the test belongs to: same seed, same charge, no lock-out, and the tested coalition is its final coalition
    run = next((s for s in S if s["seed"] == seed_f and not s["lock"] and (float(s["pha"]), float(s["tau"])) == charge_f
                and set(s["final_members"]) == S_f and abs(s["fr"] - 0.001) < 1e-12), None)
    if run is None:
        print(f"  stability file not matched to a run: {os.path.basename(f)} (seed {seed_f}, charge {charge_f}, S = {len(S_f)} members)"); continue
    hit = next((k for k, c in configs.items() if c["tag"] == run["tag"] and k.endswith(("_pen", "_sur", "_0"))), None) \
        or next((k for k, c in configs.items() if c["tag"] == run["tag"]), None)
    if hit is None:   # a tested run the text does not quote by role (the EU + China club at the V31 threshold, say): keep it under its own key
        inst = "pen" if run["pha"] == 0 else "sur"; charge = f"{run['tau']:g}" if run["pha"] == 0 else f"{run['pha']}"
        hit = f"{ABBR[seed_f]}_{inst}_{charge}"
        add(hit, f"{SEEDS[seed_f]} · " + (f"penalty {run['tau']:g}%" if run["pha"] == 0 else f"surcharge {run['pha']:,} USD/ha"), run)
    rows = v30.stability_table(f)
    if hit in stab:   # a second file of the same run (one more outsider tested, the Japan test of 4 Oct): add the regions it tests
        have = {t["region"] for t in stab[hit]}; new = [t for t in rows if t["region"] not in have]
        stab[hit] += new; print(f"  stability {hit}: +{len(new)} rows ({', '.join(t['region'] for t in new)}) from {os.path.basename(f)}")
    else:
        stab[hit] = rows; print(f"  stability {hit}: {len(rows)} rows from {os.path.basename(f)}")
for key in ("EU_pen", "EU_sur", "EUM_0", "EUC_pen"):
    if key in configs and key not in stab: print(f"  stability {key}: no one-deviation test of this run on the disk")

slim = lambda s: {k: v for k, v in s.items() if k not in ("ev_path", "members_by_round")}
data = dict(version=VERSION, label=LABEL, headline=HEADLINE, gdp=gdp, T=T, bau=base, thresholds=thr, configs=configs, runs=[slim(s) for s in S], stability=stab,
            top=v30.TOP, seeds=SEEDS)
json.dump(data, open(here("all_data.json"), "w"))
with open(here("brazil_runs.txt"), "w") as f:
    for key in ("EU_pen", "EU_sur"):
        if key in configs:
            c = configs[key]; f.write(f"{'penalty' if key == 'EU_pen' else 'surcharge'} forest_{c['tag']} NATDEF_{c['last']}.sl4\n")
print(f"wrote {os.path.basename(here('all_data.json'))}:", len(configs), "configs,", len(S), "runs,", len(stab), "stability tables")
