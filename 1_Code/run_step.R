## Rscript run_step.R <script name>: runs one script of this folder outside RStudio (run_chain_v34.bat calls it three times).
## The scripts find the model folder from the RStudio API; under Rscript the environment variable FOREST_CLUB_SCRIPT gives them their
## own path instead. The script's console output goes to the terminal; an error ends Rscript with a non-zero status (the .bat stops).
a <- commandArgs(trailingOnly = TRUE); f <- grep("^--file=", commandArgs(), value = TRUE)
here <- dirname(normalizePath(sub("^--file=", "", f[1])))
if (length(a) < 1 || !file.exists(file.path(here, a[1]))) stop("usage: Rscript run_step.R <script in ", here, ">")
Sys.setenv(FOREST_CLUB_SCRIPT = normalizePath(file.path(here, a[1])))
cat(format(Sys.time()), "run_step:", a[1], "\n")
source(file.path(here, a[1]), local = FALSE, echo = FALSE)
