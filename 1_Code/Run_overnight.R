## =====================================================================================
##  Run_overnight.R  -  chains full runs of CGE_Game_Theory_GTAPAEZ_all_V26.R
##
##  One row of `grid` = one complete game run (one seed, one price scenario, one tau, one approach),
##  followed by its stability check when stability = TRUE. Edit the grid, open this file in RStudio and run it (Ctrl+Alt+R).
##  Timing (accurate solves, 5-6 min each): a run = 3 to 10 solves = 20 min to 1 h; the stability check adds one solve per
##  region tested (41 with stability_scope = "all"), so keep stability = FALSE for a first night and switch it on later for
##  the coalitions worth testing, with stability_scope limited to the regions that matter.
##  Each run writes its own folder 3_Output/<approach>/forest_<run_tag>/Scenario_D/, its own 4_DB csv and
##  4_DB/Stability_<approach>_forest_<run_tag>.txt, so runs never overwrite each other. Progress and errors go
##  to 3_Output/overnight_log.txt; an error in one run does not stop the next.
##  Requirements: 1_Code/Calibrate_BAU_productivity.R then 1_Code/Baseline_EUDR.R have been run once with the same bau_horizon and bau_eta.
##
##  Columns:  seed          regions inside at iteration 1 (the EU is always added) | "auto" = the V13-V21 start
##            seed_name     label used in run_tag and file names
##            dynamics      "on" = join/leave rule from the seed until convergence | "off" = the seed is the coalition
##            stability     TRUE = one-deviation check of the final coalition (one solve per region tested)
##            bau_outsiders "cover" = non-members' forest follows the BAU path, as in the baseline (V23) | "tinc" = wedge shock, forest endogenous (V21; does not solve for large tinc*)
##            min_face      lowest acceptable accuracy "face" number (0-10) of a solve; below it the solve is redone with the accurate settings
##            stability_scope  outsiders tested for joining: "all" or e.g. "brasil,indonesia,china,us"
##            approach      Realistic_wi_china | Diplomatic | Realistic_wo_china | Idealist  (threshold sheet; also the output folder)
##            friction      "sheet" = thresholds of the approach | a number = both thresholds are friction x base (see Run_overnight_friction.R)
##            friction_base "trade" = the region's exports + imports of the 17 charged commodities, basedata.har (V25) | "gdp" = GDP_values.xlsx (V22)
##            friction_floor $M, lowest threshold under a numeric friction (default 2)
##            tmsf_sheet    AVE_pha400 | AVE_pha2000 | AVE_pha10000 | AVE_co2_50 | AVE_co2_100 | AVE_co2_190
##            tau           0 = coalition (footprint charge only) | > 0 = club (+ flat penalty, % on the tariff power)
##            tau_scope     "charged" = the 17 land-based sectors | "all" = every commodity (Nordhaus club)
##            eudr_in_loop  "none" = the scenario is the club/coalition alone, the EUDR only in the baseline | "outsiders" = EU keeps the EUDR cost on non-members on top of the charge
##            solve_mode    "accurate" = RunGTAP settings, 5-6 min per solve | "fast" = Gragg 2-4-6 in one subinterval, 0.7 min - NOT accurate enough for the BAU cover shocks (face 4)
##            max_pass      forest passes per iteration (bau_horizon = 0 only)
##            join_rule     "consecutive" (V13) | "baseline" (path-independent)
##            bau_horizon   years of business-as-usual clearing in the baseline
##            bau_eta       productivity of the cleared hectares (0.66 = the model's yield of new cropland; 0 = none, the V21-V23 baseline)
## =====================================================================================
library("rstudioapi")

script_folder <- dirname(getSourceEditorContext()$path)
game_script   <- file.path(script_folder, "CGE_Game_Theory_GTAPAEZ_all_V26.R")
log_file      <- file.path(dirname(script_folder), "3_Output", "overnight_log.txt")

seeds <- data.frame(
  seed_name = c("EU",   "EUMercosur",                             "EUMercosurChina"),
  seed      = c("eu27", "eu27,brasil,argentina,paraguay,uruguay", "eu27,brasil,argentina,paraguay,uruguay,china"),
  stringsAsFactors = FALSE)

configs <- data.frame(
  tmsf_sheet   = c("AVE_pha400", "AVE_pha2000", "AVE_pha400", "AVE_pha400", "AVE_pha400", "AVE_co2_100", "AVE_pha0"),
  tau          = c(0,            0,             2,            5,            7,            0,             5),
  tau_scope    = "charged",
  eudr_in_loop = "none",                 # the scenario is the club/coalition alone; the EUDR is only in the baseline (iteration 0). "outsiders" = the EUDR kept on non-members on top of the charge (runs of 19-20 Sept)
  approach     = "Realistic_wi_china",   # threshold sheet (and output folder)
  friction     = "sheet",                # the approach's thresholds; a number = uniform friction on the charged trade, see Run_overnight_friction.R
  dynamics     = "on",
  stability    = FALSE,                  # no one-deviation check tonight: the dynamics of every configuration only
  stability_scope = "all",
  bau_outsiders = "cover",               # V23: non-members' forest on the BAU path (the baseline's own lines)
  min_face     = 7,                      # V23: a solve scoring below this accuracy face is redone with the accurate settings
  solve_mode   = "accurate",             # 5-6 min per solve; "fast" (0.7 min) is not accurate enough for the cover shocks
  max_pass     = 2,
  join_rule    = "consecutive",          # "consecutive" (V13 rule) or "baseline" (path-independent)
  bau_horizon  = 5,                      # Baseline_EUDR.R must have been run with the same value
  bau_eta      = 0.66,                   # V24: productivity of the cleared hectares; Calibrate_BAU_productivity.R and Baseline_EUDR.R must have been run with the same value
  stringsAsFactors = FALSE)
## col 1-2  coalition at 400 and 2 000 $/ha            col 3-5  club, 400 $/ha + 2 %, + 5 %, + 7 % on the charged sectors
## col 6    carbon charge, 100 $/tCO2 on the embodied deforestation emissions (CBAM-like), no penalty
## col 7    pure penalty: no footprint charge (sheet AVE_pha0, all zeros) + 5 % on every non-member (Nordhaus club on the 17 sectors)
## 3 seeds x 7 configurations = 21 runs, in this order, 3 to 10 accurate solves each: the last ones may still be running in the morning
## later: "AVE_pha10000" tau 0, tau_scope = "all" (cycles: run it alone); stability = TRUE for the coalitions worth testing

## every seed for every configuration, configuration by configuration; delete rows to shorten the night
grid <- do.call(rbind, lapply(seq_len(nrow(configs)), function(k) cbind(configs[k, ], seeds, stringsAsFactors = FALSE)))
rownames(grid) <- NULL

run_all <- function(grid, game_script, log_file) {
  force(grid); force(game_script); force(log_file)      # keep local copies: the game script clears the global environment
  dir.create(dirname(log_file), recursive = TRUE, showWarnings = FALSE)
  for (k in seq_len(nrow(grid))) {
    assign("run_config", c(as.list(grid[k, ]), script_path = game_script), envir = globalenv())   # the game script reads its folder from this path
    msg <- paste(format(Sys.time()), "START run", k, "of", nrow(grid), ":", paste(names(grid), grid[k, ], sep = "=", collapse = " "))
    cat(msg, "\n"); cat(msg, "\n", file = log_file, append = TRUE)
    t0  <- Sys.time()
    res <- tryCatch({ source(game_script, local = FALSE); "OK" },
                    error = function(e) paste("ERROR:", conditionMessage(e)))
    msg <- paste(format(Sys.time()), "END   run", k, res, "-", round(as.numeric(difftime(Sys.time(), t0, units = "mins"))), "min")
    cat(msg, "\n"); cat(msg, "\n", file = log_file, append = TRUE)
  }
  if (exists("run_config", envir = globalenv())) rm("run_config", envir = globalenv())
}

run_all(grid, game_script, log_file)
