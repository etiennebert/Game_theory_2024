## =====================================================================================
##  Run_minimum.R  -  finds the LOWEST conditions at which the club and the coalition work, by bisection on real runs.
##
##  "Works" = the regions of must_include (Brazil by default) end inside the final coalition of a run started from the EU
##  alone. Three searches, each one a sequence of full game runs (CGE_Game_Theory_GTAPAEZ_all_V26.R, one run = 3 to 10
##  accurate solves) where the next value is chosen from the result of the previous one:
##    1. club      : no footprint charge (price 0), flat penalty tau on the 17 charged sectors - the lowest tau (%)
##    2. coalition : footprint charge only, no penalty - the lowest price (USD/ha), any price through price_ha (V26)
##    3. carbon    : carbon charge only - the lowest carbon price (USD/tCO2), through co2_price (V26); slow (15 min per solve)
##  plus one run of the seeded coalition (EU + Mercosur) at price 0 and no penalty: does it hold with no charge at all?
##  Each search: start value, then steps up until a value works (or down until one fails), then bisection until the bracket
##  is narrower than tol. Every run is logged to 3_Output/overnight_log.txt as usual and summarised in
##  4_DB/Minimum_search_<date>.txt (value, works, members, forest, EV). Runs land in the usual folders, so a value that has
##  already been run (e.g. tau 5 or 7 on the sheet night) is NOT reused: delete a search or move its start if you want to skip.
##
##  Expected without the EUDR (from the rounds of 19-20 Sept). Friction 0.1 % of the charged trade (Brazil's threshold 73 M USD):
##  club about 1 %, coalition about 2 600 USD/ha (searches start at 2 % and 3 000). Realistic sheet (Brazil 581): club between
##  5.5 and 6 %, coalition around 4 000 USD/ha if China joins first (searches start at 6 % and 4 000). Carbon: 25-50 USD/tCO2.
##  Timing: club 3 runs x 25-30 min, coalition 3-4 runs x 20-30 min, seeded 15 min: about 3.5 hours; carbon 2-3 runs x 1.5-2 h.
## =====================================================================================
library("rstudioapi")

threshold_rule <- 0.001        # 0.001 = uniform friction, 0.1 % of the region's trade in the 17 charged commodities (V25: Brazil 73, China 215, EU 227 M USD) | "sheet" = Realistic_wi_china thresholds
must_include   <- c("brasil")  # the run works when these regions end inside (e.g. c("brasil", "indonesia") for the carbon charge)
searches       <- c("club", "coalition", "seeded0")   # in this order ("carbon" = the carbon-price search, left out)

main <- function(threshold_rule, must_include, searches) {
  script_folder <- dirname(getSourceEditorContext()$path)
  game_script   <- file.path(script_folder, "CGE_Game_Theory_GTAPAEZ_all_V26.R")
  parent_folder <- dirname(script_folder)
  log_file      <- file.path(parent_folder, "3_Output", "overnight_log.txt")
  result_file   <- file.path(parent_folder, "4_DB", paste0("Minimum_search_", format(Sys.Date()), ".txt"))
  dir.create(dirname(log_file), recursive = TRUE, showWarnings = FALSE)

  base <- list(tau_scope = "charged", eudr_in_loop = "none",
               approach = if (identical(threshold_rule, "sheet")) "Realistic_wi_china" else "Friction",
               friction = threshold_rule, friction_base = "trade", friction_floor = 2,
               dynamics = "on", stability = FALSE, stability_scope = "all", bau_outsiders = "cover", min_face = 7,
               solve_mode = "accurate", max_pass = 2, join_rule = "consecutive", bau_horizon = 5, bau_eta = 0.66,
               seed = "eu27", seed_name = "EU", tmsf_sheet = "AVE_pha400", tau = 0)

  run_tag_of <- function(cfg) {   # mirror of the game script's run_tag (V17-V26)
    label <- if (!is.null(cfg$price_ha)) paste0("pha", format(cfg$price_ha, scientific = FALSE)) else
             if (!is.null(cfg$co2_price)) paste0("co2_", format(cfg$co2_price, scientific = FALSE)) else sub("^AVE_", "", cfg$tmsf_sheet)
    paste0("forest_", label, "_tau", cfg$tau, if (cfg$tau > 0) cfg$tau_scope else "", "_eudr0_bau", cfg$bau_horizon, "_eta", cfg$bau_eta,
           "_seed", cfg$seed_name, if (cfg$dynamics == "off") "_fixed" else "", "_out", cfg$bau_outsiders,
           if (!identical(cfg$friction, "sheet")) paste0("_fr", format(cfg$friction, scientific = FALSE), cfg$friction_base) else "")
  }

  read_result <- function(cfg) {   # the run's aggregated csv -> members, forest, EV of the final coalition
    f <- file.path(parent_folder, "4_DB", paste0("Database_GTAPAEZ_all_results_2024_agg_", run_tag_of(cfg), ".csv"))
    if (!file.exists(f)) return(NULL)
    d <- read.csv(f, stringsAsFactors = FALSE)
    last <- max(d$Iteration); d0 <- d[d$Iteration == 0, ]; d1 <- d[d$Iteration == last, ]
    ev0 <- setNames(d0$EV, d0$Country); ev1 <- setNames(d1$EV, d1$Country)
    members <- sort(d1$Country[d1$Club == "inside"])
    list(members = members, n = length(members), iterations = last, converged = last < 24,
         works = all(must_include %in% members),
         forest_Mha = (sum(d1$Tropical) - sum(d0$Tropical)) / 1e6,
         world = sum(ev1) - sum(ev0), brasil = unname(ev1["brasil"] - ev0["brasil"]), china = unname(ev1["china"] - ev0["china"]),
         eu27 = unname(ev1["eu27"] - ev0["eu27"]), indonesia = unname(ev1["indonesia"] - ev0["indonesia"]))
  }

  run_one <- function(label, x, cfg) {   # one full game run; returns TRUE / FALSE (works) or NA (the run failed)
    assign("run_config", c(cfg, script_path = game_script), envir = globalenv())
    msg <- paste(format(Sys.time()), "START", label, "=", x, ":", paste(names(cfg), unlist(cfg), sep = "=", collapse = " "))
    cat(msg, "\n"); cat(msg, "\n", file = log_file, append = TRUE)
    t0  <- Sys.time()
    res <- tryCatch({ source(game_script, local = FALSE); "OK" }, error = function(e) paste("ERROR:", conditionMessage(e)))
    r   <- if (res == "OK") read_result(cfg) else NULL
    line <- if (is.null(r)) paste(label, x, "run failed:", res) else
      sprintf("%-10s %8s  works=%-5s members=%2d converged=%-5s forest=%+.2f Mha  dEV world=%+.0f brasil=%+.0f china=%+.0f eu27=%+.0f indonesia=%+.0f  | %s",
              label, x, r$works, r$n, r$converged, r$forest_Mha, r$world, r$brasil, r$china, r$eu27, r$indonesia, paste(r$members, collapse = " "))
    msg <- paste(format(Sys.time()), "END  ", label, "=", x, res, "-", round(as.numeric(difftime(Sys.time(), t0, units = "mins"))), "min |", line)
    cat(msg, "\n"); cat(msg, "\n", file = log_file, append = TRUE); cat(line, "\n", file = result_file, append = TRUE)
    if (is.null(r)) NA else r$works
  }

  search <- function(label, make_cfg, start, step, min_x, max_x, tol, digits) {
    ## bracket: from start, step up until a value works (or down until one fails); then bisect the bracket down to tol
    x <- start; ok <- run_one(label, x, make_cfg(x)); if (is.na(ok)) return(paste(label, ": the run at", x, "failed, search stopped"))
    lo <- NA; hi <- NA               # lo = highest value that fails, hi = lowest value that works
    if (ok) hi <- x else lo <- x
    while (is.na(lo) || is.na(hi)) {
      x <- if (is.na(lo)) round(hi - step, digits) else round(lo + step, digits)
      if (x < min_x || x > max_x) break
      ok <- run_one(label, x, make_cfg(x)); if (is.na(ok)) break
      if (ok) hi <- x else lo <- x
    }
    while (!is.na(lo) && !is.na(hi) && (hi - lo) > tol + 1e-9) {
      x <- round((lo + hi) / 2, digits); if (x <= lo || x >= hi) break
      ok <- run_one(label, x, make_cfg(x)); if (is.na(ok)) break
      if (ok) hi <- x else lo <- x
    }
    if (!is.na(lo) && !is.na(hi)) paste0(label, ": lowest working value between ", lo, " (fails) and ", hi, " (works)") else
    if (is.na(hi)) paste0(label, ": nothing works up to ", max(lo, start, na.rm = TRUE)) else paste0(label, ": works at every value tested down to ", hi)
  }

  sheet <- identical(threshold_rule, "sheet")   # start values: near the expected minimum of each threshold rule
  cat(paste0("== Minimum search, ", format(Sys.time()), ", thresholds: ", threshold_rule, ", must end inside: ", paste(must_include, collapse = " "), "\n"), file = result_file, append = TRUE)
  out <- character(0)
  for (s in searches) {
    out <- c(out, switch(s,
      club      = search("club_tau", function(x) modifyList(base, list(price_ha = 0, tau = x)),  start = if (sheet) 6 else 2,       step = if (sheet) 1 else 0.5,    min_x = 0.5, max_x = 12,    tol = if (sheet) 0.5 else 0.25, digits = 2),
      coalition = search("price_ha", function(x) modifyList(base, list(price_ha = x, tau = 0)),  start = if (sheet) 4000 else 3000, step = if (sheet) 2000 else 1000, min_x = 500, max_x = 12000, tol = 500, digits = -2),
      carbon    = search("co2",      function(x) modifyList(base, list(co2_price = x, tau = 0)), start = 50,   step = 25,   min_x = 10,  max_x = 190,   tol = 25,  digits = 0),
      seeded0   = { ok <- run_one("seeded0", 0, modifyList(base, list(price_ha = 0, tau = 0, seed = "eu27,brasil,argentina,paraguay,uruguay", seed_name = "EUMercosur")))
                    paste0("seeded coalition at price 0, no penalty: ", if (isTRUE(ok)) "holds (Brazil stays without any charge)" else if (isFALSE(ok)) "does not hold" else "run failed") },
      paste("unknown search", s)))
    cat(paste0("== ", out[length(out)], "\n"), file = result_file, append = TRUE)
  }
  if (exists("run_config", envir = globalenv())) rm("run_config", envir = globalenv())
  cat("\n== RESULTS ==\n", paste(out, collapse = "\n"), "\n")
  invisible(out)
}

main(threshold_rule, must_include, searches)
