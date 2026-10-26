## =====================================================================================
##  V34 (Oct 2026): the business-as-usual clearing of each region is allocated to its AEZs with the observed clearing shares
##  (HILDA+ v2.1, bau_deforestation.xlsx rebuilt by 0_External_data/DeDuCE_rework/zenodo_v2.1/build_deduce_tables.py) instead of
##  the forest-cover shares of V32-V33; everything else as V33. The whole programme runs from one launch: generation = "v34" (set
##  below), Y = X = "auto" - the headline penalty and surcharges are read from the grid results when the first block that needs
##  them starts (lockouts), as the rule the paper states: the lowest grid value at which the club / the coalition forms, and the
##  surcharge at which Brazil joins on its own first-round loss. Lock-outs of regions that never join the base run are skipped
##  (V33 hard-coded that for the US and Indonesia below 3,500 USD/ha). Set Y and X to numbers to force them (V33: 1.25, c(2500, 4000)).
## -------------------------------------------------------------------------------------
##  V33 (20-21 Oct 2026): the Miranda-calibrated land-supply elasticities (generation = "v33", see the setting in main()). The
##  programme runs in two phases; a run whose csv exists is reused, so the script can be relaunched after an interruption and
##  picks up where it was. Results: 4_DB/V33_runs_<date>.txt, one line per run. The V32 programme as it was run on 7 Oct is
##  kept in 9_Archive/Run_V32_all_v32_2026-10-07.R, the phase-1 script in 9_Archive/Run_V32_all_phase1_2026-10-20.R.
##
##  PHASE 1 (20-21 Oct, done): the grid alone at the 0.1 % switching cost - every EU-alone charge, the seeds and the combined
##  instruments (blocks grid_core, grid_penalty, grid_surcharge, grid_floor, grid_seeds, grid_combined; 26 runs, 172 solves, 12 h).
##  Read in 3_Output/V33_grid_vs_V32_2026-10-21.md: the club forms from 1.25 % (Brazil joins in round 2 on its own first-round
##  loss, 88 M USD against a switching cost of 73); the EU-alone surcharge forms the coalition from 2,500 USD/ha (Brazil's own loss
##  56 < 73: the importers enter in round 3 and Brazil follows in round 4) and brings Brazil in on its own loss from 3,500 (75;
##  4,000: 84); 2,000 fails (Brazil outside; it worked in V32 on a 0.5 % margin of Colombia's). EU + China: 0.87 % and 1,000 as in
##  V32. Combined: 0.5 % + 2,000 works, 0.62 % + 1,000 fails (0.87 % works). coalition_4000 failed on a locked file left by the
##  stopped V32 batch and is run again here (block grid_core).
##
##  PHASE 2 (this file): the runs that depend on the headline, at Y = 1.25 % and at BOTH surcharges X = 2,500 and 4,000, so that
##  the two ways of presenting the surcharge (lowest charge at which the coalition forms / lowest at which Brazil joins on its own
##  loss, the V32 value) are both on the table:
##    "lockouts"    Brazil, the US, the US + China (Referee #4's conservative alliance) and Indonesia locked out of the 1.25 % club
##                  (4 runs); Brazil and the US + China locked out of the 2,500 coalition (2 runs: the US and Indonesia never join
##                  at 2,500, so locking them out alone is the base run); Brazil, the US, the US + China and Indonesia locked out of
##                  the 4,000 coalition (4 runs). 10 runs, ~70 solves, ~6 h
##    "stability"   one-deviation tests of the five core clubs - club 1.25 %, coalitions 2,500 and 4,000, EU + Mercosur at zero,
##                  EU + China 1.12 % - with dynamics off from the converged club S: every member (the EU excepted) out alone, and,
##                  with stability_scope = "all", EVERY outsider in alone (V32 tested the 19 regions of a list and ran the other
##                  outsiders of the 4,000 coalition and Japan in two extra blocks; here they are all in the one test). One solve per
##                  region: 35 + 6, 17 + 24, ~22 + 19, 11 + 30, 34 + 7 -> ~210 solves, 15-18 h. Written to
##                  4_DB/Stability_Friction_forest_<tag>_seedSmin<name>_fixed_<...>.txt
##    "japan"       the V32 remark kept for the SI: Japan joining the 1.5 % club alone (Japan is a member of the 1.25 % club, so
##                  there is nothing to test there; at 1.5 % it joins in round 3 and leaves). Dynamics off, no member test, one solve
##    "brackets"    the switching-cost sensitivity, halved (fr = 0.0005) and doubled (0.002), bracketed automatically for each
##                  instrument: the V32 working value is run first (club 0.75 % and coalition 1,000 at 0.0005; club 2.5 % and
##                  coalition 9,000 at 0.002); if it works the next lower grid value is run until one fails, if it fails the next
##                  higher until one works. "Works" = converged with Brazil inside (V32: club 0.5 % at 0.0005 hit the round cap with
##                  Brazil inside and counts as failing). 8-12 runs, 80-120 solves, 7-10 h
##  About 30 h in all after the grid. Order: grid (reused, coalition_4000 run), lockouts, stability, japan, brackets.
## -------------------------------------------------------------------------------------
##  The V32 programme of 7 Oct (9_Archive/Run_V32_all_v32_2026-10-07.R), for reference: blocks core, brackets, complement,
##  penalty_up, stability, brackets2, plane, sensitivity, alliance, brackets3, brackets4, japan, brackets5, coalition_outsiders -
##  45-47 runs, 462 solves, ~32 h, at Y = 1.5 % and X = 4,000 (the EU-alone minima of 30 Sept). Same world and settings here:
##  two-stage baseline, pin all, EUDR kept on outsiders in every solve, switching cost 0.1 % of trade (floor 2 M USD), experience
##  rule, safeguard 0.1 % of GDP, welfare net of the forest-land wedge term, round cap 15 solves.
## =====================================================================================
library("rstudioapi")

blocks <- c("grid_core", "grid_penalty", "grid_surcharge", "grid_floor", "grid_floor_penalty", "grid_seeds", "grid_combined",   # PHASE 1: the grid (a run whose csv exists is reused)
            "lockouts", "stability", "japan", "brackets")                                                                      # PHASE 2: what hangs on the headline
generation <- "v34"   # the generation of runs: "v34" (BAU clearing by HILDA+ AEZ shares), "v33" (the Miranda-calibrated elasticities, 20 Oct 2026),
                      # "v32" (the runs of 7 Oct). Baseline folder Baseline_2stage_bau5_eta0.66_<generation>, run tags _<generation>, summary 4_DB/<GENERATION>_runs_<date>.txt
Y <- "auto"           # the headline penalty (%): a number (V33: 1.25), or "auto" = the lowest value of the EU-alone penalty grid at which the club forms
                      # (converged with Brazil inside), read from the grid results when the first headline block starts
X <- "auto"           # the headline surcharges (USD/ha), all run: a vector (V33: c(2500, 4000)), or "auto" = c(the lowest grid value at which the coalition
                      # forms, the one at which Brazil joins in the second round on its own first-round loss: 4,000 kept while it still does, else the lowest grid value where it does)
stability_scope <- "all"   # outsiders tested for joining alone in the stability block: "all", or a comma-separated list (V32: 19 regions)

main <- function(blocks, stability_scope, Y, X, generation) {
  force(blocks); force(stability_scope); force(Y); force(X); force(generation)   # local copies: the game script clears the global environment
  script_folder <- dirname(if (nzchar(Sys.getenv("FOREST_CLUB_SCRIPT"))) Sys.getenv("FOREST_CLUB_SCRIPT") else getSourceEditorContext()$path)   # FOREST_CLUB_SCRIPT: set by run_step.R when run with Rscript (no RStudio), see run_chain_v34.bat
  game_script   <- file.path(script_folder, "CGE_Game_Theory_GTAPAEZ_all_V32.R")
  parent_folder <- dirname(script_folder)
  log_file      <- file.path(parent_folder, "3_Output", "overnight_log.txt")
  gen_sfx       <- if (generation == "v32") "" else paste0("_", generation)
  result_file   <- file.path(parent_folder, "4_DB", paste0(toupper(generation), "_runs_", format(Sys.Date()), ".txt"))
  two_stage <- file.path(parent_folder, "3_Output", paste0("Baseline_2stage_bau5_eta0.66", gen_sfx))
  if (!file.exists(file.path(two_stage, "A_bau", "gdata_bau.upd")) || !file.exists(file.path(two_stage, "B_eudr", "NATDEF_B.sl4")))
    stop("run 1_Code/Baseline_2stage.R first (Stages A and B): ", two_stage)
  if (!file.exists(game_script)) stop("game script not found: ", game_script)

  base <- list(tau_scope = "charged", eudr_in_loop = "none", approach = "Friction",
               friction = 0.001, friction_base = "trade", friction_floor = 2,
               dynamics = "on", stability = FALSE, stability_scope = "all", min_face = 7,
               solve_mode = "accurate", max_pass = 2, join_rule = "experience", max_rounds = 15, bau_horizon = 5, bau_eta = 0.66,
               seed = "eu27", seed_name = "EU", tmsf_sheet = "AVE_pha400", tau = 0, safeguard = "baseline", locked_out = "",
               start_from = "bau", eudr_outsiders = "keep", member_pin = "all",   # V30 settings of the 30 Sept - 1 Oct runs
               welfare = "ev_net_wedge",                                          # V31
               generation = generation)                                           # V33

  run_tag_of <- function(cfg) {   # mirror of the V32 script's run_tag
    label <- if (!is.null(cfg$price_ha)) paste0("pha", format(cfg$price_ha, scientific = FALSE)) else
             if (!is.null(cfg$co2_price)) paste0("co2_", format(cfg$co2_price, scientific = FALSE)) else sub("^AVE_", "", cfg$tmsf_sheet)
    lock  <- if (!is.null(cfg$locked_out) && nzchar(cfg$locked_out)) paste0("_lock", paste(setdiff(tolower(trimws(strsplit(cfg$locked_out, ",")[[1]])), "eu27"), collapse = "-")) else ""
    paste0("forest_", label, "_tau", cfg$tau, if (cfg$tau > 0) cfg$tau_scope else "", if (identical(cfg$eudr_in_loop, "none")) "_eudr0" else "_eudr", "_bau", cfg$bau_horizon, "_eta", cfg$bau_eta,
           "_seed", cfg$seed_name, if (cfg$dynamics == "off") "_fixed" else "", lock, "_outfree",
           paste0("_fr", format(cfg$friction, scientific = FALSE), cfg$friction_base),
           c(baseline = "_sgb", level = "", off = "_sgoff")[[cfg$safeguard]],
           c(consecutive = "", baseline = "_jrbase", experience = "_jrexp")[[cfg$join_rule]],
           paste0("_frombau_eudr", cfg$eudr_outsiders, if (identical(cfg$member_pin, "all")) "_pinall" else ""),
           if (identical(cfg$welfare, "ev_net_wedge")) "_wnet" else "", "_", cfg$generation)   # V32 / V33
  }

  read_decomp <- function(folder, i) {   # the round's decomposition: Welfare_decomp_round_<i>.txt, else the last solve of that round
    f <- file.path(folder, paste0("Welfare_decomp_round_", i, ".txt"))
    if (!file.exists(f)) { cands <- list.files(folder, pattern = paste0("^Welfare_decomp_iter_", i, "(_pass_[0-9]+)?\\.txt$"), full.names = TRUE)
                           if (length(cands) == 0) return(NULL); f <- cands[which.max(file.mtime(cands))] }
    read.table(f, header = TRUE, stringsAsFactors = FALSE)
  }
  read_result <- function(cfg) {   # the run's aggregated csv -> members, forest kept / leaked, EV (net and gross) of the final coalition; NULL if not run
    f <- file.path(parent_folder, "4_DB", paste0("Database_GTAPAEZ_all_results_2024_agg_", run_tag_of(cfg), ".csv"))
    if (!file.exists(f)) return(NULL)
    d <- read.csv(f, stringsAsFactors = FALSE)
    last <- max(d$Iteration); d0 <- d[d$Iteration == 0, ]; d1 <- d[d$Iteration == last, ]
    ev0 <- setNames(d0$EV, d0$Country); ev1 <- setNames(d1$EV, d1$Country)
    tr0 <- setNames(d0$Tropical, d0$Country); tr1 <- setNames(d1$Tropical, d1$Country)
    al0 <- setNames(d0$Tropical + d0$Temperate + d0$Boreal, d0$Country); al1 <- setNames(d1$Tropical + d1$Temperate + d1$Boreal, d1$Country)
    members <- sort(d1$Country[d1$Club == "inside"]); outsiders <- setdiff(d1$Country, members)
    ins <- d[d$Club == "inside", ]; join_round <- if (nrow(ins)) tapply(ins$Iteration, ins$Country, min) else integer(0)   # the first round a region is inside (2 = it joined on its first-round loss)
    folder <- file.path(parent_folder, "3_Output", cfg$approach, run_tag_of(cfg), "Scenario_D")
    summ <- file.path(folder, "Run_summary.txt")
    outcome <- if (file.exists(summ)) sub("^outcome: ", "", grep("^outcome:", readLines(summ, warn = FALSE), value = TRUE)[1]) else if (last < cfg$max_rounds - 1) "converged" else "stopped at the round cap"
    g0 <- read_decomp(folder, 0); g1 <- read_decomp(folder, last)
    gross <- if (!is.null(g0) && !is.null(g1)) setNames(g1$ev_gross[match(names(ev1), g1$region)] - g0$ev_gross[match(names(ev1), g0$region)], names(ev1)) else NULL
    key <- c("brasil", "china", "eu27", "us", "nigeria", "ivorycoast", "malasya", "drc", "bolivia", "angola")
    list(members = members, outsiders = outsiders, n = length(members), iterations = last, outcome = outcome, converged = startsWith(outcome, "converged"),
         join_round = join_round, ever_inside = names(join_round),
         kept_Mha = sum(tr1[members] - tr0[members]) / 1e6, kept_all_Mha = sum(al1[members] - al0[members]) / 1e6,
         leak_Mha = -sum(tr1[outsiders] - tr0[outsiders]) / 1e6, leak_all_Mha = -sum(al1[outsiders] - al0[outsiders]) / 1e6,
         world_net = sum(ev1) - sum(ev0), world_gross = if (!is.null(gross)) sum(gross) else NA,
         net = ev1[key] - ev0[key], gross = if (!is.null(gross)) gross[key] else setNames(rep(NA, length(key)), key))
  }
  line_of <- function(label, r) {
    fmt <- function(x) ifelse(is.na(x), "na", sprintf("%+.0f", x))
    sprintf("%-32s members=%2d %-34s kept=%+.2f Mha (all %+.2f) leakage=%+.3f Mha (all %+.3f) | dEV net: world=%s brasil=%s china=%s eu27=%s us=%s nigeria=%s ivorycoast=%s malasya=%s drc=%s bolivia=%s angola=%s | dEV gross: world=%s brasil=%s nigeria=%s drc=%s | %s",
            label, r$n, r$outcome, r$kept_Mha, r$kept_all_Mha, r$leak_Mha, r$leak_all_Mha,
            fmt(r$world_net), fmt(r$net["brasil"]), fmt(r$net["china"]), fmt(r$net["eu27"]), fmt(r$net["us"]), fmt(r$net["nigeria"]), fmt(r$net["ivorycoast"]), fmt(r$net["malasya"]), fmt(r$net["drc"]), fmt(r$net["bolivia"]), fmt(r$net["angola"]),
            fmt(r$world_gross), fmt(r$gross["brasil"]), fmt(r$gross["nigeria"]), fmt(r$gross["drc"]), paste(r$members, collapse = " "))
  }

  run_one <- function(label, cfg) {
    r <- read_result(cfg)
    if (!is.null(r) && !isTRUE(cfg$stability)) {
      msg <- paste(format(Sys.time()), "REUSE", label, "- already run:", run_tag_of(cfg))
      cat(msg, "\n"); cat(msg, "\n", file = log_file, append = TRUE); cat(line_of(label, r), "\n", file = result_file, append = TRUE)
      return(r)
    }
    if (isTRUE(cfg$stability)) {
      st <- file.path(parent_folder, "4_DB", paste0("Stability_", cfg$approach, "_", run_tag_of(cfg), ".txt"))
      if (file.exists(st) && !is.null(r)) { msg <- paste(format(Sys.time()), "REUSE", label, "- stability already done:", st); cat(msg, "\n"); cat(msg, "\n", file = log_file, append = TRUE); return(r) }
    }
    assign("run_config", c(cfg, script_path = game_script), envir = globalenv())
    msg <- paste(format(Sys.time()), "START", label, ":", paste(names(cfg), unlist(cfg), sep = "=", collapse = " "))
    cat(msg, "\n"); cat(msg, "\n", file = log_file, append = TRUE)
    t0  <- Sys.time()
    res <- tryCatch({ source(game_script, local = FALSE); "OK" }, error = function(e) paste("ERROR:", conditionMessage(e)))
    r   <- if (res == "OK") read_result(cfg) else NULL
    line <- if (is.null(r)) paste(label, "run failed:", res) else line_of(label, r)
    msg <- paste(format(Sys.time()), "END  ", label, res, "-", round(as.numeric(difftime(Sys.time(), t0, units = "mins"))), "min |", line)
    cat(msg, "\n"); cat(msg, "\n", file = log_file, append = TRUE); cat(line, "\n", file = result_file, append = TRUE)
    r
  }
  works <- function(r) !is.null(r) && isTRUE(r$converged) && ("brasil" %in% r$members)   # a run "works" when it converges with Brazil inside

  coalition <- function(price, seed = "eu27", name = "EU", ...) modifyList(base, list(price_ha = price, tau = 0, seed = seed, seed_name = name, ...))
  club      <- function(tau, seed = "eu27", name = "EU", ...)   modifyList(base, list(price_ha = 0, tau = tau, seed = seed, seed_name = name, ...))
  MERCOSUR  <- "eu27,brasil,argentina,paraguay,uruguay"
  fmtv      <- function(x) format(x, scientific = FALSE, trim = TRUE)
  runs <- list(
    ## PHASE 1 - the grid at the 0.1 % switching cost (the values of the V32 grid of 7 Oct)
    club_1.5            = club(1.5),
    coalition_4000      = coalition(4000),
    mercosur_0          = coalition(0, MERCOSUR, "EUMercosur"),
    euchina_club_1.12   = club(1.12, "eu27,china", "EUChina"),
    club_1.25           = club(1.25),
    club_1              = club(1),
    club_0.75           = club(0.75),
    club_0.62           = club(0.62),      # V34: the penalty floor chain, run only while the value above works (as grid_floor for the surcharge)
    club_0.5            = club(0.5),
    club_2.5            = club(2.5),
    club_5              = club(5),
    coalition_3500      = coalition(3500),
    coalition_3000      = coalition(3000),
    coalition_2500      = coalition(2500),
    coalition_2000      = coalition(2000),
    coalition_6000      = coalition(6000),
    coalition_1500      = coalition(1500),
    coalition_1000      = coalition(1000),
    coalition_500       = coalition(500),
    euchina_club_0.87   = club(0.87, "eu27,china", "EUChina"),
    euchina_club_0.75   = club(0.75, "eu27,china", "EUChina"),
    euchina_coal_1000   = coalition(1000, "eu27,china", "EUChina"),
    euchina_coal_500    = coalition(500, "eu27,china", "EUChina"),
    mercosurchina_0     = coalition(0, paste0(MERCOSUR, ",china"), "EUMercosurChina"),
    mercosur5_0         = coalition(0, paste0(MERCOSUR, ",bolivia"), "EUMercosur5"),
    tau0.75_at_pha2000  = modifyList(base, list(price_ha = 2000, tau = 0.75)),
    tau0.5_at_pha2000   = modifyList(base, list(price_ha = 2000, tau = 0.5)),
    tau1.12_at_pha1000  = modifyList(base, list(price_ha = 1000, tau = 1.12)),
    tau0.87_at_pha1000  = modifyList(base, list(price_ha = 1000, tau = 0.87)),
    tau0.62_at_pha1000  = modifyList(base, list(price_ha = 1000, tau = 0.62)))
  ## PHASE 2 - the headline runs (Y, X) and what hangs on them: resolved from the grid results when the first headline block starts
  grid_axes <- list(penalty   = c("club_0.5", "club_0.62", "club_0.75", "club_1", "club_1.25", "club_1.5", "club_2.5", "club_5"),   # the EU-alone grids, low to high (Y = X = "auto" read these)
                    surcharge = c("coalition_500", "coalition_1000", "coalition_1500", "coalition_2000", "coalition_2500", "coalition_3000", "coalition_3500", "coalition_4000", "coalition_6000"))
  value_of <- function(nm) as.numeric(sub("^[a-z]+_", "", nm))
  blocks_def <- list(
    grid_core      = c("club_1.5", "coalition_4000", "mercosur_0", "euchina_club_1.12"),
    grid_penalty   = c("club_1.25", "club_1", "club_0.75", "club_2.5", "club_5"),
    grid_surcharge = c("coalition_3500", "coalition_3000", "coalition_2500", "coalition_2000", "coalition_6000"),
    grid_floor     = c("coalition_1500", "coalition_1000", "coalition_500"),   # a chain: the next one only if the previous works (Brazil inside)
    grid_floor_penalty = c("club_0.62", "club_0.5"),                         # the same below club_0.75, started only if club_0.75 works (V34)
    grid_seeds     = c("euchina_club_0.87", "euchina_club_0.75", "euchina_coal_1000", "euchina_coal_500", "mercosurchina_0", "mercosur5_0"),
    grid_combined  = c("tau0.75_at_pha2000", "tau0.5_at_pha2000", "tau1.12_at_pha1000", "tau0.87_at_pha1000", "tau0.62_at_pha1000"),
    lockouts = NULL, stability = NULL, japan = NULL)   # filled by resolve_headline() from Y and X
  brackets_def <- list(   # the switching-cost brackets: start = the V33 working value; grid = the candidate values, low to high
    list(fr = 0.0005, inst = "club",      start = 0.75, grid = c(0.25, 0.5, 0.62, 0.75, 0.87, 1, 1.12, 1.25, 1.5)),
    list(fr = 0.0005, inst = "coalition", start = 1000, grid = c(250, 500, 750, 1000, 1500, 2000, 2500)),
    list(fr = 0.002,  inst = "club",      start = 2.5,  grid = c(1.5, 2, 2.5, 3, 4, 5)),
    list(fr = 0.002,  inst = "coalition", start = 9000, grid = c(4000, 6000, 8000, 9000, 10000, 12000)))
  cat(paste0("== ", toupper(generation), " runs, ", format(Sys.time()), " - welfare = ev_net_wedge | start_from = bau, eudr_outsiders = keep, member_pin = all | Y = ", paste(Y, collapse = "/"), " % | X = ", paste(X, collapse = " / "), " USD/ha | stability_scope = ", stability_scope, " | blocks: ", paste(blocks, collapse = " "), "\n"), file = result_file, append = TRUE)
  note <- function(msg) { print(msg); cat(msg, "\n", file = result_file, append = TRUE) }
  done <- list()
  headline <- NULL
  resolve_headline <- function() {   # Y and X from the grid results on the disk (numbers are kept as given), then the lock-out runs and the stability / Japan lists
    on_disk <- function(nm) { r <- done[[nm]]; if (is.null(r)) r <- read_result(runs[[nm]]); r }
    tested  <- function(axis) axis[vapply(axis, function(n) !is.null(on_disk(n)), logical(1))]
    if (identical(Y, "auto")) {
      ok <- grid_axes$penalty[vapply(grid_axes$penalty, function(n) works(on_disk(n)), logical(1))]
      if (length(ok) == 0) stop("Y = \"auto\": no EU-alone club of the penalty grid forms (converged with Brazil inside) - run the grid blocks first, or extend grid_axes$penalty")
      Y <<- value_of(ok[1])
      note(paste0("headline penalty: Y = ", Y, " % - the lowest value of the grid at which the club forms (grid on the disk: ", paste(tested(grid_axes$penalty), collapse = " "), ")",
                  if (ok[1] == grid_axes$penalty[1]) " - WARNING: the lowest value of the grid works, the threshold is not bracketed from below" else ""))
    }
    if (identical(X, "auto")) {
      ok <- grid_axes$surcharge[vapply(grid_axes$surcharge, function(n) works(on_disk(n)), logical(1))]
      if (length(ok) == 0) stop("X = \"auto\": no EU-alone coalition of the surcharge grid forms - run the grid blocks first, or extend grid_axes$surcharge")
      own <- ok[vapply(ok, function(n) isTRUE(on_disk(n)$join_round["brasil"] <= 2), logical(1))]   # Brazil inside from the second round: it joined on its own first-round loss
      x_min <- value_of(ok[1]); x_own <- if ("coalition_4000" %in% own) 4000 else if (length(own)) value_of(own[1]) else NA
      X <<- unique(c(x_min, x_own[!is.na(x_own)]))
      note(paste0("headline surcharges: X = ", paste(X, collapse = " / "), " USD/ha - ", x_min, " = the lowest grid value at which the coalition forms (grid on the disk: ", paste(tested(grid_axes$surcharge), collapse = " "), ")",
                  if (is.na(x_own)) "; Brazil joins on its own first-round loss at none of the working values" else
                  paste0("; ", x_own, " = ", if (x_own == 4000) "the V32-V33 value, at which Brazil still joins on its own first-round loss (round 2)" else "the lowest grid value at which Brazil joins on its own first-round loss (round 2)")))
    }
    cat(paste0("== headline: Y = ", Y, " % | X = ", paste(X, collapse = " / "), " USD/ha\n"), file = result_file, append = TRUE)   # the line 5_Figures/common/extract_all.py reads
    headline <<- list(club = paste0("club_", fmtv(Y)), coalitions = paste0("coalition_", fmtv(X)))
    for (nm in c(headline$club, headline$coalitions)) if (is.null(runs[[nm]])) stop("headline run not in the grid: ", nm)
    lockouts <- character(0)
    for (lk in c("brasil", "us", "us,china", "indonesia")) {   # the club: all four
      nm <- paste0(headline$club, "_lock", gsub(",", "_", lk)); runs[[nm]] <<- club(Y, locked_out = lk); lockouts <- c(lockouts, nm)
    }
    for (x in X) for (lk in c("brasil", "us", "us,china", "indonesia")) {
      nm <- paste0("coalition_", fmtv(x), "_lock", gsub(",", "_", lk)); runs[[nm]] <<- coalition(x, locked_out = lk); lockouts <- c(lockouts, nm)
    }
    blocks_def$lockouts  <<- lockouts                                                                    # a lock-out of regions that never join the base run is skipped when the block runs
    blocks_def$stability <<- c(headline$club, headline$coalitions, "mercosur_0", "euchina_club_1.12")   # the clubs tested (one-deviation, dynamics off)
    blocks_def$japan     <<- unique(c("club_1.5", headline$club))                                       # Japan joining alone where it is an outsider (nothing to test where it is a member)
  }
  for (blk in blocks) {
    if (blk %in% c("lockouts", "stability", "japan") && is.null(headline)) resolve_headline()
    cat(paste0("== block ", blk, "\n"), file = result_file, append = TRUE)
    if (blk %in% c("grid_floor", "grid_floor_penalty")) {   # 7 Oct: the floor of the surcharge - each run only if the one above it works (Brazil inside at convergence); V34: the same for the penalty
      parent <- c(grid_floor = NA, grid_floor_penalty = "club_0.75")[[blk]]
      if (!is.na(parent)) { rp <- done[[parent]]; if (is.null(rp)) rp <- read_result(runs[[parent]]); if (!works(rp)) { note(paste(blk, ":", parent, "does not work (or is not run) - nothing lower to run")); next } }
      for (nm in blocks_def[[blk]]) {
        r <- run_one(nm, runs[[nm]]); done[[nm]] <- r
        if (!works(r)) { note(paste(blk, ":", nm, if (is.null(r)) "failed to run" else "fails (Brazil outside) - the floor is bracketed, no lower run needed")); break }
      }
      next
    }
    if (blk == "lockouts") {   # a lock-out only changes the game when a locked-out region joins the base run (V33: the US and Indonesia never join below 3,500 USD/ha)
      for (nm in blocks_def$lockouts) {
        base_nm <- sub("_lock.*$", "", nm); rb <- done[[base_nm]]; if (is.null(rb)) rb <- read_result(runs[[base_nm]])
        regs <- trimws(strsplit(runs[[nm]]$locked_out, ",")[[1]])
        if (!is.null(rb) && !any(regs %in% rb$ever_inside)) { note(paste0(nm, ": ", runs[[nm]]$locked_out, " never joins ", base_nm, " - the lock-out would repeat the base run, skipped")); next }
        done[[nm]] <- run_one(nm, runs[[nm]])
      }
      next
    }
    if (blk == "stability") {   # one-deviation tests of the converged core clubs (dynamics off, S = the final members, every member out alone, every outsider of stability_scope in alone)
      for (nm in blocks_def$stability) {
        r <- done[[nm]]; if (is.null(r)) r <- read_result(runs[[nm]])
        if (is.null(r) || !r$converged) { note(paste("no converged run for the stability test of", nm)); next }
        cfg <- modifyList(runs[[nm]], list(seed = paste(r$members, collapse = ","), seed_name = paste0("Smin", gsub("[^A-Za-z0-9]", "", nm)), dynamics = "off", stability = TRUE, stability_scope = stability_scope))
        run_one(paste0("stability of ", nm, " (", r$n, " members)"), cfg)
      }
      next
    }
    if (blk == "japan") {   # Japan joining a club alone - one solve, no member test (the V32 remark on the 1.5 % club)
      for (nm in blocks_def$japan) {
        r <- done[[nm]]; if (is.null(r)) r <- read_result(runs[[nm]])
        if (is.null(r) || !r$converged) { note(paste("no converged run for the Japan test of", nm)); next }
        if ("japan" %in% r$members) { note(paste("Japan is a member of", nm, "- nothing to test")); next }
        cfg <- modifyList(runs[[nm]], list(seed = paste(r$members, collapse = ","), seed_name = paste0("Smin", gsub("[^A-Za-z0-9]", "", nm), "japan"), dynamics = "off", stability = TRUE, stability_scope = "japan", stability_members = "none"))
        run_one(paste0("stability of ", nm, ": Japan joining alone"), cfg)
      }
      next
    }
    if (blk == "brackets") {   # the switching-cost brackets, found automatically from the V32 working value (see brackets_def)
      for (b in brackets_def) {
        mk <- function(v) { cfg <- if (b$inst == "club") club(v, friction = b$fr) else coalition(v, friction = b$fr); list(name = paste0(b$inst, "_", fmtv(v), "_fr", fmtv(b$fr)), cfg = cfg) }
        i <- match(b$start, b$grid); if (is.na(i)) stop("bracket start not in its grid: ", b$inst, " ", b$fr)
        x <- mk(b$grid[i]); r <- run_one(x$name, x$cfg); done[[x$name]] <- r
        if (works(r)) {   # go down until a run fails
          j <- i - 1; lo <- NA
          while (j >= 1) { x <- mk(b$grid[j]); r2 <- run_one(x$name, x$cfg); done[[x$name]] <- r2; if (!works(r2)) { lo <- b$grid[j]; break }; i <- j; j <- j - 1 }
          note(paste0("brackets ", b$inst, " fr ", fmtv(b$fr), ": works from ", fmtv(b$grid[i]), if (is.na(lo)) " (nothing below it fails - grid exhausted)" else paste0(", fails at ", fmtv(lo))))
        } else {          # go up until a run works
          j <- i + 1; hi <- NA
          while (j <= length(b$grid)) { x <- mk(b$grid[j]); r2 <- run_one(x$name, x$cfg); done[[x$name]] <- r2; if (works(r2)) { hi <- b$grid[j]; break }; i <- j; j <- j + 1 }
          note(paste0("brackets ", b$inst, " fr ", fmtv(b$fr), ": fails at ", fmtv(b$grid[i]), if (is.na(hi)) " (nothing above it works - grid exhausted)" else paste0(", works from ", fmtv(hi))))
        }
      }
      next
    }
    if (is.null(blocks_def[[blk]])) { print(paste("unknown block", blk)); next }
    for (nm in blocks_def[[blk]]) done[[nm]] <- run_one(nm, runs[[nm]])
  }
  print(paste("done - see", result_file))
}
main(blocks, stability_scope, Y, X, generation)
