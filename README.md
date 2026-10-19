# Forest Club — model, runs and figures

Code and results behind *The Forest Club* (Nature, revision 1, October 2026): a trade-based club in which members hold their forest at its 2019 extent, are deemed compliant with the EU Deforestation Regulation, and apply a border charge to the land-based commodities they import from non-members. The membership game is run on the GTAP-AEZ v7 computable general equilibrium model (GEMPACK), 42 regions × 35 sectors × 18 agro-ecological zones, with the GTAP Data Base aggregation of `2_Model\in\gtp32_45.agg`.

*Status, 7 October 2026 (evening): the folder has been tidied; everything the paper does not use is in `9_Archive\` (moved, not deleted; `REORGANISATION_2026-10-07.md` lists what went where and the few items still to move).*

## The pipeline in four steps

| Step | Script | Reads | Writes |
|---|---|---|---|
| 1. Border charge and baseline inputs | `0_External_data\DeDuCE_rework\zenodo_v2.1\build_h_table.py` (DeDuCE v2.1 → embodied-deforestation intensities and ad valorem equivalents); `1_Code\Calibrate_BAU_productivity.R` (productivity of the land cleared on the business-as-usual path) | DeDuCE v2.1 (Zenodo 10.5281/zenodo.10633818), `2_Model\in\basedata.har`, `sets.har` | `DeDuCE_rework\h_table_DeDuCE.xlsx`, `tms_f_initial_shocks_DeDuCE.xlsx`, `tms_f_shocks_bilateral_AVE_*.csv`; `DeDuCE_rework\bau_afeall_eta0.66.txt` (the calibration solves themselves are archived in `9_Archive\0. Old Output\Calibrate_BAU_productivity\`) |
| 2. Two-stage baseline | `1_Code\Baseline_2stage.R` | `DeDuCE_rework\bau_deforestation.xlsx` (business-as-usual clearing by cell), `eudr_cut_shares.xlsx` (the EUDR as an import cut by origin), `bau_afeall_eta0.66.txt` | `3_Output\Baseline_2stage_bau5_eta0.66\A_bau\` (Stage A: the clearing), `B_eudr\` (Stage B: the EU alone under the EUDR — the baseline of every result), `EUDR_effect_by_region.txt`, `EUDR_effect_by_cell.txt` |
| 3. The membership game | `1_Code\Run_V32_all.R` (the programme of runs, one block per question of the paper) driving `1_Code\CGE_Game_Theory_GTAPAEZ_all_V32.R` (one run: rounds of solves, the decision rule, the one-deviation tests) | step 2, `DeDuCE_rework\tms_f_initial_shocks_DeDuCE.xlsx` and `tms_f_shocks_bilateral_<sheet>.csv`, `0_External_data\GDP_values.xlsx` (the 0.1 %-of-GDP safeguard) | `3_Output\Friction\forest_<run tag>_v32\Scenario_D\` (every solve of the run), `4_DB\Database_GTAPAEZ_all_results_2024_agg_forest_<run tag>_v32.csv` (one row per region and round), `4_DB\Stability_Friction_forest_<run tag>_v32.txt` (one-deviation tests), `4_DB\V32_runs_<date>.txt` (one line per run), `3_Output\overnight_log.txt` |
| 4. Figures, tables and numbers of the text | `5_Figures\make_all.py`: `common\extract_*.py` extract the runs into `5_Figures\data\`, then one script per figure in `Fig_2_script\` … `ExtData_Fig_2_script\`, `Tables_script\`, `SI_script\` (`si_v32_extract.R`, `si_figures.py`) | step 3, `2_Model\in\basedata.har` (SI and Fig. 5 extraction) | `5_Figures\<Figure>_Output\`: png, pdf and source-data csv of Figs 2–5, Extended Data Figs 1–2, Tables 1–3, SI Figs S7, S9–S11 and Tables S9–S12 (`5_Figures\README.md`) |

Launch of step 3: open `1_Code\Run_V32_all.R` in RStudio and run it (Ctrl+Alt+R); the script finds the model folder from its own location. A run whose csv already exists is reused, so the programme can be relaunched after an interruption and continues where it stopped. Blocks are listed in the header of the runner, in the order they were run (core, brackets, complement, penalty_up, stability, brackets2, plane, sensitivity, alliance, brackets3, brackets4, japan, brackets5, coalition_outsiders); each takes 1–6 hours at 5–10 minutes per solve.

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
| `_v32` | the generation of runs the paper reports (earlier generations are in the archive) |

## Folder map

| Folder | What it holds | In git? |
|---|---|---|
| `0_External_data\DeDuCE_rework\` | the border-charge tables and their construction (`README.md` inside), the EUDR cut shares, the business-as-usual clearing, the productivity calibration; `zenodo_v2.1\` the DeDuCE source file, the commodity mapping and `build_h_table.py` | yes, except the two GTAP-derived sheets noted in `DeDuCE_rework\README.md` before any public release |
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
