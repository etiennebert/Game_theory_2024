# Miranda calibration (19 October 2026, updated 20 October)

Gives the GTAP-AEZ v12 model the Miranda et al. (2024) land-supply elasticities, which the first revision reported but which no v12 run has used (the v12 parameter file has no ETR1 header, so the TAB's default of -0.25 applied everywhere).

Files
- `default_2023_v10_miranda.prm` : the 2023 parameter file (v10 data base, 37 regions). Header ETL1 holds the Miranda values as CET elasticities (ETRAEL1 = -epsilon) for 12 producer regions, -0.2 elsewhere. Source of the targets; not usable by the v12 model as it is.
- `Calibrate_ETR1_Miranda.R` : builds the v12 header ETR1 from it (mapping: AEZ New n -> AEZ n; regions by name; AngDRC -> Angola and DRC; SSA -> WAfr, CAfr, EAfr, SAfr; MENA -> MENA and NAfr) and calibrates the Miranda cells so that the model's response of agricultural land to a 1 % producer-price rise equals Miranda's epsilon. Agricultural land is measured on the land services the CET allocates to the 11 agricultural activities of the cell (rent-weighted `qes`), the quantity ETRAEL1 governs; the cover response (cropland + pasture hectares, which the cover block derives through harvested area and `areaadjust` and which went negative in 12 cells in the run of 19 October) is kept in the csv for information only. One solve per target region and pass (`shock_mode = "separate"`, 11 regions, 1-2 min each in fast mode), up to 4 passes after the measuring pass 0; each pass multiplies ETRAEL1 by at most 4 either way.

Settings added on 20 October (top of the script)
- `max_price_move = 3` : the degenerate-sector rule. A shocked activity whose supply price moves by more than 3 % under the 1 % subsidy is a near-empty sector feeding on its own output (found on 20 October in the DRC: paddy rice -33 %, sugar crops -8 %, which pulled the region's output-weighted producer price to -2.4 % and made every DRC cell read a negative elasticity). The activity is dropped from the region's shock, the region is solved again, and the exclusion holds for the later passes; the log names them and `pass_<k>/price_diag_pass<k>.csv` gives, for every agricultural activity of every region solved, its output share, whether it was shocked or excluded, and its supply price, producer price, output and export changes.
- `warm_start` : path of a previous `ETR1_calibrated.csv`; the passes then start from its `etr1_final` instead of the 2023 values.
- `run_label` : suffix of the output folder (a diagnostic run does not overwrite the main results); `only_regions` : solve and calibrate a subset of the target regions; `keep_sl4 = TRUE` : keep every solution file as `pass_<k>/NATDEF_<region>.sl4`.

Run of 19 October (fast mode, 5 passes, 55 solves, 70 min): 10 cells calibrated within 7 % (Brazil AEZ5 -0.20, Brazil AEZ6 -0.07, Peru AEZ4-6, Ghana AEZ4-6, Angola AEZ5, Paraguay AEZ6), 6 cells at 61-76 % of the target and still converging (Bolivia AEZ4-5, Colombia AEZ6, Indonesia AEZ6, Malaysia AEZ6; Bolivia AEZ6 non-monotonic), 8 cells pinned at -5 with forestry at 0.2-8 % of the cell's land rent (unreachable: the CET moves land in proportion to rent), 4 cells without a usable response (Colombia AEZ4 and Peru AEZ2, no forest to speak of; DRC AEZ5-6, the degenerate-sector problem above). The file `default_miranda.prm` of that run carries -5 in the bound cells and -0.2 in the non-Miranda cells: do not run the baseline with it as it is.

Before running: `2_Model/BU` (NATDEF.cmf, NATDEF.har of RunGTAP) must be in place; it is in `9_Archive/0. Old model/BU/` after the archive clean-up. Run the script from RStudio like the other scripts.

Outputs, in `3_Output/Miranda_calibration/`
- `pass_<k>/` : the parameter file tried, the CMF and solver log of every solve
- `ETR1_calibrated.csv` : every AEZ x region cell: 2023 value, source region, target, forest and agricultural covers, agricultural land rent, forestry rent share, the model's land-services elasticity (`eps_model`), cover elasticity (`eps_cover`, information), producer-price change and ETRAEL1 at every pass, final value, bound flag
- `default_miranda.prm` : `in/default.prm` plus the calibrated ETR1 header, ready for the baseline and the game
- `calibration_log.txt`

Pass 0 answers the question of 19 October on its own: it measures the model's price elasticity of agricultural land with the 2023 values as they are. If it is already within tolerance of Miranda's, the 2023 convention was right and nothing moves.

To use the result: copy `default_miranda.prm` over `2_Model/in/default.prm` (keep the original as `default_v7defaults.prm`) or point `file gtapPARM =` in `BU/NATDEF.cmf` to it; then `Calibrate_BAU_productivity.R`, `Baseline_2stage.R`, `Run_V32_all.R` under a new run tag.
