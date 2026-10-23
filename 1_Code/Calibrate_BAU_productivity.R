## =====================================================================================
##  Calibrate_BAU_productivity.R  -  sister script of Baseline_EUDR.R; run it BEFORE the baseline
##
##  Why. The BAU clearing is imposed on the land-cover identity (forest cover -x % per AEZ cell), but the land the
##  receiving activities use in production - qes(AEZ, act, r), allocated by the CET on land rents - rises far less
##  than the hectares they receive: Ivory Coast AEZ6, pasture hectares +73 %, land used by grazing -0.2 %; Brazil AEZ6,
##  hectares +12 %, land used +7 %. The cleared hectares reach production at whatever ratio the 2017 rent shares
##  imply, from 0 to 0.9 depending on the region. In the model clearing then destroys value, and a member that stops
##  clearing gains instead of paying.
##
##  What this script does. It gives the cleared hectares a stated productivity. In every BAU cell (region x AEZ) the
##  cleared hectares are split across the activities DeDuCE attributes the region's clearing to (h_table_DeDuCE.xlsx,
##  sheet D_unamort_w2018_2023: cattle, dairy and wool for pasture, cocoa/coffee/rubber = ocr, soy/palm = osd, ...),
##  and each receiving activity's land services must rise by at least
##        T(cell, act) = eta x 100 x hectares(cell, act) / land base(cell, act)
##  land base = the activity's land in the cell (AREA for the eight crops, Pastureland cover split by EVOS rent shares
##  for ruminant / rmk / wol; activities under min_base_ha are skipped, an activity takes at most max_ratio x its own
##  land, the rest goes to the cell's other activities); eta = 0.66, the model's own yield of newly converted cropland
##  (ETA in E_harvstaez). Land services = qes + afeall, where afeall(AEZ, act, r) is the land-augmenting technical
##  change of E_qfe, exogenous in the closure. Because qes is endogenous, afeall is found by iteration on the baseline
##  solve itself (EUDR cut + BAU cover path, exactly as Baseline_EUDR.R writes it), with the measured response of each
##  cell's land use to its own shock (section 5), until the hectare-weighted shortfall is small. Where the CET already
##  gives an activity more land than T (land drawn from other uses in the AEZ) nothing is taken away: "at least", never
##  a productivity cut. One accurate solve per pass (5 min); a previous run's passes are reused as a warm start.
##
##  Output. 0_External_data/DeDuCE_rework/bau_afeall_eta<eta>.txt: region, aez, activity, hectares, land_base_ha,
##  target_pct, qes_pct, afeall_pct. Baseline_EUDR.R (bau_eta > 0) and the game script read it: non-members get the
##  afeall shocks with their cover path, members get neither (no clearing, no free land). Nothing here is saved as a
##  baseline - run Baseline_EUDR.R afterwards with the same bau_horizon, bau_cap_pct, eudr settings and bau_eta.
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

## ---- parameters (keep them identical to Baseline_EUDR.R) -----------------------------------------
eudr_sheet  <- "shocks"
eudr_scale  <- 1
bau_horizon <- 5
bau_cap_pct <- 25
bau_eta     <- 0.66      # yield of the cleared hectares relative to the activity's existing land (0.66 = the model's ETA for new cropland)
generation  <- "v33"     # V33 (20 Oct 2026): the Miranda-calibrated land-supply elasticities (2_Model/in/default.prm = default_miranda_final.prm); suffix of the
                         # output file and the log folder so that nothing of V32 is overwritten ("" = the V32 files)
max_pass    <- 6
dedu_sheet  <- "D_unamort_w2018_2023"   # DeDuCE hectares by region x GTAP activity, the window of bau_deforestation.xlsx
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
gen_sfx  <- if (nzchar(generation)) paste0("_", generation) else ""
out_file <- paste0(external_data_path, "/DeDuCE_rework/bau_afeall_eta", bau_eta, gen_sfx, ".txt")
log_dir  <- file.path(parent_folder, "3_Output", paste0("Calibrate_BAU_productivity", gen_sfx), "/"); dir.create(log_dir, recursive = TRUE, showWarnings = FALSE)
if (nzchar(generation)) print(paste0("generation ", generation, ": parameter file ", normalizePath("in/default.prm"), " (must be the Miranda-calibrated one); output ", out_file))

## ---- 1. start from the RunGTAP backup, zero tariff header (as Baseline_EUDR.R) ------------------------
for (f in c("NATDEF.cmf", "NATDEF.har")) file.copy(file.path(parent_folder, "2_Model", "BU", f), file.path(GTAPAEZ_path, f), overwrite = TRUE)
shock <- read_har('NATDEF.har'); shock[["0101"]][] <- 0; write_har(shock, 'NATDEF.har', maxSize = 1e4)

## ---- 2. the EUDR cut lines (as Baseline_EUDR.R) ------------------------------------------------------
cuts <- as.data.frame(read_excel(paste0(external_data_path, "/DeDuCE_rework/eudr_cut_shares.xlsx"), sheet = eudr_sheet))
cuts$cut <- -100 * pmin(cuts$s_u * eudr_scale, 0.95)
lines_eudr <- c(sprintf('swap qxs("%s","%s","%s") = ams("%s","%s","%s");', cuts$comm, cuts$source, cuts$dest, cuts$comm, cuts$source, cuts$dest),
                sprintf('shock qxs("%s","%s","%s") = %s;', cuts$comm, cuts$source, cuts$dest, format(cuts$cut, scientific = FALSE, digits = 10)))

## ---- 3. the BAU cover lines (as Baseline_EUDR.R, same cells, same drop rule) ---------------------------
bau <- as.data.frame(read_excel(paste0(external_data_path, "/DeDuCE_rework/bau_deforestation.xlsx"), sheet = "cells"))
bau$shock_pct <- -pmin(100 * (bau$bau_loss_ha / bau$horizon_yr) * bau_horizon / bau$forest_cover_ha, bau_cap_pct)
base <- read_har('in/basedata.har')
lcov <- base[["lcov"]]; area <- base[["area"]]; evos <- base[["evos"]]           # 1000 ha; 1000 ha; $M
bau$agri_cover_ha <- 1000 * sapply(seq_len(nrow(bau)), function(k) sum(lcov[tolower(bau$aez[k]), c("cropland", "pastureland"), tolower(bau$region[k])]))
bau <- bau[bau$agri_cover_ha > 0, ]
bau$cleared_ha <- -bau$shock_pct / 100 * bau$forest_cover_ha                    # what the baseline really imposes (cap included)
lines_bau <- c(sprintf('swap p_LANDCOVER_L("%s","Forestland","%s") = tinc("%s","forest","%s");', bau$aez, bau$region, bau$aez, bau$region),
               sprintf('shock p_LANDCOVER_L("%s","Forestland","%s") = %s;', bau$aez, bau$region, format(bau$shock_pct, scientific = FALSE, digits = 10)))

## ---- 4. targets: in every cell, who gets the cleared hectares and how much land it is for them ----------
##  The cell's cleared hectares are split across the activities DeDuCE attributes the region's clearing to; pasture
##  (DeDuCE cattle + dairy + wool) goes to "ruminant", the model's only grazing activity: in this aggregation rmk and
##  wol are not land-using activities (DLUA = crops, ctl, frs), their AEZ land sits outside the land nests and the
##  cover identity, and a productivity shock on them is absorbed by their own land demand (ESUBVA = 0.29) - the first
##  calibration spent its passes on exactly those cells. An activity absorbs at most max_ratio x its own land in the
##  cell (the rest goes to the cell's other activities); activities under min_base_ha are skipped; the target is
##  T(cell, act) = eta x 100 x hectares / land base. Cells where no attributed activity has land keep their forest
##  loss but get no productivity shock (reported).
max_ratio   <- 0.5       # an activity absorbs at most this share of its own land in the cell
min_base_ha <- 5000      # activities with less land than this in the cell receive nothing (noise cells)
D <- as.data.frame(read_excel(paste0(external_data_path, "/DeDuCE_rework/h_table_DeDuCE.xlsx"), sheet = dedu_sheet))
names(D)[1] <- "reg"; D$reg <- tolower(D$reg)
for (a in c("rmk", "wol")) if (a %in% names(D)) { D$ruminant <- D$ruminant + ifelse(is.na(D[[a]]), 0, D[[a]]); D[[a]] <- NULL }   # pasture -> ruminant
acts_all <- setdiff(names(D), "reg")                                            # c_b gro ocr osd pdr pfb ruminant v_f wht
crops <- dimnames(area)[[2]]
tg <- data.frame(); unabsorbed <- 0; no_attr <- character(0)
for (k in seq_len(nrow(bau))) {
  r <- bau$region[k]; e <- bau$aez[k]; rl <- tolower(r); el <- tolower(e); H <- bau$cleared_ha[k]
  if (!(rl %in% D$reg)) { no_attr <- union(no_attr, r); unabsorbed <- unabsorbed + H; next }
  d <- unlist(D[D$reg == rl, acts_all]); d[is.na(d)] <- 0
  L <- sapply(acts_all, function(a) if (a %in% crops) 1000 * area[el, a, rl] else if (a == "ruminant") 1000 * lcov[el, "pastureland", rl] else 0)
  names(L) <- acts_all
  present <- L >= min_base_ha & d > 0
  if (!any(present)) { unabsorbed <- unabsorbed + H; next }
  alloc <- setNames(rep(0, length(acts_all)), acts_all); capped <- !present; rest <- H
  repeat {                                                                    # share the hectares, capping each activity at max_ratio x its land
    open <- !capped; if (!any(open) || rest <= 0) break
    add <- rest * d * open / sum(d * open); alloc <- alloc + add; rest <- 0
    over <- alloc > max_ratio * L & open
    if (!any(over)) break
    rest <- sum(alloc[over] - max_ratio * L[over]); alloc[over] <- max_ratio * L[over]; capped[over] <- TRUE
  }
  unabsorbed <- unabsorbed + rest
  for (a in acts_all[alloc > 0])
    tg <- rbind(tg, data.frame(region = r, aez = e, activity = a, hectares = alloc[a], land_base_ha = L[a],
                               target_pct = bau_eta * 100 * alloc[a] / L[a], stringsAsFactors = FALSE))
}
tg <- tg[tg$target_pct >= 0.05, ]                                               # below 0.05 % nothing to calibrate
tg$qes_pct <- NA_real_; tg$afeall_pct <- 0; tg$k <- NA_real_
tg$key <- paste(tg$region, tg$aez, tg$activity)
print(paste0("targets: ", nrow(tg), " AEZ x activity cells in ", length(unique(tg$region)), " regions; hectares absorbed ", round(sum(tg$hectares) / 1e6, 2),
             " Mha of ", round(sum(bau$cleared_ha) / 1e6, 2), " cleared (", round(unabsorbed / 1e3), " kha without a receiving activity",
             if (length(no_attr) > 0) paste0("; no DeDuCE attribution: ", paste(no_attr, collapse = " ")) else "", "); largest target ",
             round(max(tg$target_pct), 1), " % (", tg$region[which.max(tg$target_pct)], " ", tg$aez[which.max(tg$target_pct)], " ", tg$activity[which.max(tg$target_pct)], "); eta = ", bau_eta))
print(aggregate(target_pct ~ region, tg, max))

## ---- 4b. warm start from the last passes of a previous run (same cell, same target) -----------------------
##  Every pass is one accurate solve; the previous run's last two pass files give a starting afeall and the response
##  k = -dqes/dafeall of every cell, which the update below uses.
warm_start <- TRUE
prev <- sort(list.files(log_dir, pattern = "^targets_pass_[0-9]+\\.txt$", full.names = TRUE))
prev <- prev[order(as.integer(sub(".*targets_pass_([0-9]+)\\.txt$", "\\1", prev)))]
if (warm_start && length(prev) >= 1) {
  p_last <- read.table(tail(prev, 1), header = TRUE, stringsAsFactors = FALSE); p_last$key <- paste(p_last$region, p_last$aez, p_last$activity)
  m <- match(tg$key, p_last$key); same <- !is.na(m) & abs(p_last$target_pct[m] - tg$target_pct) < 1e-6
  tg$afeall_pct[same] <- pmax(0, p_last$afeall_pct[m[same]] + 0.7 * pmax(0, tg$target_pct[same] - p_last$qes_pct[m[same]] - p_last$afeall_pct[m[same]]) / (1 - 0.3))
  if (length(prev) >= 2) {
    p_prev <- read.table(tail(prev, 2)[1], header = TRUE, stringsAsFactors = FALSE); p_prev$key <- paste(p_prev$region, p_prev$aez, p_prev$activity)
    m2 <- match(tg$key, p_prev$key); ok <- same & !is.na(m2) & abs(p_last$afeall_pct[m] - p_prev$afeall_pct[m2]) >= 0.5
    kk <- -(p_last$qes_pct[m] - p_prev$qes_pct[m2]) / (p_last$afeall_pct[m] - p_prev$afeall_pct[m2])
    tg$k[ok] <- pmin(pmax(kk[ok], -1), 0.85)
  }
  print(paste("warm start from", basename(tail(prev, 1)), ":", sum(same), "cells reuse their previous shock,", sum(!is.na(tg$k)), "with a measured land response"))
  pass_offset <- length(prev)
} else pass_offset <- 0

## ---- 5. calibration passes -------------------------------------------------------------------------------
##  Update: land services of a cell respond to its productivity shock with slope 1 - k (k = -dqes/dafeall, measured
##  from the last two passes; k is 0.77 for an activity whose land is just a value-added factor, near 0 for the
##  crops in the land nests, negative where output expands). afeall <- afeall + damp x shortfall / (1 - k), floored at
##  0 and capped at afe_cap. Stop when the hectare-weighted shortfall is below tol_w points and no cell with more
##  than big_cell_ha is more than tol_big points below its target.
damp <- 0.8; k_default <- 0.3; afe_cap <- 100; tol_w <- 0.3; tol_big <- 1; big_cell_ha <- 50000
cmf_path <- paste0(GTAPAEZ_path, "/NATDEF.cmf")
lines0 <- readLines(cmf_path, warn = FALSE)
cutoff_line <- which(lines0 == "! Part for productivity shocks;")
if (length(cutoff_line) == 0) stop("The line '! Part for productivity shocks;' was not found in BU/NATDEF.cmf")
lines0 <- lines0[1:cutoff_line]
afe_prev <- NULL; qes_prev <- NULL
for (pass in seq_len(max_pass)) {
  on <- tg$afeall_pct > 0
  lines_afe <- if (any(on)) sprintf('shock afeall("%s","%s","%s") = %s;', tg$aez[on], tg$activity[on], tg$region[on],
                                    format(tg$afeall_pct[on], scientific = FALSE, digits = 10)) else character(0)
  lines <- c(lines0, 'Shock tms_f =  file NATDEF.har header "0101";', '! Part for productivity shocks from R;', lines_eudr, lines_bau, lines_afe)
  writeLines(set_solver_lines(lines, "accurate"), cmf_path)
  p_id <- pass + pass_offset
  file.copy(cmf_path, paste0(log_dir, "NATDEF_pass_", p_id, ".cmf"), overwrite = TRUE)
  solve_log <- paste0(log_dir, "Solve_pass_", p_id, ".log")
  mtime_before <- file.info("NATDEF.sl4")$mtime; t0 <- Sys.time()
  status <- system2("GTAPV7-AEZ.exe", c("-cmf", "NATDEF.CMF"), stdout = solve_log, stderr = solve_log)
  face <- suppressWarnings(as.integer(sub('.*"face" number is ([0-9]+).*', "\\1", grep('Variable accuracy "face" number', readLines(solve_log, warn = FALSE), value = TRUE))))
  face <- if (length(face) > 0) tail(face, 1) else NA_integer_
  if (!identical(as.integer(status), 0L) || identical(file.info("NATDEF.sl4")$mtime, mtime_before)) {
    cat(tail(readLines(solve_log, warn = FALSE), 40), sep = "\n"); stop("GEMPACK did not produce a new solution in pass ", p_id, " - see ", solve_log)
  }
  data <- read_SL4('NATDEF.sl4')
  qes <- data[["qes"]]; if (length(dim(qes)) == 4) qes <- qes[, , , 1]
  tg$qes_pct <- sapply(seq_len(nrow(tg)), function(k) qes[tolower(tg$aez[k]), tolower(tg$activity[k]), tolower(tg$region[k])])
  short <- pmax(tg$target_pct - (tg$qes_pct + tg$afeall_pct), 0)                # shortfall below the target (an activity above it is left alone)
  w_short <- sum(tg$hectares * short) / sum(tg$hectares); within1 <- sum(tg$hectares[short < 1]) / sum(tg$hectares)
  big <- tg$hectares >= big_cell_ha; big_short <- if (any(big)) max(short[big]) else 0
  print(paste0("pass ", p_id, ": ", round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1), " min, accuracy face ", face, "/10 | shortfall: hectare-weighted ",
               round(w_short, 2), " points, ", round(100 * within1), " % of the cleared hectares within 1 point, largest in a cell above ", big_cell_ha / 1e3, " kha ",
               round(big_short, 2), " (", tg$region[big][which.max(short[big])], " ", tg$aez[big][which.max(short[big])], " ", tg$activity[big][which.max(short[big])],
               ") | shocks: ", sum(tg$afeall_pct > 0), ", largest ", round(max(tg$afeall_pct), 1), " %"))
  write.table(tg[, setdiff(names(tg), "key")], file = paste0(log_dir, "targets_pass_", p_id, ".txt"), row.names = FALSE)
  if (w_short < tol_w && big_short < tol_big) break
  if (!is.null(afe_prev)) {                                                     # measured response of every cell's land use to its own shock
    d_afe <- tg$afeall_pct - afe_prev; ok <- abs(d_afe) >= 0.5
    tg$k[ok] <- pmin(pmax(-(tg$qes_pct[ok] - qes_prev[ok]) / d_afe[ok], -1), 0.85)
  }
  afe_prev <- tg$afeall_pct; qes_prev <- tg$qes_pct
  kk <- ifelse(is.na(tg$k), k_default, tg$k)
  tg$afeall_pct <- pmin(afe_cap, pmax(0, tg$afeall_pct + damp * (tg$target_pct - (tg$qes_pct + tg$afeall_pct)) / (1 - kk)))
}
if (w_short >= tol_w || big_short >= tol_big) print(paste("not converged after", max_pass, "passes - the shocks of the last pass are written anyway"))

## ---- 6. output, and restore the backup files --------------------------------------------------------------
write.table(tg[, setdiff(names(tg), "key")], file = out_file, row.names = FALSE)
print(paste("written:", out_file, "-", sum(tg$afeall_pct > 0), "afeall shocks in", nrow(tg), "receiving cells; largest", round(max(tg$afeall_pct), 1),
            "%; hectare-weighted shortfall", round(w_short, 2), "points. Now run Baseline_EUDR.R (solve_mode accurate) with bau_eta =", bau_eta))
for (f in c("NATDEF.cmf", "NATDEF.har", "NATDEF.sl4")) file.copy(file.path(parent_folder, "2_Model", "BU", f), file.path(GTAPAEZ_path, f), overwrite = TRUE)
