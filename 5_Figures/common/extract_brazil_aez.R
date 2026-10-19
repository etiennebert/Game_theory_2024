## Brazil's land use by agro-ecological zone at the club equilibrium, from the GEMPACK solutions (needs R + HARr).
## The two-stage baseline: Stage A (business-as-usual clearing over five years, solved on the 2019 data -> gdata_bau.upd) and
## Stage B (the EUDR, solved on the Stage A data: the paper's baseline, "the EUDR world"). Every game solve starts from the Stage A
## data too, so the club's changes and Stage B's changes are measured from the same level, and the club relative to the baseline is
## (club change - Stage B change). Levels: 2019 from basedata.har; EUDR world = 2019 + A + B; club = 2019 + A + club.
## Writes brazil_aez_<label>.csv next to this script: one row per instrument x AEZ x item with the 2019 level and the three
## changes (Stage A, Stage B, club), all in kha. Items: the land covers (forestland, cropland, pastureland) from del_luc, the eight
## crops from del_harvarea (harvested area), and the national output change of the land-using sectors (qo, % - not kha).
## The runs come from brazil_runs_<label>.txt (written by extract_all.py: instrument, run folder, converged solution file).
## Usage: Rscript extract_brazil_aez.R [repo] [label]   (defaults: FOREST_CLUB_REPO / C:/runGTAP375/Game_theory_2024, V32)
suppressMessages(library(HARr))
args  <- commandArgs(trailingOnly = TRUE)
repo  <- if (length(args) >= 1) args[1] else Sys.getenv("FOREST_CLUB_REPO", "C:/runGTAP375/Game_theory_2024")
label <- if (length(args) >= 2) args[2] else { v <- Sys.getenv("FOREST_CLUB_VERSION", "_wnet_v32"); c("_wnet_v32" = "V32", "_wnet" = "V31")[v] }
if (is.na(label)) label <- "V30"
here  <- tryCatch(dirname(normalizePath(sys.frame(1)$ofile)), error = function(e) {
  f <- grep("^--file=", commandArgs(), value = TRUE); if (length(f)) dirname(normalizePath(sub("^--file=", "", f[1]))) else getwd() })
runs_file <- file.path(here, paste0("brazil_runs_", label, ".txt"))
if (!file.exists(runs_file)) stop("no ", runs_file, " - run extract_all.py first")
runs <- read.table(runs_file, col.names = c("instrument", "folder", "sl4"), stringsAsFactors = FALSE)
r <- "brasil"
bd <- read_har(file.path(repo, "2_Model/in/basedata.har"))
BASE <- file.path(repo, "3_Output/Baseline_2stage_bau5_eta0.66")
A <- read_SL4(file.path(BASE, "A_bau/NATDEF_A.sl4"))
B <- read_SL4(file.path(BASE, "B_eudr/NATDEF_B.sl4"))
aezs <- paste0("aez", 1:18); crops <- c("pdr", "wht", "gro", "v_f", "osd", "c_b", "pfb", "ocr"); covs <- c("forestland", "cropland", "pastureland")
acts <- c(crops, "ruminant", "rmk", "wol", "ruminantmeat", "dairy", "vegoil", "sgr", "pcr")
rows <- list()
for (k in seq_len(nrow(runs))) {
  inst <- runs$instrument[k]; f <- file.path(repo, "3_Output/Friction", runs$folder[k], "Scenario_D", runs$sl4[k])
  if (!file.exists(f)) { cat("missing", f, "- skipped\n"); next }
  sol <- read_SL4(f)
  for (a in aezs) {
    for (cv in covs) rows[[length(rows) + 1]] <- data.frame(instrument = inst, aez = a, item = cv, level_2019_kha = bd[["lcov"]][a, cv, r],
      stageA_change_kha = A[["del_luc"]][a, cv, r, 1], stageB_change_kha = B[["del_luc"]][a, cv, r, 1], club_change_kha = sol[["del_luc"]][a, cv, r, 1])
    for (cr in crops) rows[[length(rows) + 1]] <- data.frame(instrument = inst, aez = a, item = cr, level_2019_kha = bd[["area"]][a, cr, r],
      stageA_change_kha = A[["del_harvarea"]][a, cr, r, 1], stageB_change_kha = B[["del_harvarea"]][a, cr, r, 1], club_change_kha = sol[["del_harvarea"]][a, cr, r, 1])
  }
  for (ac in acts) rows[[length(rows) + 1]] <- data.frame(instrument = inst, aez = "national", item = paste0("qo_", ac), level_2019_kha = NA,
    stageA_change_kha = A[["qo"]][ac, r, 1], stageB_change_kha = B[["qo"]][ac, r, 1], club_change_kha = sol[["qo"]][ac, r, 1])   # % changes, not kha
  fo <- sum(sol[["del_luc"]][aezs, "forestland", r, 1]); fa <- sum(A[["del_luc"]][aezs, "forestland", r, 1]); fb <- sum(B[["del_luc"]][aezs, "forestland", r, 1])
  cat(sprintf("%-9s %s: Brazil forest  Stage A %+.1f kha  Stage B %+.1f kha  club %+.1f kha  -> club vs the EUDR world %+.1f kha\n", inst, runs$sl4[k], fa, fb, fo, fo - fb))
}
out <- do.call(rbind, rows)
f_out <- file.path(here, "..", "data", paste0("brazil_aez_", label, ".csv"))   # 5_Figures\data\
write.csv(out, f_out, row.names = FALSE)
cat("wrote", f_out, nrow(out), "rows\n")
