## =====================================================================================
##  Run_overnight_friction.R  -  the join/leave dynamics with ONE uniform friction instead of the Realistic_wi_china
##  thresholds (V25): seven runs, about 4.5 hours, chosen to answer four questions:
##    1. Does China still join on noise, and does the seeded coalition still hold?   runs 1-2 (coalition 400, EU seed and EU + Mercosur seed)
##    2. Does the coalition form by itself from the EU alone at 2 000 USD/ha?       run 3   (Brazil's threshold falls from 581 to 73 M USD)
##    3. What penalty makes the club form from the EU alone?                         runs 4-5 (club 400 + 2 %, + 5 %; the sheet needed 7 %)
##    4. Does the 7 % snowball survive the new thresholds (18 members under the sheet, China in and out, the small
##       members oscillating)?                                                        run 6   (club 400 + 7 %, EU alone)
##    plus the carbon charge from the EU alone (run 7, the long one: 15 min per solve).
##  Same game script (CGE_Game_Theory_GTAPAEZ_all_V25.R) and configurations as the sheet night, so every run has its twin
##  in 3_Output/Realistic_wi_china/; results go to 3_Output/Friction/forest_<run_tag>_fr0.001trade/Scenario_D/ and
##  4_DB/..._fr0.001trade.csv. Nothing of the sheet night is touched. eudr_in_loop = "none": the EUDR is in the baseline
##  only, the scenarios are the club or coalition mechanism alone (the sheet night had the EUDR kept on non-members, run_tag "_eudr";
##  these runs carry "_eudr0").
##
##  The friction (V25): both thresholds of a region = max(friction_floor, friction x its trade in the 17 charged
##  commodities) - exports (VFOB) + imports (VCIF) of the tms_f sectors with the other regions of the model, from
##  2_Model/in/basedata.har, in the USD M of the data base (the units of EV); the intra-region trade of the composite
##  regions (65 % of the EU's exports of these goods) is excluded because the club never charges it. A region joins
##  when the last round cost it more than that, a member leaves when the last round cost it more than that.
##  friction = 0.001 (0.1 % of the charged trade): EU 227 M USD, China 215, US 196, SEAsia 104, Brazil 73, India 50,
##  Indonesia 43, Argentina 37, Malaysia 26, Ivory Coast 6.9, Uruguay 5.0, Nigeria 4.9, Paraguay 4.8, Ghana 4.0,
##  DRC / Madagascar / Bolivia at the floor (2 M USD). Sheet for comparison: Brazil 411 / 581, China 500 / 20,
##  Ivory Coast 6 / 6, Ghana 8.4 / 8.4 (leave / join). Thresholds_used.txt in every run folder lists them all.
##  What the sheet night predicts for these thresholds (Brazil's worst round: -12 at 400 and -56 at 2 000 USD/ha from the
##  EU alone, -193 at 2 %, -484 at 5 %; China's -77 at 400): China stays out at 400, Brazil stays out at 2 000 (the
##  coalition would need about 2 600 USD/ha), Brazil joins the 2 % club. The runs say whether that holds once everybody
##  else's thresholds move too.
##
##  Later: friction 0.0005 and 0.002 (sensitivity), the full 3 seeds x 7 configurations, stability = TRUE on the
##  coalitions worth testing. Requirements: the eta 0.66 baseline, as for Run_overnight.R. Progress and errors go to
##  3_Output/overnight_log.txt; an error in one run does not stop the next.
##
##  Columns: as in Run_overnight.R, plus
##            friction       a number: both thresholds = friction x base (USD M) | "sheet" = the approach's thresholds
##            friction_base  "trade" = exports + imports of the 17 charged commodities (basedata.har) | "gdp" = GDP_values.xlsx (V22)
##            friction_floor USD M, lowest threshold under a numeric friction (nobody moves for less)
##            approach       with a numeric friction only the name of the output folder (3_Output/Friction/) and of the Approach column
## =====================================================================================
library("rstudioapi")

script_folder <- dirname(getSourceEditorContext()$path)
game_script   <- file.path(script_folder, "CGE_Game_Theory_GTAPAEZ_all_V25.R")
log_file      <- file.path(dirname(script_folder), "3_Output", "overnight_log.txt")

common <- data.frame(
  tau_scope    = "charged",
  eudr_in_loop = "none",                 # the scenario is the club/coalition alone; the EUDR is only in the baseline (iteration 0). "outsiders" = the EUDR kept on non-members on top of the charge (runs of 19-20 Sept)
  approach     = "Friction",             # output folder 3_Output/Friction/ (the threshold sheets are not read)
  friction     = 0.001,                  # 0.1 % of the region's trade in the charged commodities
  friction_base = "trade",               # V25
  friction_floor = 2,                    # USD M
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
  tmsf_sheet = c("AVE_pha400", "AVE_pha400",                             "AVE_pha2000", "AVE_pha400", "AVE_pha400", "AVE_pha400", "AVE_co2_100"),
  tau        = c(0,            0,                                        0,             2,            5,            7,            0),
  seed_name  = c("EU",         "EUMercosur",                             "EU",          "EU",         "EU",         "EU",         "EU"),
  seed       = c("eu27",       "eu27,brasil,argentina,paraguay,uruguay", "eu27",        "eu27",       "eu27",       "eu27",       "eu27"),
  stringsAsFactors = FALSE)
## 1 coalition 400 from the EU alone: does China still join (its threshold is now 215, its round was -77)?
## 2 coalition 400 seeded EU + Mercosur: does the seeded coalition hold with the new thresholds, and does China still come in?
## 3 coalition 2 000 from the EU alone: does Brazil join now that its threshold is 73 (its worst round was -260 when China joined, -56 from the EU alone)?
## 4-5 club 400 + 2 % and + 5 % from the EU alone: the sheet needed 7 %; with Brazil at 73 the 2 % club should already recruit it
## 6 club 400 + 7 % from the EU alone: the sheet's snowball (Brazil and Argentina in round 3, 18 members, China in and out twice in
##   the China-seeded run) with the new thresholds - who joins, in which round, and whether the small members still oscillate
## 7 carbon charge from the EU alone: Brazil (-462 in round 1) and Indonesia (-207, threshold 43) should join in round 2
## delete rows to shorten; the full 3 seeds x 7 configurations is the grid of Run_overnight.R with friction = 0.001

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
