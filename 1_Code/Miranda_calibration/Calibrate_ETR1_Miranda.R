## =====================================================================================
##  Calibrate_ETR1_Miranda.R  -  the Miranda et al. (2024) land-supply elasticities in the GTAP-AEZ v12 model
##  (19 October 2026; 20 October: diagnostics options and the degenerate-sector rule; lives in 1_Code/Miranda_calibration/,
##   writes to 3_Output/Miranda_calibration<run_label>/)
##
##  Background. The 2023 parameter file (v10 data base, 37 regions, header ETL1, kept here as
##  default_2023_v10_miranda.prm) carries the Miranda elasticities, plugged in directly as the CET elasticity
##  of transformation between forestry and agriculture (ETRAEL1 = -epsilon) for 12 producer regions, -0.2
##  elsewhere. The v12 model (gtapv7-aez.tab) reads that parameter from header ETR1 of the parameter file if
##  the header exists and uses -0.25 otherwise; in/default.prm has no ETR1, so every v12 run so far used -0.25.
##
##  What the script does.
##   1. Builds ETR1 for the v12 sets (18 AEZs x 42 regions) from the 2023 file: AEZ New<n> -> AEZ<n>; regions
##      by name; AngDRC -> Angola and DRC; SSA -> WAfr, CAfr, EAfr, SAfr; MENA -> MENA and NAfr. A cell whose
##      2023 value is not the 2023 default (-0.2) is a Miranda cell: its target is epsilon_target = -value.
##   2. Calibrates ETRAEL1 in the Miranda cells so that the MODEL's response of agricultural land to a 1 % rise
##      in the producer price of every agricultural activity of the region equals epsilon_target, which is what
##      Miranda et al. estimate (agricultural land area against a commodity price index). Agricultural land is
##      measured as the land services the CET allocates to the 11 agricultural activities of the cell (qes,
##      rent-weighted), i.e. the quantity ETRAEL1 governs; the cover response (cropland + pasture hectares of
##      the cover block, where cropland follows harvested area and the balance is booked to forest through
##      areaadjust) is reported for information only, since it is not monotonic in ETRAEL1 and went negative
##      in 12 cells in the run of 19 October. One pass = one solve per target region from the 2019 data base:
##      a 1 % output subsidy on every agricultural activity of the region that weighs at least min_output_share
##      of its agricultural output (shock to(a,a,r) = -1; no swap, so no singular system on a tiny sector), then
##      epsilon_model(cell) = % change of agricultural land services / % change of the region's producer price
##      (po, output-weighted over the shocked activities), and
##          ETRAEL1 <- ETRAEL1 x (epsilon_target / epsilon_model)^damping, the step capped at x/÷ max_step, bounded,
##      until every Miranda cell is within `tolerance` of its target (cells pinned at a bound excepted) or
##      `max_pass` passes are done. shock_mode = "joint" does all target regions in one solve per pass (faster,
##      small cross effects).
##   3. Writes default_miranda.prm (in/default.prm + the calibrated ETR1), ETR1_calibrated.csv (every cell:
##      2023 value, target, land-services and cover elasticities of each pass, final value), and calibration_log.txt.
##      Nothing in 2_Model/in is modified; to use the file in the baseline and the game, either copy it over
##      in/default.prm (keep a copy of the original) or point `file gtapPARM =` of BU/NATDEF.cmf to it.
##
##  Needs: 2_Model/BU/NATDEF.cmf and BU/NATDEF.har (the RunGTAP backup the other scripts start from; if the
##  BU folder is in 9_Archive/0. Old model/, move it back first), HARr, rstudioapi. Run from RStudio.
## =====================================================================================
rm(list = ls())
library(HARr)
library("rstudioapi")

script_path   <- getSourceEditorContext()$path
script_folder <- dirname(script_path)                      # 1_Code/Miranda_calibration
parent_folder <- dirname(dirname(script_folder))           # the repository
GTAPAEZ_path  <- file.path(parent_folder, "2_Model/")
setwd(GTAPAEZ_path)

## ---- settings ---------------------------------------------------------------------------------------------
file_2023   <- file.path(script_folder, "default_2023_v10_miranda.prm")   # the 2023 file (header ETL1, v10 sets)
default_v12 <- "in/default.prm"                                            # the parameter file of every v12 run (no ETR1)
run_label   <- ""           # suffix of the output folder (e.g. "_drc_check" writes to 3_Output/Miranda_calibration_drc_check/ and leaves the main results alone)
out_path    <- paste0(file.path(parent_folder, "3_Output", paste0("Miranda_calibration", run_label)), "/")
only_regions <- NULL        # e.g. c("drc"): solve and calibrate these target regions only (diagnostics); NULL = every region with a Miranda cell
keep_sl4    <- FALSE        # TRUE: keep the solution file of every solve as pass_<k>/NATDEF_<region>.sl4 (11 MB each) for diagnostics
warm_start  <- NULL         # path of a previous ETR1_calibrated.csv: the passes start from its etr1_final instead of the 2023 values (e.g. the 19 October run)
max_price_move <- 3         # %: a shocked activity whose supply price moves by more than this under the 1 % subsidy is degenerate (a near-empty sector
                            # feeding on its own output: DRC paddy rice -33 %, sugar crops -8 %); it is dropped from the region's shock, the region is
                            # solved again, and the exclusion is kept for the later passes (listed in the log and in price_diag_pass<k>.csv)
shock_mode  <- "separate"   # "separate": one solve per target region and pass | "joint": one solve per pass, all target regions shocked together
solve_mode  <- "fast"       # "fast": Gragg 2-4-6, 1 subinterval (enough for a 1 % subsidy); a failed solve is retried once with automatic accuracy and 3 subintervals
subsidy_shock <- -1         # % change of the power of the output tax of the agricultural activities (negative = a subsidy that raises the producer price)
min_output_share <- 0.01    # an activity is shocked only if it weighs at least this share of the region's agricultural output (tiny sectors make the solve unstable)
max_pass    <- 4            # calibration passes (pass 0 measures the 2023 values as they are)
tolerance   <- 0.05         # stop when every Miranda cell has |epsilon_model / epsilon_target - 1| below this
damping     <- 0.8          # ETRAEL1 <- ETRAEL1 x ratio^damping
max_step    <- 4            # one pass multiplies or divides ETRAEL1 by at most this factor (the response is concave in ETRAEL1: a huge first ratio would overshoot)
bounds      <- c(-5, -0.02) # ETRAEL1 is kept inside these values
default_2023 <- -0.2        # the value the 2023 file carries where there is no Miranda estimate
agri_acts   <- c("pdr", "wht", "gro", "v_f", "osd", "c_b", "pfb", "ocr", "ruminant", "rmk", "wol")   # the land-using activities except forestry
region_map  <- list(angdrc = c("angola", "drc"), ssa = c("wafr", "cafr", "eafr", "safr"), mena = c("mena", "nafr"))   # 2023 region -> v12 regions; others by name

dir.create(out_path, recursive = TRUE, showWarnings = FALSE)
logf <- paste0(out_path, "calibration_log.txt"); cat("", file = logf)
say <- function(...) { msg <- paste0(...); print(msg); cat(msg, "\n", file = logf, append = TRUE) }

## ---- sets and base land covers ------------------------------------------------------------------------------
sets <- read_har("in/sets.har")
reg_v12 <- tolower(as.character(unlist(sets[["reg"]]))); aez_v12 <- tolower(as.character(unlist(sets[["aezs"]])))
reg_case <- as.character(unlist(sets[["reg"]])); names(reg_case) <- reg_v12          # the spelling the CMF needs
bd <- read_har("in/basedata.har")
lcov <- bd[["lcov"]]; if (length(dim(lcov)) == 4) lcov <- lcov[, , , 1]                # aez x cover x reg, 1000 ha
evfb <- bd[["evfb"]]                                                                   # endw x acts x reg, M USD (land rents by AEZ)
cov_crop <- lcov[aez_v12, "cropland", reg_v12]; cov_past <- lcov[aez_v12, "pastureland", reg_v12]; cov_forest <- lcov[aez_v12, "forestland", reg_v12]
rent_forest <- evfb[aez_v12, "forest", reg_v12]; rent_agri <- apply(evfb[aez_v12, agri_acts, reg_v12], c(1, 3), sum)
maks <- bd[["maks"]]; if (length(dim(maks)) == 4) maks <- maks[, , , 1]                   # comm x acts x reg, M USD: output of each activity
out_of <- function(r) sapply(agri_acts, function(a) maks[a, a, r])                        # output of the 11 agricultural activities in region r
excluded_acts <- list()                                                                    # per region: activities found degenerate (see max_price_move)
acts_of <- function(r) { o <- out_of(r); a <- agri_acts[o >= min_output_share * sum(o)]; setdiff(a, excluded_acts[[r]]) }   # the activities that carry the price shock

## ---- 1. ETR1 from the 2023 file -----------------------------------------------------------------------------
old <- read_har(file_2023); etl1 <- old[["etl1"]]; if (length(dim(etl1)) == 3) etl1 <- etl1[, , 1]
aez_old <- tolower(dimnames(etl1)[[1]]); reg_old <- tolower(dimnames(etl1)[[2]])
aez_num <- as.integer(sub("^[^0-9]*", "", aez_old)); if (any(is.na(aez_num))) stop("AEZ names of the 2023 file not understood: ", paste(aez_old, collapse = " "))
source_2023 <- setNames(rep(NA_character_, length(reg_v12)), reg_v12)
for (r in reg_old) { targets <- if (!is.null(region_map[[r]])) region_map[[r]] else r; for (t in targets) if (t %in% reg_v12) source_2023[t] <- r }
if (any(is.na(source_2023))) stop("no 2023 source region for: ", paste(reg_v12[is.na(source_2023)], collapse = " "))
etr1 <- matrix(NA_real_, 18, length(reg_v12), dimnames = list(AEZS = aez_v12, REG = reg_v12))
for (r in reg_v12) for (k in seq_along(aez_old)) etr1[paste0("aez", aez_num[k]), r] <- etl1[aez_old[k], source_2023[r]]
if (any(is.na(etr1))) stop("ETR1 incomplete")
is_target <- abs(etr1 - default_2023) > 1e-6                                           # a Miranda estimate in the 2023 file
eps_target <- ifelse(is_target, round(-etr1, 4), NA)
cells <- data.frame(aez = rep(aez_v12, times = length(reg_v12)), region = rep(reg_v12, each = 18), source_2023 = rep(source_2023, each = 18),
                    etr1_2023 = as.vector(etr1), eps_target = as.vector(eps_target),
                    forest_kha = as.vector(cov_forest), agri_kha = as.vector(cov_crop + cov_past), agri_rent_musd = as.vector(rent_agri),
                    forest_rent_share = as.vector(rent_forest / pmax(rent_forest + rent_agri, 1e-9)), stringsAsFactors = FALSE)
cells$calibrate <- !is.na(cells$eps_target) & cells$forest_kha > 0 & cells$agri_kha > 0 & cells$agri_rent_musd > 0 & cells$forest_rent_share > 0
say("ETR1 built from the 2023 file: ", sum(is_target), " Miranda cells in ", length(unique(cells$region[is_target])), " regions (",
    paste(unique(reg_case[cells$region[is_target]]), collapse = ", "), "); ", sum(cells$calibrate), " of them can respond in the model (forest, agriculture and a forestry rent in the cell); ",
    "every other cell carries the 2023 value ", default_2023)
skipped <- cells[!is.na(cells$eps_target) & !cells$calibrate, ]
if (nrow(skipped) > 0) say("Miranda cells kept at their 2023 value because the model cannot move land there: ", paste(skipped$region, skipped$aez, collapse = "; "))
target_regions <- unique(cells$region[cells$calibrate])
if (!is.null(only_regions)) { target_regions <- intersect(target_regions, tolower(only_regions)); if (length(target_regions) == 0) stop("only_regions matches no target region"); say("only_regions: ", paste(target_regions, collapse = ", ")) }

write_prm <- function(etr1_matrix, path) {                 # in/default.prm + ETR1 -> path (HARr round trip checked 19 Oct 2026)
  prm <- read_har(default_v12)
  x <- array(etr1_matrix, dim = c(18, length(reg_v12)), dimnames = list(AEZS = aez_v12, REG = reg_v12))
  attr(x, "description") <- "elast. of AEZ land transformation: top nest (Miranda 2024)"
  prm[["etr1"]] <- x
  write_har(prm, path, maxSize = 1e5)
  back <- read_har(path)
  if (!("etr1" %in% names(back)) || !isTRUE(all.equal(as.numeric(back[["etr1"]]), as.numeric(x), tolerance = 1e-6))) stop("ETR1 did not round-trip in ", path)
  invisible(path)
}

## ---- the solve ------------------------------------------------------------------------------------------------
bu_dir <- if (dir.exists("BU")) "BU" else stop("2_Model/BU (NATDEF.cmf, NATDEF.har of RunGTAP) is missing - move it back from 9_Archive/0. Old model/ first")
set_line <- function(lines, pattern, new) { k <- grep(pattern, lines, ignore.case = TRUE); if (length(k) > 0) lines[k[1]] <- new else lines <- append(lines, new, after = grep("Extrapolation accuracy file", lines, ignore.case = TRUE)[1]); lines }
prepare_cmf <- function(extra_lines, prm_path) {
  for (f in c("NATDEF.cmf", "NATDEF.har")) file.copy(file.path(bu_dir, f), f, overwrite = TRUE)
  shock <- read_har("NATDEF.har"); shock[["0101"]][] <- 0; write_har(shock, "NATDEF.har", maxSize = 1e4)       # no border charge
  lines <- readLines("NATDEF.cmf", warn = FALSE)
  k <- grep("^\\s*file\\s+gtapPARM\\s*=", lines, ignore.case = TRUE); if (length(k) != 1) stop("'file gtapPARM = ...' not found once in BU/NATDEF.cmf")
  p <- normalizePath(prm_path, winslash = "\\", mustWork = TRUE); lines[k] <- paste0("file gtapPARM = ", if (grepl(" ", p)) paste0('"', p, '"') else p, ";")
  cutoff <- which(lines == "! Part for productivity shocks;"); if (length(cutoff) == 0) stop("marker '! Part for productivity shocks;' not found in BU/NATDEF.cmf")
  lines <- c(lines[1:cutoff], 'Shock tms_f =  file NATDEF.har header "0101";', "! Miranda calibration: producer-price shock from R;", extra_lines)
  lines <- set_line(lines, "^!? *Method *=", "Method = Gragg;")
  lines <- set_line(lines, "^!? *Steps *=", "Steps = 2 4 6;")
  lines <- set_line(lines, "^!? *automatic accuracy *=", if (solve_mode == "fast") "automatic accuracy = no;" else "automatic accuracy = yes;")
  lines <- set_line(lines, "^!? *subintervals *=", if (solve_mode == "fast") "subintervals = 1;" else "subintervals = 3;")
  lines <- set_line(lines, "Extrapolation accuracy file", "Extrapolation accuracy file = NO ;")
  lines <- set_line(lines, "^!? *slc file *=", "slc file = no ;")
  writeLines(lines, "NATDEF.cmf"); invisible("NATDEF.cmf")
}
solve_gtap <- function(log_file) {                          # TRUE if GEMPACK wrote a new solution
  mtime_before <- file.info("NATDEF.sl4")$mtime; t0 <- Sys.time()
  status <- system2("GTAPV7-AEZ.exe", c("-cmf", "NATDEF.CMF"), stdout = log_file, stderr = log_file)
  ok <- identical(as.integer(status), 0L) && !identical(file.info("NATDEF.sl4")$mtime, mtime_before)
  say("   ", if (ok) "solved" else "FAILED", " in ", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), " min (", basename(log_file), ")")
  ok
}
solve_region_group <- function(g, prm_pass, pass_dir) {       # fast first, then once more with automatic accuracy; FALSE if both fail
  tag <- paste(g, collapse = "_")
  prepare_cmf(price_lines(g), prm_pass)
  if (solve_gtap(paste0(pass_dir, "Solve_", tag, ".log"))) { file.copy("NATDEF.cmf", paste0(pass_dir, "NATDEF_", tag, ".cmf"), overwrite = TRUE); return(TRUE) }
  solve_mode <<- "accurate"; prepare_cmf(price_lines(g), prm_pass); solve_mode <<- "fast"
  ok <- solve_gtap(paste0(pass_dir, "Solve_", tag, "_accurate.log")); file.copy("NATDEF.cmf", paste0(pass_dir, "NATDEF_", tag, ".cmf"), overwrite = TRUE)
  if (!ok) say("   ", tag, ": both solves failed - its cells keep their current value; see the two logs")
  ok
}
price_lines <- function(regions) unlist(lapply(regions, function(r) { a <- acts_of(r)
  sprintf('shock to("%s","%s","%s") = %s;', a, a, reg_case[r], format(subsidy_shock, scientific = FALSE)) }))
agri_response <- function(sol, regions) {                   # epsilon_model = % change of the cell's agricultural land services / % change of the region's producer price
  qs <- sol[["qes"]]; if (length(dim(qs)) == 4) qs <- qs[, , , 1]                   # land services supplied to each activity, % (the quantity the CET moves)
  pl <- sol[["p_landcover_l"]]; if (length(dim(pl)) == 4) pl <- pl[, , , 1]          # covers, % (information only)
  po <- sol[["po"]]; if (length(dim(po)) == 3) po <- po[, , 1]
  out <- NULL
  for (r in regions) { a <- acts_of(r); w <- out_of(r)[a]; dpo <- sum(w * po[a, r]) / sum(w)          # producer price of the shocked activities, output-weighted, %
    w_land <- evfb[aez_v12, agri_acts, r]                                                             # base land rents of the 11 agricultural activities, by AEZ
    land_serv  <- rowSums(w_land * qs[aez_v12, agri_acts, r]) / pmax(rowSums(w_land), 1e-9)         # rent-weighted qes = the CET's agricultural land of the AEZ, %
    land_cover <- (cov_crop[, r] * pl[aez_v12, "cropland", r] + cov_past[, r] * pl[aez_v12, "pastureland", r]) / pmax(cov_crop[, r] + cov_past[, r], 1e-9)
    if (!is.finite(dpo) || abs(dpo) < 1e-4) { say("   ", r, ": the producer price did not move (", signif(dpo, 3), " %) - no elasticity measured"); land_serv[] <- NA; land_cover[] <- NA }
    out <- rbind(out, data.frame(aez = aez_v12, region = r, eps_model = land_serv / dpo, eps_cover = land_cover / dpo, dpo = dpo, stringsAsFactors = FALSE)) }
  out
}

price_diag <- function(sol, regions, pass) {                 # one row per agricultural activity of the regions solved: the prices and quantities behind dpo
  ps <- sol[["ps"]]; if (length(dim(ps)) == 4) ps <- ps[, , , 1]
  po <- sol[["po"]]; if (length(dim(po)) == 3) po <- po[, , 1]
  qo <- sol[["qo"]]; if (length(dim(qo)) == 3) qo <- qo[, , 1]
  qxw <- sol[["qxw"]]; if (length(dim(qxw)) == 3) qxw <- qxw[, , 1]
  out <- NULL
  for (r in regions) { a <- acts_of(r); o <- out_of(r)
    out <- rbind(out, data.frame(pass = pass, region = r, activity = agri_acts, shocked = agri_acts %in% a, excluded = agri_acts %in% excluded_acts[[r]],
                                 output_share = round(o / sum(o), 4), ps_pct = round(sapply(agri_acts, function(k) ps[k, k, r]), 4), po_pct = round(po[agri_acts, r], 4),
                                 qo_pct = round(qo[agri_acts, r], 4), qxw_pct = round(qxw[agri_acts, r], 3), stringsAsFactors = FALSE)) }
  out
}
degenerate_acts <- function(sol, regions) {                  # shocked activities whose supply price moved by more than max_price_move %
  ps <- sol[["ps"]]; if (length(dim(ps)) == 4) ps <- ps[, , , 1]
  out <- list()
  for (r in regions) { a <- acts_of(r); if (length(a) == 0) next; x <- sapply(a, function(k) ps[k, k, r]); bad <- a[is.finite(x) & abs(x) > max_price_move]
    if (length(bad) > 0) out[[r]] <- setNames(round(x[bad], 2), bad) }
  out
}

## ---- 2. the passes ----------------------------------------------------------------------------------------------
current <- etr1
if (!is.null(warm_start)) {                                                                # start from the final values of a previous run
  ws <- read.csv(warm_start, stringsAsFactors = FALSE); ws <- ws[ws$calibrate %in% c(TRUE, "TRUE") & is.finite(ws$etr1_final), ]
  idx_ws <- cbind(match(ws$aez, aez_v12), match(ws$region, reg_v12)); ok_ws <- !is.na(idx_ws[, 1]) & !is.na(idx_ws[, 2])
  current[idx_ws[ok_ws, , drop = FALSE]] <- pmin(pmax(ws$etr1_final[ok_ws], bounds[1]), bounds[2])
  say("warm start from ", warm_start, ": ", sum(ok_ws), " calibrated cells start from their previous final value")
}
for (pass in 0:max_pass) {
  pass_dir <- paste0(out_path, "pass_", pass, "/"); dir.create(pass_dir, showWarnings = FALSE)
  prm_pass <- write_prm(current, paste0(pass_dir, "default_miranda_pass", pass, ".prm"))
  say("pass ", pass, ": ETRAEL1 of the Miranda cells between ", round(min(current[is_target]), 3), " and ", round(max(current[is_target]), 3), " - solving (", shock_mode, ")")
  groups <- if (shock_mode == "joint") list(target_regions) else as.list(target_regions)
  resp <- NULL
  diag <- NULL
  for (g in groups) {
    if (!solve_region_group(g, prm_pass, pass_dir)) next
    sol <- read_SL4("NATDEF.sl4")
    bad <- degenerate_acts(sol, g)                                                       # degenerate sectors: drop them from the shock and solve the group again
    if (length(bad) > 0) {
      for (r in names(bad)) { excluded_acts[[r]] <- union(excluded_acts[[r]], names(bad[[r]]))
        say("   ", r, ": ", paste0(names(bad[[r]]), " (ps ", sprintf("%+.1f", bad[[r]]), " %)", collapse = ", "), " move by more than ", max_price_move, " % under a 1 % subsidy - degenerate, excluded from the shock; solving again") }
      if (!solve_region_group(g, prm_pass, pass_dir)) next
      sol <- read_SL4("NATDEF.sl4")
      still <- degenerate_acts(sol, g); if (length(still) > 0) say("   still degenerate after the exclusion: ", paste(unlist(lapply(names(still), function(r) paste(r, names(still[[r]])))), collapse = "; "))
    }
    if (keep_sl4) file.copy("NATDEF.sl4", paste0(pass_dir, "NATDEF_", paste(g, collapse = "_"), ".sl4"), overwrite = TRUE)
    diag <- rbind(diag, price_diag(sol, g, pass)); resp <- rbind(resp, agri_response(sol, g))
  }
  if (!is.null(diag)) write.csv(diag, paste0(pass_dir, "price_diag_pass", pass, ".csv"), row.names = FALSE)
  if (is.null(resp)) stop("no solve succeeded in pass ", pass)
  m <- match(paste(cells$aez, cells$region), paste(resp$aez, resp$region))
  cells[[paste0("eps_model_pass", pass)]] <- resp$eps_model[m]; cells[[paste0("eps_cover_pass", pass)]] <- resp$eps_cover[m]
  cells[[paste0("dpo_pass", pass)]] <- resp$dpo[m]; cells[[paste0("etr1_pass", pass)]] <- as.vector(current)
  k <- cells$calibrate; em <- cells[[paste0("eps_model_pass", pass)]][k]; et <- cells$eps_target[k]
  ratio <- et / em; dead <- !is.finite(ratio) | is.na(em) | em <= 0
  if (any(dead)) say("   no usable response in: ", paste(cells$region[k][dead], cells$aez[k][dead], collapse = "; "), " - kept as they are")
  idx <- cbind(match(cells$aez[k][!dead], aez_v12), match(cells$region[k][!dead], reg_v12))
  stuck <- (abs(current[idx] - bounds[1]) < 1e-9 & ratio[!dead] > 1) | (abs(current[idx] - bounds[2]) < 1e-9 & ratio[!dead] < 1)   # at a bound and asking to go further
  gap <- abs(ratio[!dead] - 1)
  write.csv(cells, paste0(out_path, "ETR1_calibrated.csv"), row.names = FALSE)
  if (length(gap) == 0) { say("no cell gave a usable response in pass ", pass, " - stopping; check the solver logs and dpo in ETR1_calibrated.csv"); break }
  say("   producer price ", sprintf("%+.3f", median(resp$dpo, na.rm = TRUE)), " % (median over regions); epsilon_model / epsilon_target: median ", round(median(1 / ratio[!dead]), 3), ", range ", round(min(1 / ratio[!dead]), 3), " to ", round(max(1 / ratio[!dead]), 3),
      "; cells within ", 100 * tolerance, " %: ", sum(gap < tolerance), " of ", sum(!dead), if (any(stuck)) paste0(" (", sum(stuck), " pinned at a bound)") else "")
  if (all(gap < tolerance | stuck)) { say("converged after pass ", pass, if (any(stuck)) " (cells pinned at a bound excepted)" else ""); break }
  if (pass == max_pass) { say("stopped at max_pass = ", max_pass, " without full convergence; ETR1_calibrated.csv shows the remaining gaps"); break }
  upd <- current
  step <- pmin(pmax(ratio[!dead]^damping, 1 / max_step), max_step)                   # damped, capped multiplicative update
  upd[idx] <- pmin(pmax(current[idx] * step, bounds[1]), bounds[2])
  current <- upd
}

## ---- 3. the result ------------------------------------------------------------------------------------------------
final_prm <- write_prm(current, paste0(out_path, "default_miranda.prm"))
cells$etr1_final <- as.vector(current)
cells$at_bound <- cells$calibrate & (abs(cells$etr1_final - bounds[1]) < 1e-9 | abs(cells$etr1_final - bounds[2]) < 1e-9)
write.csv(cells, paste0(out_path, "ETR1_calibrated.csv"), row.names = FALSE)
if (any(cells$at_bound)) say("cells at a bound of ", bounds[1], " / ", bounds[2], " (the CET cannot reach the Miranda value there, usually because forestry earns almost no rent in the cell): ",
                             paste(cells$region[cells$at_bound], cells$aez[cells$at_bound], round(cells$etr1_final[cells$at_bound], 3), collapse = "; "))
say("done: ", final_prm, " (in/default.prm + header ETR1), ", paste0(out_path, "ETR1_calibrated.csv"), ", solver logs and CMFs in pass_*/")
say("to run the baseline and the game with it: copy it over 2_Model/in/default.prm (keep the original as default_v7defaults.prm) or point 'file gtapPARM =' in BU/NATDEF.cmf to it; the TAB needs no change")
