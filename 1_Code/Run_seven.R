## =====================================================================================
##  Run_seven.R  -  the nine informative runs, with the EUDR in the baseline only (eudr_in_loop = "none"): the scenario is
##  the club or coalition mechanism alone. One switch, threshold_rule, selects the thresholds:
##      "sheet"  = Realistic_wi_china (GDP-based: 0.01-0.03 % of GDP by HDI, capped at 500 M USD, x diplomatic multiplier)
##      0.001    = the uniform friction of V25 (0.1 % of the region's trade in the 17 charged commodities, floor 2 M USD)
##  Output: 3_Output/<Realistic_wi_china | Friction>/forest_<run_tag>_eudr0_.../Scenario_D/ and 4_DB/..._eudr0_...csv
##  ("_eudr0" = no EUDR in the loop; the runs of 19-20 Sept carry "_eudr" and kept the EUDR on non-members - not comparable).
##
##  The nine runs (about 5.5 hours):
##    1. coalition 400 USD/ha from the EU alone            who joins without the EUDR exemption as a carrot
##    2. coalition 400 USD/ha seeded EU + Mercosur          does the seeded coalition hold, does China come in
##    3. coalition 2 000 USD/ha from the EU alone           does Brazil join
##    4-6. club 400 USD/ha + 2 %, + 5 %, + 7 % from the EU alone   the penalty that recruits Brazil, and the 7 % snowball
##    7-8. pure penalty, no footprint charge (sheet AVE_pha0, all zeros) + 5 % and + 7 % from the EU alone: the Nordhaus club
##    9. carbon charge 100 USD/tCO2 from the EU alone       the snowball under the carbon charge (15 min per solve)
##  Game script: CGE_Game_Theory_GTAPAEZ_all_V26.R. Requirements: the eta 0.66 baseline. Progress and errors go to
##  3_Output/overnight_log.txt; an error in one run does not stop the next. Delete rows of `runs` to shorten.
##
##  Columns: as in Run_overnight.R (friction, friction_base, friction_floor: see V25; approach names the output folder).
## =====================================================================================
library("rstudioapi")

threshold_rule <- "sheet"   # "sheet" = Realistic_wi_china thresholds | 0.001 = uniform friction, 0.1 % of the charged trade (V25)

script_folder <- dirname(getSourceEditorContext()$path)
game_script   <- file.path(script_folder, "CGE_Game_Theory_GTAPAEZ_all_V26.R")
log_file      <- file.path(dirname(script_folder), "3_Output", "overnight_log.txt")

common <- data.frame(
  tau_scope    = "charged",
  eudr_in_loop = "none",                 # the scenario is the club/coalition alone; the EUDR is only in the baseline (iteration 0). "outsiders" = the EUDR kept on non-members on top of the charge (runs of 19-20 Sept)
  approach     = if (identical(threshold_rule, "sheet")) "Realistic_wi_china" else "Friction",   # threshold sheet and output folder | "Friction": folder only
  friction     = threshold_rule,         # "sheet" | a number: uniform friction x the region's trade in the charged commodities (V25)
  friction_base = "trade",               # V25 (used only with a numeric friction)
  friction_floor = 2,                    # USD M (idem)
  dynamics     = "on",
  stability    = FALSE,                  # the dynamics only, as on the sheet night
  stability_scope = "all",
  bau_outsiders = "cover",               # V23: non-members' forest on the BAU path (the baseline's own lines)
  min_face     = 7,                      # V23: a solve scoring below this accuracy face is redone with the accurate settings
  solve_mode   = "accurate",             # 5-6 min per solve (15 min for the carbon charge)
  max_pass     = 2,
  join_rule    = "consecutive",          # "consecutive" (V13 rule) or "baseline" (path-independent)
  bau_horizon  = 5,                      # Baseline_EUDR.R must have been run with the same value
  bau_eta      = 0.66,                   # V24: Calibrate_BAU_productivity.R and Baseline_EUDR.R must have been run with the same value
  stringsAsFactors = FALSE)

runs <- data.frame(
  tmsf_sheet = c("AVE_pha400", "AVE_pha400",                             "AVE_pha2000", "AVE_pha400", "AVE_pha400", "AVE_pha400", "AVE_pha0", "AVE_pha0", "AVE_co2_100"),
  tau        = c(0,            0,                                        0,             2,            5,            7,            5,          7,          0),
  seed_name  = c("EU",         "EUMercosur",                             "EU",          "EU",         "EU",         "EU",         "EU",       "EU",       "EU"),
  seed       = c("eu27",       "eu27,brasil,argentina,paraguay,uruguay", "eu27",        "eu27",       "eu27",       "eu27",       "eu27",     "eu27",     "eu27"),
  stringsAsFactors = FALSE)
## with the EUDR kept on non-members (19-20 Sept, sheet thresholds) these gave: 1 Ivory Coast + China, 1.05 Mha | 2 held, + China + Ivory Coast,
## 8.8 Mha | 3 + Ghana, Brazil out (-260 in the round China joined, threshold 581) | 4-5 Brazil out (-193, -484) | 6 Brazil + Argentina
## in round 3, 18 members, 10.2 Mha | 7 (pure penalty 5 %) identical to 400 + 5 % to the last member | 9 Brazil + Indonesia in
## round 4, 14 members, 11.05 Mha. Without the EUDR in the scenario,
## joining no longer lifts the EUDR cut (2.6 % on Brazilian beef into the EU), so recruitment at 400-2 000 USD/ha should be harder.

grid <- cbind(runs, common[rep(1, nrow(runs)), ], stringsAsFactors = FALSE)
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
