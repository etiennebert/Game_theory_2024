"""
Build the embodied-deforestation intensity table h(sector, region) and the
border-charge (AVE) tables for the Forest Coalition rework, from:
  - DeDuCE v2.1 (Singh & Persson 2026), country x commodity x year hectares & emissions
  - the live R1 GTAP-AEZ v7 database (42 regions, 35 sectors): output values (MAKS),
    domestic use matrix (VDFB) for a domestic Leontief pass, bilateral tariffs (VMSB/VCIF)
Outputs (in ./out):
  h_table.xlsx           all intermediate and final tables
  tms_f_bilateral_<tag>.csv   long table (comm, source, dest, shock %) per price scenario
"""
import sys, numpy as np, pandas as pd
sys.path.insert(0, "/tmp/HARPY")
from harpy import HarFileObj

BASE = "/mnt/user-data/uploads/Game_theory_2024/2_Model/in"
OUT = "/tmp/claude-0/-home-claude/4124e020-d2c1-5af1-8b6d-b33bb2cbec4b/scratchpad/deduce/out"
import os; os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- GTAP sets & data
S = HarFileObj(f"{BASE}/sets.har")
def els(h): return [str(x).strip() for x in S[h].array.flatten()]
REG, COMM, ACTS = els("REG"), els("COMM"), els("ACTS")
DREG, MREG = els("DREG"), els("MREG")
reg_of = dict(zip(DREG, MREG))          # gtap country code -> model region
D = HarFileObj(f"{BASE}/basedata.har")
MAKS = D["MAKS"].array   # (COMM, ACTS, REG)  $ million
VDFB = D["VDFB"].array   # (COMM, ACTS, REG)  domestic intermediate use, basic prices
VMSB = D["VMSB"].array   # (COMM, REG_s, REG_d) imports at basic prices (cif + duty)
VCIF = D["VCIF"].array   # (COMM, REG_s, REG_d)
VOM = MAKS.sum(axis=0)   # (ACTS, REG) output value by activity
assert COMM == ACTS

# ---------------------------------------------------------------- DeDuCE
df = pd.read_pickle("deduce.pkl")
U  = "Deforestation attribution, unamortized (ha)"
A  = "Deforestation risk, amortized (ha)"
EA = "Deforestation emissions incl. peat drainage, amortized (MtCO2)"
EU_ = "Deforestation emissions excl. peat drainage, unamortized (MtCO2)"
PE = "Peatland drainage emissions (MtCO2)"

# --- commodity -> GTAP land-using activity
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

# --- ISO -> GTAP model region.  Direct where GTAP has the country; residuals by group.
iso_special = {"ROU":"rou","XKX":"xer","SSD":"xec","SDN":"sdn","MMR":"xse","TLS":"xse",
               "COD":"cod","COG":"cog","CIV":"civ"}
group_fallback = {"Africa":None, "Europe":"xer", "North Asia":"xsu", "North and Central America":"xca",
                  "Oceania":"xoc", "Rest of Asia":"xws", "South America":"xsm", "Southeast Asia":"xse"}
africa_fallback = {  # UN geoscheme -> GTAP residual
  "xnf":["LBY","ESH"], "xwf":["CPV","GMB","GNB","LBR","SLE","MRT"], "xcf":["CMR","CAF","TCD","COG","GNQ","GAB","STP"],
  "xac":[], "xec":["BDI","COM","DJI","ERI","ETH","KEN","MDG","MWI","MUS","MOZ","RWA","SYC","SOM","SSD","SDN","TZA","UGA","ZMB","ZWE"],
  "xsc":["BWA","LSO","NAM","SWZ","ZAF"]}
africa_lookup = {iso:r for r, l in africa_fallback.items() for iso in l}
def map_iso(iso, group):
    code = iso_special.get(iso, iso.lower())
    if code in reg_of: return reg_of[code]
    if group == "Africa":
        code = africa_lookup.get(iso, "xec")
    else:
        code = group_fallback[group]
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

# pasture deforestation (DeDuCE: cattle meat + leather) is split across the three grazing
# activities in proportion to their AEZ land rents (EVFB), so dairy and wool carry their share
EVFB = D["EVFB"].array
ENDW = els("ENDW"); aez_rows = [i for i, e in enumerate(ENDW) if e.startswith("AEZ")]
land_rent = EVFB[aez_rows, :, :].sum(axis=0)                     # ACTS x REG
graz = ["ruminant", "rmk", "wol"]
gi = [ACTS.index(a) for a in graz]
tot = land_rent[gi, :].sum(axis=0)
pasture_share = pd.DataFrame({a: np.where(tot > 0, land_rent[ACTS.index(a), :] / np.where(tot > 0, tot, 1), [1,0,0][k])
                              for k, a in enumerate(graz)}, index=REG)
def split_pasture(tab):
    tab = tab.copy()
    rum = tab["ruminant"].copy()
    for a in graz:
        tab[a] = rum * pasture_share[a]
    return tab

tables = {}
for w, (a, b) in windows.items():
    tables[f"D_unamort_{w}"] = split_pasture(window_mean(U, a, b))          # ha/yr
    tables[f"D_amort_{w}"]   = split_pasture(window_mean(A, a, b))          # ha/yr, 5-yr amortised
    tables[f"E_amort_{w}"]   = split_pasture(window_mean(EA, a, b) * 1e6)   # tCO2/yr incl. peat
    tables[f"E_unamort_{w}"] = split_pasture((window_mean(EU_, a, b) + window_mean(PE, a, b)) * 1e6)
tables["pasture_share_ruminant_rmk_wol"] = pasture_share

acts_land = ["pdr","wht","gro","v_f","osd","c_b","pfb","ocr","ruminant","rmk","wol"]
# ha-weighted Integrated Quality Index per region x activity (main window)
_sub = df[(df.Year >= 2018) & (df.Year <= 2023) & (df.act != "forest")].copy()
_sub["wq"] = _sub[U] * _sub["Integrated Quality Index"]
_g = _sub.groupby(["reg","act"]).agg(wq=("wq","sum"), ha=(U,"sum"))
tables["IQI_w2018_2023"] = (_g.wq / _g.ha).unstack("act").reindex(REG)
vom = pd.DataFrame(VOM.T, index=REG, columns=ACTS)          # $ million
tables["VOM_$M"] = vom

# ---------------------------------------------------------------- h direct & Leontief-total
def leontief_total(hd):   # hd: DataFrame (REG x ACTS) ha per $ ; returns REG x ACTS
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
        hd = Dw / (vom * 1e6).replace(0, np.nan)             # ha per $
        hd = hd.fillna(0.0)
        tables[f"h_direct_{kind}_{w}"] = hd
        tables[f"h_total_{kind}_{w}"]  = leontief_total(hd)
        Ew = tables[f"E_{kind}_{w}"].reindex(columns=ACTS).fillna(0.0)
        ed = (Ew / (vom * 1e6).replace(0, np.nan)).fillna(0.0)   # tCO2 per $
        tables[f"e_direct_{kind}_{w}"] = ed
        tables[f"e_total_{kind}_{w}"]  = leontief_total(ed)
        # tCO2 per ha (activity level) for reporting
        tables[f"tCO2_per_ha_{kind}_{w}"] = (Ew / Dw.replace(0, np.nan)).fillna(0.0)

# ---------------------------------------------------------------- AVE tables (main case: amortised, 2018-2023)
MAIN = "amort_w2018_2023"
h_tot = tables[f"h_total_{MAIN}"]
e_tot = tables[f"e_total_{MAIN}"]
p_ha_grid = [400, 2000, 10000]
pco2_grid = [50, 100, 190]
ave = {}
for p in p_ha_grid:
    ave[f"AVE_pha{p}"] = h_tot * p                # $/ha * ha/$ -> fraction
for pc in pco2_grid:
    ave[f"AVE_co2_{pc}"] = (e_tot * pc).clip(lower=0.0)   # tCO2/$ * $/tCO2 -> fraction; no negative charges
tables.update(ave)

# ---------------------------------------------------------------- bilateral tariff-power shocks
t0 = np.where(VCIF > 0, VMSB / np.where(VCIF > 0, VCIF, 1) - 1.0, 0.0)   # (COMM, s, d)
charged = ["pdr","wht","gro","v_f","osd","c_b","pfb","ocr","ruminant","rmk","wol","RuminantMeat","vegoil","pcr","sgr","lea","dairy"]
for tag, avetab in ave.items():
    rows = []
    for ci, c in enumerate(COMM):
        if c not in charged: continue
        for si, s in enumerate(REG):
            a = avetab.loc[s, c]
            if a <= 0: continue
            for di, d in enumerate(REG):
                if si == di or VCIF[ci, si, di] <= 0: continue
                rows.append((c, s, d, 100.0 * a / (1.0 + t0[ci, si, di]), 100.0 * a, VCIF[ci, si, di]))
    pd.DataFrame(rows, columns=["comm","source","dest","shock_tms_f_pct","AVE_pct","VCIF_$M"]) \
      .to_csv(f"{OUT}/tms_f_bilateral_{tag}.csv", index=False)

# ---------------------------------------------------------------- write workbook
with pd.ExcelWriter(f"{OUT}/h_table.xlsx") as xw:
    readme = pd.DataFrame({"note":[
      "DeDuCE v2.1 (Zenodo 18953516) mapped to the R1 GTAP-AEZ v7 database (42 regions, 35 sectors).",
      "D_* : attributed deforestation, ha/yr, window mean; amort = 5-yr amortised 'embodied in production' (Pendrill/DeDuCE convention).",
      "E_* : tCO2/yr incl. peat drainage. Forest plantations excluded. Pasture (cattle meat + leather) -> ruminant.",
      "h_direct = D / output value (MAKS, $); h_total = h_direct x domestic Leontief inverse (I-A)^-1, A from VDFB.",
      "AVE_phaX = h_total x X $/ha ; AVE_co2_P = e_total x P $/tCO2. Fractions (0.01 = 1%).",
      "tms_f_bilateral_*.csv: shock = 100 x AVE / (1 + t0), t0 = VMSB/VCIF - 1, for flows with VCIF>0.",
      "Charged sectors in csv: primary land-using (incl. rmk, wol) + RuminantMeat, vegoil, pcr, sgr, lea, dairy.",
      "Pasture deforestation split across ruminant/rmk/wol by AEZ land-rent shares (sheet pasture_share_ruminant_rmk_wol).",
      "Leontief pass excludes own-use (diagonal of A) to avoid amplification from circular flows in poor-data regions (e.g. DRC pdr).",
      "IQI_w2018_2023: hectare-weighted DeDuCE quality index; >0.6 ~ direct (spatial) attribution, lower = statistical attribution."]})
    readme.to_excel(xw, sheet_name="README", index=False)
    for k, v in tables.items():
        v.to_excel(xw, sheet_name=k[:31])

# ---------------------------------------------------------------- console summary for the 12 producers
prod = ["Brasil","Indonesia","DRC","IvoryCoast","Bolivia","Argentina","Paraguay","Malasya","Colombia","Peru","Ghana","Angola"]
show = ["osd","ruminant","RuminantMeat","rmk","dairy","vegoil","ocr","c_b","sgr","gro","pdr","pcr","v_f","pfb","wht","lea"]
print("\n=== attributed deforestation (ha/yr, amortised, 2018-2023), producers x land activities ===")
print(tables[f"D_amort_w2018_2023"].loc[prod, acts_land].round(0).to_string())
print("\n=== h_total (ha per $1000 of output), amortised 2018-2023 ===")
print((h_tot.loc[prod, show]*1000).round(4).to_string())
print("\n=== AVE at $400/ha (%) ===");   print((ave["AVE_pha400"].loc[prod, show]*100).round(2).to_string())
print("\n=== AVE at $2000/ha (%) ===");  print((ave["AVE_pha2000"].loc[prod, show]*100).round(2).to_string())
print("\n=== AVE at $10000/ha (%) ===");  print((ave["AVE_pha10000"].loc[prod, show]*100).round(1).to_string())
print("\n=== AVE at $100/tCO2 (%) ===");  print((ave["AVE_co2_100"].loc[prod, show]*100).round(1).to_string())
print("\n=== tCO2 per ha (amortised 2018-2023) ===")
print(tables[f"tCO2_per_ha_{MAIN}"].loc[prod, acts_land].round(0).to_string())
print("\n=== base tariff t0 into EU27 (%), producers x sectors ===")
eu = REG.index("EU27")
print(pd.DataFrame({c: [100*t0[COMM.index(c), REG.index(r), eu] for r in prod] for c in show}, index=prod).round(1).to_string())
