# 5_Figures — every figure, table and number of the Results, one folder per figure

The pipeline reads the runs of one generation (the paper's: tag suffix `_wnet_v33`, the Miranda-calibrated elasticities of 20 October 2026; `_wnet_v32` is the previous generation, selected with `FOREST_CLUB_VERSION=_wnet_v32`) from `4_DB\` and `3_Output\` of the model folder (the parent of this folder), extracts them once into `data\`, and draws each figure from there. Each figure has a `<Figure>_script\` folder holding its one script and a `<Figure>_Output\` folder holding its png, pdf and source-data csv; the script finds its output folder from its own location, so a figure is redrawn with `python Fig_3_script\fig3_plane.py` and lands in `Fig_3_Output\`. Fig. 1 of the paper is the schematic and is not drawn here.

## Layout

| Folder | What it holds |
|---|---|
| `make_all.py` | runs everything in order (below) |
| `common\` | the shared modules (`paths.py` locations and generation, `figstyle.py` house style and map drawers, `mapping.py` Natural Earth → model regions, `v30.py` the readers of the run files) and the extraction scripts (`extract_all.py`, `extract_plane.py`, `stats.py`, `extract_brazil_aez.R`), plus the shared data they need (`ne110\` Natural Earth countries, `brazil_aez.geojson` and the `build_brazil_aez_map.py` that made it, `DB_GTAPAEZ_ISO-Code_2024.csv`, `switching_costs_0.1pct.txt`) |
| `data\` | the extracted data of the generation, suffixed with its label: `all_data_V32.json` (every run, the configurations the text quotes keyed by role, thresholds, stability tests, GDP, switching costs, the two-stage baseline), `stats_V32.json`, `plane_runs_V32.json`, `top_deforesters_V32.json`, `counterfactuals_V32.json`, `brazil_aez_V32.csv`, `brazil_runs_V32.txt` |
| `Fig_2_script\` → `Fig_2_Output\` | `fig2_forest.py`: maps of forest kept (a), the cascade (b), forest kept by region (c), leakage in hectares (d) |
| `Fig_3_script\` → `Fig_3_Output\` | `fig3_plane.py`: the instrument plane with Brazil's fitted break-even and the beef-tariff axis (a–c), the eight largest deforesters (d), the lock-outs (e) |
| `Fig_4_script\` → `Fig_4_Output\` | `fig4_welfare.py`: welfare maps (a), region × starting point grid (b), one-deviation stability with every profitable deviation labelled (c) |
| `Fig_5_script\` → `Fig_5_Output\` | `fig5_brazil_aez.py`: Brazil's land use by agro-ecological zone at the club equilibrium (`FOREST_CLUB_FIG5=surcharge` draws the coalition; both are in the source data) |
| `ExtData_Fig_1_script\` → `ExtData_Fig_1_Output\` | `extdata_fig1_thresholds.py`: Brazil's first-round loss against each instrument with the switching costs as rules, the bracket runs at Brazil's actual loss (a), the club just below and just above each threshold (b, c) |
| `ExtData_Fig_2_script\` → `ExtData_Fig_2_Output\` | `extdata_fig2_deforesters.py`: the largest deforesters' first-round loss at the headline charges (a) and joining round in every EU-alone run (b) |
| `Tables_script\` → `Tables_Output\` | `tables.py`: `Tables_V32.md` (ready to paste) and `Table1/2/3_V32.csv` — Table 1 every starting point at its lowest working charge and the headline charges, Table 2 the EU-alone thresholds by switching cost, Table 3 the lock-outs |
| `SI_script\` → `SI_Output\` | `si_extract.R` (R, HARr: baseline forest change by region and zone, welfare decomposition, sectoral supply responses, Brazil's commodities, from `NATDEF_A/B.sl4`, the headline solutions and `basedata.har`) writes `SI_script\data_<label>\*.csv`; `si_figures.py` draws Figs S7, S9, S10, S11 and writes Tables S9–S12 as markdown |
| `SI_docx_tools\` | the tooling that wrote the tracked changes into the SI Word file, one `make_ops_*.py` per pass (`make_ops_v32.py` 4 Oct, `make_ops_v32b.py` 7 Oct) feeding `redline.py` (text), `table_edit.py` (rows and cells of an existing table), `insert_images.py` (pictures) and `fix_rpr.py` (formatting), after `accept_prior.py` / `accept_prior2.py` have accepted the earlier passes inside the paragraphs being rewritten; `reject_date.py` checks that rejecting one pass restores the previous text. Not part of the figure pipeline |

## Running it

```
cd 5_Figures
python make_all.py                 # everything: data\ then every <Figure>_Output\ (needs the model folder for the extraction steps)
python make_all.py --figures       # redraw the figures and tables from data\ alone, without the model folder
python make_all.py --no-r          # skip the two R steps (Fig. 5 and the SI figures use the last csv files)
python make_all.py --version _wnet # another generation (V31; "" for V30): its data files get their own label
```

`make_all.py` runs, in order: `common\extract_all.py` → `extract_plane.py` → `stats.py` → `Tables_script\tables.py` → `common\extract_brazil_aez.R` → the six figure scripts → `SI_script\si_extract.R` → `SI_script\si_figures.py`, and stops at the first failure. The R steps need R with `HARr` and run with `Rscript` when it is on the PATH; otherwise the command to run by hand is printed. Each script also runs on its own from its folder. The model folder is the parent of `5_Figures` (or the environment variable `FOREST_CLUB_REPO`); `FOREST_CLUB_VERSION` selects the generation.

Nothing is hard-coded to a run: the headline charges come from `HEADLINE` at the top of `extract_all.py` (`Y` = 1.5 % and `X` = 4,000 USD/ha of the runner), and the thresholds, the columns of the grids, the plane's extent, the annotated regions, the member counts, the bracket markers and the stability rows all come from the runs on the disk. A run that is not there yet is reported and left out; a run that reached the round cap is neither failing nor working (grey marker and † in Extended Data Fig. 1). A stability file is matched to its run on the seed named in the file, the charge and the final coalition, and a supplementary test of the same coalition (`SminclubYjapan`, `SmincoalitionXouts`) is merged into the run's table. Every figure carries its generation label in a footnote and every source-data file the run tags.

## What the data are measured against

Round 0 of every run is Stage B of the two-stage baseline (the EUDR world): forest kept and welfare are the club world minus that world, over five years. Welfare is the decision measure (GTAP's EV net of the forest-land wedge term, `Welfare_decomp_round_<n>.txt`); the gross EV is kept alongside (`ev_gross`, `world_gross` in `all_data`, and in the source data of Figs 3 and 4). Leakage is in hectares: non-members' forest is endogenous. The switching costs in `run_stats` are scaled by the run's share of trade (`fr / 0.001`); the table on the disk is the one at 0.1 %. The reference frames are spelled out in the docstring of `common\v30.py`.

## Requirements

Python 3.10+ with `matplotlib`, `numpy`, `pandas`, `openpyxl`, `geopandas`, `shapely`, `pyproj`, `Pillow` (`rasterio` only to rebuild `brazil_aez.geojson`); R with `HARr` for the two R steps. The figures use Arial where it is installed (Windows, Mac) and otherwise Liberation Sans or Arimo, its metric-compatible clones (`common\figstyle.py`, `_font()`); the layout is the same with either.

## History

Built 29 September – 7 October 2026. The flat layout of 2–7 October (`scripts_v32\`, figures in `Figures_v2\<label>\`) and the earlier `Figures_v2\scripts\` of 29–30 September, with the V31 and V30 figures and data files, are in `9_Archive\`. The runs themselves: `1_Code\CGE_Game_Theory_GTAPAEZ_all_V32.R` driven by `1_Code\Run_V32_all.R`; result csv suffix of the paper's runs `_eudr0_bau5_eta0.66_seed<EU|EUChina|EUMercosur|EUMercosurChina|EUMercosur5>[_lock<region>]_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32` (`fr0.0005` and `fr0.002` for the switching-cost sensitivity).

V33 (21–22 October 2026): the same pipeline on the `_wnet_v33` runs (12 calibrated land-supply cells, −0.25 elsewhere); headline club 1.25 % (the lowest working penalty), coalition 4,000 USD/ha, lowest working surcharge 2,500 USD/ha (`EU_sur_min`, with its own lock-outs); `common\extract_all.py` reads the headline per version, `common\extract_brazil_aez.R` the suffixed baseline, `SI_script\si_v33_extract.R` writes `SI_script\data_v33\`. Outputs: `data\*_V33.*`, `Tables_Output\*_V33.*`, and the figure folders (the V32 figures are regenerated with `FOREST_CLUB_VERSION=_wnet_v32 python make_all.py`).

V34 (October 2026): the business-as-usual clearing of each region is allocated to its AEZs with the HILDA+ v2.1 clearing shares (`0_External_data\DeDuCE_rework\bau_deforestation.xlsx`, rebuilt by `build_deduce_tables.py`) instead of the forest-cover shares; runs tagged `_wnet_v34`, baseline `Baseline_2stage_bau5_eta0.66_v34`. The pipeline is generation-generic from here: `common\extract_all.py` reads the headline (`Y`, `X`) from the batch's results file `4_DB\<LABEL>_runs_<date>.txt` when the generation is not in its table, `common\extract_brazil_aez.R` and `SI_script\si_extract.R` (replacing `si_v32_extract.R` / `si_v33_extract.R`) take the label from `FOREST_CLUB_VERSION` and read the suffixed baseline, the SI csv go to `SI_script\data_<label>\`. `common\build_brazil_aez_map.py` (Fig. 5a) was corrected on 23 October: GAEZ thermal class 2 (tropics highland) belongs to the temperate zone, as in the FAO 18-class AEZ map and the model's GTAP-AEZ land cover; the earlier polygons put 20 Mha of southern Brazil in AEZ 6 instead of AEZ 12.
