# Forest Coalition rework — DeDuCE-based border charge, first pass (18 Sep 2026)

Nothing outside this folder was modified: the R script, CMFs, database and existing external-data sheets are untouched. GitHub note: the GTAP database files (`2_Model\in\basedata.har`, `baserate.har`, `baseview.har`, `gtapSAM.har`, `default.prm`, the `gsdf*.har`) are licensed and must not go in a public repository; the `.gitignore` at the repo root excludes them and the GEMPACK work files. The `VCIF_$M` column in the bilateral csv and the `VOM_$M` sheet in `h_table_DeDuCE.xlsx` are GTAP-derived values too — drop them before making the repo public, or keep it private.

## What is here

| File | What it is |
|---|---|
| `h_table_DeDuCE.xlsx` | Everything behind the numbers: DeDuCE hectares and tCO2 by region × GTAP activity (two windows, amortised and unamortised), GTAP output values, `h_direct`, `h_total` (domestic Leontief), `e_total`, AVE tables for p_ha ∈ {400, 2000, 10000} $/ha and P_CO2 ∈ {50, 100, 190} $/tCO2, and the hectare-weighted DeDuCE quality index. |
| `tms_f_initial_shocks_DeDuCE.xlsx` | Same layout as your `tms_f_initial_shocks.xlsx`, one sheet per price scenario, values = 100 × AVE. Sheet `OLD_current_file` = what the model uses today. Destination-independent (ignores t0) — use for the paper table and quick looks. |
| `tms_f_shocks_bilateral_<tag>.csv` | The exact shocks for header 0101: `100 × AVE(c, source) / (1 + t0(c, source, dest))`, one row per (commodity, source, destination) with VCIF > 0 and AVE ≥ 0.01 % (smaller charges dropped). This is what `rework_functions.R` reads. |
| `old_vs_new_tariffs.csv` | Old reverse-engineered rates vs new footprint-based rates, 12 producers × 9 sectors. |
| `rework_functions.R` | Drop-in replacements: one outsider rule (`footprint + tau`) for the five tariff-filling functions, `generate_text_for_forest` for `generate_text_for_qes`, transfer/revenue helpers. |

Sources: DeDuCE v2.1, Singh, Persson, Croft, Kastner & West (2026), Zenodo 10.5281/zenodo.18953516 (file 1, 2001–2023); method: Singh & Persson, *Nature Food* 7, 138–151 (2026). GTAP data: your live R1 database `C:\runGTAP375\Game_theory_2024\2_Model\in` (42 regions, 35 sectors, GTAP v12p2 aggregation).

## How the numbers are built

1. DeDuCE commodity → GTAP land-using activity: cereals → `pdr`/`wht`/`gro`; fruit, vegetables, roots, pulses → `v_f`; oilseeds and oleaginous fruits (soy, palm fruit, coconut…) → `osd`; sugar crops → `c_b`; fibre crops → `pfb` except rubber, tobacco, mint, pyrethrum → `ocr`; stimulants/spices (cocoa, coffee, tea…) → `ocr`; pasture (cattle meat + leather) → the three grazing activities `ruminant`, `rmk`, `wol` in proportion to their AEZ land rents (Brazil 69 / 29 / 2 %), so dairy and wool carry their share without double counting; forest plantations excluded.
2. DeDuCE ISO → model region via the `MREG` mapping in `sets.har` (residual regions by UN group; Myanmar sits in `xse`).
3. `D(a, r)` = mean annual attributed hectares over the window. Main case: **amortised (5-yr), 2018–2023** = "embodied in production" in the Pendrill/DeDuCE convention. Also provided: unamortised, and 2012–2019 for comparison with your HILDA+ results.
4. `h_direct(a, r) = D / VOM` (ha per $, VOM = column sum of MAKS). `h_total = h_direct × (I − A)^-1` with `A` the domestic intermediate-use coefficients from VDFB, **own-use diagonal set to zero** (otherwise DRC `pdr`, with 98% own-use in GTAP, inflates by ×50). This carries cattle → beef, raw milk → dairy, soy/palm → vegoil, cane → sugar, paddy → milled rice, hides → leather.
5. `AVE = p_ha × h_total` (fractions). Carbon variant: `AVE = P_CO2 × e_total`, `e_total` from DeDuCE emissions incl. peat drainage, negative values floored at 0 (Ivory Coast cocoa agroforestry is net negative in DeDuCE).
6. Bilateral shock: `100 × AVE / (1 + t0)`, `t0 = VMSB/VCIF − 1` from `basedata.har`. Matters: EU MFN on beef is 32%, sugar 23%, rice 21%.

## Orders of magnitude (amortised 2018–2023)

Brazil: pasture 1.42 Mha/yr (of which 0.98 Mha to cattle, 0.41 to dairy), soy 117 kha/yr. At $400/ha the charge is 1.5% on live cattle, 0.8% on beef, 1.5% on raw milk, 0.5% on dairy products, 0.14% on soybeans; ×5 at $2 000/ha, ×25 at $10 000/ha. At $100/tCO₂ (514 tCO₂/ha in DeDuCE for Brazilian pasture) beef is ~115%, soybeans 12%, Indonesian palm oil 27% (peat).
Country averages over the eleven old sectors: old file 1.6–17% (Ivory Coast 17%, Paraguay 9%); new at $400/ha 0.1–3% (DRC highest); at $2 000/ha 0.4–15%.

## What to change in the R script (all in `rework_functions.R`)

- `source("0_External_data/DeDuCE_rework/rework_functions.R")` after the Parameters block; set `p_ha_tag` and `tau`.
- Replace `shock_eu27`, `shock_ABCD`, `shock_CD`, `shock_BD`, `shock_D` by one call, `shock_outsiders_into_members(shock, members, outsiders)`, with `outsiders` = every region not in the coalition. It writes `footprint AVE shock + tau` in every cell: with `tau = 0` a consumer without deforestation pays nothing (coalition), with `tau > 0` every outsider also pays the flat penalty (club).
- Replace `shock_eu27_exp` by `shock_members_zero`.
- Replace `generate_text_for_qes(club_producer)` by the two-pass: solve with `generate_text_for_forest(club_producer, bind_all = FALSE)` (no constraint), `fc <- read_forest_change_by_aez("NATDEF.sl4", club_producer)`, then `generate_text_for_forest(club_producer, forest_change = fc)` and solve again. The constraint is `swap p_LANDCOVER_L(AEZi,"Forestland",r) = tinc(AEZi,"forest",r); shock p_LANDCOVER_L(...) = 0;` — `tinc` is exogenous in your closure, so no TAB change. The solved `tinc(AEZi,"forest",r)` is the forest-land subsidy that holds the forest; in $/ha: `tinc% × EVOS(AEZi,"forest",r) / LCOV(AEZi,"Forestland",r) × 10` (EVOS in $M, LCOV in 1000 ha).
- Delete the GlobTari step. Drop every `qes`/`afeall` line.
- Check `del_LUC` in the SL4 has dims AEZS × LCOV × REG (the reader assumes that order).

Status (19 Sep 2026): the functions above are now inside the scripts themselves — `1_Code/CGE_Game_Theory_GTAPAEZ_all_V14.R` (new tariff values, sheet `AVE_pha400`), `V15.R` (forest commitment through `p_LANDCOVER_L`/`tinc`, parameter `"forest"`), `V16.R` (EUDR baseline as iteration 0). `rework_functions.R` is kept for reference only. Still to come: the bilateral tariff rule with the `tau` switch (coalition vs club).

## EUDR baseline (`eudr_cut_shares.xlsx`, used by `1_Code/Baseline_EUDR.R`)

The baseline is the EU alone applying the EUDR: its imports of the covered products from each origin fall by `s_u`, the share of that origin's output of the sector that comes from land deforested after the cut-off (31 Dec 2020). `s_u` = DeDuCE unamortised attribution 2021–2023 (ha, cumulative) ÷ the sector's land base in the GTAP-AEZ base data (harvested area `AREA` for `ocr`, `osd`; `Pastureland` cover `LCOV` for cattle). Covered: cattle meat + leather → `ruminant`, `RuminantMeat`; cocoa, coffee, natural rubber → `ocr`; soya, oil palm → `osd`, `vegoil`. GTAP `lea` is mostly footwear (outside the EUDR) and is not cut; wood is not attributed by DeDuCE and is not covered. Sheet `shocks` = the 94 EU import flows with `s_u ≥ 0.1 %` and positive base imports ($23.7 bn of EU imports); the other sheets show the ingredients. Orders of magnitude: Brazil pasture 2.6 %, Brazil soy 0.6 %, Indonesia palm 1.1 %, Ivory Coast `ocr` 6.2 %, DRC `ocr` 14.6 %; value-weighted cut on EU imports: `ocr` 1.6 %, `vegoil` 0.7 %, `RuminantMeat` 0.4 %. `eudr_scale` in the script multiplies the shares (traceability scenario: unverifiable output also excluded).

A ban, not a tax: for each cut flow `swap qxs(c,r,"eu27") = ams(c,r,"eu27")`, `shock qxs = −100·s_u`; the model solves the iceberg import cost that produces the cut, no tariff revenue. The solved `ams` is saved (`ams_baseline.txt`) and the game script (V16, `eudr_in_loop = "outsiders"`) keeps it as an exogenous cost on non-members' exports to the EU; members are deemed compliant.

## Caveats to carry into the SI

- DRC and Ivory Coast attributions are mostly statistical (quality index ≈ 0.2); Brazil soy 0.87, Argentina soy 0.80, Indonesia/Malaysia palm 0.6–0.7. Report the IQI sheet.
- Indonesia's attributed deforestation fell from 587 kha/yr (2012–19) to 265 kha/yr (2018–23); Argentina and Paraguay halved; Brazil rose. The window choice is a result, show both.
- The charge is origin-neutral: LatinAmer, SEAsia, CAfr, WAfr, Madagascar, Nigeria, Mozambique, Venezuela, Uruguay, Mexico… get their own (small) rates where DeDuCE attributes deforestation, and `shock_outsiders_into_members` applies them. Only the twelve producers can take the forest commitment (they are the ones with AEZ coefficients); everyone else can join as a consumer.
- `rmk` and `wol`: charged, at their land-rent share of pasture deforestation (not at the cattle rate as before, which double-counted the hectares).
- Peat drainage emissions are in the carbon variant; they are ongoing emissions from existing plantations, not new clearing — say so if you use that variant.
