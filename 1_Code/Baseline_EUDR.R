## =====================================================================================
##  Baseline_EUDR.R  -  sister script of CGE_Game_Theory_GTAPAEZ_all_V16.R
##
##  Solves the baseline ONCE: the EU alone applies the EUDR. Its imports of the covered
##  products from each origin fall by the share of that origin's output that comes from land
##  deforested after the EUDR cut-off (31 Dec 2020): DeDuCE 2021-2023 attributed hectares over
##  the sector's land base (0_External_data/DeDuCE_rework/eudr_cut_shares.xlsx, sheet "shocks").
##  A ban, not a tax: for each cut flow, qxs(c,r,"eu27") is made exogenous and ams(c,r,"eu27"),
##  the iceberg import cost, endogenous - the model solves the cost that produces the cut, and
##  no tariff revenue is created. No border charge, no coalition, no forest commitment.
##
##  Writes 3_Output/Baseline_EUDR/:
##    EV_baseline.txt           region, EV ($M)           -> iteration 0 of the game script
##    ams_baseline.txt          the solved ams per cut flow -> EUDR cost kept on non-members in the game script
##    Forest_LU_baseline_ha.txt forest cover change by region x AEZ (ha)
##    NATDEF_baseline.cmf/.har/.sl4
##  Run it from RStudio like the main script (same folder structure). One solve.
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
out_path   <- file.path(parent_folder, "3_Output", "Baseline_EUDR", "/")
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
cmf_path <- paste0(GTAPAEZ_path, "/NATDEF.cmf")
lines <- readLines(cmf_path, warn = FALSE)
cutoff_line <- which(lines == "! Part for productivity shocks;")
if (length(cutoff_line) == 0) stop("The line '! Part for productivity shocks;' was not found in BU/NATDEF.cmf")
lines <- c(lines[1:cutoff_line],
           'Shock tms_f =  file NATDEF.har header "0101";',
           '! Part for productivity shocks from R;',
           lines_eudr)
writeLines(lines, cmf_path)
file.copy(cmf_path, paste0(out_path, "NATDEF_baseline.cmf"), overwrite = TRUE)
print(paste("EUDR baseline:", nrow(cuts), "EU import flows cut, scale", eudr_scale))

## ---- 3. solve --------------------------------------------------------------------------------
system2("GTAPV7-AEZ.exe", c("-cmf", "NATDEF.CMF"))

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

file.copy("NATDEF.sl4", paste0(out_path, "NATDEF_baseline.sl4"), overwrite = TRUE)
file.copy("NATDEF.har", paste0(out_path, "NATDEF_baseline.har"), overwrite = TRUE)

## ---- 5. restore the backup files so RunGTAP and the game script start clean -------------------
for (f in c("NATDEF.cmf", "NATDEF.har", "NATDEF.sl4")) {
  file.copy(file.path(parent_folder, "2_Model", "BU", f), file.path(GTAPAEZ_path, f), overwrite = TRUE)
}
print(paste("Baseline solved. EV (eu27):", round(values_EV[region_sets == "eu27"], 2),
            "- results in", out_path))
