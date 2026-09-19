## =====================================================================================
##  Run_overnight.R  -  chains full runs of CGE_Game_Theory_GTAPAEZ_all_V17.R
##
##  One row of `grid` = one complete game run (one approach, one price scenario, one tau).
##  Edit the grid, open this file in RStudio and run it (Ctrl+Alt+R). Each run writes its own
##  folder 3_Output/<approach>/forest_<run_tag>/Scenario_D/ and its own 4_DB csv, so runs never
##  overwrite each other. Progress and errors go to 3_Output/overnight_log.txt; an error in one
##  run does not stop the next. Requirements: 1_Code/Baseline_EUDR.R has been run once.
##
##  Columns:  approach      Realistic_wi_china | Diplomatic | Realistic_wo_china | Idealist
##            tmsf_sheet    AVE_pha400 | AVE_pha2000 | AVE_pha10000 | AVE_co2_50 | AVE_co2_100 | AVE_co2_190
##            tau           0 = coalition (footprint charge only) | > 0 = club (+ flat penalty, % on the tariff power)
##            tau_scope     "charged" = the 17 land-based sectors | "all" = every commodity (Nordhaus club)
##            eudr_in_loop  "outsiders" = EU keeps the EUDR cost on non-members | "none" = the coalition replaces it
## =====================================================================================
library("rstudioapi")

script_folder <- dirname(getSourceEditorContext()$path)
game_script   <- file.path(script_folder, "CGE_Game_Theory_GTAPAEZ_all_V17.R")
log_file      <- file.path(dirname(script_folder), "3_Output", "overnight_log.txt")

grid <- data.frame(
  approach     = "Realistic_wi_china",
  tmsf_sheet   = c("AVE_pha400", "AVE_pha400", "AVE_pha400", "AVE_pha2000", "AVE_pha10000", "AVE_pha400", "AVE_co2_100"),
  tau          = c(0,            5,            5,            0,             0,              0,            0),
  tau_scope    = c("charged",    "charged",    "all",        "charged",     "charged",      "charged",    "charged"),
  eudr_in_loop = c("outsiders",  "outsiders",  "outsiders",  "outsiders",   "outsiders",    "none",       "outsiders"),
  stringsAsFactors = FALSE)
## row 1  coalition at 400 $/ha                 row 2  club, 5 % penalty on the charged sectors
## row 3  club, 5 % penalty on everything       row 4-5 coalition at 2 000 and 10 000 $/ha
## row 6  coalition replacing the EUDR          row 7  carbon variant, 100 $/tCO2
## Delete rows to shorten the night; add rows for other approaches.

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
