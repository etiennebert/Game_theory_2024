"""Replay the V32 membership decisions of a run from its result csv (EV by region and iteration, membership by iteration) with the
experience rule of CGE_Game_Theory_GTAPAEZ_all_V32.R, under the thresholds of the run (validation: the replay must reproduce the
membership path) and under alternative threshold schedules (first divergence, margins of every decision)."""
import csv, os, sys
import openpyxl
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.environ.get("FOREST_CLUB_REPO", os.path.abspath(os.path.join(HERE, "..", "..", "..")))   # 5_Figures/SI_script/switching_costs_check -> the model folder
DB = os.path.join(REPO, "4_DB")
SUFFIX = "_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32"
def load_run(tag):
    f = os.path.join(DB, f"Database_GTAPAEZ_all_results_2024_agg_forest_{tag}.csv")
    rows = list(csv.DictReader(open(f)))
    its = sorted({int(r["Iteration"]) for r in rows})
    ev = {}; club = {}
    for r in rows:
        k = int(r["Iteration"]); ev.setdefault(k, {})[r["Country"]] = float(r["EV"]); club.setdefault(k, {})[r["Country"]] = (r["Club"] == "inside")
    return its, ev, club
def thresholds_trade():
    t = {}
    for line in open(os.path.join(REPO, "5_Figures", "common", "switching_costs_0.1pct.txt")):
        p = line.split()
        if len(p) >= 3 and p[0] != "region": t[p[0]] = (float(p[1]), float(p[2]))
    return t
def gdp():
    wb = openpyxl.load_workbook(os.path.join(REPO, "0_External_data", "GDP_values.xlsx"), data_only=True); ws = wb.active
    return {str(r[0]).lower(): r[1] for r in ws.iter_rows(values_only=True) if r[0] and isinstance(r[1], (int, float))}
GDP = gdp()
def replay(tag, thr, locked=(), anchor="eu27", verbose=False, record=None):
    """thr: region -> (threshold_leave, threshold_join). Returns the membership path (dict iteration -> set) and the list of
    decisions: (iteration k, region, status, measure, threshold, margin, moves) where moves = the decision taken under thr."""
    its, ev, club = load_run(tag)
    regions = sorted(ev[0].keys())
    members = {k: club[k] for k in its}            # actual path, for the comparison
    # replay
    path = {0: set(r for r in regions if club[0][r])}   # iteration 0 solve: the seed
    ev_in_last = {r: None for r in regions}; ev_out_last = {r: ev[0][r] for r in regions}
    decisions = []
    cur = set(path[0])                                      # membership during the current solve
    for k in its[1:]:
        # the solve of iteration k used membership 'cur' (decided after k-1); check against the actual file
        actual = set(r for r in regions if club[k][r])
        if record is not None: record.append((k, cur == actual, sorted(cur ^ actual)))
        if cur != actual:
            return path, decisions, k, sorted(cur - actual), sorted(actual - cur)
        path[k] = set(cur)
        # update the experience record with this solve
        for r in regions:
            if r in cur: ev_in_last[r] = ev[k][r]
            else: ev_out_last[r] = ev[k][r]
        if k == its[-1]: break
        nxt = set()
        for r in regions:
            if r == anchor: nxt.add(r); continue
            if r in locked: continue
            now = ev[k][r]; tl, tj = thr[r]
            if r in cur:
                loss_vs_out = ev_out_last[r] - now              # positive: worse than the last time outside
                sg = False
                if k >= 3:
                    m3 = all(r in path[j] for j in (k, k - 1, k - 2))
                    sg = m3 and all((ev[j][r] - ev[0][r]) < -0.001 * GDP[r] for j in (k, k - 1, k - 2))
                leave = (loss_vs_out > tl) or sg
                decisions.append((k, r, "member", loss_vs_out, tl, loss_vs_out - tl, "leaves" if leave else "stays", sg))
                if not leave: nxt.add(r)
            else:
                ref = ev_in_last[r] if ev_in_last[r] is not None else ev[k - 1][r]
                loss_vs_in = ref - now                           # positive: worse than the reference (last time inside, or the previous round)
                join = loss_vs_in > tj
                decisions.append((k, r, "outsider", loss_vs_in, tj, loss_vs_in - tj, "joins" if join else "stays out", False))
                if join: nxt.add(r)
        cur = nxt
    return path, decisions, None, [], []
if __name__ == "__main__":
    thr = thresholds_trade()
    for tag, lock in [("pha0_tau1.5charged", ()), ("pha4000_tau0", ()), ("pha2000_tau0", ()), ("pha1500_tau0", ()), ("pha0_tau1.25charged", ()), ("pha0_tau1charged", ())]:
        full = tag + SUFFIX
        try:
            path, dec, kdiv, extra, missing = replay(full, thr, locked=lock)
        except FileNotFoundError as e:
            print(tag, "missing"); continue
        n_close = sum(1 for d in dec if abs(d[5]) < 0.5 * d[4])
        print(f"{tag:22s} replay {'OK' if kdiv is None else f'DIVERGES at iteration {kdiv}: replay has {extra}, file has {missing}'}; decisions {len(dec)}, within +-50% of the threshold: {n_close}")
