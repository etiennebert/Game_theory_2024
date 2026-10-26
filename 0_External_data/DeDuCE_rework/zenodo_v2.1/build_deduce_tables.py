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
    bau_deforestation.xlsx                the business-as-usual clearing of every region x AEZ cell (Calibrate_BAU_productivity.R,
                                          Baseline_2stage.R): DeDuCE unamortised 2018-2023 by region, split across the region's AEZs
                                          with the HILDA+ v2.1 shares of HILDA_v2.1_transitions_country_AEZ.csv (--hilda, built by
                                          hilda_country_aez_tables.py from the HILDA+ netCDF files), see the README sheet
    eudr_cut_shares.xlsx                  the EUDR as an import cut by origin (Baseline_2stage.R, Calibrate_BAU_productivity.R): s_u =
                                          DeDuCE unamortised attribution 2021-2023 of the covered commodities / the sector's land base
                                          in the GTAP-AEZ data, the EU import flows with s_u >= 0.1 % (sheet shocks), see its README

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
ap.add_argument("--hilda", default=None, help="HILDA+ transitions by country x AEZ x year (default <out>/HILDA_v2.1_transitions_country_AEZ.csv)")
ap.add_argument("--hilda-window", nargs=2, type=int, default=[2012, 2019], help="years of HILDA+ transitions averaged for the AEZ shares")
ap.add_argument("--hilda-classes", default="forest", choices=["forest", "forest55"],
                help="source classes of the conversions: forest = HILDA+ forest classes 40-45; forest55 = + unmanaged grass/shrubland (55)")
ap.add_argument("--hilda-55-for", default="ARG", help="ISO3 codes (comma-separated) whose class-55 conversions are counted with --hilda-classes forest; '' = none")
ap.add_argument("--bau-horizon", type=int, default=5, help="years of business-as-usual clearing in the baseline")
ap.add_argument("--bau-cap", type=float, default=25.0, help="a cell never loses more than this %% of its forest cover over the horizon")
ap.add_argument("--bau-min", type=float, default=10000.0, help="regions clearing less than this (ha/yr, DeDuCE 2018-2023) get no BAU shock")
ap.add_argument("--bau-shares-override", default=None, help="csv (region, aez, share) replacing the HILDA+ shares of the regions it lists, e.g. a national deforestation product (default <out>/bau_shares_override.csv if it exists)")
ap.add_argument("--no-bau", action="store_true", help="do not rebuild bau_deforestation.xlsx")
ap.add_argument("--eudr-years", nargs=2, type=int, default=[2021, 2023], help="DeDuCE years summed for the EUDR shares (clearing after the cut-off of 31 Dec 2020)")
ap.add_argument("--eudr-cap", type=float, default=0.5, help="cap on s_u, the share of an origin's output of the sector from post-cut-off clearing")
ap.add_argument("--eudr-min", type=float, default=0.001, help="flows with s_u below this are not cut (sheet shocks)")
ap.add_argument("--no-eudr", action="store_true", help="do not rebuild eudr_cut_shares.xlsx")
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
    def pkg_root(c):   # the folder that holds the harpy package: c itself, or one level down (a zip extracted into a folder of the same name)
        if c is None: return None
        for d in [c] + [os.path.join(c, x) for x in (os.listdir(c) if os.path.isdir(c) else [])]:
            if os.path.isfile(os.path.join(d, "harpy", "har_file.py")): return d
        return ""
    test = os.path.join(GTAP, "sets.har")
    if not hasattr(np, "chararray"): np.chararray = np.char.chararray   # HARPY still uses np.chararray, dropped from the top level of numpy 2.x
    for c in [pkg_root(c) for c in cands]:
        if c == "": continue
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

# ---------------------------------------------------------------- bau_deforestation.xlsx: the BAU clearing by region x AEZ
# D_region = DeDuCE unamortised attribution 2018-2023 (all commodities except forest plantations), regions clearing >= --bau-min ha/yr.
# Split across the region's AEZs with the HILDA+ v2.1 shares: conversions of natural vegetation (forest classes 40-45, plus the
# unmanaged grass/shrubland class 55 where asked) to annual crops (22), tree crops (23), agroforestry (24) and pasture (33), summed
# over the countries of the region and the years of --hilda-window, by GTAP AEZ (HILDA_v2.1_transitions_country_AEZ.csv, from
# hilda_country_aez_tables.py, which assigns every 0.01-degree HILDA+ cell to a country and to the AEZ of the FAO GAEZ 18-class map).
# The clearing lands on the model's forest cells (Forestland cover > 0 and forestry land rent > 0: tinc must have leverage); the shares
# of AEZs without such a cell are spread over the cells in proportion to theirs; a cell never loses more than --bau-cap % of its cover
# over the horizon, the excess going to the region's other cells (water-filling; what no cell can take is reported as unplaced).
AEZS = els("AEZS"); COVS = els("COVS"); ENDW = els("ENDW")
LCOV = D["LCOV"].array; EVOS = D["EVOS"].array
if not args.no_bau:
    hilda_path = args.hilda or os.path.join(OUT, "HILDA_v2.1_transitions_country_AEZ.csv")
    if not os.path.exists(hilda_path):
        sys.exit(f"HILDA+ table not found: {hilda_path}\n(run hilda_country_aez_tables.py on the HILDA+ netCDF files and copy its transitions csv there, or pass --hilda; --no-bau skips the workbook)")
    hz = pd.read_csv(hilda_path)
    y0, y1 = args.hilda_window; n_years = y1 - y0 + 1
    forest_cls = [40, 41, 42, 43, 44, 45]; iso55 = {x.strip().upper() for x in args.hilda_55_for.split(",") if x.strip()} if args.hilda_classes == "forest" else None
    hz = hz[hz.year.between(y0, y1) & hz.to_class.isin([22, 23, 24, 33])].copy()
    keep = hz.from_class.isin(forest_cls) | ((hz.from_class == 55) & (hz.iso3.isin(iso55) if iso55 is not None else True))
    hz = hz[keep].copy()
    cls_label = "HILDA+ classes 40-45 + 55" if args.hilda_classes == "forest55" else ("HILDA+ classes 40-45" + (f" (+ 55 for {', '.join(sorted(iso55))})" if iso55 else ""))
    iso_group = df.drop_duplicates("ISO").set_index("ISO")["Continent/Country group"].to_dict()
    def region_of_iso(iso):
        if not isinstance(iso, str) or not iso: return None
        if iso in iso_group: return map_iso(iso, iso_group[iso])
        code = iso_special.get(iso, iso.lower())
        return reg_of.get(code)
    hz["reg"] = [region_of_iso(i) for i in hz.iso3]
    skipped = hz[hz.reg.isna()].groupby("country").area_ha.sum() / n_years
    if len(skipped): say("HILDA+ countries without a model region (left out, ha/yr):", ", ".join(f"{c} {v:,.0f}" for c, v in skipped.sort_values(ascending=False).items()))
    hz = hz[hz.reg.notna()]
    H = hz.groupby(["reg", "aez"]).area_ha.sum().unstack("aez").reindex(REG).fillna(0.0) / n_years        # ha/yr by region x AEZ (1..18, 0 = no AEZ)
    H = H.reindex(columns=range(1, 19), fill_value=0.0); H.columns = [f"AEZ{a}" for a in H.columns]
    H_countries = hz.groupby(["reg", "iso3", "country"]).area_ha.sum().reset_index(); H_countries["area_ha"] /= n_years
    D_reg = tables["D_unamort_w2018_2023"].reindex(columns=acts_land).sum(axis=1)                          # ha/yr, forest plantations excluded
    fi = COVS.index("Forestland"); ai = ACTS.index("forest"); aez_rows = [ENDW.index(a) for a in AEZS]
    cover = pd.DataFrame(LCOV[:, fi, :] * 1000.0, index=AEZS, columns=REG)                                  # ha
    rent = pd.DataFrame(EVOS[aez_rows, ai, :], index=AEZS, columns=REG)                                      # $ million
    H_years = n_years; cap = args.bau_cap / 100.0; horizon = args.bau_horizon
    ovr_path = args.bau_shares_override or os.path.join(OUT, "bau_shares_override.csv")
    override = {}
    if os.path.exists(ovr_path):   # region, aez (AEZ5 or 5), share (any scale: normalised per region), optional source
        ov = pd.read_csv(ovr_path); ov["aez"] = ["AEZ" + str(a).upper().replace("AEZ", "") for a in ov.aez]
        for r, g in ov.groupby("region"):
            override[r] = (g.set_index("aez")["share"].astype(float).reindex(AEZS).fillna(0.0), str(g["source"].iloc[0]) if "source" in g else os.path.basename(ovr_path))
        say(f"BAU shares overridden for {', '.join(sorted(override))} from {ovr_path}")
    cells_rows, region_rows, share_rows = [], [], []
    for r in REG:
        Dr = float(D_reg[r])
        if Dr < args.bau_min: continue
        L = Dr * horizon
        in_model = [a for a in AEZS if cover.loc[a, r] > 0 and rent.loc[a, r] > 0]
        h = H.loc[r].reindex(AEZS).fillna(0.0)
        share_src = "HILDA+"
        if r in override and override[r][0].sum() > 0: share_src = "override: " + override[r][1]; h = override[r][0]
        elif h.sum() <= 0:                                                     # no HILDA+ clearing in the region: fall back to the cover shares
            share_src = "cover"; h = pd.Series([cover.loc[a, r] if a in in_model else 0.0 for a in AEZS], index=AEZS)
        s_raw = h / h.sum()
        for a in AEZS:
            if h[a] > 0 or a in in_model:
                share_rows.append((r, a, round(float(h[a]), 1) if share_src == "HILDA+" else np.nan, round(100 * float(s_raw[a]), 3), a in in_model))
        s_in = s_raw.reindex(in_model)
        unplaced_share = max(0.0, 1.0 - float(s_in.sum()))
        if s_in.sum() <= 0: share_src = "cover"; s_in = pd.Series([cover.loc[a, r] for a in in_model], index=in_model)
        s_in = s_in / s_in.sum()
        cov = pd.Series([cover.loc[a, r] for a in in_model], index=in_model)
        loss = L * s_in; capv = cap * cov; fixed = pd.Series(False, index=in_model); unplaced_ha = 0.0
        while True:                                                            # water-filling under the cap
            over = (loss > capv + 1e-6) & ~fixed
            if not over.any(): break
            excess = float((loss[over] - capv[over]).sum()); loss[over] = capv[over]; fixed |= over
            free = ~fixed
            if not free.any(): unplaced_ha = excess; break
            loss[free] += excess * s_in[free] / float(s_in[free].sum())
        for a in in_model:
            cells_rows.append((r, a, round(float(cov[a])), round(float(rent.loc[a, r]), 2), round(float(loss[a])), round(-100 * float(loss[a]) / float(cov[a]), 4),
                               bool(fixed[a]), round(Dr), horizon, round(100 * float(s_raw[a]), 3), round(100 * float(loss[a]) / L, 3), round(float(h[a]), 1) if share_src == "HILDA+" else np.nan))
        n_c = int((H_countries.reg == r).sum())
        region_rows.append((r, round(Dr), cov.sum() / 1e6, float(loss.sum()) / 1e6, round(100 * float(loss.sum()) / float(cov.sum()), 2), len(in_model), bool(fixed.any()),
                            round(float(H.loc[r].sum())) if share_src == "HILDA+" else 0, n_c, share_src, round(100 * unplaced_share, 2), unplaced_ha / 1e6))
    aez_no = lambda a: a.str.replace("AEZ", "").astype(int)
    cells = pd.DataFrame(cells_rows, columns=["region", "aez", "forest_cover_ha", "forestry_rent_M", "bau_loss_ha", "shock_pct", "capped", "D_region_ha_yr", "horizon_yr", "hilda_share_pct", "share_used_pct", "hilda_ha_yr"])
    cells = cells.assign(_k=aez_no(cells.aez), _r=cells.region.str.lower()).sort_values(["_r", "_k"]).drop(columns=["_k", "_r"]).reset_index(drop=True)
    by_region = pd.DataFrame(region_rows, columns=["region", "D_ha_yr", "forest_cover_Mha", "bau_loss_Mha", "pct_of_cover", "n_aez", "capped", "hilda_ha_yr", "n_countries", "share_source", "unplaced_share_pct", "unplaced_Mha"])
    by_region = by_region.assign(_r=by_region.region.str.lower()).sort_values("_r").drop(columns="_r").reset_index(drop=True)
    shares = pd.DataFrame(share_rows, columns=["region", "aez", "hilda_ha_yr", "share_pct", "in_model"])
    shares = shares.assign(_k=aez_no(shares.aez), _r=shares.region.str.lower()).sort_values(["_r", "_k"]).drop(columns=["_k", "_r"]).reset_index(drop=True)
    H_countries = H_countries.rename(columns={"area_ha": "hilda_ha_yr"}).sort_values(["reg", "hilda_ha_yr"], ascending=[True, False])
    with pd.ExcelWriter(os.path.join(OUT, "bau_deforestation.xlsx")) as xw:
        pd.DataFrame({"README": [
          "Business-as-usual (BAU) clearing imposed in the baseline and kept on non-members: forest cover falls by shock_pct in each (region, AEZ) cell.",
          "D_region_ha_yr = mean annual DeDuCE v2.1 unamortised deforestation attribution 2018-2023, all commodities except forest plantations (h_table_DeDuCE.xlsx, sheet D_unamort_w2018_2023). Horizon = %d years: bau_loss = D x horizon. Regions with D < %s ha/yr are left out." % (horizon, format(args.bau_min, ",.0f")),
          "Allocated across the region's AEZs in proportion to the observed clearing by AEZ (hilda_share_pct): HILDA+ v2.1 conversions of %s to annual crops, tree crops, agroforestry and pasture, %d-%d, summed over the countries of the region (sheets hilda_shares, hilda_countries; HILDA_v2.1_transitions_country_AEZ.csv from hilda_country_aez_tables.py, every 0.01-degree cell assigned to a country and to the AEZ of the FAO GAEZ 18-class map)." % (cls_label, y0, y1),
          "Cells = AEZs with Forestland cover (GTAP-AEZ LCOV) and forestry land rent (EVOS) > 0, where tinc has leverage; the shares of the other AEZs are spread over the cells in proportion to theirs (unplaced_share_pct in by_region). share_source = cover where HILDA+ has no clearing for the region; 'override: ...' where a bau_shares_override.csv (region, aez, share) replaces the HILDA+ shares, e.g. with a national deforestation product.",
          "A cell never loses more than %.0f %% of its cover over the horizon: the excess is moved to the region's other cells in proportion to their shares (capped = True marks the cells at the cap; unplaced_Mha = what no cell could take). shock_pct = -100 x bau_loss / cover. The R scripts recompute shock_pct from bau_loss_ha, horizon_yr and forest_cover_ha and apply the same cap." % args.bau_cap,
          "Model use: baseline  swap p_LANDCOVER_L(AEZ,\"Forestland\",r) = tinc(AEZ,\"forest\",r); shock p_LANDCOVER_L = shock_pct;  -> solved tinc* = implicit clearing incentive. Game: non-members  shock tinc = tinc* (forest endogenous, leakage possible); members  swap p_LANDCOVER_L = tinc; shock 0 (no net loss).",
          "Sources: DeDuCE v2.1 (Zenodo 10.5281/zenodo.18953516); HILDA+ v2.1-crop (Winkler et al., Zenodo 10.5281/zenodo.8419004); FAO GAEZ v4; GTAP-AEZ base data of the model (LCOV, EVOS). Built by 0_External_data/DeDuCE_rework/zenodo_v2.1/build_deduce_tables.py."]}).to_excel(xw, sheet_name="README", index=False)
        cells.to_excel(xw, sheet_name="cells", index=False)
        by_region.to_excel(xw, sheet_name="by_region", index=False)
        shares.to_excel(xw, sheet_name="hilda_shares", index=False)
        H_countries[["reg", "iso3", "country", "hilda_ha_yr"]].rename(columns={"reg": "region"}).to_excel(xw, sheet_name="hilda_countries", index=False)
    say(f"\n=== BAU clearing ({cls_label}, HILDA+ {y0}-{y1}; DeDuCE 2018-2023 x {horizon} yr; cap {args.bau_cap:g} %) ===")
    say(by_region.round(3).to_string(index=False))
    say("\nshares by AEZ (%) of the 12 producers, as used:")
    for r in producers:
        c = cells[cells.region == r]
        say(f"  {r:<11}", " ".join(f"{a}:{v:.0f}{'*' if k else ''}" for a, v, k in zip(c.aez, c.share_used_pct, c.capped) if v >= 0.5), "(* at the cap)")
    say(f"bau_deforestation.xlsx: {len(cells)} cells, {by_region.bau_loss_Mha.sum():.2f} Mha over {horizon} years, unplaced {by_region.unplaced_Mha.sum():.2f} Mha")

# ---------------------------------------------------------------- eudr_cut_shares.xlsx: the EUDR as an import cut by origin
# s_u(sector, origin) = DeDuCE unamortised attribution over --eudr-years (cumulative ha, the clearing after the cut-off of 31 Dec 2020)
# of the covered commodities / the sector's land base in the GTAP-AEZ data (harvested area AREA for ocr and osd, Pastureland cover LCOV
# for cattle), capped at --eudr-cap. Baseline_2stage.R and Calibrate_BAU_productivity.R shock the EU's imports of the flows of sheet
# shocks (s_u >= --eudr-min and positive base imports): shock qxs(c, r, eu27) = -100 x s_u, with ams(c, r, eu27) endogenous.
if not args.no_eudr:
    ey0, ey1 = args.eudr_years
    EUDR_MAP = {"Cattle meat": "ruminant", "Leather": "ruminant", "Cocoa beans": "ocr", "Coffee, green": "ocr", "Natural rubber in primary forms": "ocr",
                "Soya beans": "osd", "Oil palm fruit": "osd", "Palm nuts and kernels": "osd"}
    CARRIED = [("ruminant", "ruminant"), ("RuminantMeat", "ruminant"), ("ocr", "ocr"), ("osd", "osd"), ("vegoil", "osd")]   # GTAP commodity -> the sector whose share it carries
    EU = "EU27"
    missing = [c for c in EUDR_MAP if c not in set(df.Commodity)]
    assert not missing, f"DeDuCE commodity names not found: {missing}"
    esub = df[df.Year.between(ey0, ey1) & df.Commodity.isin(EUDR_MAP)]
    detail = esub.groupby(["reg", "Commodity"])[U].sum().unstack("Commodity").reindex(REG).reindex(columns=sorted(EUDR_MAP)).fillna(0.0)
    esub = esub.assign(sector=esub.Commodity.map(EUDR_MAP))
    num = esub.groupby(["reg", "sector"])[U].sum().unstack("sector").reindex(REG).reindex(columns=["ocr", "osd", "ruminant"]).fillna(0.0)   # ha, cumulative
    AREA = D["AREA"].array; CROP = els("CROP")
    den = pd.DataFrame({"ruminant": LCOV[:, COVS.index("Pastureland"), :].sum(axis=0) * 1000.0,
                        "ocr": AREA[:, CROP.index("ocr"), :].sum(axis=0) * 1000.0, "osd": AREA[:, CROP.index("osd"), :].sum(axis=0) * 1000.0}, index=REG)   # ha
    unc = (num / den.reindex(columns=num.columns).replace(0, np.nan)).fillna(0.0)
    capd = unc.clip(upper=args.eudr_cap)
    pairs = []
    for r in REG:
        if r == EU: continue
        for comm, sec in CARRIED:
            su = round(float(capd.loc[r, sec]), 5)
            pairs.append((comm, r, EU, su, round(-100 * su, 3), round(float(VCIF[COMM.index(comm), REG.index(r), REG.index(EU)]), 3), round(float(num.loc[r, sec]), 1), round(float(den.loc[r, sec]), 1)))
    pairs = pd.DataFrame(pairs, columns=["comm", "source", "dest", "s_u", "cut_pct", "VCIF_EU_import_M", f"numerator_ha_{ey0}_{str(ey1)[2:]}", "denominator_ha"])
    shocks = pairs[(pairs.s_u >= args.eudr_min) & (pairs.VCIF_EU_import_M > 0)].reset_index(drop=True)
    pair_cols = [c for c in pairs.columns if c != "VCIF_EU_import_M" or args.with_gtap_values]   # the EU import values are GTAP data: written only with --with-gtap-values
    with pd.ExcelWriter(os.path.join(OUT, "eudr_cut_shares.xlsx")) as xw:
        pd.DataFrame({"README": [
          "EUDR baseline: share s_u of each origin's output of the covered sectors that comes from land deforested after the EUDR cut-off (31 Dec 2020).",
          "s_u = [DeDuCE v2.1 unamortised deforestation attribution, %d-%d cumulative, ha] / [sector land base in GTAP-AEZ base data: harvested area (AREA) for ocr and osd, Pastureland cover (LCOV) for cattle]." % (ey0, ey1),
          "Covered DeDuCE commodities: Cattle meat + Leather -> ruminant (also carried by RuminantMeat; GTAP lea = mostly footwear, outside the EUDR scope, not cut); Cocoa beans, Coffee green, Natural rubber -> ocr; Soya beans, Oil palm fruit, Palm nuts and kernels -> osd (also carried by vegoil). Wood is not attributed by DeDuCE and is not covered here.",
          "Shares are capped at %g (sheet shares_uncapped shows the raw ratio). The baseline script applies shock qxs(c,r,eu27) = cut_pct for the rows of sheet shocks (s_u >= %g and positive base EU imports in the GTAP data), with ams(c,r,eu27) endogenous.%s" % (args.eudr_cap, args.eudr_min, "" if args.with_gtap_values else " The EU import values (VCIF, GTAP data) are not written: --with-gtap-values restores the column (never deposit such a file)."),
          "Sources: DeDuCE v2.1 (Zenodo 10.5281/zenodo.18953516; Singh & Persson, Nature Food 2026); GTAP-AEZ base data of the model (2_Model/in/basedata.har). Built by 0_External_data/DeDuCE_rework/zenodo_v2.1/build_deduce_tables.py."]}).to_excel(xw, sheet_name="README", index=False)
        shocks[pair_cols].to_excel(xw, sheet_name="shocks", index=False)
        pairs[pair_cols].to_excel(xw, sheet_name="all_pairs", index=False)
        (100 * capd).round(3).rename(columns=lambda c: c + "_pct").rename_axis("reg").reset_index().to_excel(xw, sheet_name="shares_capped_pct", index=False)
        (100 * unc).round(3).rename(columns=lambda c: c + "_pct").rename_axis("reg").reset_index().to_excel(xw, sheet_name="shares_uncapped", index=False)
        num.round(1).rename_axis("reg").reset_index().to_excel(xw, sheet_name=f"numerator_ha_{ey0}_{ey1}", index=False)
        den.round(1).rename_axis("reg").to_excel(xw, sheet_name="denominator_ha_GTAP")
        detail.round(1).rename_axis("reg").reset_index().to_excel(xw, sheet_name=f"DeDuCE_detail_ha_{ey0}_{ey1}", index=False)
    say(f"\n=== EUDR cut shares ({ey0}-{ey1}, cap {args.eudr_cap:g}): {len(shocks)} EU import flows with s_u >= {100 * args.eudr_min:g} % (of {len(pairs)} pairs) ===")
    say((100 * capd.loc[producers]).round(3).rename(columns=lambda c: c + "_pct").to_string())

# ---------------------------------------------------------------- console summary for the 12 producers
show = ["osd", "ruminant", "RuminantMeat", "rmk", "dairy", "vegoil", "ocr", "c_b", "sgr", "gro", "pdr", "pcr", "v_f", "pfb", "wht", "lea"]
say("\n=== attributed deforestation (ha/yr, amortised, 2018-2023), producers x land activities ===")
say(tables["D_amort_w2018_2023"].loc[producers, acts_land].round(0).to_string())
say("\n=== h_total (ha per $1000 of output), amortised 2018-2023 ===")
say((h_tot.loc[producers, show] * 1000).round(4).to_string())
say("\n=== AVE at $10000/ha (%) ===");  say((ave["AVE_pha10000"].loc[producers, show] * 100).round(2).to_string())
say("\n=== AVE at $100/tCO2 (%) ===");  say((ave["AVE_co2_100"].loc[producers, show] * 100).round(2).to_string())
say(f"\nwritten to {OUT}: h_table_DeDuCE.xlsx, tms_f_initial_shocks_DeDuCE.xlsx, {len(n_rows)} tms_f_shocks_bilateral_*.csv" + ("" if args.no_bau else ", bau_deforestation.xlsx") + ("" if args.no_eudr else ", eudr_cut_shares.xlsx"))
