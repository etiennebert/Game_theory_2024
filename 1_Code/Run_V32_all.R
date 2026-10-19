## =====================================================================================
##  Run_V32_all.R  -  the whole programme of the paper on V32 (V31 + the EUDR kept on non-members in every solve, the bug of
##  V30 fixed on 2 Oct; "_wnet_v32" files). Every run is redone: nothing of V30/V31 is reused (the tags differ).
##  Same world and settings as the V30/V31 runs of 30 Sept - 2 Oct (two-stage baseline, pin all, EUDR kept on outsiders -
##  now really applied in every solve -, switching cost 0.1 % of trade, experience rule, safeguard 0.1 % of GDP, welfare net
##  of the forest-land wedge term). No search: the runs are at fixed values with brackets on both sides (the thresholds may
##  move a little with the EUDR now in the solves: every first-round loss grows by the region's own EUDR cost, Brazil's by
##  about 13 M USD). A run whose csv exists is reused, so the script can be relaunched after an interruption and picks up
##  where it was. Blocks, in order (times at 5-10 min per solve):
##    "core"        the four headline configurations (club 1.5 %, coalition 4,000, EU + Mercosur 0, EU + China 1.12 %)
##    "brackets"    the runs just below the minima and the remaining seeds: club 1.25 %, coalition 3,500, EU + China club 0.87 %
##                  and coalition 1,000 / 500, EU + Mercosur + China at zero (6 runs, ~2.5 h)
##    "complement"  Brazil and the US locked out at both minima; the penalty at 2,000 and 1,000 USD/ha of surcharge (the exchange
##                  rate: 0.75 / 0.5 % and 1.12 / 0.87 %) (8 runs, ~5 h)
##    "penalty_up"  does a higher penalty bring DRC, Angola, Bolivia in: the club at 2.5 % and 5 %; and Bolivia in the Mercosur
##                  seed (EU + Mercosur-5 at zero) (3 runs, ~2 h)
##    "stability"   one-deviation tests of the four core clubs (dynamics off, every member out alone, every outsider of
##                  stability_scope in alone) (4 runs, ~5 h)
##    "brackets2"   added 2 Oct: on the net measure the club forms at 1.25 % (Brazil's first-round loss 74.3 against a switching cost
##                  of 73.4), so the bracket moves down: club 1.0 % and 0.75 %; and the penalty at 1,000 USD/ha of surcharge works at
##                  0.87 %, so 0.62 % is run to close that bracket (3 runs, ~1.5 h)
##    "plane"       the coalition at 6,000 USD/ha (the club at 2.5 % is in penalty_up) (1 run, ~1 h)
##    "sensitivity" the switching cost halved (club 1.0 / 0.5 %, coalition 1,000 / 500) and doubled (club 2.5 / 2 %, coalition
##                  4,000 / 6,000) (8 runs, ~6 h)
##    "alliance"    Referee #4's conservative alliance: the US and China locked out together; and Indonesia locked out; both
##                  instruments (4 runs, ~3 h)
##    "brackets3"   added 4 Oct, after the first V32 pass: the open brackets. The coalition at 3,000 USD/ha (3,500 now works, with
##                  Brazil's first-round loss 73.7 against a switching cost of 73.4, and nothing fails below it); the EU + China club
##                  at 0.75 % (0.87 % works, nothing fails below it); the coalition at 8,000 USD/ha at the doubled switching cost
##                  (6,000 fails, nothing works above it); and the club at 0.75 % at the halved switching cost (0.5 % hit the round
##                  cap with Brazil inside, 1 % works) (4 runs, ~3 h)
##    "brackets4"   added 4 Oct evening, after brackets3: the coalition at 3,000 USD/ha WORKS (Brazil's first-round loss 64 < 73, but the
##                  round-3 coalition of 18 charges it 222 and it joins in round 4; 18 members with China inside, 12.65 Mha), so the
##                  surcharge bracket is still open below: 2,500 and 2,000; and at the doubled switching cost 8,000 fails with Brazil's
##                  first-round loss 143 against 147, so 9,000 (3 runs, ~2.5 h). The EU + China club at 0.75 % fails (0.87 works) and the
##                  club at 0.75 % at the halved cost works: those two brackets are closed.
##    "japan"       one-deviation test of Japan joining the 1.5 % club alone (Japan is the only outsider of that club not in the
##                  stability_scope of the "stability" block): dynamics off, no member test, one solve (~10 min). Written to
##                  Stability_*_seedSminclubYjapan_*.txt; the figure pipeline reads it as a second table of the same run
##    "brackets5"   added 7 Oct, after brackets4: 2,500 and 2,000 USD/ha both WORK (Brazil's first-round loss 55 and 45 < 73; the
##                  round-3 importers charge it 0.20 / 0.19 bn and it joins in round 4), so the surcharge still has no failing run
##                  below. A chain: 1,500, then 1,000 if 1,500 works, then 500 if 1,000 works (the EU + China seed fails at 500 and
##                  works at 1,000, so the EU-alone floor should be in between). Stops at the first run that fails (1-3 runs, ~1 h each)
##    "coalition_outsiders"  added 7 Oct: one-deviation test of the outsiders of the 4,000 coalition that the "stability" block did
##                  not test (the 12 regions outside stability_scope: Japan, Korea, the UK, Russia, the Middle East, North Africa, South
##                  Asia, Myanmar, Oceania, Southern Africa, Western Africa, rest of world), each joining alone: dynamics off, no member
##                  test, one solve per region (~2 h). Written to Stability_*_seedSmincoalitionXouts_*.txt; the pipeline merges it
##                  into the coalition's stability table as it does the Japan file
##  45-47 runs, about 32 h. Summary: 4_DB/V32_runs_<date>.txt, one line per run with members, hectares kept and leaked, and the
##  EV of the key regions on both measures (net = the decision measure, gross = GTAP's EV).
## =====================================================================================
library("rstudioapi")

blocks          <- c("core", "brackets", "complement", "penalty_up", "stability", "brackets2", "plane", "sensitivity", "alliance", "brackets3", "brackets4", "japan", "brackets5", "coalition_outsiders")   # the blocks already run are reused if their csv exists
stability_scope <- "brasil,argentina,paraguay,uruguay,china,indonesia,malasya,ivorycoast,ghana,colombia,us,india,seasia,bolivia,nigeria,drc,angola,cafr,venezuela"
Y <- 1.5; X <- 4000                       # the EU-alone minima found on 30 Sept (penalty %, surcharge USD/ha)

main <- function(blocks, stability_scope, Y, X) {
  force(blocks); force(stability_scope); force(Y); force(X)   # local copies: the game script clears the global environment
  script_folder <- dirname(getSourceEditorContext()$path)
  game_script   <- file.path(script_folder, "CGE_Game_Theory_GTAPAEZ_all_V32.R")
  parent_folder <- dirname(script_folder)
  log_file      <- file.path(parent_folder, "3_Output", "overnight_log.txt")
  result_file   <- file.path(parent_folder, "4_DB", paste0("V32_runs_", format(Sys.Date()), ".txt"))
  two_stage <- file.path(parent_folder, "3_Output", "Baseline_2stage_bau5_eta0.66")
  if (!file.exists(file.path(two_stage, "A_bau", "gdata_bau.upd")) || !file.exists(file.path(two_stage, "B_eudr", "NATDEF_B.sl4")))
    stop("run 1_Code/Baseline_2stage.R first (Stages A and B): ", two_stage)
  if (!file.exists(game_script)) stop("game script not found: ", game_script)

  base <- list(tau_scope = "charged", eudr_in_loop = "none", approach = "Friction",
               friction = 0.001, friction_base = "trade", friction_floor = 2,
               dynamics = "on", stability = FALSE, stability_scope = "all", min_face = 7,
               solve_mode = "accurate", max_pass = 2, join_rule = "experience", max_rounds = 15, bau_horizon = 5, bau_eta = 0.66,
               seed = "eu27", seed_name = "EU", tmsf_sheet = "AVE_pha400", tau = 0, safeguard = "baseline", locked_out = "",
               start_from = "bau", eudr_outsiders = "keep", member_pin = "all",   # V30 settings of the 30 Sept - 1 Oct runs
               welfare = "ev_net_wedge")                                          # V31

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
           if (identical(cfg$welfare, "ev_net_wedge")) "_wnet" else "", "_v32")   # V32
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
    folder <- file.path(parent_folder, "3_Output", cfg$approach, run_tag_of(cfg), "Scenario_D")
    summ <- file.path(folder, "Run_summary.txt")
    outcome <- if (file.exists(summ)) sub("^outcome: ", "", grep("^outcome:", readLines(summ, warn = FALSE), value = TRUE)[1]) else if (last < cfg$max_rounds - 1) "converged" else "stopped at the round cap"
    g0 <- read_decomp(folder, 0); g1 <- read_decomp(folder, last)
    gross <- if (!is.null(g0) && !is.null(g1)) setNames(g1$ev_gross[match(names(ev1), g1$region)] - g0$ev_gross[match(names(ev1), g0$region)], names(ev1)) else NULL
    key <- c("brasil", "china", "eu27", "us", "nigeria", "ivorycoast", "malasya", "drc", "bolivia", "angola")
    list(members = members, outsiders = outsiders, n = length(members), iterations = last, outcome = outcome, converged = startsWith(outcome, "converged"),
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

  coalition <- function(price, seed = "eu27", name = "EU", ...) modifyList(base, list(price_ha = price, tau = 0, seed = seed, seed_name = name, ...))
  club      <- function(tau, seed = "eu27", name = "EU", ...)   modifyList(base, list(price_ha = 0, tau = tau, seed = seed, seed_name = name, ...))
  MERCOSUR  <- "eu27,brasil,argentina,paraguay,uruguay"
  runs <- list(
    ## core
    club_Y              = club(Y),
    coalition_X         = coalition(X),
    mercosur_0          = coalition(0, MERCOSUR, "EUMercosur"),
    euchina_club_1.12   = club(1.12, "eu27,china", "EUChina"),
    ## brackets and the remaining seeds
    club_1.25           = club(1.25),
    coalition_3500      = coalition(3500),
    euchina_club_0.87   = club(0.87, "eu27,china", "EUChina"),
    euchina_coal_1000   = coalition(1000, "eu27,china", "EUChina"),
    euchina_coal_500    = coalition(500, "eu27,china", "EUChina"),
    mercosurchina_0     = coalition(0, paste0(MERCOSUR, ",china"), "EUMercosurChina"),
    ## complement: lock-outs and the exchange rate
    club_Y_lockbrasil       = club(Y, locked_out = "brasil"),
    coalition_X_lockbrasil  = coalition(X, locked_out = "brasil"),
    club_Y_lockus           = club(Y, locked_out = "us"),
    coalition_X_lockus      = coalition(X, locked_out = "us"),
    tau0.75_at_pha2000      = modifyList(base, list(price_ha = 2000, tau = 0.75)),
    tau0.5_at_pha2000       = modifyList(base, list(price_ha = 2000, tau = 0.5)),
    tau1.12_at_pha1000      = modifyList(base, list(price_ha = 1000, tau = 1.12)),
    tau0.87_at_pha1000      = modifyList(base, list(price_ha = 1000, tau = 0.87)),
    ## a higher penalty, and Bolivia in the Mercosur seed
    club_2.5            = club(2.5),
    club_5              = club(5),
    mercosur5_0         = coalition(0, paste0(MERCOSUR, ",bolivia"), "EUMercosur5"),
    ## brackets, second pass (2 Oct)
    club_1              = club(1),
    club_0.75           = club(0.75),
    tau0.62_at_pha1000  = modifyList(base, list(price_ha = 1000, tau = 0.62)),
    ## plane
    coalition_6000      = coalition(6000),
    ## switching-cost sensitivity, at the values the V30 searches found
    club_1_fr0.0005         = club(1,    friction = 0.0005),
    club_0.5_fr0.0005       = club(0.5,  friction = 0.0005),
    coalition_1000_fr0.0005 = coalition(1000, friction = 0.0005),
    coalition_500_fr0.0005  = coalition(500,  friction = 0.0005),
    club_2.5_fr0.002        = club(2.5,  friction = 0.002),
    club_2_fr0.002          = club(2,    friction = 0.002),
    coalition_4000_fr0.002  = coalition(4000, friction = 0.002),
    coalition_6000_fr0.002  = coalition(6000, friction = 0.002),
    ## Referee #4: a conservative alliance (US + China out), and Indonesia out
    club_Y_lockus_china        = club(Y, locked_out = "us,china"),
    coalition_X_lockus_china   = coalition(X, locked_out = "us,china"),
    club_Y_lockindonesia       = club(Y, locked_out = "indonesia"),
    coalition_X_lockindonesia  = coalition(X, locked_out = "indonesia"),
    ## brackets, third pass (4 Oct): the open sides
    coalition_3000             = coalition(3000),
    euchina_club_0.75          = club(0.75, "eu27,china", "EUChina"),
    coalition_8000_fr0.002     = coalition(8000, friction = 0.002),
    club_0.75_fr0.0005         = club(0.75, friction = 0.0005),
    ## brackets, fourth pass (4 Oct evening): below 3,000 and above 8,000
    coalition_2500             = coalition(2500),
    coalition_2000             = coalition(2000),
    coalition_9000_fr0.002     = coalition(9000, friction = 0.002),
    ## brackets, fifth pass (7 Oct): the floor of the surcharge, run as a chain (see the "brackets5" block)
    coalition_1500             = coalition(1500),
    coalition_1000             = coalition(1000),
    coalition_500              = coalition(500))
  blocks_def <- list(
    core        = c("club_Y", "coalition_X", "mercosur_0", "euchina_club_1.12"),
    brackets    = c("club_1.25", "coalition_3500", "euchina_club_0.87", "euchina_coal_1000", "euchina_coal_500", "mercosurchina_0"),
    complement  = c("club_Y_lockbrasil", "coalition_X_lockbrasil", "club_Y_lockus", "coalition_X_lockus", "tau0.75_at_pha2000", "tau0.5_at_pha2000", "tau1.12_at_pha1000", "tau0.87_at_pha1000"),
    penalty_up  = c("club_2.5", "club_5", "mercosur5_0"),
    brackets2   = c("club_1", "club_0.75", "tau0.62_at_pha1000"),
    plane       = c("coalition_6000"),
    sensitivity = c("club_1_fr0.0005", "club_0.5_fr0.0005", "coalition_1000_fr0.0005", "coalition_500_fr0.0005", "club_2.5_fr0.002", "club_2_fr0.002", "coalition_4000_fr0.002", "coalition_6000_fr0.002"),
    alliance    = c("club_Y_lockus_china", "coalition_X_lockus_china", "club_Y_lockindonesia", "coalition_X_lockindonesia"),
    brackets3   = c("coalition_3000", "euchina_club_0.75", "coalition_8000_fr0.002", "club_0.75_fr0.0005"),
    brackets4   = c("coalition_2500", "coalition_2000", "coalition_9000_fr0.002"),
    brackets5   = c("coalition_1500", "coalition_1000", "coalition_500"))   # run as a chain: the next one only if the previous works
  cat(paste0("== V32 runs, ", format(Sys.time()), " - welfare = ev_net_wedge | start_from = bau, eudr_outsiders = keep, member_pin = all | blocks: ", paste(blocks, collapse = " "), "\n"), file = result_file, append = TRUE)
  done <- list()
  for (blk in blocks) {
    cat(paste0("== block ", blk, "\n"), file = result_file, append = TRUE)
    if (blk == "stability") {   # one-deviation tests of the converged core clubs (dynamics off, S = the final members)
      for (nm in blocks_def$core) {
        r <- done[[nm]]; if (is.null(r)) r <- read_result(runs[[nm]])
        if (is.null(r) || !r$converged) { print(paste("no converged run for the stability test of", nm)); next }
        cfg <- modifyList(runs[[nm]], list(seed = paste(r$members, collapse = ","), seed_name = paste0("Smin", gsub("[^A-Za-z0-9]", "", nm)), dynamics = "off", stability = TRUE, stability_scope = stability_scope))
        run_one(paste0("stability of ", nm, " (", r$n, " members)"), cfg)
      }
      next
    }
    if (blk == "brackets5") {   # 7 Oct: the floor of the surcharge - each run only if the one above it works (Brazil inside at convergence)
      for (nm in blocks_def$brackets5) {
        r <- run_one(nm, runs[[nm]]); done[[nm]] <- r
        if (is.null(r) || !("brasil" %in% r$members)) { msg <- paste("brackets5:", nm, if (is.null(r)) "failed to run" else "fails (Brazil outside) - the floor is bracketed, no lower run needed"); print(msg); cat(msg, "\n", file = result_file, append = TRUE); break }
      }
      next
    }
    if (blk == "coalition_outsiders") {   # 7 Oct: the outsiders of the 4,000 coalition that the stability block did not test, each joining alone
      r <- done[["coalition_X"]]; if (is.null(r)) r <- read_result(runs[["coalition_X"]])
      if (is.null(r) || !r$converged) { print("no converged coalition_X for the outsiders test"); next }
      untested <- setdiff(r$outsiders, c(trimws(strsplit(stability_scope, ",")[[1]]), "eu27"))
      if (length(untested) == 0) { print("every outsider of coalition_X is in stability_scope: nothing to test"); next }
      cfg <- modifyList(runs[["coalition_X"]], list(seed = paste(r$members, collapse = ","), seed_name = "SmincoalitionXouts", dynamics = "off", stability = TRUE,
                                                     stability_scope = paste(untested, collapse = ","), stability_members = "none"))
      run_one(paste0("stability of coalition_X: ", length(untested), " untested outsiders joining alone (", paste(untested, collapse = " "), ")"), cfg)
      next
    }
    if (blk == "japan") {   # 4 Oct: Japan joining the 1.5 % club alone - one solve, no member test
      r <- done[["club_Y"]]; if (is.null(r)) r <- read_result(runs[["club_Y"]])
      if (is.null(r) || !r$converged) { print("no converged club_Y for the Japan test"); next }
      if ("japan" %in% r$members) { print("Japan is a member of club_Y: nothing to test"); next }
      cfg <- modifyList(runs[["club_Y"]], list(seed = paste(r$members, collapse = ","), seed_name = "SminclubYjapan", dynamics = "off", stability = TRUE, stability_scope = "japan", stability_members = "none"))
      run_one("stability of club_Y: Japan joining alone", cfg)
      next
    }
    if (is.null(blocks_def[[blk]])) { print(paste("unknown block", blk)); next }
    for (nm in blocks_def[[blk]]) done[[nm]] <- run_one(nm, runs[[nm]])
  }
  print(paste("done - see", result_file))
}
main(blocks, stability_scope, Y, X)
