## =====================================================================================
##  Forest Coalition rework - drop-in replacements for CGE_Game_Theory_GTAPAEZ_all_V13R1.R
##  source() this file after the "## Parameters" block of the main script.
##  It replaces: shock_values_tmsf / shock_ABCD / shock_CD (producer tariffs),
##               shock_BD / shock_D / non-producer branch of shock_eu27 (consumer penalty),
##               generate_text_for_qes (member commitment).
## =====================================================================================

## ---- run parameters -----------------------------------------------------------------
p_ha_tag <- "AVE_pha400"   # AVE_pha400 | AVE_pha2000 | AVE_pha10000 | AVE_co2_50 | AVE_co2_100 | AVE_co2_190
tau      <- 0              # flat penalty tariff (%) on NON-PRODUCER non-members: 0 = coalition, >0 = club (Nordhaus)
rework_path <- paste0(external_data_path, "/DeDuCE_rework/")

## sectors that carry the border charge (primary land-using incl. dairy/wool + processed carriers)
list_commodity <- c("sgr","ruminant","gro","ocr","osd","pcr","pfb","v_f","wht","rmk","wol",
                    "RuminantMeat","dairy","vegoil","lea","pdr","c_b")
## sectors used to decide where the member forest constraint is material (your qes sheets)
list_commodity_land <- c("sgr","ruminant","gro","ocr","osd","pcr","pfb","v_f","wht")

## ---- 1. border charge: bilateral tms_f shocks from DeDuCE-based AVEs --------------------
## shock = 100 x AVE(c, source) / (1 + t0(c, source, dest));  AVE = p_ha x h_total (see h_table_DeDuCE.xlsx)
tmsf_bil <- read.csv(paste0(rework_path, "tms_f_shocks_bilateral_", p_ha_tag, ".csv"), stringsAsFactors = FALSE)
tmsf_lookup <- setNames(tmsf_bil$shock_tms_f_pct,
                        tolower(paste(tmsf_bil$comm, tmsf_bil$source, tmsf_bil$dest, sep = "|")))
get_shock <- function(commodity, source, dest) {
  v <- tmsf_lookup[tolower(paste(commodity, source, dest, sep = "|"))]
  ifelse(is.na(v), 0, as.numeric(v))
}

## ONE rule for every non-member exporting into any member (replaces shock_eu27, shock_ABCD,
## shock_CD, shock_BD, shock_D):   charge = footprint-based AVE shock  +  tau
##   coalition (tau = 0): only the footprint counts, so a consumer with no deforestation pays 0
##   club (tau > 0):      everybody outside also pays the flat Nordhaus penalty
## The footprint charge is origin-neutral: any region with attributed deforestation in DeDuCE
## (LatinAmer, SEAsia, CAfr, Nigeria, ...) gets its own rate, not only the twelve producers.
shock_outsiders_into_members <- function(shock, members, outsiders) {
  for (m in members) for (o in outsiders) for (cm in list_commodity)
    shock[["0101"]][cm, o, m] <- get_shock(cm, o, m) + tau
  shock
}

## members do not charge each other
shock_members_zero <- function(shock, members) {
  for (a in members) for (b in members) if (a != b) for (cm in list_commodity)
    shock[["0101"]][cm, a, b] <- 0.0
  shock
}

## ---- 2. member commitment: no net forest loss per AEZ, forest-land subsidy endogenous -----
## Note: forest commitments are written only for members in list_producer_countries (the twelve with
## qes sheets, i.e. with AEZ-level coefficients). Other regions can join as consumers (tariff only).
## Replaces the qes/afeall swaps. For each member producer and each AEZ where your Eq.10
## coefficient is material (any negative entry in qes_values.xlsx for that AEZ), hold the
## Forestland cover at baseline and let tinc(AEZ,"forest",r) - the income tax/subsidy on
## forest land - absorb it. tinc is exogenous in the closure, so the swap is legal as is.
## Two-pass use: pass 1 with forest_change = NULL and bind_all = FALSE writes NO constraint;
## read del_LUC from the SL4, then pass 2 binds only the AEZs where forest fell.
aez_is_material <- function(producer, i) {
  any(sapply(list_commodity_land, function(cm) {
    v <- get(sprintf("shock_value_aez_%d", i), inherits = TRUE)[[producer]][[cm]]
    is.finite(v) && v < 0
  }))
}
generate_text_for_forest <- function(club_producer, forest_change = NULL, bind_all = FALSE) {
  out <- character(0)
  for (producer in club_producer) {
    for (i in 1:18) {
      aez <- sprintf("AEZ%d", i)
      if (!aez_is_material(producer, i)) next
      falls <- if (bind_all) TRUE else (!is.null(forest_change) && isTRUE(forest_change[[producer]][[aez]] < 0))
      if (falls) {
        out <- c(out,
          sprintf('swap p_LANDCOVER_L("%s","Forestland","%s") = tinc("%s","forest","%s");', aez, producer, aez, producer),
          sprintf('shock p_LANDCOVER_L("%s","Forestland","%s") = 0;', aez, producer))
      }
    }
  }
  out
}

## forest change by member x AEZ from the last solution (for the two-pass logic)
read_forest_change_by_aez <- function(sl4 = "NATDEF.sl4", producers) {
  d   <- read_SL4(sl4)
  nm  <- names(d)[tolower(names(d)) == "del_luc"]
  luc <- d[[nm]]                               # HARr: AEZS x LCOV x REG (x subtotal column)
  if (length(dim(luc)) == 4) luc <- luc[, , , 1]
  dn  <- dimnames(luc)
  li  <- match("forestland", tolower(dn[[2]]))
  res <- list()
  for (p in producers) {
    ri <- match(tolower(p), tolower(dn[[3]]))
    res[[p]] <- setNames(as.list(luc[, li, ri]), dn[[1]])
  }
  res
}

## ---- 3. transfers and stability (post-processing, no model change) -----------------------
## ev_in : named EV vector of the equilibrium with member i inside
## ev_out: named EV vector of the deviation run with member i outside
transfer_needed <- function(ev_in, ev_out, member) max(0, ev_out[[member]] - ev_in[[member]])

## coalition tariff revenue on the charged sectors, from the updated data (VMSB - VCIF summed
## over charged commodities, non-member sources, member destinations); read with HARr from gdata.upd
coalition_revenue <- function(upd = "gdata.upd", members, outsiders) {
  g <- read_har(upd); vmsb <- g[["vmsb"]]; vcif <- g[["vcif"]]
  dn <- dimnames(vmsb); cm <- tolower(dn[[1]]); src <- tolower(dn[[2]]); dst <- tolower(dn[[3]])
  ci <- which(cm %in% tolower(list_commodity)); si <- which(src %in% tolower(outsiders)); di <- which(dst %in% tolower(members))
  sum(vmsb[ci, si, di] - vcif[ci, si, di])
}
