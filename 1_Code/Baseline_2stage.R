## =====================================================================================
##  Baseline_2stage.R  -  the baseline in two solves (successor of Baseline_EUDR.R, 29 Sept 2026)
##
##  Baseline_EUDR.R solves the EUDR and the business-as-usual (BAU) clearing together in ONE solve, with the
##  forest cover of the 175 BAU cells exogenous. In that solve the forest change IS the DeDuCE rate x horizon by
##  construction, so the EUDR cannot change a hectare in those cells: its effect on clearing is only visible in
##  the solved clearing incentive tinc*. This script separates the two:
##
##   Stage A "BAU"  - no EUDR. Forest cover falls by the DeDuCE clearing rate x horizon in every BAU cell
##                    (swap p_LANDCOVER_L = tinc; shock p_LANDCOVER_L = -x), the cleared hectares get their
##                    productivity (afeall shocks of Calibrate_BAU_productivity.R). The solve calibrates the
##                    clearing incentive tinc* of every cell and writes the UPDATED DATABASE gdata_bau.upd:
##                    the world after <horizon> years of clearing, with the incentives embedded as income
##                    taxes on forest land (INCTAX = EVFB - EVOS), the cover in LCOV, the areas in AREA.
##   Stage B "EUDR" - starts from gdata_bau.upd. Forest cover is ENDOGENOUS everywhere (no cover lines), tinc
##                    and afeall are exogenous and unshocked (their levels are in the data), and the EU applies
##                    the EUDR: swap qxs(c,r,"eu27") = ams(c,r,"eu27"); shock qxs = -100 s_u. The solved forest
##                    change (del_luc) is the EUDR's effect on clearing, in hectares, relative to the DeDuCE rate;
##                    the solved EV is the EUDR's welfare effect. Writes gdata_eudr.upd: the world with the EUDR
##                    in force, the starting point of a game that lets every country's forest move (V30).
##
##  Writes 3_Output/Baseline_2stage_bau<horizon>_eta<eta>/
##    A_bau/   gdata_bau.upd, bau_baseline.txt (tinc*, as before), bau_afeall.txt, Forest_LU_A_ha.txt,
##             EV_A.txt (vs the 2019 data), NATDEF_A.cmf/.sl4, Solve_A.log
##    B_eudr/  gdata_eudr.upd, ams_baseline.txt (solved ams per cut flow), Forest_LU_B_ha.txt (the EUDR's forest
##             effect by region x AEZ, ha, relative to the BAU world), EV_B.txt (the EUDR's welfare effect, M USD),
##             NATDEF_B.cmf/.sl4, Solve_B.log
##    EUDR_effect_by_region.txt  per region: BAU clearing (ha, tropical / all zones), EUDR effect (ha), EUDR effect in
##             % of the BAU clearing (negative = the EUDR accelerates clearing there, positive = it slows it), EV_B
##    EUDR_effect_by_cell.txt    the same per region x AEZ cell
##
##  Run it from RStudio like the other scripts (same folder structure). Two accurate solves, 5-6 min each; the
##  solver's screen output goes to Solve_A.log / Solve_B.log and the script stops with the solver's message if a
##  solve fails. The afeall shocks are those calibrated for the one-solve baseline (with the EUDR); the shortfall
##  check printed after Stage A says whether they need recalibrating without it (Calibrate_BAU_productivity.R
##  with eudr_scale = 0).
## =====================================================================================
rm(list = ls())
library(HARr)
library("readxl")
library("rstudioapi")

script_path <- if (nzchar(Sys.getenv("FOREST_CLUB_SCRIPT"))) Sys.getenv("FOREST_CLUB_SCRIPT") else getSourceEditorContext()$path   # FOREST_CLUB_SCRIPT: set by run_step.R when run with Rscript (no RStudio), see run_chain_v34.bat
script_folder <- dirname(script_path)
parent_folder <- dirname(script_folder)
GTAPAEZ_path <- file.path(parent_folder, "2_Model/")
external_data_path <- file.path(parent_folder, "0_External_data/")
setwd(GTAPAEZ_path)

## ---- parameters (keep them identical to Baseline_EUDR.R / Calibrate_BAU_productivity.R) ----------------
eudr_sheet  <- "shocks"   # sheet of eudr_cut_shares.xlsx: comm, source, dest, s_u (share of output from post-2020 deforestation)
eudr_scale  <- 1          # multiplies s_u: 1 = only non-compliant output is excluded; >1 = traceability scenario
solve_mode  <- "accurate" # "accurate" = Gragg 2-4-6, automatic accuracy, 3 subintervals (the only mode accurate enough for the BAU shocks)
bau_horizon <- 5          # years of business-as-usual clearing
bau_cap_pct <- 25         # a cell never loses more than this share of its forest cover over the horizon
bau_eta     <- 0.66       # productivity of the cleared hectares (bau_afeall_eta<eta>.txt from Calibrate_BAU_productivity.R); 0 = none
run_stage   <- c("A", "B")  # "A" alone recalibrates the BAU world; "B" alone reuses an existing A_bau/gdata_bau.upd
generation  <- "v34"      # V34 (23 Oct 2026): BAU clearing by the observed AEZ shares (bau_deforestation.xlsx of build_deduce_tables.py); V33 (20 Oct 2026): the Miranda-calibrated elasticities; suffix of the output folder and of the productivity file
                          # (bau_afeall_eta<eta>_<generation>.txt from Calibrate_BAU_productivity.R) so that nothing of V32 is overwritten ("" = V32)
gen_sfx     <- if (nzchar(generation)) paste0("_", generation) else ""

set_solver_lines <- function(lines, mode) {   # identical to Baseline_EUDR.R
  set_line <- function(lines, pattern, new) {
    k <- grep(pattern, lines, ignore.case = TRUE)
    if (length(k) > 0) lines[k[1]] <- new else lines <- append(lines, new, after = grep("Extrapolation accuracy file", lines, ignore.case = TRUE)[1])
    lines
  }
  lines <- set_line(lines, "^!? *Method *=",            "Method = Gragg;")
  lines <- set_line(lines, "^!? *Steps *=",             if (mode == "retry") "Steps = 4 8 12;" else "Steps = 2 4 6;")
  lines <- set_line(lines, "^!? *automatic accuracy *=", if (mode == "fast") "automatic accuracy = no;" else "automatic accuracy = yes;")
  lines <- set_line(lines, "^!? *subintervals *=",       c(fast = "subintervals = 1;", accurate = "subintervals = 3;", retry = "subintervals = 6;")[mode])
  lines <- set_line(lines, "Extrapolation accuracy file", if (mode == "fast") "Extrapolation accuracy file = NO ;" else "Extrapolation accuracy file = YES ;")
  lines <- set_line(lines, "^!? *slc file *=",           "slc file = no ;")
  lines
}
out_path <- file.path(parent_folder, "3_Output", paste0("Baseline_2stage_bau", bau_horizon, if (bau_eta > 0) paste0("_eta", bau_eta) else "", gen_sfx), "/")
out_A <- paste0(out_path, "A_bau/"); out_B <- paste0(out_path, "B_eudr/")
dir.create(out_A, recursive = TRUE, showWarnings = FALSE); dir.create(out_B, recursive = TRUE, showWarnings = FALSE)

## ---- helpers ----------------------------------------------------------------------------------------------
restore_bu <- function() for (f in c("NATDEF.cmf", "NATDEF.har", "NATDEF.sl4")) file.copy(file.path(parent_folder, "2_Model", "BU", f), file.path(GTAPAEZ_path, f), overwrite = TRUE)

prepare_cmf <- function(extra_lines, data_file = NULL) {
  ## start from the RunGTAP backup: its closure, a zero border-charge header, optionally another starting database
  for (f in c("NATDEF.cmf", "NATDEF.har")) file.copy(file.path(parent_folder, "2_Model", "BU", f), file.path(GTAPAEZ_path, f), overwrite = TRUE)
  shock <- read_har('NATDEF.har'); shock[["0101"]][] <- 0; write_har(shock, 'NATDEF.har', maxSize = 1e4)
  cmf_path <- paste0(GTAPAEZ_path, "/NATDEF.cmf")
  lines <- readLines(cmf_path, warn = FALSE)
  if (!is.null(data_file)) {                                  # Stage B: start from the updated database of Stage A
    k <- grep("^\\s*file\\s+gtapDATA\\s*=", lines, ignore.case = TRUE)
    if (length(k) != 1) stop("the line 'file gtapDATA = ...' was not found once in BU/NATDEF.cmf")
    lines[k] <- paste0("file gtapDATA = ", if (grepl(" ", data_file)) paste0('"', data_file, '"') else data_file, ";")
  }
  cutoff_line <- which(lines == "! Part for productivity shocks;")
  if (length(cutoff_line) == 0) stop("The line '! Part for productivity shocks;' was not found in BU/NATDEF.cmf")
  lines <- c(lines[1:cutoff_line], 'Shock tms_f =  file NATDEF.har header "0101";', '! Part for productivity shocks from R;', extra_lines)
  lines <- set_solver_lines(lines, solve_mode)
  writeLines(lines, cmf_path)
  cmf_path
}
updated_db_path <- function(cmf_path) {                       # where GEMPACK writes the updated database (the CMF's own line)
  lines <- readLines(cmf_path, warn = FALSE)
  k <- grep("^\\s*Updated\\s+file\\s+gtapDATA\\s*=", lines, ignore.case = TRUE)
  if (length(k) != 1) stop("the line 'Updated file gtapDATA = ...' was not found once in the CMF; add it (RunGTAP writes it) so that the updated database is saved")
  p <- trimws(sub(";.*$", "", sub("^[^=]*=", "", lines[k]))); p <- gsub('^"|"$', "", p)
  if (!grepl("^([A-Za-z]:|/|\\\\)", p)) p <- file.path(GTAPAEZ_path, p)
  p
}
solve_gtap <- function(log_file) {
  mtime_before <- file.info("NATDEF.sl4")$mtime; t0 <- Sys.time()
  status <- system2("GTAPV7-AEZ.exe", c("-cmf", "NATDEF.CMF"), stdout = log_file, stderr = log_file)
  print(paste("solve time:", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min - solver output in", log_file))
  if (!identical(as.integer(status), 0L) || identical(file.info("NATDEF.sl4")$mtime, mtime_before)) {
    cat(tail(readLines(log_file, warn = FALSE), 40), sep = "\n")
    stop("GEMPACK did not produce a new solution (exit code ", status, "). The last 40 lines of ", log_file, " are printed above.")
  }
  lg <- readLines(log_file, warn = FALSE)
  faces <- regmatches(lg, regexpr('"face" number is [0-9]+', lg)); if (length(faces) > 0) print(paste("accuracy:", paste(faces, collapse = "; ")))
  invisible(status)
}
sets <- read_har('sets.har'); region_sets <- unlist(data.frame(sets["reg"]))
aez_names <- paste0("aez", 1:18); zone_of <- c(rep("tropical", 6), rep("temperate", 6), rep("boreal", 6))
mat <- function(x) { if (length(dim(x)) == 4) x <- x[, , , 1]; x }

## ---- the BAU cells (as Baseline_EUDR.R: same cells, same cap, same drop rule) ---------------------------------
bau <- as.data.frame(read_excel(paste0(external_data_path, "/DeDuCE_rework/bau_deforestation.xlsx"), sheet = "cells"))
bau$shock_pct <- -pmin(100 * (bau$bau_loss_ha / bau$horizon_yr) * bau_horizon / bau$forest_cover_ha, bau_cap_pct)
lcov <- read_har('in/basedata.har')[["lcov"]]
bau$agri_cover_ha <- 1000 * sapply(seq_len(nrow(bau)), function(k) sum(lcov[tolower(bau$aez[k]), c("cropland", "pastureland"), tolower(bau$region[k])]))
if (any(bau$agri_cover_ha <= 0)) {
  drop <- bau$agri_cover_ha <= 0
  print(paste("BAU cells without crop or pasture cover, dropped:", paste(bau$region[drop], bau$aez[drop], round(-bau$shock_pct[drop] / 100 * bau$forest_cover_ha[drop]), "ha", collapse = "; ")))
  bau <- bau[!drop, ]
}
bau$bau_imposed_ha <- -bau$shock_pct / 100 * bau$forest_cover_ha
lines_bau <- c(sprintf('swap p_LANDCOVER_L("%s","Forestland","%s") = tinc("%s","forest","%s");', bau$aez, bau$region, bau$aez, bau$region),
               sprintf('shock p_LANDCOVER_L("%s","Forestland","%s") = %s;', bau$aez, bau$region, format(bau$shock_pct, scientific = FALSE, digits = 10)))
print(paste("BAU clearing:", nrow(bau), "region x AEZ cells,", round(sum(bau$bau_imposed_ha) / 1e6, 2), "Mha over", bau_horizon, "years"))

lines_afe <- character(0); afe <- NULL
if (bau_eta > 0) {
  afe_file <- paste0(external_data_path, "/DeDuCE_rework/bau_afeall_eta", bau_eta, gen_sfx, ".txt")
  if (!file.exists(afe_file)) stop("Run 1_Code/Calibrate_BAU_productivity.R with bau_eta = ", bau_eta, " first: ", afe_file, " not found")
  afe <- read.table(afe_file, header = TRUE, stringsAsFactors = FALSE); afe <- afe[afe$afeall_pct > 0, ]
  lines_afe <- sprintf('shock afeall("%s","%s","%s") = %s;', afe$aez, afe$activity, afe$region, format(afe$afeall_pct, scientific = FALSE, digits = 10))
  print(paste("productivity of the cleared hectares: eta =", bau_eta, "-", nrow(afe), "afeall shocks, largest", round(max(afe$afeall_pct), 1), "%"))
}

## ---- the EUDR cut lines (as Baseline_EUDR.R) ---------------------------------------------------------------------
cuts <- as.data.frame(read_excel(paste0(external_data_path, "/DeDuCE_rework/eudr_cut_shares.xlsx"), sheet = eudr_sheet))
cuts$cut <- -100 * pmin(cuts$s_u * eudr_scale, 0.95)
lines_eudr <- c(sprintf('swap qxs("%s","%s","%s") = ams("%s","%s","%s");', cuts$comm, cuts$source, cuts$dest, cuts$comm, cuts$source, cuts$dest),
                sprintf('shock qxs("%s","%s","%s") = %s;', cuts$comm, cuts$source, cuts$dest, format(cuts$cut, scientific = FALSE, digits = 10)))

## =================================== Stage A: the BAU world =====================================================
if ("A" %in% run_stage) {
  cmf_A <- prepare_cmf(c(lines_bau, lines_afe))
  file.copy(cmf_A, paste0(out_A, "NATDEF_A.cmf"), overwrite = TRUE)
  print("Stage A: business-as-usual clearing, no EUDR")
  solve_gtap(paste0(out_A, "Solve_A.log"))
  data <- read_SL4('NATDEF.sl4')
  ev_A <- as.numeric(unlist(data.frame(data["ev"])))
  write.table(cbind(region_sets, ev_A), file = paste0(out_A, "EV_A.txt"), row.names = FALSE, col.names = FALSE)
  luc <- mat(data[["del_luc"]])
  write.table(t(luc[, "forestland", ] * 1000), file = paste0(out_A, "Forest_LU_A_ha.txt"), col.names = FALSE)
  tt <- mat(data[["tinc"]]); pl <- mat(data[["p_landcover_l"]])
  bau$tinc_solved <- sapply(seq_len(nrow(bau)), function(k) tt[tolower(bau$aez[k]), "forest", tolower(bau$region[k])])
  bau$cover_change_pct <- sapply(seq_len(nrow(bau)), function(k) pl[tolower(bau$aez[k]), "forestland", tolower(bau$region[k])])
  write.table(bau[, c("region", "aez", "forest_cover_ha", "agri_cover_ha", "shock_pct", "cover_change_pct", "tinc_solved")],
              file = paste0(out_A, "bau_baseline.txt"), row.names = FALSE)
  print(paste("BAU check: largest gap between asked and solved cover change =", signif(max(abs(bau$cover_change_pct - bau$shock_pct)), 3), "% (should be ~0)"))
  if (!is.null(afe)) {                                    # same yardstick as the calibration: are the cleared hectares productive without the EUDR?
    qs <- mat(data[["qes"]])
    afe$qes_baseline <- sapply(seq_len(nrow(afe)), function(k) qs[tolower(afe$aez[k]), tolower(afe$activity[k]), tolower(afe$region[k])])
    afe$shortfall <- pmax(0, afe$target_pct - (afe$qes_baseline + afe$afeall_pct))
    write.table(afe, file = paste0(out_A, "bau_afeall.txt"), row.names = FALSE)
    print(paste0("productivity check: hectare-weighted shortfall of land services below target = ", round(sum(afe$hectares * afe$shortfall) / sum(afe$hectares), 2),
                 " points, ", round(100 * sum(afe$hectares[afe$shortfall < 1]) / sum(afe$hectares)), " % of the cleared hectares within 1 point",
                 " (the one-solve baseline gave the same check with the EUDR in; a clearly larger shortfall means: recalibrate with eudr_scale = 0)"))
  }
  upd <- updated_db_path(cmf_A)
  if (!file.exists(upd)) stop("the updated database ", upd, " was not written")
  file.copy(upd, paste0(out_A, "gdata_bau.upd"), overwrite = TRUE)
  file.copy("NATDEF.sl4", paste0(out_A, "NATDEF_A.sl4"), overwrite = TRUE)
  print(paste("Stage A done: the BAU world is", paste0(out_A, "gdata_bau.upd")))
}

## =================================== Stage B: the EUDR on the BAU world ==========================================
if ("B" %in% run_stage) {
  db_A <- normalizePath(paste0(out_A, "gdata_bau.upd"), winslash = "\\", mustWork = TRUE)
  cmf_B <- prepare_cmf(lines_eudr, data_file = db_A)
  file.copy(cmf_B, paste0(out_B, "NATDEF_B.cmf"), overwrite = TRUE)
  print(paste("Stage B: the EUDR on the BAU world -", nrow(cuts), "EU import flows cut, scale", eudr_scale, "- forest endogenous everywhere"))
  solve_gtap(paste0(out_B, "Solve_B.log"))
  data <- read_SL4('NATDEF.sl4')
  ev_B <- as.numeric(unlist(data.frame(data["ev"])))
  write.table(cbind(region_sets, ev_B), file = paste0(out_B, "EV_B.txt"), row.names = FALSE, col.names = FALSE)
  ams <- mat(data[["ams"]])
  cuts$ams_solved <- sapply(seq_len(nrow(cuts)), function(k) ams[tolower(cuts$comm[k]), tolower(cuts$source[k]), tolower(cuts$dest[k])])
  write.table(cuts[, c("comm", "source", "dest", "s_u", "cut", "ams_solved")], file = paste0(out_B, "ams_baseline.txt"), row.names = FALSE)
  luc_B <- mat(data[["del_luc"]])[, "forestland", ] * 1000          # aez x region, ha, relative to the BAU world
  write.table(t(luc_B), file = paste0(out_B, "Forest_LU_B_ha.txt"), col.names = FALSE)
  pl_B <- mat(data[["p_landcover_l"]])[, "forestland", ]
  upd <- updated_db_path(cmf_B)
  file.copy(upd, paste0(out_B, "gdata_eudr.upd"), overwrite = TRUE)
  file.copy("NATDEF.sl4", paste0(out_B, "NATDEF_B.sl4"), overwrite = TRUE)

  ## ---- the EUDR's effect next to the DeDuCE rate ------------------------------------------------------------------
  bau_mat <- matrix(0, nrow = 18, ncol = length(region_sets), dimnames = list(aez_names, tolower(region_sets)))
  for (k in seq_len(nrow(bau))) bau_mat[tolower(bau$aez[k]), tolower(bau$region[k])] <- bau$bau_imposed_ha[k]
  regs <- tolower(region_sets); luc_B <- luc_B[aez_names, regs]
  cell <- expand.grid(aez = aez_names, region = regs, stringsAsFactors = FALSE)
  cell$zone <- zone_of[match(cell$aez, aez_names)]
  cell$bau_clearing_ha <- as.vector(bau_mat); cell$eudr_effect_ha <- as.vector(luc_B); cell$eudr_effect_pct_cover <- as.vector(pl_B[aez_names, regs])
  cell$eudr_effect_pct_of_bau <- ifelse(cell$bau_clearing_ha > 0, 100 * cell$eudr_effect_ha / cell$bau_clearing_ha, NA)
  cell <- cell[abs(cell$eudr_effect_ha) >= 1 | cell$bau_clearing_ha > 0, ]
  write.table(cell, file = paste0(out_path, "EUDR_effect_by_cell.txt"), row.names = FALSE)
  trop <- zone_of == "tropical"
  reg <- data.frame(region = region_sets,
                    bau_clearing_trop_ha = colSums(bau_mat[trop, ]), bau_clearing_all_ha = colSums(bau_mat),
                    eudr_effect_trop_ha = colSums(luc_B[trop, ]), eudr_effect_all_ha = colSums(luc_B),
                    EV_eudr_MUSD = ev_B, stringsAsFactors = FALSE)
  reg$eudr_effect_pct_of_bau_trop <- ifelse(reg$bau_clearing_trop_ha > 0, 100 * reg$eudr_effect_trop_ha / reg$bau_clearing_trop_ha, NA)
  reg <- reg[order(-reg$bau_clearing_all_ha), ]
  write.table(reg, file = paste0(out_path, "EUDR_effect_by_region.txt"), row.names = FALSE)
  w <- c(bau_trop = sum(bau_mat[trop, ]), bau_all = sum(bau_mat), eudr_trop = sum(luc_B[trop, ]), eudr_all = sum(luc_B), ev_world = sum(ev_B))
  print("The EUDR next to the DeDuCE rate (a positive forest effect = the EUDR slows clearing; negative = it accelerates it):")
  print(paste0("  world: BAU clearing ", round(w["bau_all"] / 1e6, 2), " Mha (", round(w["bau_trop"] / 1e6, 2), " tropical); EUDR effect ", round(w["eudr_all"] / 1e3), " kha (",
               round(w["eudr_trop"] / 1e3), " tropical), i.e. ", round(100 * w["eudr_trop"] / w["bau_trop"], 2), " % of the tropical BAU clearing; world EV ", round(w["ev_world"]), " M USD"))
  top <- head(reg[!is.na(reg$eudr_effect_pct_of_bau_trop), ], 12)
  print(top[, c("region", "bau_clearing_trop_ha", "eudr_effect_trop_ha", "eudr_effect_pct_of_bau_trop", "EV_eudr_MUSD")], row.names = FALSE)
  print(paste("Stage B done: the EUDR world is", paste0(out_B, "gdata_eudr.upd"), "- results in", out_path))
}

## ---- restore the backup files so RunGTAP and the game script start clean -----------------------------------------
restore_bu()
