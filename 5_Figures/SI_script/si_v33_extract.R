## V33 (22 Oct 2026): the 1.25 % club (NATDEF_7.sl4) and the 4,000 coalition (NATDEF_7.sl4) of the Miranda-calibrated runs, baseline _v33; writes to SI_script/data_v33
suppressMessages(library(HARr))
args <- commandArgs(trailingOnly = TRUE)   # Rscript si_v32_extract.R [repo] [output folder]
here <- tryCatch(dirname(normalizePath(sys.frame(1)$ofile)), error = function(e) { f <- grep("^--file=", commandArgs(), value = TRUE); if (length(f)) dirname(normalizePath(sub("^--file=", "", f[1]))) else getwd() })
repo <- if (length(args) >= 1) args[1] else Sys.getenv("FOREST_CLUB_REPO", normalizePath(file.path(here, "..", "..")))
U <- file.path(repo, "3_Output"); OUT <- if (length(args) >= 2) args[2] else file.path(here, "data_v33"); dir.create(OUT, showWarnings = FALSE, recursive = TRUE)
runs <- list(club = file.path(U, "Friction/forest_pha0_tau1.25charged_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v33/Scenario_D/NATDEF_7.sl4"),
             coalition = file.path(U, "Friction/forest_pha4000_tau0_eudr0_bau5_eta0.66_seedEU_outfree_fr0.001trade_sgb_jrexp_frombau_eudrkeep_pinall_wnet_v33/Scenario_D/NATDEF_7.sl4"))
A <- read_SL4(file.path(U, "Baseline_2stage_bau5_eta0.66_v33/A_bau/NATDEF_A.sl4"))
B <- read_SL4(file.path(U, "Baseline_2stage_bau5_eta0.66_v33/B_eudr/NATDEF_B.sl4"))
bd <- read_har(file.path(repo, "2_Model", "in", "basedata.har"))
regs <- dimnames(A[["ev"]])[[1]]
zone <- function(aez) { n <- as.integer(sub("aez", "", aez)); ifelse(n <= 6, "tropical", ifelse(n <= 12, "temperate", "boreal")) }
# ---- 1. forest change of the baseline by region and climate zone (kha): Stage A (vs 2019) and Stage B (vs A)
luc <- function(s) { x <- s[["del_luc"]]; if (length(dim(x)) == 4) x <- x[, , , 1]; x[, "forestland", ] }   # aez x region, kha? (del_luc units)
fa <- luc(A); fb <- luc(B)
rows <- list()
for (r in regs) for (z in c("tropical", "temperate", "boreal")) {
  idx <- zone(rownames(fa)) == z
  rows[[length(rows) + 1]] <- data.frame(region = r, zone = z, stageA = sum(fa[idx, r]), stageB = sum(fb[idx, r]))
}
f1 <- do.call(rbind, rows); write.csv(f1, file.path(OUT, "si_forest_baseline.csv"), row.names = FALSE)
cat("del_luc forest totals: A", sum(fa), "B", sum(fb), "(units of del_luc)\n")
# ---- 2. welfare decomposition at the two equilibria, relative to Stage B (M USD/yr), all regions
dec <- function(s) {
  wedge <- { cq <- s[["cntqe"]]; if (length(dim(cq)) == 3) cq <- cq[, , 1]; colSums(cq[grepl("^aez", rownames(cq)), , drop = FALSE]) }
  alloc <- { a <- s[["cntalleffr"]]; if (length(dim(a)) == 3) a <- a[, , 1]; rowSums(a) }
  tech <- { a <- s[["cnttechr"]]; if (length(dim(a)) == 3) a <- a[, , 1]; colSums(a) }
  data.frame(region = regs, ev_gross = s[["ev"]][regs, 1], wedge = wedge[regs], alloc = alloc[regs], endow = s[["cntendwr"]][regs, 1], tech = tech[regs],
             tot = s[["cnttotr"]][regs, 1], pinv = s[["cntpinv"]][regs, 1], qgdp = s[["qgdp"]][regs, 1], tot_pct = s[["tot"]][regs, 1])
}
dB <- dec(B)
for (nm in names(runs)) {
  s <- read_SL4(runs[[nm]]); d <- dec(s)
  out <- data.frame(region = regs)
  for (v in c("ev_gross", "wedge", "alloc", "endow", "tech", "tot", "pinv", "qgdp", "tot_pct")) out[[v]] <- d[[v]] - dB[[v]]
  out$ev_net <- out$ev_gross - out$wedge
  write.csv(out, file.path(OUT, paste0("si_welfare_decomp_", nm, ".csv")), row.names = FALSE)
  cat(nm, "world: gross", round(sum(out$ev_gross)), "wedge", round(sum(out$wedge)), "net", round(sum(out$ev_net)), "alloc", round(sum(out$alloc)), "tech", round(sum(out$tech)), "tot", round(sum(out$tot)), "pinv", round(sum(out$pinv)), "endow", round(sum(out$endow)), "\n")
  # ---- 3. sectoral supply response: qo (% vs Stage B) and the value of output (MAKS summed over commodities, M USD)
  qo <- s[["qo"]][, , 1] - B[["qo"]][, , 1]   # sector x region
  maks <- bd[["maks"]]; vom <- apply(maks, c(2, 3), sum)   # activity x region (MAKS: commodity x activity x region)
  if (!all(dimnames(qo)[[1]] %in% dimnames(vom)[[1]])) vom <- apply(maks, c(1, 3), sum)
  rows <- list()
  for (r in regs) for (a in dimnames(qo)[[1]]) rows[[length(rows) + 1]] <- data.frame(region = r, sector = a, qo_pct = qo[a, r], vom_musd = vom[a, r])
  write.csv(do.call(rbind, rows), file.path(OUT, paste0("si_supply_", nm, ".csv")), row.names = FALSE)
  # ---- 4. Brazil's commodities and land rents
  r <- "brasil"; rows <- list()
  for (c in c("pdr","wht","gro","v_f","osd","c_b","pfb","ocr","ruminant","rmk","wol","ruminantmeat","dairy","vegoil","pcr","sgr","lea"))
    rows[[length(rows) + 1]] <- data.frame(item = c, qo = qo[c, r], qxw = s[["qxw"]][c, r, 1] - B[["qxw"]][c, r, 1], pxw = s[["pxw"]][c, r, 1] - B[["pxw"]][c, r, 1],
                                           vom_musd = vom[c, r])
  bz <- do.call(rbind, rows); write.csv(bz, file.path(OUT, paste0("si_brazil_", nm, ".csv")), row.names = FALSE)
  rents <- list()
  for (v in c("pecroplnd", "pegrazlnd", "peforslnd")) { x <- s[[v]][, r, 1] - B[[v]][, r, 1]; for (a in names(x)) rents[[length(rents) + 1]] <- data.frame(var = v, aez = a, change_pct = x[[a]]) }
  write.csv(do.call(rbind, rents), file.path(OUT, paste0("si_brazil_rents_", nm, ".csv")), row.names = FALSE)
}
# world price changes at the club (pw) for the 17 commodities
s <- read_SL4(runs[["club"]]); pw <- s[["pw"]][, 1] - B[["pw"]][, 1]; write.csv(data.frame(item = names(pw), pw_pct = pw), file.path(OUT, "si_world_prices_club.csv"), row.names = FALSE)
cat("done\n")
