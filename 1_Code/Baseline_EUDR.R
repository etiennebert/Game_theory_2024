## =====================================================================================
##  Baseline_EUDR.R  -  sister script of CGE_Game_Theory_GTAPAEZ_all_V21.R
##
##  Solves the baseline ONCE: the world as it is = the EU alone applies the EUDR, and clearing
##  goes on everywhere at the observed rate (business as usual, BAU).
##   - EUDR: EU imports of the covered products from each origin fall by the share of that origin's
##     output that comes from land deforested after 31 Dec 2020 (eudr_cut_shares.xlsx, sheet "shocks").
##     A ban, not a tax: swap qxs(c,r,"eu27") = ams(c,r,"eu27"); shock qxs = -100 s_u. The solved ams
##     (the iceberg cost) is what the game script keeps on non-members.
##   - BAU (bau_horizon > 0): in every (region, AEZ) cell of bau_deforestation.xlsx, forest cover falls
##     by the DeDuCE clearing rate x horizon: swap p_LANDCOVER_L(AEZ,"Forestland",r) = tinc(AEZ,"forest",r);
##     shock p_LANDCOVER_L = -x. The solved tinc* (the implicit clearing incentive) is what the game
##     script keeps on non-members; members are pinned at 0 instead (no net loss).
##
##   - Productivity of the cleared hectares (bau_eta > 0, V24): the afeall shocks calibrated by Calibrate_BAU_productivity.R
##     (0_External_data/DeDuCE_rework/bau_afeall_eta<eta>.txt) are added, so the activities that receive the cleared
##     land get eta x the hectares in land services. Without them the CET leaves most cleared hectares unused.
##
##  Writes 3_Output/Baseline_EUDR_bau<horizon>_eta<eta>/ (Baseline_EUDR_bau<horizon>/ when bau_eta = 0; Baseline_EUDR/ when bau_horizon = 0):
##    EV_baseline.txt           region, EV ($M)           -> iteration 0 of the game script
##    ams_baseline.txt          solved ams per cut flow    -> EUDR cost on non-members
##    bau_baseline.txt          solved tinc* per BAU cell  -> clearing incentive on non-members (cells without crop or
##                              pasture cover are dropped: forest cannot be converted there, the model would be singular)
##    bau_afeall.txt            the afeall shocks (region, aez, activity, afeall_pct, ...) -> productivity on non-members
##    Forest_LU_baseline_ha.txt forest cover change by region x AEZ (ha)
##    NATDEF_baseline.cmf/.har/.sl4
##  Run it from RStudio like the main script (same folder structure). One solve; its screen output goes to
##  Baseline_solve.log in the output folder and the script stops with the solver's message if the solve fails.
## =====================================================================================
rm(list = ls())
library(HARr)
library("readxl")
library("rstudioapi")

script_path <- getSourceEditorContext()$path
script_folder <- dirname(script_path)
parent_folder <- dirname(script_folder)
GTAPAEZ_path <- file.path(parent_folder, "2_Model/")
external_data_path <- file.path(parent_folder, "0_External_data/")
setwd(GTAPAEZ_path)

## ---- parameters --------------------------------------------------------------------------
eudr_sheet <- "shocks"   # sheet of eudr_cut_shares.xlsx: comm, source, dest, s_u (share of output from post-2020 deforestation)
eudr_scale <- 1          # multiplies s_u: 1 = only non-compliant output is excluded; >1 = traceability scenario (unverifiable output also excluded)
solve_mode <- "accurate" # "accurate" = RunGTAP settings (Gragg 2-4-6, automatic accuracy, 3 subintervals; 5-6 min) | "fast" = one subinterval, no accuracy iteration - NOT accurate enough for the BAU shocks (face 4, arithmetic failures)
bau_horizon <- 5         # years of business-as-usual clearing in the baseline (0 = none: the V16-V20 baseline)
bau_cap_pct <- 25        # a cell never loses more than this share of its forest cover over the horizon
bau_eta     <- 0.66      # productivity of the cleared hectares, from Calibrate_BAU_productivity.R (run it first with this value); 0 = none, the V21-V23 baseline
set_solver_lines <- function(lines, mode) {   # identical to the game script's (V23)
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
out_path   <- file.path(parent_folder, "3_Output", if (bau_horizon > 0) paste0("Baseline_EUDR_bau", bau_horizon, if (bau_eta > 0) paste0("_eta", bau_eta) else "") else "Baseline_EUDR", "/")
dir.create(out_path, recursive = TRUE, showWarnings = FALSE)

## ---- 1. start from the RunGTAP backup: closure from BU/NATDEF.cmf, zero tariff header ------
for (f in c("NATDEF.cmf", "NATDEF.har")) {
  file.copy(file.path(parent_folder, "2_Model", "BU", f), file.path(GTAPAEZ_path, f), overwrite = TRUE)
}
shock <- read_har('NATDEF.har')
shock[["0101"]][] <- 0                                  # no border charge in the baseline
write_har(shock, 'NATDEF.har', maxSize = 1e4)

## ---- 2. the EUDR cut lines ------------------------------------------------------------------
cuts <- read_excel(paste0(external_data_path, "/DeDuCE_rework/eudr_cut_shares.xlsx"), sheet = eudr_sheet)
cuts <- as.data.frame(cuts)
cuts$cut <- -100 * pmin(cuts$s_u * eudr_scale, 0.95)   # % change of the EU import quantity, never below -95
lines_eudr <- character(0)
for (k in seq_len(nrow(cuts))) {
  lines_eudr <- c(lines_eudr,
    sprintf('swap qxs("%s","%s","%s") = ams("%s","%s","%s");',
            cuts$comm[k], cuts$source[k], cuts$dest[k], cuts$comm[k], cuts$source[k], cuts$dest[k]),
    sprintf('shock qxs("%s","%s","%s") = %s;',
            cuts$comm[k], cuts$source[k], cuts$dest[k], format(cuts$cut[k], scientific = FALSE, digits = 10)))
}
## ---- 2b. business-as-usual clearing ---------------------------------------------------------
lines_bau <- character(0); bau <- NULL
if (bau_horizon > 0) {
  bau <- as.data.frame(read_excel(paste0(external_data_path, "/DeDuCE_rework/bau_deforestation.xlsx"), sheet = "cells"))
  bau$shock_pct <- -pmin(100 * (bau$bau_loss_ha / bau$horizon_yr) * bau_horizon / bau$forest_cover_ha, bau_cap_pct)   # rescaled to bau_horizon
  ## Forest can only be converted to crop or pasture land of the same AEZ (E_areaadjust: the productive covers of an
  ## AEZ sum to a fixed area). A cell with no crop or pasture cover cannot lose forest: swapping its cover with tinc
  ## makes the model structurally singular (US AEZ16 in the v11 data). Such cells are dropped, and the room left in
  ## the others is reported.
  lcov <- read_har('in/basedata.har')[["lcov"]]                                    # 1000 ha by AEZ x cover x region
  bau$agri_cover_ha <- 1000 * sapply(seq_len(nrow(bau)), function(k) sum(lcov[tolower(bau$aez[k]), c("cropland", "pastureland"), tolower(bau$region[k])]))
  if (any(bau$agri_cover_ha <= 0)) {
    drop <- bau$agri_cover_ha <= 0
    print(paste("BAU cells without crop or pasture cover, dropped:", paste(bau$region[drop], bau$aez[drop], round(-bau$shock_pct[drop] / 100 * bau$forest_cover_ha[drop]), "ha", collapse = "; ")))
    bau <- bau[!drop, ]
  }
  room <- -bau$shock_pct / 100 * bau$forest_cover_ha / bau$agri_cover_ha
  print(paste("BAU clearing as a share of the cell's crop + pasture area: largest", round(100 * max(room)), "% (", bau$region[which.max(room)], bau$aez[which.max(room)], ")"))
  for (k in seq_len(nrow(bau))) {
    lines_bau <- c(lines_bau,
      sprintf('swap p_LANDCOVER_L("%s","Forestland","%s") = tinc("%s","forest","%s");', bau$aez[k], bau$region[k], bau$aez[k], bau$region[k]),
      sprintf('shock p_LANDCOVER_L("%s","Forestland","%s") = %s;', bau$aez[k], bau$region[k], format(bau$shock_pct[k], scientific = FALSE, digits = 10)))
  }
  print(paste("BAU clearing:", nrow(bau), "region x AEZ cells,", round(sum(bau$forest_cover_ha * -bau$shock_pct / 100) / 1e6, 1), "Mha over", bau_horizon, "years"))
}
## ---- 2c. productivity of the cleared hectares (V24): the afeall shocks calibrated by Calibrate_BAU_productivity.R ----
lines_afe <- character(0); afe <- NULL
if (bau_horizon > 0 && bau_eta > 0) {
  afe_file <- paste0(external_data_path, "/DeDuCE_rework/bau_afeall_eta", bau_eta, ".txt")
  if (!file.exists(afe_file)) stop("Run 1_Code/Calibrate_BAU_productivity.R with bau_eta = ", bau_eta, " first: ", afe_file, " not found")
  afe <- read.table(afe_file, header = TRUE, stringsAsFactors = FALSE)
  afe <- afe[afe$afeall_pct > 0, ]
  lines_afe <- sprintf('shock afeall("%s","%s","%s") = %s;', afe$aez, afe$activity, afe$region, format(afe$afeall_pct, scientific = FALSE, digits = 10))
  print(paste("productivity of the cleared hectares: eta =", bau_eta, "-", nrow(afe), "afeall shocks on", length(unique(afe$region)), "regions, largest", round(max(afe$afeall_pct), 1), "%"))
}
cmf_path <- paste0(GTAPAEZ_path, "/NATDEF.cmf")
lines <- readLines(cmf_path, warn = FALSE)
cutoff_line <- which(lines == "! Part for productivity shocks;")
if (length(cutoff_line) == 0) stop("The line '! Part for productivity shocks;' was not found in BU/NATDEF.cmf")
lines <- c(lines[1:cutoff_line],
           'Shock tms_f =  file NATDEF.har header "0101";',
           '! Part for productivity shocks from R;',
           lines_eudr, lines_bau, lines_afe)
lines <- set_solver_lines(lines, solve_mode)
writeLines(lines, cmf_path)
file.copy(cmf_path, paste0(out_path, "NATDEF_baseline.cmf"), overwrite = TRUE)
print(paste("EUDR baseline:", nrow(cuts), "EU import flows cut, scale", eudr_scale))

## ---- 3. solve --------------------------------------------------------------------------------
solve_log <- paste0(out_path, "Baseline_solve.log")           # the solver's screen output (the error message, if any, is at the end)
mtime_before <- file.info("NATDEF.sl4")$mtime; t0 <- Sys.time()
status <- system2("GTAPV7-AEZ.exe", c("-cmf", "NATDEF.CMF"), stdout = solve_log, stderr = solve_log)
print(paste("solve time:", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), "min - solver output in", solve_log))
if (!identical(as.integer(status), 0L) || identical(file.info("NATDEF.sl4")$mtime, mtime_before)) {
  cat(tail(readLines(solve_log, warn = FALSE), 40), sep = "\n")
  stop("GEMPACK did not produce a new solution (exit code ", status, "). The last 40 lines of ", solve_log, " are printed above.")
}

## ---- 4. results ------------------------------------------------------------------------------
data <- read_SL4('NATDEF.sl4')
sets <- read_har('sets.har')
region_sets <- unlist(data.frame(sets["reg"]))
values_EV <- as.numeric(unlist(data.frame(data["ev"])))
write.table(cbind(region_sets, values_EV), file = paste0(out_path, "EV_baseline.txt"), row.names = FALSE, col.names = FALSE)

ams <- data[["ams"]]
if (length(dim(ams)) == 4) ams <- ams[, , , 1]
cuts$ams_solved <- NA_real_
for (k in seq_len(nrow(cuts))) {
  cuts$ams_solved[k] <- ams[tolower(cuts$comm[k]), tolower(cuts$source[k]), tolower(cuts$dest[k])]
}
write.table(cuts[, c("comm", "source", "dest", "s_u", "cut", "ams_solved")],
            file = paste0(out_path, "ams_baseline.txt"), row.names = FALSE)

luc <- data[["del_luc"]]
if (length(dim(luc)) == 4) luc <- luc[, , , 1]
write.table(t(luc[, "forestland", ] * 1000), file = paste0(out_path, "Forest_LU_baseline_ha.txt"), col.names = FALSE)

if (bau_horizon > 0) {                                   # solved clearing incentive per BAU cell, and a check that the cover fell as asked
  tt <- data[["tinc"]]; if (length(dim(tt)) == 4) tt <- tt[, , , 1]
  pl <- data[["p_landcover_l"]]; if (length(dim(pl)) == 4) pl <- pl[, , , 1]
  bau$tinc_solved <- NA_real_; bau$cover_change_pct <- NA_real_
  for (k in seq_len(nrow(bau))) {
    bau$tinc_solved[k]      <- tt[tolower(bau$aez[k]), "forest", tolower(bau$region[k])]
    bau$cover_change_pct[k] <- pl[tolower(bau$aez[k]), "forestland", tolower(bau$region[k])]
  }
  write.table(bau[, c("region", "aez", "forest_cover_ha", "agri_cover_ha", "shock_pct", "cover_change_pct", "tinc_solved")],
              file = paste0(out_path, "bau_baseline.txt"), row.names = FALSE)
  print(paste("BAU check: largest gap between asked and solved cover change =", signif(max(abs(bau$cover_change_pct - bau$shock_pct)), 3), "% (should be ~0)"))
}

if (!is.null(afe)) {                                    # V24: land services of the receiving activities vs their targets, and the shocks for the game script
  qs <- data[["qes"]]; if (length(dim(qs)) == 4) qs <- qs[, , , 1]
  afe$qes_baseline <- sapply(seq_len(nrow(afe)), function(k) qs[tolower(afe$aez[k]), tolower(afe$activity[k]), tolower(afe$region[k])])
  afe$shortfall <- pmax(0, afe$target_pct - (afe$qes_baseline + afe$afeall_pct))
  write.table(afe, file = paste0(out_path, "bau_afeall.txt"), row.names = FALSE)
  print(paste0("productivity check (same yardstick as the calibration): hectare-weighted shortfall of land services below target = ",
               round(sum(afe$hectares * afe$shortfall) / sum(afe$hectares), 2), " points, ", round(100 * sum(afe$hectares[afe$shortfall < 1]) / sum(afe$hectares)),
               " % of the cleared hectares within 1 point, largest in a cell above 50 kha = ", round(max(afe$shortfall[afe$hectares >= 5e4]), 2)))
}
file.copy("NATDEF.sl4", paste0(out_path, "NATDEF_baseline.sl4"), overwrite = TRUE)
file.copy("NATDEF.har", paste0(out_path, "NATDEF_baseline.har"), overwrite = TRUE)

## ---- 5. restore the backup files so RunGTAP and the game script start clean -------------------
for (f in c("NATDEF.cmf", "NATDEF.har", "NATDEF.sl4")) {
  file.copy(file.path(parent_folder, "2_Model", "BU", f), file.path(GTAPAEZ_path, f), overwrite = TRUE)
}
print(paste("Baseline solved. EV (eu27):", round(values_EV[region_sets == "eu27"], 2),
            "- results in", out_path))
