# Tidying `C:\runGTAP375\Game_theory_2024` — the moves (nothing is deleted)

Goal: a folder in which a reviewer finds, in five places and nothing else, the inputs, the model, the scripts, the runs and the figures of the paper (`README.md`). Everything that preceded the V32 generation goes, unchanged, into `9_Archive\`, mirroring the path it came from, so that any old file is found again at `9_Archive\<its old path>`.

Done from the cloud session on 7 October: `5_Figures\` created (the figure pipeline, copied from `Revision 1\Figures_v2\scripts_v32\` with self-locating paths), `README.md`, `9_Archive\README.md`, `.gitignore` updated (`9_Archive/` ignored). The moves below need the file system: the session's shell on this computer is blocked by a Windows update of 8 September (the Claude app's workspace cannot mount the folders until the latest Windows update is installed and the computer restarted). Once it runs again, every move below can be done from the session in one pass; until then they are a few drag-and-drops in File Explorer, listed in the order that keeps the folder usable at every step.

## 1. Root

| Move | To | Why |
|---|---|---|
| `0. Old\` (3.7 GB: `2_Model_R0`, `2_Model_R1 - Copy`, `2_Model_R1_old`, `2_Model_V0`, `3_Output_7Threshold`, `2_Model_R1.zip`, `Book1.xlsx`, `test.tab`) | `9_Archive\0. Old\` | model copies and outputs of the first submission; the model copies contain the licensed GTAP Data Base — they stay off git whatever their folder |
| `2_Model.zip` (196 MB) | `9_Archive\` | a zipped copy of the model folder |
| `Revision 1\` (the copy inside the repository: `Figures_v2\`, two drafts of 28 September) | `9_Archive\Revision 1 (copy of 28 Sept)\` | a stale copy of the manuscript folder, which lives on OneDrive |
| `~$e scenario and parameters may lead to different dynamic of the system.docx` (162 bytes) | `9_Archive\` | a Word lock file left behind |

## 2. `1_Code\` — keep four scripts

Keep: `Baseline_2stage.R`, `Calibrate_BAU_productivity.R`, `CGE_Game_Theory_GTAPAEZ_all_V32.R`, `Run_V32_all.R`, and `Baseline_EUDR.R` (the one-solve baseline that calibrated the productivity shocks; `Baseline_2stage.R` refers to it).

| Move | To |
|---|---|
| `0. Old\` (the game script V13 → V31, `Run_V30_all.R`, `Run_V30_test.R`, `Run_V31.R`) | `9_Archive\1_Code\0. Old\` |
| `CGE_Game_Theory_GTAPAEZ_all_V13R1.R`, `CGE_Game_Theory_GTAPAEZ_all_V14.R` | `9_Archive\1_Code\` |
| `Run_complement.R`, `Run_fill.R`, `Run_minimum.R`, `Run_overnight.R`, `Run_overnight_friction.R`, `Run_sensitivity.R`, `Run_seven.R`, `Run_V31_all.R` (the runners of the V22–V31 generations) | `9_Archive\1_Code\` |
| `patch_v31.py`, `patch_v32.py` (the scripts that produced V31 and V32 from V30/V31; the result is the V32 script itself) | `9_Archive\1_Code\` |
| `.Rhistory` | `9_Archive\1_Code\` |

## 3. `2_Model\` — keep the model and its data base

Keep everything that is not listed here (TAB, CMF, closure, shocks, executables, `in\`).

| Move | To | Why |
|---|---|---|
| `BU\` (`qxwGlobT\`, `tmsEUprodT\`, old `NATDEF.*`) | `9_Archive\2_Model\BU\` | back-ups of solves of the first submission |
| `SaveSims\` | `9_Archive\2_Model\SaveSims\` | a saved simulation of 2025 |
| `in\BU\`, `in\sets - Copy.har` | `9_Archive\2_Model\in\` | back-up of the data base (licensed — never push) and an old sets file |
| `5. Tariff_SIM.zip`, `NATDEF_BU.cmf`, `gpx10.log` … `gpx15.log`, `gpxx1.log` … `gpxx9.log` | `9_Archive\2_Model\` | an old tariff simulation and compile logs |

## 4. `3_Output\` — keep the baseline, the calibration and the 49 V32 runs

| Move | To | Why |
|---|---|---|
| `0. Old\` (`Baseline_EUDR`, `Baseline_EUDR_bau5`, `Baseline_EUDR_bau5_eta0.66`, `Idealist`, `Realistic_wi_china`, `Realistic_wo_China`) | `9_Archive\3_Output\0. Old\` | the one-solve baselines and the three scenarios of the first submission |
| every folder of `Friction\` whose name does **not** end in `_v32` (about 150 folders; the families `_outcover_` = V22–V27, `_eudrkeep` = V28–V29, `_pinall` = V30, `_pinall_wnet` = V31) | `9_Archive\3_Output\Friction\` | the runs of the earlier generations |

Explorer recipe for `Friction\`: open `3_Output\Friction`, type `_v32` in the search box (49 folders are found — the list is at the end), select all, cut, paste them into a new folder `3_Output\Friction_v32`; then move `Friction\` to `9_Archive\3_Output\Friction\` and rename `Friction_v32` to `Friction`. The runner reuses a run when `4_DB\…_<tag>_v32.csv` exists, so it is unaffected by the move.

## 5. `4_DB\` — keep the V32 result tables

Keep: the 98 `Database_GTAPAEZ_all_results_2024[_agg]_forest_*_v32.csv`, the 5 `Stability_Friction_forest_*_v32.txt`, the 3 `V32_runs_*.txt`.

| Move | To | Why |
|---|---|---|
| the 386 result csv without `_v32` and the 13 `Stability_*.txt` without `_v32` | `9_Archive\4_DB\` | results of the earlier generations (1 GB) |
| `Complement_runs_2026-09-27.txt`, `Fill_runs_2026-09-24.txt`, `Fill_runs_2026-09-27.txt`, `Minimum_search_2026-09-21.txt`, `Sensitivity_2026-09-21.txt`, `Sensitivity_2026-09-24.txt`, `Sensitivity_2026-09-27.txt`, `V30_runs_2026-09-30.txt`, `V31_runs_2026-10-01.txt` | `9_Archive\4_DB\` | run summaries of the earlier generations |
| `DB_GTAPAEZ_all.yxmd`, `DB_GTAPAEZ_all.bak`, `Database_GTAPAEZ_all_results_2024_agg_pivot.yxmd`, `…pivot.bak`, `DB_Main_Figure_areas_Global_Results.xlsx`, `List_GTAP_countries.xlsx`, `List_producers.xlsx` | `9_Archive\4_DB\` | Alteryx workflows and tables of the first submission's figures; nothing in V32 reads them |

Explorer recipe: in `4_DB`, search `_v32` (103 files), select all, cut, paste into `4_DB_v32`; add the three `V32_runs_*.txt`; move `4_DB` to `9_Archive\4_DB`, rename `4_DB_v32` to `4_DB`.

## 6. `0_External_data\` — keep what the scripts read

Keep: `DeDuCE_rework\` (all of it), `GDP_values.xlsx`, `GDP_values_original_formulas.xlsx`, `qo_values.xlsx`, `qxw_values.xlsx`, `Original_EV.xlsx` (the last three are legacy inputs that `CGE_Game_Theory_GTAPAEZ_all_V32.R` still loads at start-up — moving them would stop the script), `Mapping_GTAPAEZ_ISO_coordinates.csv` and `.xlsx`.

| Move | To | Why |
|---|---|---|
| `0. Old\` | `9_Archive\0_External_data\0. Old\` | superseded threshold and parameter sheets |
| `Diplomatic\`, `Idealist\`, `Realistic_wi_china\`, `Realistic_wo_china\` (the `Thresholds_GTAPAEZ_Game_theory.xlsx` sheets and their `0. Old`) | `9_Archive\0_External_data\` | the region-specific thresholds of the first submission; V32 uses a uniform switching cost (`fr0.001trade`) and never opens them |
| `qes_values.xlsx`, `tms_f_initial_shocks.xlsx` | `9_Archive\0_External_data\` | the supply-shock and reverse-engineered tariff mechanisms of the first submission (`qes_values.xlsx` is opened only when a run uses the `qes` mechanism, which no V32 run does) |
| `API_NY.GDP.MKTP.CD_DS2_en_excel_v2_5607200.xls`, `API_SP.POP.TOTL_DS2_en_excel_v2_4488557.xls`, `HDI_data.xlsx`, `HDR21-22_Composite_indices_complete_time_series.csv`, `HDR_Indicators_Aggregation_02072023.yxmd` and `.bak`, `HILDA_Average_Decade_Deforestation.xlsx`, `Mapping_GTAP.xlsx`, `gist.githubusercontent.com_…countries_codes_and_coordinates.csv`, `Original_forest.xlsx`, `Original_forest_treated.xlsx`, `Original_forest_values.yxmd` and `.bak` | `9_Archive\0_External_data\` | sources of the first submission (HDI, population, HILDA+ deforestation, the old forest baseline) |

## 7. `5_Visualisation\` — archive whole

`5_Visualisation\` (Tableau workbooks and Alteryx flows that drew the figures of the first submission; the figures of the revision are drawn by `5_Figures\`) → `9_Archive\5_Visualisation\`.

## After the moves

The repository has: `README.md`, `.gitignore`, `0_External_data\`, `1_Code\` (5 scripts), `2_Model\`, `3_Output\` (`Baseline_2stage_bau5_eta0.66\`, `Calibrate_BAU_productivity\`, `Friction\` with 49 folders, `overnight_log.txt`), `4_DB\` (106 files), `5_Figures\`, `9_Archive\`. Check with `git status` that nothing tracked disappeared except what `.gitignore` now excludes (`9_Archive/`), and commit.

## Appendix — the 49 run folders of `3_Output\Friction\` that stay

- `forest_pha0_tau0.5charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.0005trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau0.75charged_eudr0_bau5_eta0.66_seedEUChina_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau0.75charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.0005trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau0.75charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau0.87charged_eudr0_bau5_eta0.66_seedEUChina_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau0_eudr0_bau5_eta0.66_seedEUMercosur5_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau0_eudr0_bau5_eta0.66_seedEUMercosurChina_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau0_eudr0_bau5_eta0.66_seedEUMercosur_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau0_eudr0_bau5_eta0.66_seedSminmercosur0_fixed_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau1.12charged_eudr0_bau5_eta0.66_seedEUChina_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau1.12charged_eudr0_bau5_eta0.66_seedSmineuchinaclub112_fixed_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau1.25charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau1.5charged_eudr0_bau5_eta0.66_seedEU_lockbrasil_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau1.5charged_eudr0_bau5_eta0.66_seedEU_lockindonesia_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau1.5charged_eudr0_bau5_eta0.66_seedEU_lockus-china_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau1.5charged_eudr0_bau5_eta0.66_seedEU_lockus_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau1.5charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau1.5charged_eudr0_bau5_eta0.66_seedSminclubY_fixed_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau1.5charged_eudr0_bau5_eta0.66_seedSminclubYjapan_fixed_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau1charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.0005trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau1charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau2.5charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau2.5charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.002trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau2charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.002trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha0_tau5charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha1000_tau0.62charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha1000_tau0.87charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha1000_tau0_eudr0_bau5_eta0.66_seedEUChina_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha1000_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.0005trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha1000_tau1.12charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha2000_tau0.5charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha2000_tau0.75charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha2000_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha2500_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha3000_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha3500_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha4000_tau0_eudr0_bau5_eta0.66_seedEU_lockbrasil_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha4000_tau0_eudr0_bau5_eta0.66_seedEU_lockindonesia_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha4000_tau0_eudr0_bau5_eta0.66_seedEU_lockus-china_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha4000_tau0_eudr0_bau5_eta0.66_seedEU_lockus_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha4000_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha4000_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.002trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha4000_tau0_eudr0_bau5_eta0.66_seedSmincoalitionX_fixed_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha500_tau0_eudr0_bau5_eta0.66_seedEUChina_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha500_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.0005trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha6000_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha6000_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.002trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha8000_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.002trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`
- `forest_pha9000_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.002trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`


## Status on the evening of 7 October (after the moves)

Done, checked from the session: root `0. Old` → `9_Archive\0. Old General` (1,767 entries, identical); `2_Model.zip` and the repo's `Revision 1` copy → `9_Archive\`; `1_Code` down to the five scripts (+ `.Rhistory`, ignored by git), the 35 old scripts and runners → `9_Archive\0. Old Code`; `3_Output\0. Old` and the 158 pre-V32 run folders → `9_Archive\0. Old Output` (with `Calibrate_BAU_productivity\`, whose result the baseline reads from `0_External_data\DeDuCE_rework\bau_afeall_eta0.66.txt`, so nothing breaks); `3_Output\Friction` holds the 51 `_v32` runs and nothing else; 399 of the 415 old `4_DB` files → `9_Archive\0. Old DB`; `5_Visualisation` → `9_Archive\0. Old Visualisation`; `2_Model\BU`, `SaveSims`, `5. Tariff_SIM.zip`, `NATDEF_BU.cmf` and the `gpx*.log` → `9_Archive\0. Old model`; the old threshold folders → `0_External_data\0. Old` (inside the folder, ignored by git — fine). `5_Figures` rebuilt as one `<Figure>_script\` / `<Figure>_Output\` pair per figure (its `README.md`).

To fix: **`2_Model\in\` was moved whole into `9_Archive\0. Old model\in\`** — it holds the live data base (`basedata.har`, `default.prm`, `sets.har`, `SUMMARY.har`, `DECOMP.har`, `GTAPVOL.har`, `gtp32_45.agg`), which the CMF (`file gtapDATA = in\basedata.har` …) and the R scripts read on every solve. Move it back to `2_Model\in`, then move only `in\BU\` and `in\sets - Copy.har` to the archive.

Still to move (small): in `4_DB`, the 12 `Stability_*.txt` without `_v32`, the two `.bak` files and the two `…pha500_…fr0.0005…_pinall_wnet.csv` (V31) → `9_Archive\0. Old DB`; the three files left in `5_Visualisation` (`.bak`, `.twbr`) and the folder → the archive; in `5_Figures`, the flat files of the 7 October layout (every `.py`, `.json`, `.csv`, `.txt`, `.R`, `.geojson` directly in `5_Figures\` except `make_all.py` and `README.md`, plus `ne110\` and `si\`) and the whole `Figures_v2\` folder moved in from OneDrive (old flat figures of 28–30 Sept, `scripts\`, `scripts_v32\`, `V31\`, `V32\`) → `9_Archive\0. Old Visualisation\5_Figures_flat_2026-10-07\`; the root Word lock file `~$e scenario … .docx`; optionally the first-submission sources left in `0_External_data` (the HDI, population and HILDA+ files, `Original_forest*`, `qes_values.xlsx`, `tms_f_initial_shocks.xlsx`, `Mapping_GTAP.xlsx`, the gist csv, the Alteryx `.yxmd`/`.bak`).
