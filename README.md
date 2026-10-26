# Forest Club — model, runs and figures

Code and results behind *The Forest Club* (Nature, revision 1, October 2026): a trade-based club in which members hold their forest at its 2019 extent, are deemed compliant with the EU Deforestation Regulation, and apply a border charge to the land-based commodities they import from non-members. The membership game is run on the GTAP-AEZ v7 computable general equilibrium model (GEMPACK), 42 regions × 35 sectors × 18 agro-ecological zones, with the GTAP Data Base aggregation of `2_Model\in\gtp32_45.agg`.

*Status, 7 October 2026 (evening): the folder has been tidied; everything the paper does not use is in `9_Archive\` (moved, not deleted; `REORGANISATION_2026-10-07.md` lists what went where and the few items still to move).*

## The pipeline in four steps

| Step | Script | Reads | Writes |
|---|---|---|---|
| 1. Border charge and baseline inputs | `0_External_data\DeDuCE_rework\zenodo_v2.1\build_deduce_tables.py` (DeDuCE v2.1 → embodied-deforestation intensities, ad valorem equivalents, and the business-as-usual clearing by region × AEZ, allocated with the HILDA+ shares); `1_Code\Calibrate_BAU_productivity.R` (productivity of the land cleared on the business-as-usual path; `generation` at the top) | DeDuCE v2.1 (Zenodo 10.5281/zenodo.10633818), `DeDuCE_rework\HILDA_v2.1_transitions_country_AEZ.csv` (HILDA+ v2.1 conversions by country × AEZ × year, from `hilda_country_aez_tables.py` on the HILDA+ netCDF files), `2_Model\in\basedata.har`, `sets.har`, `default.prm` (the Miranda-calibrated one, from `1_Code\Miranda_calibration\`) | `DeDuCE_rework\h_table_DeDuCE.xlsx`, `tms_f_initial_shocks_DeDuCE.xlsx`, `tms_f_shocks_bilateral_AVE_*.csv`, `bau_deforestation.xlsx`; `DeDuCE_rework\bau_afeall_eta0.66_<generation>.txt` |
| 2. Two-stage baseline | `1_Code\Baseline_2stage.R` (`generation` at the top) | `DeDuCE_rework\bau_deforestation.xlsx` (business-as-usual clearing by cell), `eudr_cut_shares.xlsx` (the EUDR as an import cut by origin), `bau_afeall_eta0.66_<generation>.txt` | `3_Output\Baseline_2stage_bau5_eta0.66_<generation>\A_bau\` (Stage A: the clearing), `B_eudr\` (Stage B: the EU alone under the EUDR — the baseline of every result), `EUDR_effect_by_region.txt`, `EUDR_effect_by_cell.txt` |
| 3. The membership game | `1_Code\Run_V32_all.R` (the programme of runs, one block per question of the paper; `generation`, `Y`, `X` at the top) driving `1_Code\CGE_Game_Theory_GTAPAEZ_all_V32.R` (one run: rounds of solves, the decision rule, the one-deviation tests) | step 2, `DeDuCE_rework\tms_f_initial_shocks_DeDuCE.xlsx` and `tms_f_shocks_bilateral_<sheet>.csv`, `0_External_data\GDP_values.xlsx` (the 0.1 %-of-GDP safeguard) | `3_Output\Friction\forest_<run tag>_<generation>\Scenario_D\` (every solve of the run), `4_DB\Database_GTAPAEZ_all_results_2024_agg_forest_<run tag>_<generation>.csv` (one row per region and round), `4_DB\Stability_Friction_forest_<run tag>_<generation>.txt` (one-deviation tests), `4_DB\<GENERATION>_runs_<date>.txt` (one line per run), `3_Output\overnight_log.txt` |
| 4. Figures, tables and numbers of the text | `5_Figures\make_all.py`: `common\extract_*.py` extract the runs into `5_Figures\data\`, then one script per figure in `Fig_2_script\` … `ExtData_Fig_2_script\`, `Tables_script\`, `SI_script\` (`si_extract.R`, `si_figures.py`) | step 3, `2_Model\in\basedata.har` (SI and Fig. 5 extraction) | `5_Figures\<Figure>_Output\`: png, pdf and source-data csv of Figs 2–5, Extended Data Figs 1–2, Tables 1–3, SI Figs S7, S9–S11 and Tables S9–S12 (`5_Figures\README.md`) |

A new generation of runs (V34 = `"v34"`, October 2026) chains through file names: (1) `python build_deduce_tables.py` in `zenodo_v2.1\` rewrites the DeDuCE tables and `bau_deforestation.xlsx`; (2) `Calibrate_BAU_productivity.R` with `generation <- "v34"` writes `bau_afeall_eta0.66_v34.txt`; (3) `Baseline_2stage.R` with `generation <- "v34"` solves stages A and B into `Baseline_2stage_bau5_eta0.66_v34\`; (4) `Run_V32_all.R` with `generation <- "v34"` runs the programme, tags `_v34`; (5) `set FOREST_CLUB_VERSION=_wnet_v34` then `python 5_Figures\make_all.py`. The Miranda calibration of the land-supply elasticities (`1_Code\Miranda_calibration\`, which installs `2_Model\in\default.prm`) does not depend on the clearing and is not rerun. Each script checks that its input exists and stops with the name of the script to run first.

Launch of step 3: open `1_Code\Run_V32_all.R` in RStudio and run it (Ctrl+Alt+R); the script finds the model folder from its own location. A run whose csv already exists is reused, so the programme can be relaunched after an interruption and continues where it stopped. The blocks are listed in the header of the runner: the grid first (grid_core, grid_penalty, grid_surcharge, grid_floor, grid_floor_penalty, grid_seeds, grid_combined), then what hangs on the headline (lockouts, stability, japan, brackets). With `Y <- "auto"` and `X <- "auto"` the headline penalty and surcharges are read from the grid results when the first of those blocks starts (the lowest grid value at which the club / the coalition forms; the surcharge at which Brazil joins on its own first-round loss), written to `4_DB\<GENERATION>_runs_<date>.txt` as `== headline: Y = … | X = …`, which the figure pipeline reads; each block takes 1–6 hours at 5–10 minutes per solve, the whole programme about 45 hours.

## Reading a run tag

`forest_pha3000_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32`

| piece | meaning |
|---|---|
| `pha3000` / `tau1.5charged` | footprint surcharge in USD per hectare deforested / flat penalty in % on the 17 charged commodities (both can be present: both instruments) |
| `seedEU`, `seedEUChina`, `seedEUMercosur`, `seedEUMercosur5`, `seedEUMercosurChina` | the starting coalition |
| `seedSmin…_fixed` | a one-deviation stability test of a converged coalition (dynamics off; `SminclubYjapan`, `SmincoalitionXouts`: supplements testing the outsiders the main test did not cover) |
| `lockbrasil`, `lockus`, `lockus-china`, `lockindonesia` | a region treated as an outsider at every decision |
| `fr0.001trade` | switching cost = 0.1 % of the region's trade in the charged commodities (`0.0005`, `0.002`: the sensitivity runs) |
| `bau5_eta0.66` | business-as-usual clearing over five years, productivity of the cleared land 0.66 |
| `sgb`, `jrexp`, `frombau`, `eudrkeep`, `pinall`, `wnet` | safeguard on the baseline; experience decision rule; solves start from the Stage A data; the EUDR stays on non-members; members pinned at zero clearing in every zone; welfare net of the forest-land wedge term |
| `_v34`, `_v33`, `_v32` | the generation of runs: `_v34` (October 2026: the business-as-usual clearing allocated to the AEZs with the HILDA+ shares, the paper's), `_v33` (20–21 October: the Miranda-calibrated land-supply elasticities), `_v32` (7 October); earlier generations are in the archive |

## Folder map

| Folder | What it holds | In git? |
|---|---|---|
| `0_External_data\DeDuCE_rework\` | the border-charge tables and their construction (`README.md` inside), the EUDR cut shares, the business-as-usual clearing (`bau_deforestation.xlsx`, with the HILDA+ table `HILDA_v2.1_transitions_country_AEZ.csv` and the script that extracts it, `hilda_country_aez_tables.py`), the productivity calibration; `zenodo_v2.1\` the DeDuCE source file and `build_deduce_tables.py` (needs HARPY, GEMPACK's .har reader: a copy of the repository in a folder named `HARPY-master` next to the script works) | yes, except `eudr_cut_shares.xlsx`'s GTAP column `VCIF_EU_import_M` (to drop before any public release) |
| `0_External_data\GDP_values.xlsx`, `qo_values.xlsx`, `qxw_values.xlsx`, `Original_EV.xlsx` | GDP (safeguard) and three legacy inputs the game script still loads at start-up although the V32 runs do not use their content | yes |
| `1_Code\` | the four scripts of steps 1–3 (`Baseline_EUDR.R` is the one-solve baseline that preceded `Baseline_2stage.R`; it calibrated the productivity shocks and is kept for that reason) | yes |
| `2_Model\` | the GTAP-AEZ v7 model: TAB file, closure, shocks, executables, `in\` the data base and sets | TAB, CMF, sets: yes. **The GTAP Data Base (`basedata.har`, `baserate.har`, `baseview.har`, `gtapSAM.har`, `gsdf*.har`, `co2.har`, `metadata.har`, `default.prm/.pel`, `altertax.*`, `gdx.zip`, `gtapv6.zip`) is licensed and never leaves this machine**; GEMPACK solution and work files are regenerated by every solve and ignored |
| `3_Output\Baseline_2stage_bau5_eta0.66\` | the two baseline solves | text outputs yes; `.sl4`, `.upd`, logs no |
| `3_Output\Friction\forest_*_v32\` | the 51 runs of the paper (45 membership processes, 6 one-deviation tests), every solve | text outputs yes; solution files no (about 100 MB per run) |
| `4_DB\` | the result tables of the 51 runs (`*_agg_*_v32.csv`), their stability files, the run summaries `V32_runs_*.txt` | the `_agg_` csv yes; the ISO × AEZ csv (above GitHub's 100 MB limit) no |
| `5_Figures\` | the figure pipeline (step 4): `common\`, `data\`, one `<Figure>_script\` and `<Figure>_Output\` pair per figure, `SI_script\`, `SI_Output\`, `SI_docx_tools\` | yes |
| `9_Archive\` | everything that preceded V32 (model copies, old runs, old scripts, old visualisations), kept but not used — `9_Archive\README.md` | no |

## Requirements

GEMPACK with RunGTAP 3.75 (the folder name `runGTAP375`) for the model; R ≥ 4.2 with `HARr`, `readxl`, `writexl`, `xlsx`, `dplyr`, `tidyr`, `rstudioapi`, `devtools` for steps 1–3 and the SI extraction; Python ≥ 3.10 with `numpy`, `pandas`, `matplotlib`, `geopandas`, `rasterio` (the Brazil zone map only) for step 4. Step 3 needs the GTAP Data Base in `2_Model\in\`; step 4 runs from the csv files of `4_DB\` alone (`python make_all.py --figures` redraws from the json files without the model folder).

## Where the manuscript is

The manuscript and its Supplementary Information live outside this repository, in `Deforestation_Nature\Nature\Revision 1\` (OneDrive); the figures they use are the ones in `5_Figures\<Figure>_Output\`.
