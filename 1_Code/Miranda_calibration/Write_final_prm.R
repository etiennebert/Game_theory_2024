## =====================================================================================
##  Write_final_prm.R  -  the parameter file of the new run from a calibration result (20 October 2026)
##
##  Reads ETR1_calibrated.csv of a calibration run and writes default_miranda_final.prm = in/default.prm + header ETR1
##  (18 AEZs x 42 regions), where
##    - a Miranda cell whose achieved response is within `keep_within` of its target takes its calibrated value;
##    - with option "B", a Miranda cell that is not at a bound and reached at least `partial_floor` of its target also
##      takes its calibrated value (the closest the model gets);
##    - every other cell (bound cells, non-responding cells, the Miranda cells the model cannot move, and the
##      non-Miranda cells) takes `fill_value`, the TAB's default that every V32 run used.
##  Also writes ETR1_final_decisions.csv (one row per Miranda cell: target, achieved, value written, reason) and
##  ETR1_final_log.txt. Run from RStudio like the calibration script; nothing in 2_Model/in is modified.
##  To use the file: copy it over 2_Model/in/default.prm (keep the original as default_v7defaults.prm), then run
##  Calibrate_BAU_productivity.R, Baseline_2stage.R and Run_V32_all.R under the new version tag.
## =====================================================================================
rm(list = ls())
library(HARr)
library(rstudioapi)
script_folder <- dirname(getSourceEditorContext()$path)
parent_folder <- dirname(dirname(script_folder))
setwd(file.path(parent_folder, "2_Model"))

## ---- settings ---------------------------------------------------------------------------------------------
source_csv    <- file.path(parent_folder, "3_Output", "Miranda_calibration_drc_check2", "ETR1_calibrated.csv")   # the calibration to use
out_path      <- paste0(file.path(parent_folder, "3_Output", "Miranda_calibration_final"), "/")
option        <- "A"        # "A": calibrated values only where the model reached the target | "B": also the partly reached cells
keep_within   <- 0.10       # a cell is "reached" when |achieved / target - 1| is below this
partial_floor <- 0.50       # option B: a cell not at a bound that reached at least this share of its target keeps its calibrated value
fill_value    <- -0.25      # every other cell: the TAB's default (gtapv7-aez.tab uses -0.25 when the parameter file has no ETR1)
bounds        <- c(-5, -0.02)
install       <- TRUE       # TRUE: back up 2_Model/in/default.prm as in/default_v7defaults.prm (once) and copy the new file over it, so that
                            # Calibrate_BAU_productivity.R, Baseline_2stage.R and the game (all of which read in/default.prm through BU/NATDEF.cmf) use it

dir.create(out_path, recursive = TRUE, showWarnings = FALSE)
logf <- paste0(out_path, "ETR1_final_log.txt"); cat("", file = logf)
say <- function(...) { msg <- paste0(...); print(msg); cat(msg, "\n", file = logf, append = TRUE) }

## ---- sets --------------------------------------------------------------------------------------------------
sets <- read_har("in/sets.har")
reg_v12 <- tolower(as.character(unlist(sets[["reg"]]))); aez_v12 <- tolower(as.character(unlist(sets[["aezs"]])))

## ---- the calibration result --------------------------------------------------------------------------------
cal <- read.csv(source_csv, stringsAsFactors = FALSE)
cal$calibrate <- cal$calibrate %in% c(TRUE, "TRUE"); cal$at_bound <- cal$at_bound %in% c(TRUE, "TRUE")
last_pass <- max(as.integer(sub("eps_model_pass", "", grep("^eps_model_pass", names(cal), value = TRUE))))
cal$achieved <- cal[[paste0("eps_model_pass", last_pass)]]
mir <- cal[is.finite(cal$eps_target), ]                                             # the 44 Miranda cells
say("source: ", source_csv, " (", last_pass + 1, " passes); option ", option, ", keep within ", 100 * keep_within, " %",
    if (option == "B") paste0(", partial floor ", 100 * partial_floor, " %") else "", ", fill value ", fill_value)

decide <- function(r) {
  if (!r$calibrate) return(list(value = fill_value, reason = "the model cannot move land in the cell (no forest, agriculture or forestry rent)"))
  if (!is.finite(r$achieved) || r$achieved <= 0) return(list(value = fill_value, reason = "no usable response"))
  ratio <- r$achieved / r$eps_target
  if (abs(ratio - 1) < keep_within) return(list(value = r$etr1_final, reason = sprintf("calibrated (achieved %.0f %% of the target)", 100 * ratio)))
  if (r$at_bound) return(list(value = fill_value, reason = sprintf("at the bound of %g with %.0f %% of the target: unreachable", bounds[1], 100 * ratio)))
  if (option == "B" && ratio >= partial_floor) return(list(value = r$etr1_final, reason = sprintf("option B: closest achievable (%.0f %% of the target)", 100 * ratio)))
  list(value = fill_value, reason = sprintf("partly reached (%.0f %% of the target): default kept under option %s", 100 * ratio, option))
}
dec <- do.call(rbind, lapply(seq_len(nrow(mir)), function(i) { d <- decide(mir[i, ])
  data.frame(aez = mir$aez[i], region = mir$region[i], eps_target = mir$eps_target[i], achieved = round(mir$achieved[i], 4),
             etr1_calibrated = round(mir$etr1_final[i], 4), etr1_written = round(d$value, 4), reason = d$reason, stringsAsFactors = FALSE) }))
write.csv(dec, paste0(out_path, "ETR1_final_decisions.csv"), row.names = FALSE)
for (i in seq_len(nrow(dec))) say(sprintf("  %-11s %-5s target %.3f achieved %6.3f -> ETRAEL1 %6.3f  (%s)", dec$region[i], dec$aez[i], dec$eps_target[i], dec$achieved[i], dec$etr1_written[i], dec$reason[i]))
say(sum(dec$etr1_written != fill_value), " of the 44 Miranda cells carry a calibrated value; every other cell of the 18 x 42 matrix carries ", fill_value)

## ---- the matrix and the file ----------------------------------------------------------------------------------
etr1 <- matrix(fill_value, 18, length(reg_v12), dimnames = list(AEZS = aez_v12, REG = reg_v12))
idx <- cbind(match(dec$aez, aez_v12), match(dec$region, reg_v12))
if (any(is.na(idx))) stop("a Miranda cell is not in the v12 sets: ", paste(dec$region[is.na(idx[, 2])], dec$aez[is.na(idx[, 1])]))
etr1[idx] <- pmin(pmax(dec$etr1_written, bounds[1]), bounds[2])
prm <- read_har("in/default.prm")
x <- array(etr1, dim = c(18, length(reg_v12)), dimnames = list(AEZS = aez_v12, REG = reg_v12))
attr(x, "description") <- "elast. of AEZ land transformation: top nest (Miranda 2024)"
prm[["etr1"]] <- x
out_file <- paste0(out_path, "default_miranda_final.prm")
write_har(prm, out_file, maxSize = 1e5)
back <- read_har(out_file)
if (!("etr1" %in% names(back)) || !isTRUE(all.equal(as.numeric(back[["etr1"]]), as.numeric(x), tolerance = 1e-6))) stop("ETR1 did not round-trip in ", out_file)
say("written: ", out_file, " (in/default.prm + header ETR1; round trip checked) and ", paste0(out_path, "ETR1_final_decisions.csv"))
if (install) {
  if (!file.exists("in/default_v7defaults.prm")) { file.copy("in/default.prm", "in/default_v7defaults.prm"); say("backup: in/default.prm saved as in/default_v7defaults.prm") }
  else say("backup in/default_v7defaults.prm already exists - kept")
  file.copy(out_file, "in/default.prm", overwrite = TRUE)
  chk <- read_har("in/default.prm"); if (!("etr1" %in% names(chk))) stop("in/default.prm has no ETR1 header after the copy")
  say("installed: 2_Model/in/default.prm now carries the ETR1 header (", sum(dec$etr1_written != fill_value), " calibrated cells, ", fill_value, " elsewhere); to go back to V32, copy in/default_v7defaults.prm over it")
} else say("to use it: copy it over 2_Model/in/default.prm (keep the original as default_v7defaults.prm); every script reads in/default.prm through BU/NATDEF.cmf")
