suppressMessages(library(HARr))
args <- commandArgs(trailingOnly = TRUE)   # Rscript brazil_v32.R [repo]
here <- tryCatch(dirname(normalizePath(sys.frame(1)$ofile)), error = function(e) { f <- grep("^--file=", commandArgs(), value = TRUE); if (length(f)) dirname(normalizePath(sub("^--file=", "", f[1]))) else getwd() })
repo <- if (length(args) >= 1) args[1] else Sys.getenv("FOREST_CLUB_REPO", normalizePath(file.path(here, "..", "..")))
U <- file.path(repo, "3_Output")
files <- list(A_bau  = file.path(U, "Baseline_2stage_bau5_eta0.66/A_bau/NATDEF_A.sl4"),
              B_eudr = file.path(U, "Baseline_2stage_bau5_eta0.66/B_eudr/NATDEF_B.sl4"),
              club   = file.path(U, "Friction/forest_pha0_tau1.5charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32/Scenario_D/NATDEF_7.sl4"),
              coal   = file.path(U, "Friction/forest_pha4000_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v32/Scenario_D/NATDEF_6.sl4"))
regs <- c("brasil","argentina","paraguay","ivorycoast","nigeria","indonesia","malasya","eu27","us","china","japan","mena")
comp <- c("ev","cntalleffr","cnttechr","cnttotr","cntpinv")
S <- list(); M <- list()
for (nm in names(files)) {
  s <- read_SL4(files[[nm]]); S[[nm]] <- s
  m <- sapply(comp, function(v) { a <- s[[v]]; x <- if (length(dim(a)) == 2) a[, 1] else if (length(dim(a)) == 3) apply(a, 2, sum) else a; x <- x[regs]; c(x, world = sum(if (length(dim(a)) == 2) a[, 1] else if (length(dim(a)) == 3) apply(a, 2, sum) else a)) })
  cq <- s[["cntqe"]]; if (length(dim(cq)) == 3) cq <- cq[, , 1]
  aez <- grepl("^aez", tolower(dimnames(cq)[[1]])); w <- colSums(cq[aez, , drop = FALSE])
  m <- cbind(m, wedge = c(w[regs], world = sum(w))); m <- cbind(m, ev_net = m[, "ev"] - m[, "wedge"])
  M[[nm]] <- m
}
cat("\n== Stage A (BAU clearing on 2019), M USD per year\n"); print(round(M[["A_bau"]]))
cat("\n== Stage B (EUDR on Stage A)\n"); print(round(M[["B_eudr"]]))
cat("\n== club minus Stage B (the paper's frame), M USD per year\n")
for (nm in c("club", "coal")) { cat("--", nm, "\n"); print(round(M[[nm]] - M[["B_eudr"]])) }
b <- S[["B_eudr"]]; r <- "brasil"
for (nm in c("club", "coal")) {
  s <- S[[nm]]
  d2 <- function(v, i, j) s[[v]][i, j, 1] - b[[v]][i, j, 1]
  d1 <- function(v, i) s[[v]][i, 1] - b[[v]][i, 1]
  cat("\n==", nm, ": Brazil, club minus Stage B (pp)\n")
  for (c in c("osd","gro","c_b","ruminant","ruminantmeat","sgr","vegoil","dairy","pfb","ocr")) cat(sprintf("   %-13s qo %+6.2f  qxw %+6.2f  pxw %+6.2f  ps(own) %+6.2f\n", c, d2("qo", c, r), d2("qxw", c, r), d2("pxw", c, r), s[["ps"]][c, c, r, 1] - b[["ps"]][c, c, r, 1]))
  cat(sprintf("   tot %+.3f  qgdp %+.4f  pgdp %+.3f\n", d1("tot", r), d1("qgdp", r), d1("pgdp", r)))
  for (v in c("pecroplnd","pegrazlnd","peforslnd")) { x <- s[[v]][, r, 1] - b[[v]][, r, 1]; x <- x[abs(x) > 0.5]; cat(sprintf("   %s: %s\n", v, paste(sprintf("%s %+.1f", names(x), x), collapse = " "))) }
  q <- s[["qgdp"]][, 1] - b[["qgdp"]][, 1]; q <- sort(q); cat("   qgdp all regions, lowest: ", paste(sprintf("%s %+.3f", names(q)[1:6], q[1:6]), collapse = "  "), "\n")
  # world prices of the land-based goods (pxw aggregated? use pw if exists)
  if (!is.null(s[["pw"]])) { pw <- s[["pw"]][, 1] - b[["pw"]][, 1]; cat("   world prices pw (pp):", paste(sprintf("%s %+.2f", names(pw), pw)[1:20], collapse = " "), "\n") }
}
