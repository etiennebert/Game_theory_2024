#!/usr/bin/env python3
"""Build the DeDuCE-based inputs of the Forest Club model from the DeDuCE data and the GTAP-AEZ database.

Everything is located relative to this file (0_External_data\\DeDuCE_rework\\zenodo_v2.1\\build_deduce_tables.py):

    repository root  = three folders up (C:\\runGTAP375\\Game_theory_2024)      --repo, or FOREST_CLUB_REPO
    DeDuCE data      = DeDuCE_Deforestation_attributed_to_commodities_2001-2023.xlsx, next to this file   --deduce
    GTAP database    = <repo>\\2_Model\\in\\sets.har and basedata.har (licensed, not in the deposit)   --gtap, or GTAP_IN
    outputs          = <repo>\\0_External_data\\DeDuCE_rework\\                                        --out

Outputs (what the R scripts read):
    h_table_DeDuCE.xlsx                   DeDuCE hectares and tCO2 by region x GTAP activity (two windows, amortised and not),
                                          the footprints per dollar h_direct / h_total, e_direct / e_total, the AVE tables
                                          (Calibrate_BAU_productivity.R reads sheet D_unamort_w2018_2023)
    tms_f_initial_shocks_DeDuCE.xlsx      100 x AVE for the 12 producers, one sheet per price scenario, old layout
                                          (CGE_Game_Theory_GTAPAEZ_all_V32.R, sheet tmsf_sheet)
    tms_f_shocks_bilateral_<tag>.csv      the exact shock of header 0101 per (commodity, source, destination):
                                          100 x AVE(c, source) / (1 + t0(c, source, dest)), flows with VCIF > 0 and AVE >= 0.01 %
                                          (the game script reads the one of tmsf_sheet; AVE_pha0 = the AVE_pha400 flows at zero)

By default the outputs carry no GTAP value: the VOM_$M sheet and the VCIF_$M column of the previous files are GTAP Data Base
content and are left out (--with-gtap-values restores them for checking; such files must not be deposited).

Requires: pandas, numpy, openpyxl, and HARPY (GEMPACK's .har reader): pip install git+https://github.com/GEMPACKsoftware/HARPY.git
The DeDuCE sheet (21 MB) takes a minute to read; it is cached next to the xlsx as a .pkl (--no-cache to re-read)."""
import argparse, os, sys, time
import numpy as np, pandas as pd

# ---------------------------------------------------------------- paths
HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
ap.add_argument("--repo", default=os.environ.get("FOREST_CLUB_REPO", os.path.abspath(os.path.join(HERE, "..", "..", ".."))))
ap.add_argument("--deduce", default=os.path.join(HERE, "DeDuCE_Deforestation_attributed_to_commodities_2001-2023.xlsx"))
ap.add_argument("--gtap", default=os.environ.get("GTAP_IN"))
ap.add_argument("--out", default=None)
ap.add_argument("--with-gtap-values", action="store_true", help="also write the VOM_$M sheet and the VCIF_$M column (GTAP data: never deposit)")
ap.add_argument("--no-cache", action="store_true", help="re-read the DeDuCE xlsx even if a .pkl cache exists")
ap.add_argument("--quiet", action="store_true")
args = ap.parse_args()
REPO = args.repo
GTAP = args.gtap or os.path.join(REPO, "2_Model", "in")
OUT = args.out or os.path.join(REPO, "0_External_data", "DeDuCE_rework")
for p, what in ((args.deduce, "DeDuCE workbook"), (os.path.join(GTAP, "sets.har"), "sets.har"), (os.path.join(GTAP, "basedata.har"), "basedata.har")):
    if not os.path.exists(p): sys.exit(f"{what} not found: {p}\n(the GTAP files are licensed and sit in 2_Model\\in of the model folder; pass --gtap or set GTAP_IN)")
os.makedirs(OUT, exist_ok=True)
def say(*a):
    if not args.quiet: print(*a, flush=True)
say(f"repository {REPO}\nDeDuCE     {args.deduce}\nGTAP       {GTAP}\noutputs    {OUT}")

def load_harpy():
    """GEMPACK's HARPY (github.com/GEMPACKsoftware/HARPY): installed (pip install git+https://github.com/GEMPACKsoftware/HARPY.git),
    or a copy of the repository folder named HARPY (or HARPY-master) next to this script, in DeDuCE_rework, or in the model folder, or HARPY_PATH."""
    cands = [None, os.environ.get("HARPY_PATH")] + [os.path.join(b, n) for b in (HERE, os.path.dirname(HERE), REPO) for n in ("HARPY", "HARPY-master")]
    test = os.path.join(GTAP, "sets.har")
    for c in cands:
        if c is not None and not os.path.isdir(os.path.join(c, "harpy")): continue
        for m in [m for m in sys.modules if m == "harpy" or m.startswith("harpy.")]: del sys.modules[m]
        if c is not None: sys.path.insert(0, c)
        try:
            from harpy import HarFileObj
            HarFileObj(test)["REG"].array      # the GEMPACK API (another package called harpy exists on PyPI)
            return HarFileObj
        except Exception:
            if c is not None: sys.path.remove(c)
    sys.exit("HARPY (GEMPACK's .har reader for Python) was not found: pip install git+https://github.com/GEMPACKsoftware/HARPY.git, "
             "or download https://github.com/GEMPACKsoftware/HARPY as a zip and extract it next to this script as a folder named HARPY")
HarFileObj = load_harpy()

# ---------------------------------------------------------------- GTAP sets & data
S = HarFileObj(os.path.join(GTAP, "sets.har"))
def els(h): return [str(x).strip() for x in S[h].array.flatten()]
REG, COMM, ACTS = els("REG"), els("COMM"), els("ACTS")
DREG, MREG = els("DREG"), els("MREG")
reg_of = dict(zip(DREG, MREG))          # gtap country code -> model region
D = HarFileObj(os.path.join(GTAP, "basedata.har"))
MAKS = D["MAKS"].array   # (COMM, ACTS, REG)  $ million
VDFB = D["VDFB"].array   # (COMM, ACTS, REG)  domestic intermediate use, basic prices
VMSB = D["VMSB"].array   # (COMM, REG_s, REG_d) imports at basic prices (cif + duty)
VCIF = D["VCIF"].array   # (COMM, REG_s, REG_d)
EVFB = D["EVFB"].array   # (ENDW, ACTS, REG) factor payments
ENDW = els("ENDW")
VOM = MAKS.sum(axis=0)   # (ACTS, REG) output value by activity
assert COMM == ACTS, "the script assumes one activity per commodity"

# ---------------------------------------------------------------- DeDuCE
cache = args.deduce + ".pkl"
if not args.no_cache and os.path.exists(cache) and os.path.getmtime(cache) >= os.path.getmtime(args.deduce):
    df = pd.read_pickle(cache); say(f"DeDuCE: {len(df):,} rows from the cache {os.path.basename(cache)}")
else:
    t = time.time(); df = pd.read_excel(args.deduce, sheet_name="Deforestation attribution")
    df.to_pickle(cache); say(f"DeDuCE: {len(df):,} rows read in {time.time() - t:.0f} s (cached as {os.path.basename(cache)})")
U  = "Deforestation attribution, unamortized (ha)"
A  = "Deforestation risk, amortized (ha)"
EA = "Deforestation emissions incl. peat drainage, amortized (MtCO2)"
EU_ = "Deforestation emissions excl. peat drainage, unamortized (MtCO2)"
PE = "Peatland drainage emissions (MtCO2)"
IQ = "Integrated Quality Index"

# --- DeDuCE commodity -> GTAP land-using activity
def map_commodity(group, name):
    n = name.lower()
    if group == "Forest plantation": return "forest"
    if group == "Pasture": return "ruminant"            # cattle meat + leather (pasture)
    if group == "Sugar crops": return "c_b"
    if group == "Cereals":
        if n.startswith("rice"): return "pdr"
        if n.startswith("wheat"): return "wht"
        return "gro"
    if group in ("Fruit and nuts", "Vegetables",
                 "Edible roots and tubers with high starch or inulin content",
                 "Pulses (dried leguminous vegetables)"): return "v_f"
    if group == "Oilseeds and oleaginous fruits": return "osd"
    if group == "Stimulant, spice and aromatic crops": return "ocr"
    if group == "Fibre crops":
        if any(k in n for k in ("rubber", "tobacco", "peppermint", "pyrethrum")): return "ocr"
        return "pfb"
    raise ValueError((group, name))
df["act"] = [map_commodity(g, c) for g, c in zip(df["Commodity group"], df["Commodity"])]

# --- ISO -> GTAP model region.  Direct where GTAP has the country; residuals by UN group.
iso_special = {"ROU": "rou", "XKX": "xer", "SSD": "xec", "SDN": "sdn", "MMR": "xse", "TLS": "xse", "COD": "cod", "COG": "cog", "CIV": "civ"}
group_fallback = {"Africa": None, "Europe": "xer", "North Asia": "xsu", "North and Central America": "xca",
                  "Oceania": "xoc", "Rest of Asia": "xws", "South America": "xsm", "Southeast Asia": "xse"}
africa_fallback = {  # UN geoscheme -> GTAP residual
  "xnf": ["LBY", "ESH"], "xwf": ["CPV", "GMB", "GNB", "LBR", "SLE", "MRT"], "xcf": ["CMR", "CAF", "TCD", "COG", "GNQ", "GAB", "STP"],
  "xac": [], "xec": ["BDI", "COM", "DJI", "ERI", "ETH", "KEN", "MDG", "MWI", "MUS", "MOZ", "RWA", "SYC", "SOM", "SSD", "SDN", "TZA", "UGA", "ZMB", "ZWE"],
  "xsc": ["BWA", "LSO", "NAM", "SWZ", "ZAF"]}
africa_lookup = {iso: r for r, l in africa_fallback.items() for iso in l}
def map_iso(iso, group):
    code = iso_special.get(iso, iso.lower())
    if code in reg_of: return reg_of[code]
    code = africa_lookup.get(iso, "xec") if group == "Africa" else group_fallback[group]
    return reg_of.get(code, "RestofWorld")
df["reg"] = [map_iso(i, g) for i, g in zip(df["ISO"], df["Continent/Country group"])]
unmapped = df[~df.reg.isin(REG)].ISO.unique()
assert len(unmapped) == 0, unmapped

# ---------------------------------------------------------------- windows
windows = {"w2012_2019": (2012, 2019), "w2018_2023": (2018, 2023)}
def window_mean(col, a, b):
    sub = df[(df.Year >= a) & (df.Year <= b) & (df.act != "forest")]
    g = sub.groupby(["reg", "act"])[col].sum() / (b - a + 1)
    return g.unstack("act").reindex(REG).fillna(0.0)

# pasture deforestation (DeDuCE: cattle meat + leather) is split across the three grazing activities
# in proportion to their AEZ land rents (EVFB), so that dairy and wool carry their share
aez_rows = [i for i, e in enumerate(ENDW) if e.startswith("AEZ")]
land_rent = EVFB[aez_rows, :, :].sum(axis=0)                     # ACTS x REG
graz = ["ruminant", "rmk", "wol"]
gi = [ACTS.index(a) for a in graz]
tot = land_rent[gi, :].sum(axis=0)
pasture_share = pd.DataFrame({a: np.where(tot > 0, land_rent[ACTS.index(a), :] / np.where(tot > 0, tot, 1), [1, 0, 0][k])
                              for k, a in enumerate(graz)}, index=REG)
def split_pasture(tab):
    tab = tab.copy(); rum = tab["ruminant"].copy()
    for a in graz: tab[a] = rum * pasture_share[a]
    return tab

tables = {}
for w, (a, b) in windows.items():
    tables[f"D_unamort_{w}"] = split_pasture(window_mean(U, a, b))          # ha/yr
    tables[f"D_amort_{w}"]   = split_pasture(window_mean(A, a, b))          # ha/yr, 5-yr amortised
    tables[f"E_amort_{w}"]   = split_pasture(window_mean(EA, a, b) * 1e6)   # tCO2/yr incl. peat
    tables[f"E_unamort_{w}"] = split_pasture((window_mean(EU_, a, b) + window_mean(PE, a, b)) * 1e6)
tables["pasture_share_ruminant_rmk_wol"] = pasture_share

acts_land = ["pdr", "wht", "gro", "v_f", "osd", "c_b", "pfb", "ocr", "ruminant", "rmk", "wol"]
# hectare-weighted Integrated Quality Index per region x activity (main window)
_sub = df[(df.Year >= 2018) & (df.Year <= 2023) & (df.act != "forest")].copy()
_sub["wq"] = _sub[U] * _sub[IQ]
_g = _sub.groupby(["reg", "act"]).agg(wq=("wq", "sum"), ha=(U, "sum"))
tables["IQI_w2018_2023"] = (_g.wq / _g.ha).unstack("act").reindex(REG)
vom = pd.DataFrame(VOM.T, index=REG, columns=ACTS)          # $ million (GTAP data: written only with --with-gtap-values)
if args.with_gtap_values: tables["VOM_$M"] = vom

# ---------------------------------------------------------------- h direct & Leontief-total
def leontief_total(hd):   # hd: DataFrame (REG x ACTS) per $ of output ; returns REG x ACTS
    out = pd.DataFrame(0.0, index=REG, columns=ACTS)
    for ri, r in enumerate(REG):
        vo = VOM[:, ri]
        Ad = np.where(vo > 0, VDFB[:, :, ri] / np.where(vo > 0, vo, 1), 0.0)   # A[c,a] = use of c per $ of a
        np.fill_diagonal(Ad, 0.0)   # drop own-use: circular flows (e.g. DRC pdr->pdr = 0.98) blow up L; footprint is per $ of gross output
        L = np.linalg.inv(np.eye(len(ACTS)) - Ad)                                # (I-A)^-1
        out.loc[r] = hd.loc[r].values @ L                                        # h_tot[j] = sum_c h_d[c] L[c,j]
    return out

for w in windows:
    for kind in ("amort", "unamort"):
        Dw = tables[f"D_{kind}_{w}"].reindex(columns=ACTS).fillna(0.0)
        hd = (Dw / (vom * 1e6).replace(0, np.nan)).fillna(0.0)             # ha per $
        tables[f"h_direct_{kind}_{w}"] = hd
        tables[f"h_total_{kind}_{w}"]  = leontief_total(hd)
        Ew = tables[f"E_{kind}_{w}"].reindex(columns=ACTS).fillna(0.0)
        ed = (Ew / (vom * 1e6).replace(0, np.nan)).fillna(0.0)             # tCO2 per $
        tables[f"e_direct_{kind}_{w}"] = ed
        tables[f"e_total_{kind}_{w}"]  = leontief_total(ed)
        tables[f"tCO2_per_ha_{kind}_{w}"] = (Ew / Dw.replace(0, np.nan)).fillna(0.0)   # tCO2 per ha (activity level) for reporting

# ---------------------------------------------------------------- AVE tables (main case: amortised, 2018-2023)
MAIN = "amort_w2018_2023"
h_tot = tables[f"h_total_{MAIN}"]; e_tot = tables[f"e_total_{MAIN}"]
ave = {}
for p in (400, 2000, 10000): ave[f"AVE_pha{p}"] = h_tot * p                        # $/ha x ha/$ -> fraction
for pc in (50, 100, 190):   ave[f"AVE_co2_{pc}"] = (e_tot * pc).clip(lower=0.0)   # tCO2/$ x $/tCO2 -> fraction; no negative charge
tables.update(ave)

# ---------------------------------------------------------------- bilateral tariff-power shocks (header 0101)
t0 = np.where(VCIF > 0, VMSB / np.where(VCIF > 0, VCIF, 1) - 1.0, 0.0)   # (COMM, s, d): the base tariff rate
charged = ["pdr", "wht", "gro", "v_f", "osd", "c_b", "pfb", "ocr", "ruminant", "rmk", "wol", "RuminantMeat", "vegoil", "pcr", "sgr", "lea", "dairy"]
MIN_AVE_PCT = 0.01   # charges below 0.01 % are dropped
def bilateral(avetab):
    rows = []
    for ci, c in enumerate(COMM):
        if c not in charged: continue
        for si, s in enumerate(REG):
            a = 100.0 * avetab.loc[s, c]
            if a < MIN_AVE_PCT: continue
            for di, d in enumerate(REG):
                if si == di or VCIF[ci, si, di] <= 0: continue
                rows.append((c, s, d, a / (1.0 + t0[ci, si, di]), a, VCIF[ci, si, di]))
    return pd.DataFrame(rows, columns=["comm", "source", "dest", "shock_tms_f_pct", "AVE_pct", "VCIF_$M"])
csv_cols = ["comm", "source", "dest", "shock_tms_f_pct", "AVE_pct"] + (["VCIF_$M"] if args.with_gtap_values else [])
n_rows = {}
for tag, avetab in ave.items():
    b = bilateral(avetab); b[csv_cols].to_csv(os.path.join(OUT, f"tms_f_shocks_bilateral_{tag}.csv"), index=False); n_rows[tag] = len(b)
    if tag == "AVE_pha400":   # AVE_pha0: the same flows at zero (a pure club penalty when tau > 0)
        z = b.copy(); z["shock_tms_f_pct"] = 0; z["AVE_pct"] = 0
        z[csv_cols].to_csv(os.path.join(OUT, "tms_f_shocks_bilateral_AVE_pha0.csv"), index=False); n_rows["AVE_pha0"] = len(z)
say("bilateral csv rows:", ", ".join(f"{k} {v:,}" for k, v in n_rows.items()))

# ---------------------------------------------------------------- h_table_DeDuCE.xlsx
with pd.ExcelWriter(os.path.join(OUT, "h_table_DeDuCE.xlsx")) as xw:
    readme = pd.DataFrame({"note": [
      "DeDuCE v2.1 (Zenodo 10.5281/zenodo.10633818) mapped to the GTAP-AEZ v7 database of the model (42 regions, 35 sectors).",
      "D_* : attributed deforestation, ha/yr, window mean; amort = 5-yr amortised 'embodied in production' (Pendrill/DeDuCE convention).",
      "E_* : tCO2/yr incl. peat drainage. Forest plantations excluded. Pasture (cattle meat + leather) -> ruminant.",
      "h_direct = D / output value (MAKS, $); h_total = h_direct x domestic Leontief inverse (I-A)^-1, A from VDFB.",
      "AVE_phaX = h_total x X $/ha ; AVE_co2_P = e_total x P $/tCO2. Fractions (0.01 = 1%).",
      "tms_f_shocks_bilateral_*.csv: shock = 100 x AVE / (1 + t0), t0 = VMSB/VCIF - 1, for flows with VCIF>0 and AVE >= 0.01 %.",
      "Charged sectors in csv: primary land-using (incl. rmk, wol) + RuminantMeat, vegoil, pcr, sgr, lea, dairy.",
      "Pasture deforestation split across ruminant/rmk/wol by AEZ land-rent shares (sheet pasture_share_ruminant_rmk_wol).",
      "Leontief pass excludes own-use (diagonal of A) to avoid amplification from circular flows in poor-data regions (e.g. DRC pdr).",
      "IQI_w2018_2023: hectare-weighted DeDuCE quality index; >0.6 ~ direct (spatial) attribution, lower = statistical attribution.",
      "Built by 0_External_data/DeDuCE_rework/zenodo_v2.1/build_deduce_tables.py; GTAP values (VOM, VCIF) are not written unless --with-gtap-values."]})
    readme.to_excel(xw, sheet_name="README", index=False)
    for k, v in tables.items(): v.to_excel(xw, sheet_name=k[:31])

# ---------------------------------------------------------------- tms_f_initial_shocks_DeDuCE.xlsx (the 12 producers, old layout)
producers = ["Brasil", "Indonesia", "Argentina", "Bolivia", "Colombia", "Angola", "Ghana", "IvoryCoast", "Malasya", "Paraguay", "Peru", "DRC"]
old_cols = ["sgr", "ruminant", "gro", "ocr", "osd", "pcr", "pfb", "v_f", "wht", "rmk", "wol", "RuminantMeat", "dairy", "vegoil", "lea", "pdr", "c_b"]
init_path = os.path.join(OUT, "tms_f_initial_shocks_DeDuCE.xlsx")
old_sheet = None   # the pre-DeDuCE rates (sheet OLD_current_file): kept from the existing workbook, or from the old tms_f_initial_shocks.xlsx
for cand, sheet in ((init_path, "OLD_current_file"), (os.path.join(REPO, "0_External_data", "tms_f_initial_shocks.xlsx"), 0),
                    (os.path.join(REPO, "0_External_data", "0. Old", "tms_f_initial_shocks.xlsx"), 0)):
    if os.path.exists(cand):
        try: old_sheet = pd.read_excel(cand, sheet_name=sheet); break
        except Exception: pass
with pd.ExcelWriter(init_path) as xw:
    pd.DataFrame({"note": [
      "Same layout as tms_f_initial_shocks.xlsx (Country rows, sector columns), values = 100 x AVE (ad-valorem equivalent, %).",
      "AVE = p_ha x h_total; h_total = embodied deforestation per $ of output (DeDuCE amortised 2018-2023, domestic Leontief) -> h_table_DeDuCE.xlsx.",
      "Destination-independent (ignores the base tariff t0). The exact tms_f shock is 100 x AVE/(1+t0), given bilaterally in tms_f_shocks_bilateral_*.csv.",
      "Pasture deforestation is split across ruminant, rmk and wol by their AEZ land-rent shares (no double counting); dairy carries rmk's share via the Leontief pass.",
      "New columns RuminantMeat, dairy, vegoil, lea, pdr, c_b: list_commodity in the game script includes them.",
      "Sheet OLD_current_file = the reverse-engineered rates of the first submission (kept for comparison; not used by the runs).",
      "AVE_pha0: no footprint charge (every value 0). With tau > 0 it gives a pure club penalty - every non-member pays the flat tau on the 17 sectors, deforestation or not.",
      "Built by 0_External_data/DeDuCE_rework/zenodo_v2.1/build_deduce_tables.py."]}).to_excel(xw, sheet_name="README", index=False)
    if old_sheet is not None: old_sheet.to_excel(xw, sheet_name="OLD_current_file", index=False)
    for tag in list(ave) + ["AVE_pha0"]:
        src = ave["AVE_pha400"] * 0 if tag == "AVE_pha0" else ave[tag]
        t = (100 * src.loc[producers, old_cols]).round(4); t.insert(0, "Country", [p.lower() for p in producers])
        t.to_excel(xw, sheet_name=tag, index=False)

# ---------------------------------------------------------------- console summary for the 12 producers
show = ["osd", "ruminant", "RuminantMeat", "rmk", "dairy", "vegoil", "ocr", "c_b", "sgr", "gro", "pdr", "pcr", "v_f", "pfb", "wht", "lea"]
say("\n=== attributed deforestation (ha/yr, amortised, 2018-2023), producers x land activities ===")
say(tables["D_amort_w2018_2023"].loc[producers, acts_land].round(0).to_string())
say("\n=== h_total (ha per $1000 of output), amortised 2018-2023 ===")
say((h_tot.loc[producers, show] * 1000).round(4).to_string())
say("\n=== AVE at $10000/ha (%) ===");  say((ave["AVE_pha10000"].loc[producers, show] * 100).round(2).to_string())
say("\n=== AVE at $100/tCO2 (%) ===");  say((ave["AVE_co2_100"].loc[producers, show] * 100).round(2).to_string())
say(f"\nwritten to {OUT}: h_table_DeDuCE.xlsx, tms_f_initial_shocks_DeDuCE.xlsx, {len(n_rows)} tms_f_shocks_bilateral_*.csv")
