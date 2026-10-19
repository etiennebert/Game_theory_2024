"""Readers for the runs of the game played from the business-as-usual world (V30 mechanics: EUDR kept on outsiders, every
member forest cell held; V31: welfare net of the forest-land wedge term; V32: the EUDR applied to non-members in every
solve) and for the two-stage baseline. Which generation is read is paths.VERSION. Shared by extract_all.py, extract_plane.py,
stats.py and extract_brazil_aez.R (through brazil_runs_<label>.txt). Nothing here draws.

Reference frames, once and for all:
  * The result csv of a run (4_DB\\Database_GTAPAEZ_all_results_2024_agg_forest_<tag>.csv) reports, for every region and
    round, EV (M USD per year; from V31 on the decision measure, net of the forest-land wedge term), the real GDP change
    (GDP_pct) and the forest change by climate zone (Tropical, Temperate, Boreal, in hectares), all relative to the
    BUSINESS-AS-USUAL world (Stage A of Baseline_2stage.R). Round 0 is the EUDR world (Stage B). Everything the paper
    reports about a club is round <last> minus round 0: the club's effect on top of the EUDR.
  * GTAP's own EV (gross of the wedge term) is read from Welfare_decomp_round_<last>.txt in the run folder (V31+), its
    round 0 being EV_B.txt; run_stats returns it as ev_gross / world_gross (None for a V30 run).
  * Business-as-usual clearing by region comes from Stage A (EUDR_effect_by_region.txt: bau_clearing_trop_ha,
    bau_clearing_all_ha), never from a run.
  * Forest kept = the members' forest change (positive: clearing forgone). Leakage = minus the outsiders' forest change
    (positive: extra clearing). Both in tropical hectares and in all-forest hectares (tropical + temperate + boreal).
"""
import csv, glob, json, os, re, collections, openpyxl
from paths import REPO, DB, EXT, OUT3, here, VERSION

SUFFIX = "_eudr0_bau5_eta0.66_seed{seed}{lock}_outfree_fr{fr}trade_sgb_jrexp_frombau_eudr{eudr}{pin}"
BASELINE = os.path.join(OUT3, "Baseline_2stage_bau5_eta0.66")
ZONES = {"Tropical": "trop", "Temperate": "temp", "Boreal": "bor"}
TOP = ["brasil", "drc", "bolivia", "seasia", "ivorycoast", "colombia", "indonesia", "nigeria"]   # the eight largest tropical deforesters

def fmt_num(v):
    """R's format(x, scientific = FALSE) for the numbers in a run tag: 1.5 -> '1.5', 4000 -> '4000', 0.0005 -> '0.0005'."""
    s = f"{v:.10f}".rstrip("0").rstrip("."); return s if s else "0"

VERSION_SUFFIX = VERSION   # paths.VERSION: "_wnet_v32" (V32), "_wnet" (V31), "" (V30)

def tag_of(pha=0, tau=0.0, seed="EU", lock="", fr=0.001, eudr="keep", pin="all", version=None):
    """The run tag the runners build (Run_V32_all.R, run_tag_of), without the leading 'forest_'."""
    lock_s = f"_lock{lock}" if lock else ""
    return f"pha{fmt_num(pha)}_tau{fmt_num(tau)}{'charged' if tau > 0 else ''}" + SUFFIX.format(seed=seed, lock=lock_s, fr=fmt_num(fr), eudr=eudr, pin="_pinall" if pin == "all" else "") + (VERSION_SUFFIX if version is None else version)

PAT = re.compile(r"agg_forest_pha(?P<pha>\d+)_tau(?P<tau>[\d.]+)(?:charged)?_eudr0_bau5_eta0\.66_seed(?P<seed>[A-Za-z0-9]+?)(?P<fixed>_fixed)?(?:_lock(?P<lock>[a-z\-]+))?"
                 r"_outfree_fr(?P<fr>[\d.]+)trade_sgb_jrexp_frombau_eudr(?P<eudr>keep|lift)(?P<pin>_pinall)?(?P<wnet>_wnet)?(?P<v32>_v32)?\.csv$")

def parse_tag(path):
    m = PAT.search(os.path.basename(path))
    if not m: return None
    d = m.groupdict()
    return dict(pha=int(d["pha"]), tau=float(d["tau"]), seed=d["seed"], fixed=bool(d["fixed"]), lock=d["lock"] or "", fr=float(d["fr"]), eudr=d["eudr"],
                pin="all" if d["pin"] else "bau", version=(d["wnet"] or "") + (d["v32"] or ""), tag=re.search(r"agg_forest_(.*)\.csv$", os.path.basename(path)).group(1))

def csv_path(tag): return os.path.join(DB, f"Database_GTAPAEZ_all_results_2024_agg_forest_{tag}.csv")
def run_dir(tag): return os.path.join(OUT3, "Friction", "forest_" + tag, "Scenario_D")

# ---------------------------------------------------------------- external data
def read_gdp():
    wb = openpyxl.load_workbook(os.path.join(EXT, "GDP_values.xlsx"), data_only=True)
    gdp = {r[0].lower().strip(): float(r[1]) for r in wb.active.iter_rows(min_row=2, values_only=True) if r[0] and r[1] is not None}
    if gdp.get("mozambique", 0) > 50000: gdp["mozambique"] = 15510.0   # guard for the old file (Central Africa's value by a copy error; corrected 30 Sept 2026, World Bank 2019)
    return gdp

def read_thresholds(tag=None):
    """Thresholds_used.txt of a run at 0.1 % of trade: region -> switching cost in M USD per year (join = leave threshold).
    Any V30 run folder at fr0.001 carries the same table; a copy is kept next to the scripts (switching_costs_0.1pct.txt)."""
    cands = ([os.path.join(run_dir(tag), "Thresholds_used.txt")] if tag else []) + \
            sorted(glob.glob(os.path.join(OUT3, "Friction", "forest_*_fr0.001trade_*_frombau_eudrkeep_pinall*", "Scenario_D", "Thresholds_used.txt"))) + [here("switching_costs_0.1pct.txt")]
    f = next((c for c in cands if os.path.exists(c)), None)
    if f is None: raise FileNotFoundError("no Thresholds_used.txt found in any V30 run folder")
    T = {}
    for line in open(f).read().splitlines()[1:]:
        p = line.split()
        if len(p) >= 3: T[p[0]] = float(p[1])
    if not os.path.exists(here("switching_costs_0.1pct.txt")):
        import shutil; shutil.copy(f, here("switching_costs_0.1pct.txt"))
    return T

# ---------------------------------------------------------------- the two-stage baseline
def read_baseline():
    """Stage A clearing and Stage B (EUDR) effect by region, Mha; EV of the EUDR, M USD per year."""
    f = os.path.join(BASELINE, "EUDR_effect_by_region.txt")
    bau_t, bau_a, eu_t, eu_a, ev = {}, {}, {}, {}, {}
    for line in open(f).read().splitlines()[1:]:
        p = [x.strip('"') for x in line.split()]
        if len(p) < 7: continue
        r = p[0].lower(); bau_t[r] = float(p[1]) / 1e6; bau_a[r] = float(p[2]) / 1e6; eu_t[r] = float(p[3]) / 1e6; eu_a[r] = float(p[4]) / 1e6; ev[r] = float(p[5])
    return dict(bau_trop=bau_t, bau_all=bau_a, eudr_trop=eu_t, eudr_all=eu_a, eudr_ev=ev,
                bau_trop_total=sum(bau_t.values()), bau_all_total=sum(bau_a.values()), eudr_trop_total=sum(eu_t.values()), eudr_all_total=sum(eu_a.values()), eudr_world=sum(ev.values()))

# ---------------------------------------------------------------- one run
def load_csv(tag):
    by = collections.defaultdict(dict)
    for r in csv.DictReader(open(csv_path(tag))): by[int(r["Iteration"])][r["Country"]] = r
    return by

def read_decomp(tag, i):
    """Welfare_decomp_round_<i>.txt of a run (V31+; the first V31 runs only have the per-solve Welfare_decomp_iter_<i>.txt):
    {region: (ev_gross, wedge, ev_decision)}, or None."""
    d = run_dir(tag)
    f = os.path.join(d, f"Welfare_decomp_round_{i}.txt")
    if not os.path.exists(f):
        c = sorted(glob.glob(os.path.join(d, f"Welfare_decomp_iter_{i}.txt")) + glob.glob(os.path.join(d, f"Welfare_decomp_iter_{i}_pass_*.txt")), key=os.path.getmtime)
        if not c: return None
        f = c[-1]
    out = {}
    for line in open(f).read().splitlines()[1:]:
        p = [x.strip('"') for x in line.split()]
        if len(p) >= 4: out[p[0].lower()] = (float(p[1]), float(p[2]), float(p[3]))
    return out or None

def read_ev_b():
    """EV_B.txt of Stage B: GTAP's EV of the EUDR world relative to the business-as-usual world (= round 0 gross)."""
    f = os.path.join(BASELINE, "B_eudr", "EV_B.txt")
    return {l.split()[0].strip('"').lower(): float(l.split()[1].strip('"')) for l in open(f).read().splitlines() if len(l.split()) >= 2}

def outcome_of(tag, last, max_rounds=15):
    f = os.path.join(run_dir(tag), "Run_summary.txt")
    if os.path.exists(f):
        for line in open(f).read().splitlines():
            if line.startswith("outcome:"): return line.split(":", 1)[1].split("|")[0].strip()
    return "converged" if last < max_rounds - 1 else "stopped at the round cap"

def run_stats(tag, gdp=None, T=None, meta=None):
    """Everything the figures and tables use about one run. Changes are round <last> minus round 0 (the club's effect on
    top of the EUDR) unless the key says otherwise."""
    by = load_csv(tag); last = max(by); regs = sorted(by[0]); gdp = gdp or read_gdp()
    meta = meta or parse_tag(csv_path(tag)) or {}
    members_by_round = {i: sorted(c for c in regs if by[i][c]["Club"] == "inside") for i in range(last + 1)}
    mem = members_by_round[last]; out = [c for c in regs if c not in mem]
    def col(i, c, k): return float(by[i][c][k])
    d = {z: {c: (col(last, c, Z) - col(0, c, Z)) / 1e6 for c in regs} for Z, z in ZONES.items()}
    d["all"] = {c: d["trop"][c] + d["temp"][c] + d["bor"][c] for c in regs}
    ev = {c: col(last, c, "EV") - col(0, c, "EV") for c in regs}
    gdp_pct = {c: col(last, c, "GDP_pct") - col(0, c, "GDP_pct") for c in regs}
    ev_path = {c: [col(i, c, "EV") for i in range(last + 1)] for c in regs}
    r1 = {c: -(ev_path[c][1] - ev_path[c][0]) for c in regs} if last >= 1 else {c: 0.0 for c in regs}   # first-round loss (positive = loss)
    joins = {c: next((i for i in range(last + 1) if by[i][c]["Club"] == "inside"), None) for c in regs}
    charge_alone = {z: sum(col(1, c, Z) - col(0, c, Z) for c in regs if c not in members_by_round[1]) / 1e6 for Z, z in ZONES.items()} if last >= 1 else {}
    outcome = outcome_of(tag, last)
    s = dict(tag=tag, **{k: v for k, v in meta.items() if k != "tag"}, last=last, outcome=outcome, converged=outcome.startswith("converged"),
             members_by_round=members_by_round, final_members=mem, outsiders=out, n=len(mem), works=outcome.startswith("converged") and "brasil" in mem,
             dtrop=d["trop"], dtemp=d["temp"], dbor=d["bor"], dall=d["all"],
             kept={c: d["trop"][c] for c in mem}, kept_all={c: d["all"][c] for c in mem},
             leak={c: -d["trop"][c] for c in out}, leak_all={c: -d["all"][c] for c in out},
             forest=sum(d["trop"][c] for c in mem), forest_all=sum(d["all"][c] for c in mem),
             leakage=-sum(d["trop"][c] for c in out), leakage_all=-sum(d["all"][c] for c in out),
             ev=ev, ev_pct={c: 100 * ev[c] / gdp[c] for c in regs}, gdp_pct=gdp_pct, world=sum(ev.values()),
             members_ev=sum(ev[c] for c in mem), outsiders_ev=sum(ev[c] for c in out), ev_path=ev_path, r1=r1, joins=joins,
             brazil_r1_loss=r1["brasil"], charge_alone=charge_alone,
             eu=ev["eu27"], brasil=ev["brasil"], china=ev["china"], us=ev["us"], top_in=[c for c in TOP if c in mem])
    s["net"] = s["forest"] - s["leakage"]; s["net_all"] = s["forest_all"] - s["leakage_all"]
    # the switching cost scales with the share of trade (fr): the table on the disk is the one at 0.1 %
    kT = s["fr"] / 0.001 if s.get("fr") else 1.0
    if T: s["T"] = {c: T[c] * kT for c in regs if T.get(c)}; s["r1_over_T"] = {c: r1[c] / (T[c] * kT) for c in regs if T.get(c)}
    # GTAP's EV gross of the wedge term (V31+): round <last> from the decomposition file, round 0 from EV_B.txt
    dec = read_decomp(tag, last) if last >= 1 else None
    if dec:
        ev_b = read_ev_b()
        s["ev_gross"] = {c: dec[c][0] - ev_b[c] for c in regs if c in dec and c in ev_b}
        s["wedge"] = {c: dec[c][1] for c in regs if c in dec}
        s["world_gross"] = sum(s["ev_gross"].values()) if len(s["ev_gross"]) == len(regs) else None
    else:
        s["ev_gross"] = None; s["wedge"] = None; s["world_gross"] = None
    return s

def stability_table(path):
    """One Stability_*.txt -> rows (region, status, gain_from_moving, threshold, ev_in_S, EV_deviation, world_EV_deviation);
    the EU anchor dropped. R prints the table in several column blocks (the split depends on the width), all with the same
    rows: every block is read and the columns are merged by row."""
    lines = [l for l in open(path).read().splitlines() if l.strip()]
    COLS = {"region", "status", "EV_baseline", "EV_in_S", "EV_in_S_vs_baseline", "EV_deviation", "world_EV_deviation", "tropical_forest_kha_deviation",
            "solve_ok", "gain_from_moving", "threshold", "wants_to_move", "wants_to_move_with_friction", "transfer_needed", "revenue_charge"}
    h1 = next(i for i, l in enumerate(lines) if l.split()[0] == "region")
    headers = [i for i in range(h1, len(lines)) if lines[i].split()[0] in COLS]
    n = (headers[1] - headers[0] - 1) if len(headers) > 1 else len(lines) - h1 - 1
    rows = [dict() for _ in range(n)]
    for h in headers:
        cols = lines[h].split()
        for k in range(n):
            vals = lines[h + 1 + k].split()
            if len(vals) != len(cols): raise ValueError(f"{os.path.basename(path)}: row {k} of block '{cols[0]}' has {len(vals)} fields for {len(cols)} columns")
            rows[k].update(zip(cols, vals))
    out = []
    for d in rows:
        if d.get("status") == "eu27_anchor": continue
        fl = lambda key: float(d[key]) if d.get(key) not in (None, "NA") else float("nan")
        out.append(dict(region=d["region"], status=d["status"], gain=fl("gain_from_moving"), threshold=fl("threshold"), ev_in_S=fl("EV_in_S_vs_baseline"),
                        ev_deviation=fl("EV_deviation"), world_deviation=fl("world_EV_deviation"), transfer=fl("transfer_needed"), revenue=fl("revenue_charge")))
    return out

def all_runs(pin="all", eudr="keep", fr=None, version=None):
    """Every dynamic (not _fixed) run on the disk with this pin / EUDR convention and version suffix (default: the current one), parsed tags."""
    out = []; version = VERSION_SUFFIX if version is None else version
    for f in sorted(glob.glob(os.path.join(DB, "Database_GTAPAEZ_all_results_2024_agg_forest_*_frombau_eudr*.csv"))):
        m = parse_tag(f)
        if not m or m["fixed"] or m["pin"] != pin or m["eudr"] != eudr or m["version"] != version: continue
        if fr is not None and abs(m["fr"] - fr) > 1e-12: continue
        out.append(m)
    return out

def brackets(runs, seed, inst, lock="", fr=0.001, pha=0):
    """Lowest working and highest failing charge of one instrument for one seed, among run summaries (run_stats): (fail, work),
    None where absent. inst = "penalty" searches tau at the surcharge `pha` (0 = pure penalty); "surcharge" searches pha at tau = 0."""
    rs = [r for r in runs if r["seed"] == seed and r["lock"] == lock and abs(r["fr"] - fr) < 1e-12 and
          ((inst == "penalty" and r["pha"] == pha) or (inst == "surcharge" and r["tau"] == 0))]
    x = (lambda r: r["tau"]) if inst == "penalty" else (lambda r: r["pha"])
    rs = sorted(rs, key=x)
    work = [r for r in rs if r["works"]]; fail = [r for r in rs if not r["works"]]
    w = min(work, key=x) if work else None
    below = [r for r in fail if w is None or x(r) < x(w)]
    f = max(below, key=x) if below else None
    return f, w
