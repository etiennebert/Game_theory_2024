
## Read ME - Start -
# Right now the program loop over the four different scenarios. 
# It stops the scenario x if there is no equilibrium after 300 iterations
# In the case you want to run the four scenario just press ctrl + alt + R (PS: don't forget to uncomment section ##Package installation if you run it for the first time )
# In the case you want to run one particular scenario (and not the four at one): See section ##scenario

## Parameters that can be modify if relevant:
#qo = located in this script ##External values 
#afe = located in this script ##External values 
## Read ME - End

## V14 (Sept 2026) - changes relative to V13R1, all marked "V14:" in the code
##  1. Border-charge values come from 0_External_data/DeDuCE_rework/tms_f_initial_shocks_DeDuCE.xlsx,
##     sheet tmsf_sheet (default AVE_pha400 = 400 $/ha of embodied deforestation), instead of tms_f_initial_shocks.xlsx
##  2. The charge applies to every column of that sheet (17 sectors: the nine of V13 + rmk, wol, ruminantmeat,
##     dairy, vegoil, lea, pdr, c_b) through list_commodity_tmsf; list_commodity (qes/qo/qxw commitments) is unchanged
##  3. Iteration 0 (EU alone charging the twelve producers) is solved by the script with the new values;
##     V13 read it from 2_Model/BU/NATDEF.sl4, which was solved with the old values written in BU/NATDEF.cmf
##  4. Outputs go to 3_Output/<approach>/<parameter>_<run_tag>/<scenario>/ and 4_DB/..._<run_tag>.csv,
##     so the V13 results are not overwritten
##  Everything else (qes/afeall member commitment, flat mean penalty on non-producer outsiders, thresholds) is unchanged.

## V15 (Sept 2026) - changes relative to V14, all marked "V15:" in the code
##  1. New member commitment, parameter "forest": in every AEZ where a member producer's forest cover would fall,
##     Forestland cover is held at its base level (p_LANDCOVER_L = 0) and tinc(AEZ,"forest",r), the income tax on
##     forest land, becomes endogenous - the model solves the forest-land subsidy that keeps the land in forest.
##     Replaces the qes/afeall land cuts of V13/V14 (which paid for the cut with a free land-productivity gain).
##  2. One-sided: AEZs where forest grows are left alone. Each iteration is solved once without the commitment,
##     the AEZs where forest fell are bound, and it is solved again (up to max_pass solves).
##  3. Diagnostics per iteration: Forest_commitment_<i>.txt = bound AEZ x member cells, solved tinc (% change in the
##     power of the tax on forest-land income, negative = subsidy), number of passes, cells still falling if any.
##  4. Outputs go to 3_Output/<approach>/forest_<run_tag>/<scenario>/ and 4_DB/..._agg_forest_<run_tag>.csv.
##  Border charge, joining thresholds and everything else exactly as in V14. The old "qo", "qes", "qxw" still run.

## V16 (Sept 2026) - changes relative to V15, all marked "V16:" in the code
##  1. Iteration 0 is the EUDR baseline solved once by the sister script 1_Code/Baseline_EUDR.R (the EU alone
##     excludes the share of each origin's covered products that comes from post-2020 deforestation; a ban, no
##     revenue). Its EV (3_Output/Baseline_EUDR/EV_baseline.txt) replaces the EU-alone charge solved by V14/V15.
##  2. eudr_in_loop = "outsiders": in every iteration the EU keeps the EUDR cost of the baseline (the solved
##     iceberg cost ams of each cut flow) on non-members' exports; members are deemed compliant (cost 0).
##     "none": the coalition replaces the EUDR. Written as "shock ams(...)" lines in each iteration's CMF.
##  3. Outputs go to 3_Output/<approach>/forest_<run_tag>_eudr/<scenario>/ (run_tag gets "_eudr", or "_eudr0"
##     with eudr_in_loop = "none"), so the V15 run is not overwritten.
##  Border charge, forest commitment, thresholds and everything else exactly as in V15.

## V17 (Sept 2026) - changes relative to V16, all marked "V17:" in the code
##  1. ONE border-charge rule: every non-member pays, into every member (the EU is always a member), its own
##     footprint charge from the bilateral table tms_f_shocks_bilateral_<tmsf_sheet>.csv (100 x AVE / (1 + t0),
##     origin-neutral: every region with attributed deforestation has its own rate)  +  tau.
##       tau = 0  -> coalition: a non-member without deforestation pays nothing
##       tau > 0  -> club: every non-member also pays the flat penalty tau (% on the tariff power), on the 17
##                   charged sectors (tau_scope = "charged") or on every commodity (tau_scope = "all", Nordhaus)
##     Members do not charge each other. Replaces the six V13 functions (producer rate from the sheet, flat MEAN
##     on non-producers) - those functions are still defined but no longer called.
##  2. Run configuration (tmsf_sheet, tau, tau_scope, eudr_in_loop, approach) can be passed by
##     1_Code/Run_overnight.R through the list run_config; set here otherwise. run_tag = <price>_tau<tau><scope>_eudr.
##  3. Robustness for unattended runs: an iteration where nobody is inside no longer crashes.
##  Forest commitment, EUDR baseline, thresholds and everything else exactly as in V16.

## V18 (Sept 2026) - one fix in the join/leave rule, marked "V18:" (found on the first overnight run)
##  The rule sends a region OUTSIDE if (outside and EV rose) or (outside and EV fell by less than its threshold)
##  or (inside and EV fell by more than its threshold), and INSIDE otherwise. When nobody moves between two
##  iterations the two runs are identical, EV is exactly equal, "rose" and "fell" are both false, and the
##  "otherwise" put every outsider inside - the whole world joined in one step. Now an outsider whose EV did not
##  fall stays outside (>= instead of >), and a region with EV exactly 0 in the baseline starts outside.
##  Everything else exactly as in V17.

## V19 (Sept 2026) - speed and robustness for the exploration runs, all marked "V19:"
##  1. solve_mode = "fast": Gragg 2-4-6, one subinterval, no automatic-accuracy iteration, no XAC/SLC files
##     (about one minute per solve instead of 3-9); "accurate" = the RunGTAP settings of BU/NATDEF.cmf.
##  2. Every solve is checked (solver exit code, a new SL4 written, finite EV, bound forest AEZs really at 0);
##     a bad solve is re-run once with heavier settings (Gragg 4-8-12, 3 subintervals), then the run stops with
##     a clear message. The solver output of each solve is kept in Solve_iter_<i>_pass_<p>.log.
##  3. The solution file is read once per solve and reused (was read up to eight times per iteration).
##  4. max_pass (forest-commitment passes per iteration) is a run parameter, default 2 (was 3).
##  5. join_rule = "consecutive" (V13 rule: EV against the previous round) or "baseline" (EV against the EUDR
##     baseline: a region joins once it is more than threshold_down below the baseline, leaves once inside it is
##     more than threshold_up below it - path-independent). Default "consecutive", i.e. unchanged.

## V20 (Sept 2026) - outputs, marked "V20:"
##  1. GDP_round_<l>.txt: real GDP change (%, qgdp) of every run, next to Equivalent_Variation_round_<l>.txt;
##     column GDP_pct in the csv.
##  2. The csv now pairs each run's EV with the membership that produced it. Iter_Region_<l> / Reset_Region_<l>
##     are the sets decided AFTER run l (they produce run l+1), so their Club column belonged one row later;
##     iteration 0 (the baseline) is all "outside".
##  3. In the _agg csv the AEZ groups were swapped: AEZ1-6 are tropical, AEZ13-18 boreal (as split_countries
##     has always had it). Column "Tropical" is now AEZ1-6, "Boreal" AEZ13-18.
##  4. The cached solution is cleared when a scenario starts (several approaches in one call read a stale one).

## V21 (Sept 2026) - business-as-usual clearing in the baseline, marked "V21:"
##  1. bau_horizon > 0 (default 5): iteration 0 is the baseline solved by Baseline_EUDR.R with the EUDR AND the
##     observed clearing of every region x AEZ cell of bau_deforestation.xlsx (DeDuCE rate x horizon), folder
##     3_Output/Baseline_EUDR_bau<horizon>/. The baseline returns tinc*, the implicit clearing incentive per cell.
##  2. In every iteration: non-members keep their clearing incentive ("shock tinc(AEZ,forest,r) = tinc*", forest
##     endogenous, so leakage can happen); members are pinned ("swap p_LANDCOVER_L = tinc; shock 0" = no net loss),
##     whichever region they are - the commitment is open to every region with attributed clearing.
##  3. One solve per iteration (the pass loop of V15 is only used when bau_horizon = 0). Forest_commitment_<i>.txt
##     lists the pinned cells with the solved subsidy tinc (negative = payment holding the forest) and tinc*.
##  4. run_tag gets "_bau<horizon>". Everything else exactly as in V20.

## V22 (Sept 2026) - explicit starting coalition and a stability check, marked "V22:"
##  1. seed = the regions inside at iteration 1 (the EU always is), e.g. "eu27,brasil,argentina,paraguay,uruguay";
##     "auto" = the V13-V21 start (every region whose baseline EV is below -threshold_down). From the seed the
##     join/leave rule runs exactly as before (simultaneous moves, thresholds, convergence) - dynamics = "on";
##     dynamics = "off" solves the seed once and stops (the seed IS the coalition).
##  2. friction = "sheet" (thresholds from <approach>/Thresholds_GTAPAEZ_Game_theory.xlsx, as before) or a number:
##     both thresholds = friction x GDP of the region (GDP_values.xlsx, $M), e.g. 0.0001 = 0.01 % of GDP.
##  3. stability = TRUE: one-deviation check of the final coalition S (d'Aspremont et al. 1983). Every test starts
##     again from S and moves ONE region - each member (EU excepted) alone out, each outsider of stability_scope
##     alone in - one solve per test. S is internally stable if no member gains by leaving, externally stable if
##     no outsider gains by joining. Also reported: the transfer that would keep each leaver, what the members
##     who prefer S could pay, and the duty the charge raises (gdata.upd, VMSB x s / (100 + s)).
##     Stability_summary.txt / Stability_tests.txt / Stability_EV_by_test.txt in the run folder; the summary and
##     the table also in 4_DB/Stability_<approach>_<run_tag>.txt. Requires bau_horizon > 0 and parameter "forest".
##  4. run_tag gets "_seed<seed_name>" (and "_fixed" when dynamics = "off"). Everything else exactly as in V21.

## V23 (Sept 2026) - how non-members carry the BAU clearing, and a solve-accuracy gate, marked "V23:"
##  1. bau_outsiders = "cover" (default): a non-member's forest cover follows the BAU path exactly as in the baseline
##     ("swap p_LANDCOVER_L = tinc; shock p_LANDCOVER_L = -x" per cell) - the same solve the baseline did, so the
##     solver handles it. The wedge tinc the model needs to hold that path is written per iteration
##     (Forest_pressure_<i>.txt) next to the baseline's tinc*: a smaller wedge than tinc* means the market would
##     clear MORE than BAU under this coalition (leakage pressure), a larger one less. Hectares of leakage are not
##     measured in this mode. "tinc" = the V21 mechanism (shock tinc = tinc*, forest endogenous): the accurate baseline
##     puts tinc* at 6 000-52 000 % in Ivory Coast, Ghana AEZ6 and US AEZ15 - shocks of that size do not solve.
##  2. run_Gtap reads the accuracy "face" number (0-10) of every solve from the solver log, prints it with the solve
##     time, records it in Solve_quality.txt, and re-solves once with the RunGTAP accurate settings when it is below
##     min_face (default 7; the fast baseline scored 4, the accurate one 9). The bound-cell check now tests every
##     BAU cell against its target (0 for members, -x for non-members).
##  3. run_tag gets "_out<bau_outsiders>". Everything else exactly as in V22.

## V24 (Sept 2026) - the cleared hectares are productive, marked "V24:"
##  In the V21-V23 baseline the BAU clearing moves hectares out of forest, but the land the receiving activities use in
##  production (qes, allocated by the CET on rents) rises far less than the hectares (Ivory Coast AEZ6: pasture
##  hectares +73 %, land used by grazing -0.2 %). Clearing then destroys value in the model, and a member that stops
##  clearing gains (Brazil +916 M$/yr, Ivory Coast +716) instead of paying. Calibrate_BAU_productivity.R fixes the
##  productivity of the cleared hectares: land-augmenting technical change afeall(AEZ, act, r) (E_qfe, exogenous in
##  the closure) calibrated so that every receiving activity's land services (qes + afeall) rise by at least
##  eta x the hectares it gains (eta = 0.66, the model's own yield of new cropland). Baseline_EUDR.R (bau_eta) writes
##  the shocks to bau_afeall.txt in its folder; here non-members get them together with their cover path, members get
##  neither (no clearing, no free land) - their commitment now costs the forgone expansion.
##  bau_eta (default 0.66) selects the baseline folder Baseline_EUDR_bau<h>_eta<eta>; run_tag gets "_eta<eta>".
##  Everything else exactly as in V23.

## V25 (Sept 2026) - a uniform friction measured on what the region has at stake, marked "V25:"
##  The V22 numeric friction multiplied GDP: at 0.01 % of GDP the thresholds are 1 464 M$ for China, 2 138 for the US,
##  1 569 for the EU, while the club moves China's EV by tens of M$ - the large economies would never move, the small
##  ones at will. friction_base = "trade" (new default for a numeric friction) measures the friction on the region's
##  trade in the 17 charged commodities: exports (VFOB, every destination) + imports (VCIF, every source) of
##  list_commodity_tmsf in 2_Model/in/basedata.har, in the data base's own $M (the units of EV), intra-region trade of
##  the composite regions (VFOB(c, r, r): 65 % of the EU's exports of these goods) excluded because the club never
##  charges it. Both thresholds = max(friction_floor, friction x base), the same for joining and leaving.
##  friction = 0.001 (0.1 %): EU 227 M$, China 215, US 196, Brazil 73, Indonesia 43, Ivory Coast 6.9, Ghana 4.0.
##  friction_base = "gdp" keeps the V22 base; friction = "sheet" (default) is unchanged. friction_floor (default 2 M$)
##  is the resolution of the game: nobody moves for less. With a numeric friction the thresholds no longer depend on
##  the approach, so list_approach defaults to the single folder 3_Output/Friction/ and run_tag gets
##  "_fr<friction><base>" (e.g. _fr0.001trade). Thresholds_used.txt in every run folder lists the thresholds applied
##  (region, threshold_leave, threshold_join, and the base under a numeric friction) - for the sheet runs as well.
##  The default of eudr_in_loop is now "none": the baseline (iteration 0) is the EUDR + BAU world and every scenario is the
##  club or coalition mechanism alone - the EUDR is not applied in the loop. "outsiders" (the setting of every run up to
##  20 Sept) keeps the EUDR cost on non-members on top of the charge; run_tag carries "_eudr0" for "none", "_eudr" for it.
##  Everything else exactly as in V24.

## V26 (Sept 2026) - the charge at any price, for the search of the lowest conditions, marked "V26:"
##  price_ha  = footprint charge in USD/ha (any value): the bilateral shocks of the AVE_pha10000 sheet are multiplied by
##              price_ha / 10000. Exact: 100 x AVE / (1 + t0) is linear in the price per hectare (checked against the 400
##              and 2 000 sheets to 1e-15; the small-price csvs only drop flows below 0.01 %, at most 0.00998 % at 400).
##  co2_price = carbon charge in USD/tCO2 (any value): the AVE_co2_190 shocks multiplied by co2_price / 190, exact as well.
##  Either overrides tmsf_sheet; run_tag carries pha<price_ha> or co2_<co2_price> (pha400, co2_100 ... as before, so a run
##  at a sheet price lands in the same folder as the sheet run). price_ha = 0 = the AVE_pha0 sheet (no footprint charge).
##  Run_minimum.R uses them to bisect the lowest penalty, the lowest price per hectare and the lowest carbon price at
##  which the pivotal producers end inside. Everything else exactly as in V25.

## V27 (Sept 2026) - two fixes found on the first run without the EUDR (club 400 + 2 %, EU seed, 20-21 Sept), marked "V27:"
##  1. safeguard = "baseline" (new default) | "level" (V13-V26) | "off". The bounded-loss safeguard of V13-V26 expels a member
##     whose EV LEVEL (against the 2019 data) is below -0.1 % of its GDP for three consecutive rounds, member or not. In the
##     new baseline (EUDR + business-as-usual clearing) Paraguay, Ivory Coast, Nigeria, Ghana, Malaysia and DRC already sit
##     below that bound before any club exists (Paraguay -183 M$ against a bound of -38), so Paraguay was expelled after one
##     round inside, rejoined the next round (loss outside > threshold), was expelled again ... : a 2-cycle for 21 rounds.
##     "baseline" measures the loss against the BASELINE (EV_i - EV_0 < -0.1 % of GDP) and counts only rounds spent as a
##     member: a region that gains inside is never expelled. run_tag carries "_sgb" ("_sgoff" for off; nothing for "level").
##  2. A cycle of the membership (period 2 to 6: the coalitions of two consecutive rounds repeat those k rounds earlier)
##     stops the loop at once: the run is reported as not converged ("cycle" in Run_summary.txt and in the log), the last
##     coalition is kept, and the 25-round cap no longer burns two hours (run 4 of 20 Sept: 21 rounds of Paraguay in/out).
##  3. join_rule = "baseline" (V19, EV against the baseline instead of the previous round) now adds "_jrbase" to run_tag,
##     so a sensitivity run no longer overwrites the folders of the consecutive rule.
##  Everything else exactly as in V26.

## V28 (21 Sept 2026) - found on the first friction runs (club 2 % and 2.5 %, EU seed, 21 Sept: 36 members by round 4, then
##  a collective oscillation of 8-13 regions until the 25-round cap, twice), marked "V28:"
##  1. join_rule = "experience" (new default): each region remembers the EV it last had as a member (ev_in_last) and as an
##     outsider (ev_out_last, initialised with the baseline). A member leaves when its EV is more than its threshold below
##     what it last had outside; an outsider joins when its EV is more than its threshold below what it last had inside
##     (or, if it has never been inside, below the previous round: the consecutive rule). The consecutive rule ("EV fell
##     since last round -> move") read the fall that the OTHER regions' entry causes to a member as a reason to leave, and
##     the leavers were taxed again and came back: with the small friction thresholds this never settled. Under the
##     experience rule a region moves only when its own record of the two states says the other one was better.
##     "consecutive" (V13-V27) and "baseline" (V19) remain available; run_tag carries "_jrexp" ("_jrbase"; nothing for
##     consecutive).
##  2. max_rounds (default 25): the round cap is a setting; the convergence and cycle checks use it.
##  Everything else exactly as in V27.

## V29 (27 Sept 2026) - the counterfactual without a keystone, marked "V29:"
##  1. locked_out (default "", i.e. nothing changes): comma-separated regions that can never become members, e.g.
##     "brasil". A locked region is treated as an outsider at every decision (decide_out returns TRUE for it) and is
##     skipped by the stability check; it cannot be in the seed (the EU cannot be locked). Used to measure what the
##     club delivers at the same charge when Brazil is kept out: its own forest and the members it pulls in after it.
##  2. run_tag gets "_lock<regions>" after the seed (e.g. _seedEU_lockbrasil), so a locked run never overwrites an
##     ordinary one; Run_summary.txt records the locked regions. Everything else exactly as in V28.

## V30 (30 Sept 2026) - the game from the business-as-usual world, leakage in hectares, marked "V30:"
##  Baseline_2stage.R solves the baseline in two steps: Stage A imposes the business-as-usual clearing alone and writes the
##  updated database A_bau/gdata_bau.upd (the world after <horizon> years of clearing, the solved clearing incentives sitting
##  in the data as income taxes on forest land); Stage B applies the EUDR to that world with every forest endogenous and
##  writes B_eudr/ (the EUDR world = iteration 0 of the game: EV_B.txt, Forest_LU_B_ha.txt, ams_baseline.txt, NATDEF_B.sl4).
##  1. start_from = "bau" (new default): every solve of the game starts from gdata_bau.upd ("file gtapDATA = ..." in the
##     CMF). Non-members get NO cover lines and NO afeall lines: their forest is endogenous and its change against the
##     business-as-usual world IS the leakage, in hectares (Forest_leakage_<i>.txt per round; the Forest_LU files and the
##     Tropical column of the csv are now relative to the BAU world). Members bring their forest cover back to its 2019
##     extent ("swap p_LANDCOVER_L = tinc; shock p_LANDCOVER_L = 100 x (1 / (1 + shock_pct / 100) - 1)", the exact reversal of
##     their BAU cells) and their productivity shocks are reversed (shock afeall = -100 a / (100 + a)). The solved tinc of a
##     member cell is the subsidy that brings the forest back (Forest_commitment_<i>.txt). No Forest_pressure files.
##     EV and forest of iteration 0 are Stage B's (relative to the BAU world), so EV_i - EV_0 is "club world vs EUDR world"
##     exactly as before, and the thresholds, decision rules, safeguard, cycle check and stability test are unchanged.
##     "2019" keeps the V21-V29 mechanics (2019 data, cover path for non-members, one-solve baseline).
##  2. eudr_outsiders = "keep" (default): the EUDR stays on non-members - it is in the data - and is waived for members
##     (their cut flows get "shock ams = 100 x (1 / (1 + ams_B / 100) - 1)", the reversal of Stage B's iceberg cost:
##     members are deemed compliant). "lift": waived for everyone, the club replaces the EUDR as in V25-V29.
##  3. run_tag gets "_outfree" instead of "_outcover" and "_frombau_eudr<keep|lift>" at the end; Run_summary.txt records it.
##  4. member_pin = "all" | "bau" (start_from = "bau"): what a member's commitment covers. "bau" (the V21-V29 convention, the runs of
##     the night of 29-30 Sept): only the cells with business-as-usual clearing are bound, so a member without DeDuCE clearing
##     (the EU, Canada, Russia ...) keeps converting forest as prices rise (Canada -975 kha, EU -623, Russia -495 in the 1.25 %
##     club). "all": every cell of a member with forest cover, forestry rent and crop or pasture cover is bound - BAU cells back
##     to 2019, the others held at 0 - so "no net loss" applies to all of a member's forest. run_tag gets "_pinall".
##  Everything else exactly as in V29. The extraction scripts must read the BAU clearing from A_bau/bau_baseline.txt
##  (shock_pct x forest_cover_ha), no longer from the Tropical column of iteration 0.
## V31 (1 Oct 2026) - the welfare measure, marked "V31:"
##  welfare = "ev" (default, V13-V30) | "ev_net_wedge": the EV every decision looks at, and every EV written out, is GTAP's EV
##  minus the allocative-efficiency contribution of the income tax on the AEZ land endowments (cntqe over the AEZ rows of the
##  Huff-Hertel decomposition in the solution file). That contribution is the deadweight-loss accounting of the clearing
##  wedge tinc that Stage A imposes to make the DeDuCE clearing happen (and that a member removes when it holds its cover):
##  +774 M USD/yr for Nigeria, +479 Malaysia, +440 Ivory Coast, +103 Brazil, 2.6 bn for the world in the 1.5 % club, most of
##  it in AEZ 6 cells where the land module takes four times more forestry land than cover (Forest_land_wedge_check_2026-09-30.md).
##  The wedge stands for the non-market drivers of clearing; its deadweight loss is a property of the device, not of the policy.
##  1. welfare_from_sol() replaces the EV read of run_Gtap (every solve, stability test included); the round-0 reference is
##     recomputed on the same measure from Stage B's solution. Thresholds, rules, safeguard, commitments, charges: unchanged.
##  2. Welfare_decomp_round_<i>.txt in the run folder (and Welfare_decomp_<label>.txt per solve): region, ev_gross, wedge,
##     ev_decision, so the gross EV is never lost (ev_gross = ev_decision + wedge). The csv carries the decision measure.
##  3. run_tag gets "_wnet" with welfare = "ev_net_wedge"; Run_summary.txt records the measure.
## V32 (4 Oct 2026) - stability_members config ("all" | "none" | list): which members the one-deviation test removes alone, so that
##  one more outsider (Japan, left out of the stability_scope of the 2-3 Oct tests) can be tested without the 35 member solves;
##  the summary line "tested - members out alone / outsiders in alone" says what a Stability file covers. Nothing else changes.
## V32 (2 Oct 2026) - the EUDR in the game solves, marked "V32:"
##  Bug of V30 (every run of 30 Sept - 2 Oct): the game solves start from A_bau/gdata_bau.upd, the business-as-usual world
##  WITHOUT the EUDR, and generate_text_for_eudr() wrote, for the members, the reversal of Stage B's iceberg cost - the
##  reversal of a cost that is not in that data. So non-members were not under the ban in any solve, and members' cut flows to
##  the EU got an import-augmenting improvement of 0.3-10 % relative to 2019 (Brazilian beef +0.44 %, Ivorian cocoa +2.4 %,
##  Malaysian live cattle +10 %), a gain booked mostly to the EU (its technology term +153 M USD/yr in the 1.5 % club, on top
##  of the 170 of EUDR cost it did not bear) and a few M USD/yr of export demand to each member. The round-0 reference (Stage
##  B = BAU world + EUDR on everyone) was right, so every first-round loss was understated by the region's own EUDR cost
##  (Brazil 13, Ivory Coast 39 M USD/yr) and the EU's and the world's EV were overstated by about 0.3 bn USD/yr.
##  Fix: with start_from = "bau" and eudr_outsiders = "keep", every solve applies Stage B's solved iceberg cost to the cut
##  flows of the NON-members ("shock ams = ams_B", exactly as eudr_in_loop = "outsiders" did in V16-V29); members get no
##  line (deemed compliant: their flows stay at the 2019 cost of the BAU world). With "lift" no line at all (the club replaces
##  the EUDR). Nothing else changes. run_tag gets "_v32" so that no V30/V31 folder or csv is overwritten; the readers must
##  accept the suffix. Every run of the programme is redone with Run_V32_all.R.

## Package installation, 
## Run these lines only once to install the packages (do this only one time)
#install.packages('devtools')
#devtools::install_git('https://github.com/USDA-ERS/MTED-HARr.git')
#install.packages("readxl")
#install.packages("xlsx", dependencies=TRUE)
#install.packages("rJava")
#install.packages("xlsx")

#clear the environment
rm(list = setdiff(ls(), "run_config"))   # V17: keep the configuration passed by Run_overnight.R

## Run these lines in each new R session where you need these packages
library(devtools)
library(xlsx)
require(HARr)
library("readxl")
library("rstudioapi")
library(dplyr)
library(writexl)
library(tidyr)

script_path <- if (exists("run_config") && !is.null(run_config$script_path)) run_config$script_path else getSourceEditorContext()$path   # V17: Run_overnight.R passes its own path
script_folder <- dirname(script_path)
parent_folder <- dirname(script_folder)
GTAPAEZ_path <- file.path(parent_folder, "2_Model/")
external_data_path <- file.path(parent_folder, "0_External_data/")

setwd(GTAPAEZ_path)

##External values 
#Values qo to stop the deforestation based on HILDA+ V2_1 calculation
# Function to process a sheet and create a list of named vectors

# Import the data
data_qo <- read_excel(paste0(external_data_path, "/qo_values.xlsx"))
## V14: border charge = DeDuCE-based table, one sheet per price scenario
## V17: run configuration - set here, or passed by 1_Code/Run_overnight.R through the list run_config
cfg <- function(name, default) if (exists("run_config") && !is.null(run_config[[name]])) run_config[[name]] else default
tmsf_sheet <- cfg("tmsf_sheet", "AVE_pha400")   # AVE_pha400 | AVE_pha2000 | AVE_pha10000 | AVE_co2_50 | AVE_co2_100 | AVE_co2_190
tau        <- cfg("tau", 0)                     # V17: flat penalty (% on the tariff power) on every non-member: 0 = coalition, > 0 = club
tau_scope  <- cfg("tau_scope", "charged")       # V17: "charged" = the 17 land-based sectors | "all" = every commodity (Nordhaus club)
solve_mode <- cfg("solve_mode", "accurate")     # V19/V24: "accurate" = RunGTAP settings (5-6 min per solve) | "fast" = one subinterval, no accuracy iteration - not accurate enough for the BAU shocks
max_pass   <- cfg("max_pass", 2)                # V19: forest-commitment solves per iteration, at most
join_rule  <- cfg("join_rule", "experience")    # V28 default "experience": each region compares its EV with what it last had in the other status | "consecutive": EV vs the previous round (V13-V27) | "baseline": EV vs the baseline (V19)
if (!(join_rule %in% c("experience", "consecutive", "baseline"))) stop('join_rule must be "experience", "consecutive" or "baseline"')   # V28
max_rounds <- as.integer(cfg("max_rounds", 25))  # V28: round cap (25 in V13-V27)
safeguard  <- cfg("safeguard", "baseline")      # V27: bounded-loss safeguard - "baseline": a member more than 0.1 % of GDP below the baseline for three consecutive rounds as a member leaves | "level": V13-V26, EV level below -0.1 % of GDP for three consecutive rounds, member or not | "off"
if (!(safeguard %in% c("baseline", "level", "off"))) stop('safeguard must be "baseline", "level" or "off"')   # V27
price_ha   <- suppressWarnings(as.numeric(cfg("price_ha", NA)))    # V26: footprint charge at any price (USD/ha): AVE_pha10000 shocks x price_ha / 10000; overrides tmsf_sheet
co2_price  <- suppressWarnings(as.numeric(cfg("co2_price", NA)))   # V26: carbon charge at any price (USD/tCO2): AVE_co2_190 shocks x co2_price / 190; overrides tmsf_sheet
if (!is.na(price_ha) && !is.na(co2_price)) stop("give price_ha or co2_price, not both")
tmsf_scale <- 1                                                     # V26: multiplier of the bilateral shocks of tmsf_sheet
if (!is.na(price_ha))  { tmsf_sheet <- "AVE_pha10000"; tmsf_scale <- price_ha / 10000 }
if (!is.na(co2_price)) { tmsf_sheet <- "AVE_co2_190";  tmsf_scale <- co2_price / 190 }
charge_label <- if (!is.na(price_ha)) paste0("pha", format(price_ha, scientific = FALSE)) else if (!is.na(co2_price)) paste0("co2_", format(co2_price, scientific = FALSE)) else sub("^AVE_", "", tmsf_sheet)
run_tag    <- paste0(charge_label, "_tau", tau, ifelse(tau > 0, tau_scope, ""))   # V17: e.g. pha400_tau0, pha400_tau5charged; V26: pha<price_ha>, co2_<co2_price>
data_tmsf  <- read_excel(paste0(external_data_path, "/DeDuCE_rework/tms_f_initial_shocks_DeDuCE.xlsx"), sheet = tmsf_sheet)
names(data_tmsf) <- tolower(names(data_tmsf))   # HARr lower-cases set elements ("RuminantMeat" -> "ruminantmeat")

## V16: baseline = EUDR, solved once by 1_Code/Baseline_EUDR.R into 3_Output/Baseline_EUDR/
eudr_in_loop  <- cfg("eudr_in_loop", "none")        # V25 default "none": the scenario is the club/coalition alone, the EUDR is only in the baseline | "outsiders": the EU keeps the EUDR cost on non-members on top of the charge (the runs of 19-20 Sept)
bau_horizon   <- cfg("bau_horizon", 5)               # V21: years of business-as-usual clearing in the baseline (0 = the V16-V20 baseline)
bau_eta       <- cfg("bau_eta", 0.66)                # V24: productivity of the cleared hectares (the baseline must have been solved with the same value); 0 = the V21-V23 baseline
baseline_path <- file.path(parent_folder, "3_Output", if (bau_horizon > 0) paste0("Baseline_EUDR_bau", bau_horizon, if (bau_eta > 0) paste0("_eta", bau_eta) else "") else "Baseline_EUDR", "/")   # V21, V24
run_tag       <- paste0(run_tag, "_eudr", ifelse(eudr_in_loop == "none", "0", ""), if (bau_horizon > 0) paste0("_bau", bau_horizon) else "",
                        if (bau_horizon > 0 && bau_eta > 0) paste0("_eta", bau_eta) else "")   # V21, V24
## V22: starting coalition, friction, stability check
seed_str  <- cfg("seed", "eu27")                     # regions inside at iteration 1, comma-separated (the EU is always added) | "auto" = the V13-V21 start
seed      <- if (identical(seed_str, "auto")) "auto" else union("eu27", tolower(trimws(strsplit(seed_str, ",")[[1]])))
seed_name <- cfg("seed_name", if (identical(seed_str, "auto")) "auto" else if (identical(seed, "eu27")) "EU" else paste(seed, collapse = "-"))
locked_out <- cfg("locked_out", "")                  # V29: regions that can never be members, comma-separated ("" = none), e.g. "brasil"
locked_out <- if (nzchar(locked_out)) setdiff(tolower(trimws(strsplit(locked_out, ",")[[1]])), "eu27") else character(0)   # V29
if (!identical(seed, "auto") && length(intersect(locked_out, seed)) > 0) stop("V29: a locked-out region cannot be in the seed: ", paste(intersect(locked_out, seed), collapse = ", "))
dynamics  <- cfg("dynamics", "on")                   # "on": the join/leave rule runs from the seed | "off": the seed is the coalition, one solve
friction  <- cfg("friction", "sheet")                # "sheet": thresholds of <approach>/Thresholds_GTAPAEZ_Game_theory.xlsx | a number: both thresholds = friction x base ($M), e.g. 0.001 = 0.1 % of the base
friction_num    <- suppressWarnings(as.numeric(friction))
friction_base   <- cfg("friction_base", "trade")     # V25: base of a numeric friction - "trade": the region's exports + imports of the 17 charged commodities (basedata.har VFOB + VCIF, $M) | "gdp": GDP_values.xlsx (V22)
friction_floor  <- as.numeric(cfg("friction_floor", 2))   # V25: $M, lowest threshold under a numeric friction (the resolution of the game: nobody moves for less)
if (!is.na(friction_num) && !(friction_base %in% c("trade", "gdp"))) stop('friction_base must be "trade" or "gdp"')   # V25
stability       <- as.logical(cfg("stability", TRUE))   # one-deviation check of the final coalition (bau_horizon > 0, parameter "forest")
stability_scope <- cfg("stability_scope", "all")     # outsiders tested for joining: "all" or a comma-separated list
stability_members <- cfg("stability_members", "all")   # V32 (4 Oct): members tested for leaving: "all", "none" or a comma-separated list (a test of one more outsider need not redo the members)
run_tag   <- paste0(run_tag, "_seed", seed_name, if (dynamics == "off") "_fixed" else "")
run_tag   <- paste0(run_tag, if (length(locked_out) > 0) paste0("_lock", paste(locked_out, collapse = "-")) else "")   # V29: e.g. _seedEU_lockbrasil
## V30: the game from the business-as-usual world of the two-stage baseline (1_Code/Baseline_2stage.R)
start_from     <- cfg("start_from", "bau")           # "bau": every solve starts from A_bau/gdata_bau.upd - non-members' forest endogenous (leakage in hectares), members bring their cover back to 2019 | "2019": V21-V29
member_pin     <- cfg("member_pin", "bau")           # start_from = "bau": "bau" = only a member's BAU cells are bound (V21-V29) | "all" = every forest cell of a member with forestry rent and crop/pasture cover is held (no net loss everywhere)
if (!(member_pin %in% c("bau", "all"))) stop('V30: member_pin must be "bau" or "all"')
eudr_outsiders <- cfg("eudr_outsiders", "keep")      # start_from = "bau": "keep" = the EUDR stays on non-members (V32: Stage B's solved iceberg cost is applied to their cut flows in every solve) and is waived for members | "lift" = waived for everyone (the club replaces the EUDR, as V25-V29)
if (!(start_from %in% c("bau", "2019"))) stop('V30: start_from must be "bau" or "2019"')
if (!(eudr_outsiders %in% c("keep", "lift"))) stop('V30: eudr_outsiders must be "keep" or "lift"')
welfare        <- cfg("welfare", "ev")               # V31: "ev" = GTAP's EV (V13-V30) | "ev_net_wedge" = EV minus the welfare contribution of the income tax on AEZ land (cntqe over the AEZ endowments): the deadweight-loss accounting of the clearing wedge tinc is left out of every decision and every EV written out
if (!(welfare %in% c("ev", "ev_net_wedge"))) stop('V31: welfare must be "ev" or "ev_net_wedge"')
if (start_from == "bau") {
  if (bau_horizon <= 0) stop("V30: start_from = bau needs bau_horizon > 0")
  baseline_path <- file.path(parent_folder, "3_Output", paste0("Baseline_2stage_bau", bau_horizon, if (bau_eta > 0) paste0("_eta", bau_eta) else ""), "/")
}
bl <- function(what) {   # V30: the baseline files of either design
  if (start_from == "bau") switch(what,
    ev   = paste0(baseline_path, "B_eudr/EV_B.txt"),            ams  = paste0(baseline_path, "B_eudr/ams_baseline.txt"),
    bau  = paste0(baseline_path, "A_bau/bau_baseline.txt"),     afe  = paste0(baseline_path, "A_bau/bau_afeall.txt"),
    sl4  = paste0(baseline_path, "B_eudr/NATDEF_B.sl4"),        luc  = paste0(baseline_path, "B_eudr/Forest_LU_B_ha.txt"),
    data = normalizePath(paste0(baseline_path, "A_bau/gdata_bau.upd"), winslash = "\\", mustWork = TRUE),
    src  = "1_Code/Baseline_2stage.R")
  else switch(what,
    ev   = paste0(baseline_path, "EV_baseline.txt"),            ams  = paste0(baseline_path, "ams_baseline.txt"),
    bau  = paste0(baseline_path, "bau_baseline.txt"),           afe  = paste0(baseline_path, "bau_afeall.txt"),
    sl4  = paste0(baseline_path, "NATDEF_baseline.sl4"),        luc  = paste0(baseline_path, "Forest_LU_baseline_ha.txt"),
    data = NULL, src = "1_Code/Baseline_EUDR.R")
}
set_data_line <- function(lines) {   # V30: point the CMF at the business-as-usual database (the RunGTAP backup points at in\basedata.har)
  if (start_from != "bau") return(lines)
  k <- grep("^\\s*file\\s+gtapDATA\\s*=", lines, ignore.case = TRUE)
  if (length(k) != 1) stop("V30: the line 'file gtapDATA = ...' was not found once in the CMF")
  lines[k] <- paste0("file gtapDATA = ", bl("data"), ";")
  lines
}
bau_outsiders <- if (start_from == "bau") "free" else cfg("bau_outsiders", "cover")   # V30: "free" = non-members' forest endogenous; V23: "cover" = non-members' forest follows the BAU path (as in the baseline) | "tinc" = V21, shock tinc = tinc* (infeasible for large tinc*)
min_face      <- cfg("min_face", 7)                  # V23: lowest acceptable accuracy "face" number of a solve (0-10); below it the solve is redone with the accurate settings
run_tag       <- paste0(run_tag, "_out", bau_outsiders)   # V23
run_tag       <- paste0(run_tag, if (!is.na(friction_num)) paste0("_fr", format(friction_num, scientific = FALSE), friction_base) else "")   # V25: e.g. _fr0.001trade
run_tag       <- paste0(run_tag, c(baseline = "_sgb", level = "", off = "_sgoff")[[safeguard]])   # V27: safeguard mode ("level" = the folders of V13-V26)
run_tag       <- paste0(run_tag, c(consecutive = "", baseline = "_jrbase", experience = "_jrexp")[[join_rule]])   # V27/V28: the decision rule in the folder name (nothing for the V13-V27 rule)
if (start_from == "bau") run_tag <- paste0(run_tag, "_frombau_eudr", eudr_outsiders, if (member_pin == "all") "_pinall" else "")   # V30
if (welfare == "ev_net_wedge") run_tag <- paste0(run_tag, "_wnet")   # V31: never overwrites a run on GTAP's EV
if (start_from == "bau") run_tag <- paste0(run_tag, "_v32")   # V32: the EUDR on non-members is in the solves - never overwrites a V30/V31 run
if (!file.exists(bl("ev")))
  stop("Run ", bl("src"), " first: ", bl("ev"), " not found")   # V30: either baseline design
ev_baseline  <- read.table(bl("ev"), header = FALSE, col.names = c("region", "EV"), stringsAsFactors = FALSE)
ams_baseline <- read.table(bl("ams"), header = TRUE, stringsAsFactors = FALSE)
bau_baseline <- NULL                                                                            # V21
if (bau_horizon > 0) {
  if (!file.exists(bl("bau")))
    stop("Run ", bl("src"), " with bau_horizon = ", bau_horizon, " first: ", bl("bau"), " not found")
  bau_baseline <- read.table(bl("bau"), header = TRUE, stringsAsFactors = FALSE)
  bau_baseline$cell <- paste(tolower(bau_baseline$aez), tolower(bau_baseline$region), sep = "|")
}
bau_afeall <- NULL                                                                              # V24
if (bau_horizon > 0 && bau_eta > 0) {
  if (!file.exists(bl("afe")))
    stop("Run ", bl("src"), " with bau_eta = ", bau_eta, " first: ", bl("afe"), " not found")
  bau_afeall <- read.table(bl("afe"), header = TRUE, stringsAsFactors = FALSE)
  bau_afeall <- bau_afeall[bau_afeall$afeall_pct > 0, ]
}

generate_text_for_bau <- function(members, outsiders) {
  # V21: non-members keep the clearing incentive solved in the baseline; members are pinned at no net loss
  if (is.null(bau_baseline)) return(list(lines = character(0), pinned = character(0)))
  if (start_from == "bau") {                                                              # V30: from the BAU world - non-members free, members back to 2019
    in_rows <- bau_baseline[tolower(bau_baseline$region) %in% tolower(members), ]
    x_back  <- 100 * (1 / (1 + in_rows$shock_pct / 100) - 1)                              # the cover fell by shock_pct in Stage A; this brings it back exactly
    lines <- c(sprintf('swap p_LANDCOVER_L("%s","Forestland","%s") = tinc("%s","forest","%s");', in_rows$aez, in_rows$region, in_rows$aez, in_rows$region),
               sprintf('shock p_LANDCOVER_L("%s","Forestland","%s") = %s;', in_rows$aez, in_rows$region, format(x_back, scientific = FALSE, digits = 10)))
    if (!is.null(bau_afeall)) {                                                            # the productivity of the hectares a member gives back is reversed too
      afe <- bau_afeall[tolower(bau_afeall$region) %in% tolower(members), ]
      lines <- c(lines, sprintf('shock afeall("%s","%s","%s") = %s;', afe$aez, afe$activity, afe$region, format(-100 * afe$afeall_pct / (100 + afe$afeall_pct), scientific = FALSE, digits = 10)))
    }
    pinned <- in_rows$cell; targets <- setNames(x_back, in_rows$cell)
    if (member_pin == "all") {                                                          # V30: the rest of a member's forest is held where it stands (no net loss everywhere)
      held <- setdiff(holdable_cells[sub(".*\\|", "", holdable_cells) %in% tolower(members)], pinned)
      if (length(held) > 0) {
        q <- strsplit(held, "|", fixed = TRUE); ha <- toupper(sapply(q, `[`, 1)); hr <- sapply(q, `[`, 2)
        lines <- c(lines, sprintf('swap p_LANDCOVER_L("%s","Forestland","%s") = tinc("%s","forest","%s");', ha, hr, ha, hr),
                          sprintf('shock p_LANDCOVER_L("%s","Forestland","%s") = 0;', ha, hr))
        pinned <- c(pinned, held); targets <- c(targets, setNames(rep(0, length(held)), held))
      }
    }
    return(list(lines = lines, pinned = pinned, out_cells = character(0), targets = targets))
  }
  out_rows <- bau_baseline[tolower(bau_baseline$region) %in% tolower(outsiders) & is.finite(bau_baseline$tinc_solved), ]
  in_rows  <- bau_baseline[tolower(bau_baseline$region) %in% tolower(members), ]
  lines_out <- if (bau_outsiders == "cover") {                                              # V23: the baseline's own lines for non-members
    c(sprintf('swap p_LANDCOVER_L("%s","Forestland","%s") = tinc("%s","forest","%s");', out_rows$aez, out_rows$region, out_rows$aez, out_rows$region),
      sprintf('shock p_LANDCOVER_L("%s","Forestland","%s") = %s;', out_rows$aez, out_rows$region, format(out_rows$shock_pct, scientific = FALSE, digits = 10)))
  } else {                                                                                  # V21: the wedge as a shock, forest endogenous
    sprintf('shock tinc("%s","forest","%s") = %s;', out_rows$aez, out_rows$region, format(out_rows$tinc_solved, scientific = FALSE, digits = 10))
  }
  if (!is.null(bau_afeall)) {                                                               # V24: non-members' cleared hectares are productive; members forgo them
    afe <- bau_afeall[tolower(bau_afeall$region) %in% tolower(outsiders), ]
    lines_out <- c(lines_out, sprintf('shock afeall("%s","%s","%s") = %s;', afe$aez, afe$activity, afe$region, format(afe$afeall_pct, scientific = FALSE, digits = 10)))
  }
  lines <- c(lines_out,
             sprintf('swap p_LANDCOVER_L("%s","Forestland","%s") = tinc("%s","forest","%s");', in_rows$aez, in_rows$region, in_rows$aez, in_rows$region),
             sprintf('shock p_LANDCOVER_L("%s","Forestland","%s") = 0;', in_rows$aez, in_rows$region))
  targets <- c(setNames(rep(0, nrow(in_rows)), in_rows$cell),                                # V23: what every bound cell must show in the solution
               if (bau_outsiders == "cover") setNames(out_rows$shock_pct, out_rows$cell) else NULL)
  list(lines = lines, pinned = in_rows$cell, out_cells = out_rows$cell, targets = targets)
}

generate_text_for_eudr <- function(outsiders) {
  # V16: the EUDR cost solved in the baseline, kept as an exogenous iceberg cost on non-members' exports to the EU
  if (start_from == "bau") {                                                              # V32: the solves start from the BAU world (no EUDR in the data): the ban is Stage B's solved iceberg cost, applied to the cut flows of the non-members ("keep"); members are deemed compliant and get no line; "lift": no line for anyone
    if (eudr_outsiders == "lift") return(character(0))
    rows <- ams_baseline[tolower(ams_baseline$source) %in% tolower(outsiders) & is.finite(ams_baseline$ams_solved) & ams_baseline$ams_solved != 0, ]
    return(sprintf('shock ams("%s","%s","%s") = %s;', rows$comm, rows$source, rows$dest, format(rows$ams_solved, scientific = FALSE, digits = 10)))
  }
  if (eudr_in_loop != "outsiders") return(character(0))
  rows <- ams_baseline[tolower(ams_baseline$source) %in% tolower(outsiders) &
                       is.finite(ams_baseline$ams_solved) & ams_baseline$ams_solved != 0, ]
  sprintf('shock ams("%s","%s","%s") = %s;', rows$comm, rows$source, rows$dest,
          format(rows$ams_solved, scientific = FALSE, digits = 10))
}
data_qxw <- read_excel(paste0(external_data_path, "/qxw_values.xlsx"))
limit <- read_excel(paste0(external_data_path,"/GDP_values.xlsx"))
limit$GDP <- -0.001 * limit$GDP

# Function to process data
process_data <- function(data) {
  country_names <- data[[1]]
  attributes <- data[-1]
  setNames(lapply(seq_len(nrow(attributes)), function(i) setNames(unlist(attributes[i, ]), names(attributes))), country_names)
}

process_sheet <- function(sheet_name) {
  # Import the data
  data <- read_excel(paste0(external_data_path, "/qes_values.xlsx"), sheet = sheet_name, col_names = TRUE, col_types = NULL, na = "", skip = 0)
  # Extract country names
  country_names <- data[[1]]
  # Remove the country names column to keep only the attributes
  attributes <- data[-1]
  # Initialize an empty list to store the country data
  shock_values <- list()
  # Loop through each row and create a named vector for each country
  for (i in 1:nrow(attributes)) {
    # Extract the row as a named vector
    country_data <- unlist(attributes[i, ])
    names(country_data) <- names(attributes)
    # Assign it to the list with the country name
    shock_values[[country_names[i]]] <- country_data
  }
  return(shock_values)
}

# Loop to process each AEZ and create separate variables
for (i in 1:18) {
  sheet_name <- paste0("AEZ", i)
  variable_name <- paste0("shock_value_aez_", i)
  assign(variable_name, process_sheet(sheet_name))
}

# Apply the function to both datasets
shock_values_qo <- process_data(data_qo)
shock_values_tmsf <- process_data(data_tmsf)
shock_values_qxw <- process_data(data_qxw)

## Parameters
## List of regions used in this simulation
sets = read_har('sets.har')
region_sets = sets["reg"]
df_r <- data.frame(region_sets)
# convert the regions used into the simulation as a vector
region_sets <- unlist(df_r)
if (!identical(seed, "auto") && length(setdiff(seed, tolower(region_sets))) > 0)   # V22
  stop("seed regions not in sets.har: ", paste(setdiff(seed, tolower(region_sets)), collapse = " "))
list_producer_countries <- c("angola", "argentina", "bolivia", "brasil", 
                             "colombia","ghana","ivorycoast",
                             "indonesia","malasya","paraguay","peru","drc")

list_non_producer_countries <- c("madagascar","mozambique","myanmar", "nigeria", "uruguay","venezuela",
                                 "newzealand","oceania","china","india","japan","korea","eastasia",
                                 "seasia","southasia","us","canada", "mexico","latinamer","eu27",
                                 "uk","russia","efta","mena","nafr","wafr","cafr","eafr","safr","restofworld")

list_commodity <- c("sgr", "ruminant", "gro", "ocr", 
                    "osd","pcr","pfb",
                    "v_f","wht")

## V14: sectors that carry the border charge = every column of the tms_f sheet (17 sectors).
## To charge only the nine sectors of V13:  list_commodity_tmsf <- list_commodity
list_commodity_tmsf <- names(data_tmsf)[-1]

## V17: bilateral footprint charge, 100 x AVE(c, source) / (1 + t0(c, source, dest)), from the DeDuCE rework
tmsf_bil    <- read.csv(paste0(external_data_path, "/DeDuCE_rework/tms_f_shocks_bilateral_", tmsf_sheet, ".csv"), stringsAsFactors = FALSE)
tmsf_lookup <- setNames(tmsf_bil$shock_tms_f_pct, tolower(paste(tmsf_bil$comm, tmsf_bil$source, tmsf_bil$dest, sep = "|")))
shock_outsiders_into_members <- function(shock, members, outsiders) {
  # every non-member pays footprint + tau into every member on the charged sectors; tau on all goods if tau_scope = "all"
  g <- expand.grid(cm = list_commodity_tmsf, o = outsiders, m = members, stringsAsFactors = FALSE)
  if (nrow(g) > 0) {
    v <- tmsf_lookup[tolower(paste(g$cm, g$o, g$m, sep = "|"))]
    v[is.na(v)] <- 0
    shock[["0101"]][as.matrix(g)] <- as.numeric(v) * tmsf_scale + tau   # V26: tmsf_scale = 1 for a sheet, price_ha / 10000 or co2_price / 190 otherwise
    if (tau_scope == "all" && tau > 0) {
      g2 <- expand.grid(cm = setdiff(dimnames(shock[["0101"]])[[1]], list_commodity_tmsf), o = outsiders, m = members, stringsAsFactors = FALSE)
      shock[["0101"]][as.matrix(g2)] <- tau
    }
  }
  shock
}

original_ev_new <- read_excel(paste0(external_data_path,"/Original_EV.xlsx"),sheet=1,col_names= FALSE,col_types=NULL,na="",skip= 0)

# Find the parameter to play with 
# qo, qoes or qxw
#list_parameter <- c("qes")
#list_parameter <- c("qo", "qes", "qxw")   # V13/V14 mechanisms, still available
list_parameter <- cfg("parameter", "forest")   # V15: forest-cover commitment, see generate_text_for_forest (V17: or from run_config)

## Scenarios
# Un-comment the line below and comment the line above to run one single scenario
scenarios <- c("Scenario_D")

#list_approach <- c("Realistic_wi_china","Realistic_wo_china","Diplomatic","Idealist")
list_approach <- cfg("approach", if (is.na(friction_num)) c("Realistic_wi_china","Diplomatic","Realistic_wo_china","Idealist") else "Friction")   # V17: or from run_config; V25: a numeric friction ignores the approach sheets - one folder
#list_approach <- c("Diplomatic")

## Reset from the previous calculation
# Loop to iterate through each BU file

# List of BU files to copy
bu_files <- c("NATDEF.har", "NATDEF.sl4", "gdata.upd", "NATDEF.cmf")

# Source and destination folders are as per your setup
source_folder_copy <- file.path(parent_folder, "2_Model", "BU/")
destination_folder_paste <- GTAPAEZ_path
for (bu_file in bu_files) {
  
  # Full path of the source and destination files
  source_file_path_copy <- file.path(source_folder_copy, bu_file)
  destination_file_path_paste <- file.path(destination_folder_paste, bu_file)
  
  # Check if the source file exists
  if (!file.exists(source_file_path_copy)) {
    print(paste("Source file does not exist:", bu_file))
    next
  }
  
  # Check if the destination folder exists
  if (!dir.exists(destination_folder_paste)) {
    print("Destination folder does not exist.")
    next
  }
  
  # Attempt to copy and overwrite if the file already exists
  result <- file.copy(source_file_path_copy, destination_file_path_paste, overwrite = TRUE)
  
  # Check the result
  if (result) {
    print(paste("File copy successful for", bu_file))
  } else {
    print(paste("File copy failed for", bu_file))
  }
}

## ---- V19: solver settings written into the CMF ----------------------------------------------
set_solver_lines <- function(lines, mode) {
  # mode "fast": Gragg 2-4-6, one subinterval, no accuracy iteration, no XAC/SLC files
  # mode "accurate": the RunGTAP settings written explicitly (V23; V19-V22 left the CMF untouched, which kept the fast
  #                  lines when a fast solve was redone): Gragg 2-4-6, automatic accuracy, 3 subintervals, XAC file
  # mode "retry": heavier automatic-accuracy solve, Gragg 4-8-12 from 6 subintervals (used once when an accurate solve fails the checks)
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

## ---- V19: the solution file is read once per solve and reused --------------------------------
sol_cache <- NULL
get_sol <- function() { if (is.null(sol_cache)) sol_cache <<- read_SL4('NATDEF.sl4'); sol_cache }

## ---- V31: the welfare measure read from a solution ----------------------------------------------
last_welfare <- NULL   # region, ev_gross, wedge, ev_decision of the last solution read (written next to the solve by run_Gtap and per round)
welfare_from_sol <- function(data) {
  #' EV of every region from a solution, in the order of the solution's REG set (= sets.har, as data["ev"] was read before).
  #' With welfare = "ev_net_wedge": minus the allocative-efficiency contribution of the income tax on the AEZ land
  #' endowments (GTAP's cntqe, Huff-Hertel decomposition) = the deadweight-loss accounting of the clearing wedge tinc.
  ev <- data[["ev"]]; if (length(dim(ev)) >= 2) ev <- ev[, 1]
  regs <- if (!is.null(names(ev))) names(ev) else dimnames(data[["ev"]])[[1]]
  ev <- as.numeric(ev); wedge <- rep(0, length(ev))
  if (welfare == "ev_net_wedge") {
    cq <- data[["cntqe"]]; if (is.null(cq)) stop("V31: cntqe (endowment income-tax welfare contribution) is not in the solution file")
    if (length(dim(cq)) == 3) cq <- cq[, , 1]
    aez <- grepl("^aez", tolower(dimnames(cq)[[1]]))
    if (!any(aez)) stop("V31: no AEZ endowment in cntqe")
    w <- colSums(cq[aez, , drop = FALSE])
    wedge <- as.numeric(w[match(tolower(regs), tolower(names(w)))])
    if (any(is.na(wedge))) stop("V31: the regions of cntqe do not match those of ev")
  }
  last_welfare <<- data.frame(region = regs, ev_gross = ev, wedge = wedge, ev_decision = ev - wedge, stringsAsFactors = FALSE)
  ev - wedge
}

## ---- V19: checked solve -----------------------------------------------------------------------
solve_log_dir <- NULL          # set to save_path inside the loop; solver logs go there as Solve_iter_<i>_pass_<p>.log
run_Gtap <- function(iter, bound_cells = character(0), label = "", targets = NULL) {
  #' Solve the model with the current NATDEF.cmf, check the solution, retry once with heavier settings,
  #' return the EV vector (x: number of regions). Stops the run if the solve fails twice.
  #' V23: targets = named vector (cell -> % change of forest cover the solution must show; 0 when NULL); the accuracy
  #' "face" number of the solve is read from the solver log and a solve below min_face is redone with the accurate settings.
  cmf_path <- paste0(GTAPAEZ_path, "/NATDEF.cmf")
  if (is.null(targets)) targets <- setNames(rep(0, length(bound_cells)), bound_cells)
  for (attempt in 1:2) {
    if (attempt == 2) {
      retry_mode <- if (solve_mode == "accurate") "retry" else "accurate"                    # V23: a bad fast solve is redone with the RunGTAP accurate settings
      lines <- readLines(cmf_path, warn = FALSE); writeLines(set_solver_lines(lines, retry_mode), cmf_path)
      print(paste("Solve check failed, retrying with the", retry_mode, "settings:", label))
    }
    log_file <- if (!is.null(solve_log_dir)) paste0(solve_log_dir, "Solve_", label, if (attempt == 2) "_retry", ".log") else "NATDEF_solve.log"
    mtime_before <- file.info('NATDEF.sl4')$mtime; t0 <- Sys.time()
    status <- system2("GTAPV7-AEZ.exe", c("-cmf", "NATDEF.CMF"), stdout = log_file, stderr = log_file)
    sol_cache <<- NULL
    minutes <- round(as.numeric(difftime(Sys.time(), t0, units = "mins")), 1)
    face <- suppressWarnings(as.integer(sub('.*"face" number is ([0-9]+).*', "\\1", grep('Variable accuracy "face" number', readLines(log_file, warn = FALSE), value = TRUE))))
    face <- if (length(face) > 0) tail(face, 1) else NA_integer_                              # the last one is the overall summary
    ok <- identical(as.integer(status), 0L) && !identical(file.info('NATDEF.sl4')$mtime, mtime_before)
    what <- if (ok) "" else "no new solution"
    if (ok) {
      data <- get_sol()
      values_EV <- welfare_from_sol(data)   # V31: GTAP's EV, or EV net of the forest-land wedge term
      ok <- all(is.finite(values_EV)) && max(abs(values_EV)) < 1e6
      if (!ok) what <- "EV not finite"
      if (ok && length(targets) > 0) {                           # bound forest AEZs must sit at their target (else the SL4 is not this CMF's solution)
        p <- data[["p_landcover_l"]]; if (length(dim(p)) == 4) p <- p[, , , 1]
        dev <- sapply(names(targets), function(cell) { q <- strsplit(cell, "|", fixed = TRUE)[[1]]; p[q[1], "forestland", q[2]] }) - targets
        ok <- all(is.finite(dev)) && max(abs(dev)) < 1e-3
        if (!ok) what <- paste("bound forest cell off target by", signif(max(abs(dev)), 3))
      }
      if (ok && !is.na(face) && face < min_face) { ok <- attempt == 2; what <- paste("accuracy face", face, "<", min_face, if (attempt == 2) "- accepted after the retry, check Solve_quality.txt") }
    }
    print(paste0("solve ", label, ": ", minutes, " min, accuracy face ", face, "/10", if (nchar(what) > 0) paste0(" - ", what)))
    if (!is.null(solve_log_dir)) cat(label, attempt, minutes, face, ok, what, "\n", file = paste0(solve_log_dir, "Solve_quality.txt"), append = TRUE)
    if (ok && !is.null(solve_log_dir) && !is.null(last_welfare)) write.table(last_welfare, file = paste0(solve_log_dir, "Welfare_decomp_", label, ".txt"), row.names = FALSE)   # V31
    if (ok) return(values_EV)
  }
  stop(paste("GEMPACK solve failed twice (exit code, missing solution, non-finite EV or bound forest AEZ off target):", label))
}

forest_data <- function(iter){
  #' Run the GEMPACK simulation and return the 
  #' @iter indicates the iteration number but is not included into the calculation
  #' Run the GEMPACK executable, read the EV results from the SL4 output of the simulation  
  #' and return the EV as a numeric vector of x values (x: number of countries into the simulation)

  # Read data and extract relevant parts
  data = get_sol()                                                     # V19: cached solution
  luc_variation = data[["del_luc"]][,'forestland',,]*1000
  df <- data.frame(luc_variation)
  
  row_indices <- rep(rownames(df),times =ncol(df))
  col_indices <- rep(colnames(df), each =nrow(df))
  
  
  unpivoted_df <- data.frame(
    col = row_indices,
    row = col_indices,
    value = as.vector(as.matrix(df))
  )
  
  luc <- unpivoted_df %>%
    pivot_wider(names_from = col, values_from = value)
  
  # Return the vector
  return(luc)
}

init_region <- function(iter){
  #' Run the GEMPACK simulation and return the 
  #' @iter indicates the iteration number but is not included into the calculation
  #' Run the GEMPACK executable, read the EV results from the SL4 output of the simulation  
  #' and return the EV as a numeric vector of x values (x: number of countries into the simulation)
  
  # Load the necessary library
  tryCatch({
    library(HARr)
  }, error = function(e) {
    stop("HARr package could not be loaded: ", e)
  })
  
  # Read data and extract relevant parts
  data = read_SL4('NATDEF.sl4')
  equivalent_variation = data["ev"]
  df <- data.frame(equivalent_variation)
  values_EV <- unlist(df)
  values_EV <- as.numeric(values_EV)
  
  # Return the vector
  return(values_EV)
}

selection_region <- function(prvs_values_EV, values_EV, region_sets, iter){
  #' Select the region names that have a EV<0 
  #' @iter indicates the iteration number but is not included into the calculation
  #' Run the GEMPACK executable, read the EV results from the SL4 output of the simulation  
  #' and return the EV as a numeric vector of x values (x: number of countries into the simulation)
  
  output_table = cbind(region_sets, prvs_values_EV, values_EV, iter)
  
  df_3 <- data.frame(output_table)
  df_3$prvs_values_EV <- as.numeric(df_3$prvs_values_EV)
  df_3$values_EV <- as.numeric(df_3$values_EV)
  
  df_4 <- df_3[df_3$values_EV > df_3$prvs_values_EV , ]
  df_4 <- subset(df_4, select = -prvs_values_EV)
  region_positiv_EV <- df_4[[1]]
  l = iter-1
  # Write the vector to a file. Include the iteration number in the file name.
  write.table(output_table, file = paste0(save_path, "Equivalent_Variation_round_", l, ".txt"), row.names = FALSE, col.names = FALSE)
  if (!is.null(last_welfare)) write.table(last_welfare, file = paste0(save_path, "Welfare_decomp_round_", l, ".txt"), row.names = FALSE)   # V31: gross EV, wedge, decision EV of this round's solution
  
  # Return the vector
  return(region_positiv_EV)  
}

move_producer_coalition <- function(iter_region) {
  producer_coalition <- intersect(iter_region, list_producer_countries)
  iter_region <- setdiff(iter_region, producer_coalition)
  return(list(iter_region = iter_region, producer_coalition = producer_coalition))
}

move_producer_reset <- function(reset_region) {
  producer_reset <- intersect(reset_region, list_producer_countries)
  reset_region <- setdiff(reset_region, producer_reset)
  return(list(reset_region = reset_region, producer_reset = producer_reset))
}

shock_eu27<- function(shock, outside_producer, outside_non_producer) {
  for(producer in outside_producer) {
    for(commodity in list_commodity_tmsf) {   # V14
      shock[["0101"]][commodity, producer, "eu27"] <- shock_values_tmsf[[producer]][commodity]
    }
  }
  for(non_producer in outside_non_producer) {
    for(commodity in list_commodity_tmsf) {   # V14
      shock[["0101"]][commodity,non_producer,"eu27"] <- mean(data_tmsf[[commodity]])
    }
  }
  
  return(shock)
}

shock_eu27_exp<- function(shock, inside_producer, inside_non_producer) {
  for(commodity in list_commodity_tmsf) {   # V14
    for(producer in inside_producer) {
      shock[["0101"]][commodity, "eu27", producer] <- 0.0
    }
    for(non_producer in inside_non_producer) {
      shock[["0101"]][commodity, "eu27", non_producer] <- 0.0
    }
  }
  
  return(shock)
}

shock_ABCD <- function(shock, club_non_producer, outside_producer) {
  for(club in club_non_producer) {
    for(producer in outside_producer) {
      for(commodity in list_commodity_tmsf) {   # V14
        shock[["0101"]][commodity, producer, club] <- shock_values_tmsf[[producer]][commodity]
      }
    }
  }
  return(shock)
}

shock_BD <- function(shock, club_non_producer, outside_non_producer) {
  for(club in club_non_producer) {
    for(non_producer in outside_non_producer) {
      for(commodity in list_commodity_tmsf) {   # V14
        shock[["0101"]][commodity,non_producer, club] <- mean(data_tmsf[[commodity]])
      }
    }
  }
  return(shock)
}

shock_D <- function(shock, club_producer, outside_non_producer) {
  for(club in club_producer) {
    for(non_producer in outside_non_producer) {
      for(commodity in list_commodity_tmsf) {   # V14
        shock[["0101"]][commodity,non_producer, club] <- mean(data_tmsf[[commodity]])
      }
    }
  }
  return(shock)
}

shock_CD <- function(shock, club_producer, outside_producer) {
  for(club in club_producer) {
    for(producer in outside_producer) {
      for(commodity in list_commodity_tmsf) {   # V14
        shock[["0101"]][commodity, producer, club] <- shock_values_tmsf[[producer]][commodity]
      }
    }
  }
  return(shock)
}

# Function to update the .cmf file
update_cmf_file <- function(new_text,i) {
  # Read the file
  cmf_path <- paste0(GTAPAEZ_path,"/NATDEF.cmf")
  
  lines <- readLines(cmf_path, warn = FALSE)
  # Find the line number for "Rest Endogenous;"
  cutoff_line <- which(lines == "! Part for productivity shocks from R;")
  # Check if the line was found
  if (length(cutoff_line) == 0) {
    stop("The line 'Rest Endogenous ;' was not found in the file.")
  }
  # Keep all lines up to and including "Rest Endogenous;"
  lines <- lines[1:cutoff_line]
  
  # Append new text
  lines <- c(lines, new_text)
  # Write the updated content back to the file
  writeLines(lines, cmf_path)
  
  filename = paste0(save_path,"CMF_iter_", i, ".cmf")
  # Modify lines to remove " and \
  cleaned_lines = gsub('"', '', lines)  # Remove double quotes
  cleaned_lines = gsub('\\\\', '', cleaned_lines)  # Remove backslashes, note double escape to represent a single backslash
  # Write to file without quotes and backslashes
  write.table(cleaned_lines, filename, sep = "\t", row.names = FALSE, col.names = FALSE, quote = FALSE)
  
}

# Function to generate text for each country
generate_swap_for_qo <- function(country) {
  swap_qo <- c()  # Create an empty vector to store results
  
  for(commodity in list_commodity) {
    line <- paste("swap qo(\"", commodity, "\",\"", country, "\") = aoall(\"", commodity, "\",\"", country, "\");", sep = "")
    swap_qo <- c(swap_qo, line)  # Append the generated string to the results
  }
  
  return(swap_qo)
}

generate_shock_for_qo <- function(club_producer) {
  results_qo <- c()  # Create an empty vector to store results
  
  for(producer in club_producer) {
    for(commodity in list_commodity) {
      value <- shock_values_qo[[producer]][commodity] 
      line <- paste("Shock qo(\"", commodity, "\",\"", producer, "\") = ", value, ";", sep = "")
      results_qo <- c(results_qo, line)  # Append the generated string to the results
    }
  }
  
  return(results_qo)
}

generate_text_for_qxw <- function(club_producer) {
  results_qxw <- c()  # Create an empty vector to store results
  
  for(producer in club_producer) {
    for(commodity in list_commodity) {
      value <- shock_values_qxw[[producer]][commodity]
      if (value < 0) {
      line_shock <- paste("Shock qxw(\"", commodity, "\",\"", producer, "\") = ", value, ";", sep = "")
      line_swap <- paste("swap qxw(\"", commodity, "\",\"", producer, "\")=tmf_f(\"", commodity, "\",\"", producer, "\");", sep = "")
      results_qxw <- c(results_qxw, line_swap, line_shock)  # Append the generated string to the results
      }
    }
  }
  
  return(results_qxw)
}

# generate_text_for_qoes <- function(club_producer) {
#   results_qoes <- c()  # Create an empty vector to store results
#   for(producer in club_producer) {
#     for(commodity in list_commodity) {
#       for (i in 1:18) {
#         shock_index <- paste0("aez", i)
#         shock_value_var_name <- paste0("shock_value_aez_", i)
#         shock_value_var <- get(shock_value_var_name)
#         value <- shock_value_var[[producer]][[commodity]]
#         
#         if (value < 0) {
#           line_shock <- paste("Shock qoes(\"", shock_index, "\", \"", commodity, "\",\"", producer, "\")=", value, ";", sep = "")
#           line_swap <- paste("swap qoes(\"", shock_index, "\", \"", commodity, "\", \"", producer, "\")=afeall(\"", shock_index, "\", \"", commodity, "\", \"", producer, "\");", sep = "")
#           results_qoes <- c(results_qoes, line_swap, line_shock)
#         }  # Append the generated string to the results
#       }
#     }
#   }
#   
#   return(results_qoes)
# }

generate_text_for_qes <- function(club_producer) {
  results_qes <- character(0)  # empty character vector
  
  for (producer in club_producer) {
    for (commodity in list_commodity) {
      for (i in 1:18) {
        # AEZ1..AEZ18 (no zero padding)
        shock_index <- sprintf("AEZ%d", i)
        
        shock_value_var_name <- sprintf("shock_value_aez_%d", i)
        shock_value_var <- get(shock_value_var_name, inherits = TRUE)
        value <- shock_value_var[[producer]][[commodity]]
        
        if (is.finite(value) && value < 0) {
          line_swap <- sprintf(
            'swap qes("%s","%s","%s")=afeall("%s","%s","%s");',
            shock_index, commodity, producer,
            shock_index, commodity, producer
          )
          line_shock <- sprintf(
            'shock qes("%s","%s","%s") = %s;',
            shock_index, commodity, producer,
            format(value, scientific = FALSE, digits = 16)
          )
          results_qes <- c(results_qes, line_swap, line_shock)
        }
      }
    }
  }
  
  results_qes
}

## ---- V15: forest commitment for member producers -------------------------------------------
## For a member producer, in every AEZ where forest cover would fall, Forestland cover is held at its base
## level and tinc(AEZ,"forest",r) is freed: the solved tinc is the forest-land subsidy that holds the forest.
## One-sided: solve without the commitment (pass 1), bind the AEZs where forest fell, solve again (pass 2, ...).
## max_pass: now a run parameter, see the configuration block (V19)
evos_forest <- read_har('in/basedata.har')[["evos"]][, "forest", ]      # V15: forestry land rent, AEZ x region ($M)
## V30 (member_pin = "all"): every cell where a member's forest can be held - forest cover, forestry rent (tinc has leverage) and crop or
## pasture cover (E_areaadjust: forest can only turn into crop or pasture of the same AEZ; without them the swap is singular)
lcov_base <- read_har('in/basedata.har')[["lcov"]]                       # 1000 ha, AEZ x cover x region
holdable_cells <- {
  cells <- character(0)
  for (r in dimnames(lcov_base)[[3]]) for (a in dimnames(lcov_base)[[1]])
    if (isTRUE(lcov_base[a, "forestland", r] > 0) && isTRUE(evos_forest[a, r] > 0) && isTRUE(sum(lcov_base[a, c("cropland", "pastureland"), r]) > 0))
      cells <- c(cells, paste(tolower(a), tolower(r), sep = "|"))
  cells
}

## V25: base of a numeric friction = what the region has at stake in the charged sectors, $M of the data base (the units of EV)
friction_base_values <- NULL
if (!is.na(friction_num)) {
  if (friction_base == "trade") {
    bd <- read_har('in/basedata.har')
    ch <- tolower(list_commodity_tmsf)
    if (length(setdiff(ch, dimnames(bd[["vfob"]])[[1]])) > 0) stop("charged commodities not in basedata.har VFOB: ", paste(setdiff(ch, dimnames(bd[["vfob"]])[[1]]), collapse = " "))
    vfob <- bd[["vfob"]][ch, , , drop = FALSE]                            # VFOB(c, r, s): exports of c from r to s at FOB prices
    vcif <- bd[["vcif"]][ch, , , drop = FALSE]                            # VCIF(c, r, s): imports of c into s from r at CIF prices
    for (r in dimnames(vfob)[[2]]) { vfob[, r, r] <- 0; vcif[, r, r] <- 0 }   # intra-region trade of the composite regions is never charged
    exports <- apply(vfob, 2, sum)                                        # by exporter r
    imports <- apply(vcif, 3, sum)                                        # by importer s
    friction_base_values <- (exports + imports[names(exports)])[tolower(region_sets)]
    rm(bd, vfob, vcif)
  } else {                                                                # "gdp": the V22 base
    gdp_tab <- read_excel(paste0(external_data_path, "/GDP_values.xlsx"))
    friction_base_values <- gdp_tab$GDP[match(tolower(region_sets), tolower(gdp_tab$country))]
  }
  if (any(is.na(friction_base_values))) stop("friction_base = ", friction_base, ": no value for ", paste(region_sets[is.na(friction_base_values)], collapse = " "))
  friction_base_values <- setNames(as.numeric(friction_base_values), region_sets)
  print(paste0("V25 friction ", format(friction_num, scientific = FALSE), " x ", friction_base, " (floor ", friction_floor, " M$): thresholds ",
               paste(paste0(c("eu27", "china", "us", "brasil", "indonesia", "ivorycoast"), " ", round(pmax(friction_floor, friction_num * friction_base_values[c("eu27", "china", "us", "brasil", "indonesia", "ivorycoast")]), 1)), collapse = ", "), " M$"))
}

read_forest_change_by_aez <- function() {
  # del_LUC(AEZ,"Forestland",r) of the last solution, 1000 ha: AEZ x region matrix (names lower-case, HARr)
  luc <- get_sol()[["del_luc"]]                                        # V19: cached solution
  if (length(dim(luc)) == 4) luc <- luc[, , , 1]
  luc[, "forestland", ]
}

forest_cells_falling <- function(club_producer, forest_change) {
  # "aezN|producer" cells where forest cover fell and forestry land exists (so tinc has leverage)
  cells <- character(0)
  for (producer in club_producer) for (i in 1:18) {
    aez <- sprintf("aez%d", i)
    if (isTRUE(forest_change[aez, producer] < 0) && isTRUE(evos_forest[aez, producer] > 0))
      cells <- c(cells, paste(aez, producer, sep = "|"))
  }
  cells
}

generate_text_for_forest <- function(cells) {
  out <- character(0)
  for (cell in cells) {
    p <- strsplit(cell, "|", fixed = TRUE)[[1]]; aez <- toupper(p[1]); producer <- p[2]
    out <- c(out,
      sprintf('swap p_LANDCOVER_L("%s","Forestland","%s") = tinc("%s","forest","%s");', aez, producer, aez, producer),
      sprintf('shock p_LANDCOVER_L("%s","Forestland","%s") = 0;', aez, producer))
  }
  out
}

read_forest_subsidy <- function(cells) {
  # solved tinc(AEZ,"forest",r) of the bound cells: % change in the power of the income tax on forest land
  t <- get_sol()[["tinc"]]                                             # V19: cached solution
  if (length(dim(t)) == 4) t <- t[, , , 1]
  sapply(cells, function(cell) { p <- strsplit(cell, "|", fixed = TRUE)[[1]]; t[p[1], "forest", p[2]] })
}

for (parameter in list_parameter){
  
  for (approach in list_approach){
  
    for(scenario in scenarios) {
    
    save_path <- file.path(parent_folder, "3_Output",approach, paste0(parameter, "_", run_tag),scenario,"/")   # V14
    dir.create(save_path, recursive = TRUE, showWarnings = FALSE)                                              # V14
    invisible(file.remove(list.files(save_path, full.names = TRUE)))   # V18: a rerun replaces the folder (stale iteration files would corrupt the csv)
    # Store the original shock data
    original_shock = read_har('NATDEF.har')

# Initialize an empty list to hold the outputs
    
outputs <- list()
area <- list()

iter_area <- list()
iter_area_producer <- list()
iter_area_wo_producer <- list()
reset_area <- list()
reset_area_producer <- list()
reset_area_wo_producer <- list()

iter_region <- list()
iter_region_producer <- list()
iter_region_wo_producer <- list()
reset_region <- list()
reset_region_producer <- list()
reset_region_wo_producer <- list()

# Get the initial output
## V16: iteration 0 = the EUDR baseline solved once by Baseline_EUDR.R (V14/V15 solved the EU-alone charge here)
file.copy(bl("sl4"), "NATDEF.sl4", overwrite = TRUE)   # so Forest_LU_Region_Ha_0 is the baseline's (V30: Stage B's, relative to the BAU world)
sol_cache <- NULL                                                                          # V20: the cache must not carry a previous scenario's solution
outputs[[1]] <- ev_baseline$EV[match(tolower(region_sets), tolower(ev_baseline$region))]
if (any(is.na(outputs[[1]]))) stop("EV_baseline.txt does not cover every region of sets.har")
if (welfare == "ev_net_wedge") {   # V31: round 0 on the same measure, from Stage B's solution (NATDEF.sl4 is its copy here)
  w0 <- welfare_from_sol(get_sol())
  outputs[[1]] <- w0[match(tolower(region_sets), tolower(last_welfare$region))]
  if (any(is.na(outputs[[1]]))) stop("V31: the baseline solution does not cover every region of sets.har")
  print(paste0("V31: welfare = EV net of the forest-land wedge term; round 0 wedge (world) = ", round(sum(last_welfare$wedge)), " M USD"))
}
if (is.na(friction_num)) {                                                                  # V22: "sheet" = the approach's thresholds, as before
thresholds <- read_excel(paste0(external_data_path,"/",approach,"/Thresholds_GTAPAEZ_Game_theory.xlsx"),sheet=2,col_names= FALSE,col_types=NULL,na="",skip= 0)
thresholds_down <- thresholds[, c(3)]
thresholds <- thresholds[, c(2)]
} else {                                                                                    # V22/V25: uniform friction, both thresholds = max(floor, friction x base)
  thresholds <- data.frame(t = pmax(friction_floor, friction_num * as.numeric(friction_base_values)))
  thresholds_down <- thresholds
}
thr_used <- data.frame(region = region_sets, threshold_leave = round(as.numeric(thresholds[[1]]), 3), threshold_join = round(as.numeric(thresholds_down[[1]]), 3))   # V25: the thresholds this run applies
if (!is.na(friction_num)) thr_used[[paste0("base_", friction_base, "_M$")]] <- round(as.numeric(friction_base_values), 1)
write.table(thr_used, file = paste0(save_path, "Thresholds_used.txt"), row.names = FALSE, quote = FALSE)

i <- 1
sign_check <- FALSE
converged <- FALSE   # V22
cycle <- FALSE       # V27: TRUE when the membership alternates between two coalitions (stopped, not converged)

while (!sign_check){
  # Get the output from the new run
  shock = read_har('NATDEF.har')
  cmf <- "NATDEF.cmf"
  if (i == 1){
    # Combine data, convert to data frame, and change column to numeric
    df <- data.frame(region_sets, V2 = as.numeric(outputs[[i]]), i, t = as.numeric(thresholds_down[[i]]))
    # Filter rows where V2 is greater than 0 and extract the first column
    area[[i]] <- if (identical(seed, "auto")) df[(df$V2 >= 0) | (df$V2 < 0 & abs(df$V2) < df$t) , "region_sets"] else setdiff(region_sets, seed)   # V18: EV exactly 0 starts outside; V22: area = who starts OUTSIDE (the switch below puts its complement, the seed, inside)
    # Write the output_table_wrt to a file
    write.table(cbind(region_sets, outputs[[i]], original_ev_new, i), file = paste0(save_path, "Equivalent_Variation_round_0", ".txt"), row.names = FALSE, col.names = FALSE)
    if (welfare == "ev_net_wedge" && !is.null(last_welfare)) write.table(last_welfare, file = paste0(save_path, "Welfare_decomp_round_0.txt"), row.names = FALSE)   # V31
  }else {
    area[[i]] <- selection_region(outputs[[i-1]], outputs[[i]], region_sets , i)
  }
  qg <- get_sol()[["qgdp"]]; if (length(dim(qg)) == 2) qg <- qg[, 1]                      # V20: real GDP change (%) of run l = i-1
  write.table(cbind(region_sets, as.numeric(qg[tolower(region_sets)])), file = paste0(save_path, "GDP_round_", i - 1, ".txt"), row.names = FALSE, col.names = FALSE)
  
  ev_ref <- if (join_rule == "baseline" && i >= 2) outputs[[1]] else if (i >= 2) outputs[[i - 1]] else NULL   # V19: reference EV of the join/leave rule
  if (i == 1) {                                   # V28: the experience record - EV last seen as a member / as an outsider (the baseline is everyone's first outside experience)
    ev_in_last  <- rep(NA_real_, length(region_sets))
    ev_out_last <- as.numeric(outputs[[1]])
  } else {
    for (r in seq_along(region_sets)) if (region_sets[[r]] %in% iter_area[[i - 1]]) ev_in_last[r] <- outputs[[i]][r] else ev_out_last[r] <- outputs[[i]][r]
  }
  decide_out <- function(r, i) {   # V28: TRUE if region r is OUTSIDE the club after decision i (outputs[[i]] = EV of the solve with the coalition iter_area[[i - 1]])
    if (region_sets[[r]] %in% locked_out) return(TRUE)   # V29: a locked-out region never joins
    member <- region_sets[[r]] %in% iter_area[[i - 1]]
    ev_now <- outputs[[i]][r]
    if (join_rule == "experience") {
      if (member) return((ev_now < ev_out_last[r] - thresholds[[1]][r]) || safeguard_exit(r, i))          # leave: worse than the last time outside, by more than the threshold
      ref <- if (is.na(ev_in_last[r])) ev_ref[r] else ev_in_last[r]                                        # never inside: the previous round is the only reference (consecutive rule)
      return(!(ev_now < ref - thresholds_down[[1]][r]))                                                   # join: worse than the last time inside, by more than the threshold
    }
    if (member) return(((ev_now < ev_ref[r]) && abs(ev_now - ev_ref[r]) > thresholds[[1]][r]) || safeguard_exit(r, i))   # V13-V27: leave if the round cost more than the threshold
    (ev_now >= ev_ref[r]) || ((ev_now < ev_ref[r]) && abs(ev_now - ev_ref[r]) < thresholds_down[[1]][r])                  # stays out unless the round cost more than the threshold
  }
  safeguard_exit <- function(r, i) {   # V27: bounded-loss safeguard of region r at decision i (outputs[[k]] = EV of the solve with the coalition iter_area[[k - 1]])
    if (safeguard == "off" || i < 3 || !(region_sets[[r]] %in% iter_area[[i - 1]])) return(FALSE)
    if (safeguard == "level") return((outputs[[i]][r] < limit$GDP[r]) && (outputs[[i - 1]][r] < limit$GDP[r]) && (outputs[[i - 2]][r] < limit$GDP[r]))   # V13-V26
    if (i < 4) return(FALSE)
    member3 <- all(sapply(c(i - 1, i - 2, i - 3), function(k) region_sets[[r]] %in% iter_area[[k]]))                  # a member in the three last solves
    member3 && all(sapply(c(i, i - 1, i - 2), function(k) (outputs[[k]][r] - outputs[[1]][r]) < limit$GDP[r]))        # and more than 0.1 % of GDP below the baseline in each
  }
  for (r in 1:42) {
    # Check if this region had a negative output in the previous iteration
    if (i == 1 ) {
      iter_area[[i]] <- setNames(area[[i]], paste0("h", seq_along(area[[i]])))
      reset_area[[i]] <- setNames(setdiff(region_sets, unlist(iter_area[[i]])), paste0("h", seq_along(setdiff(region_sets, unlist(iter_area[[i]])))))
      
      #Switch for the first iteration
      temp <- iter_area[[i]]
      iter_area[[i]] <- reset_area[[i]]
      reset_area[[i]] <- temp
      iter_region <- iter_area[[i]]
      reset_region <- reset_area[[i]]
      move <- move_producer_coalition(iter_region)
      iter_area_wo_producer[[i]] <- move$iter_region
      iter_area_producer[[i]]    <- move$producer_coalition
      iter_region_wo_producer  <- iter_area_wo_producer[[i]]
      iter_region_producer <- iter_area_producer[[i]]
      move_reset <- move_producer_reset (reset_region)
      reset_area_wo_producer[[i]] <- move_reset$reset_region
      reset_area_producer[[i]] <- move_reset$producer_reset
      reset_region_wo_producer <- reset_area_wo_producer[[i]]
      reset_region_producer <- reset_area_producer[[i]]
    }else if (i == 2) {
      if (decide_out(r, i))   # V28: one function for both rules (V13-V27 conditions unchanged under join_rule = "consecutive")
      {
        # The output was negative in the previous iteration and is positive now
        # Add the region to the switched_regions list
        reset_region <- c(reset_region, region_sets[r])
        reset_area[[i]] <- reset_region
        reset_region <- unlist(reset_region)
        move_reset <- move_producer_reset (reset_region)
        reset_area_wo_producer[[i]] <- move_reset$reset_region
        reset_area_producer[[i]] <- move_reset$producer_reset
        reset_region_wo_producer <- reset_area_wo_producer[[i]]
        reset_region_producer <- reset_area_producer[[i]]
      }else {
        iter_region <- c(iter_region, region_sets[r])
        iter_area[[i]] <- iter_region
        iter_region <- unlist(iter_region)
        move_producer <- move_producer_coalition(iter_region)
        iter_area_wo_producer[[i]] <- move_producer$iter_region
        iter_area_producer[[i]] <- move_producer$producer_coalition
        iter_region_wo_producer <- iter_area_wo_producer[[i]] 
        iter_region_producer <- iter_area_producer[[i]]
      }
    }else {
      if (decide_out(r, i))   # V28: one function for both rules (V13-V27 conditions + the V27 safeguard unchanged under join_rule = "consecutive")
      {
        # The output was negative in the previous iteration and is positive now
        # Add the region to the switched_regions list
        reset_region <- c(reset_region, region_sets[r])
        reset_area[[i]] <- reset_region
        reset_region <- unlist(reset_region)
        move_reset <- move_producer_reset (reset_region)
        reset_area_wo_producer[[i]] <- move_reset$reset_region
        reset_area_producer[[i]] <- move_reset$producer_reset
        reset_region_wo_producer <- reset_area_wo_producer[[i]]
        reset_region_producer <- reset_area_producer[[i]]
      }else {
        iter_region <- c(iter_region, region_sets[r])
        iter_area[[i]] <- iter_region
        iter_region <- unlist(iter_region)
        move_producer <- move_producer_coalition(iter_region)
        iter_area_wo_producer[[i]] <- move_producer$iter_region
        iter_area_producer[[i]] <- move_producer$producer_coalition
        iter_region_wo_producer <- iter_area_wo_producer[[i]] 
        iter_region_producer <- iter_area_producer[[i]]
      }
    } 
  }

  shock[["0101"]] <- original_shock[["0101"]]
  
  ## V17: one rule replaces shock_ABCD / shock_eu27 / shock_BD / shock_D / shock_CD / shock_eu27_exp
  members_i   <- unique(c("eu27", iter_area_producer[[i]], iter_area_wo_producer[[i]]))   # the EU is always a member
  outsiders_i <- setdiff(region_sets, members_i)
  members_final <- members_i                                                              # V22: the coalition the loop stops at
  shock <- shock_outsiders_into_members(shock, members_i, outsiders_i)

  cmf_path <- paste0(GTAPAEZ_path,"/NATDEF.cmf")
  lines <- readLines(cmf_path, warn = FALSE)
  cutoff_line <- which(lines == "! Part for productivity shocks;")
  if (length(cutoff_line) == 0) {
    stop("The line 'Rest Endogenous ;' was not found in the file.")
  }
  # Keep all lines up to and including "Rest Endogenous;"
  lines <- lines[1:cutoff_line]
  lines <- set_data_line(lines)                                                       # V30: start from the BAU world
  lines_tms_f <- 'Shock tms_f =  file NATDEF.har header "0101";'
  lines_tms_f_2 <- '! Part for productivity shocks from R;'
  bau_txt <- generate_text_for_bau(members_i, outsiders_i)                                                    # V21
  lines <- c(lines,lines_tms_f, generate_text_for_eudr(outsiders_i), bau_txt$lines, lines_tms_f_2)   # V16: EUDR cost on non-members (V17: same outsiders as the charge); V21: BAU clearing / pinned members
  lines <- set_solver_lines(lines, solve_mode)                                        # V19: solver settings
  solve_log_dir <- save_path                                                          # V19: solver logs next to the results
  # Write the updated content back to the file
  writeLines(lines, cmf_path)
  
  filename = paste0(save_path,"CMF_iter_", i, ".cmf")
  # Modify lines to remove " and \
  cleaned_lines = gsub('"', '', lines)  # Remove double quotes
  cleaned_lines = gsub('\\\\', '', cleaned_lines)  # Remove backslashes, note double escape to represent a single backslash
  # Write to file without quotes and backslashes
  write.table(cleaned_lines, filename, sep = "\t", row.names = FALSE, col.names = FALSE, quote = FALSE)

  
  if(parameter == "qo"){
    
    cmf_path <- paste0(GTAPAEZ_path,"/NATDEF.cmf")
    lines <- readLines(cmf_path, warn = FALSE)
    
    method_line_index <- grep("Method =", lines)
    step_line_index <- grep("Steps =", lines)
    subinterval_line_index <- grep("subintervals =", lines)
    accuracy_line_index <- grep("automatic accuracy =", lines)
    
    lines[method_line_index] <- "Method = Euler;"
    lines[step_line_index] <- "Steps = 2 4;"
    lines[subinterval_line_index] <- "subintervals = 3;"
    lines[accuracy_line_index] <- "automatic accuracy = no;"
    
    writeLines(lines, cmf_path)}
  
  # if(parameter == "qxw"){
  #   
  #   cmf_path <- paste0(GTAPAEZ_path,"/NATDEF.cmf")
  #   lines <- readLines(cmf_path, warn = FALSE)
  #   
  #   method_line_index <- grep("Method =", lines)
  #   step_line_index <- grep("Steps =", lines)
  #   subinterval_line_index <- grep("subinterval =", lines)
  #   accuracy_line_index <- grep("automatic accuracy =", lines)
  #   
  #   lines[method_line_index] <- "Method = Euler;"
  #   lines[step_line_index] <- "Steps = 1 2;"
  #   lines[subinterval_line_index] <- "subinterval = 3;"
  #   lines[accuracy_line_index] <- "automatic accuracy = no;"
  #   
  #   writeLines(lines, cmf_path)}
  

  # Generate productivity shock
    text_q <- generate_shock_for_qo(iter_area_producer[[i]])
    # Generate productivity swap
    text_for_all_countries <- sapply(iter_area_producer[[i]], generate_swap_for_qo)
    # Flatten text_for_all_countries if it's not already a vector
    flattened_text_for_all_countries <- as.vector(text_for_all_countries)
    
    # Combine flattened_text_for_all_countries and text_q into one vector
    # Append the additional lines
    #additional_lines_1 <- "Shock tms_f = file TMSF.har header \"0083\";"
    #combined_text <- c(flattened_text_for_all_countries, text_q, additional_lines_1)
    
    text_qes <- generate_text_for_qes(iter_area_producer[[i]])

    
    #text_qoes_for_all_countries <- sapply(iter_area_producer[[i]], generate_swap_for_qoes)
    # Flatten text_for_all_countries if it's not already a vector
    #flattened_text_qoes_for_all_countries <- as.vector(text_qoes_for_all_countries)'
    text_qxw <- generate_text_for_qxw(iter_area_producer[[i]])
    
    if (parameter == "qo"){
      combined_text <- c(flattened_text_for_all_countries, text_q)
      } else if(parameter == "qes") {combined_text <-text_qes
        } else if(parameter == "qxw") {combined_text <-text_qxw
        } else {combined_text <- character(0)}   # V15: "forest" writes its lines after pass 1, below
    
    if (length(combined_text) > 0) {
      update_cmf_file(combined_text,i)
    }

  
  tmsf <- list("0101" = shock[["0101"]])
  
  # write the different shocks
  #write_har(tmsf, "TMSF.har" , maxSize = 1e4)
  write_har(shock, 'NATDEF.har', maxSize = 1e4)
  
  # write the iteration for control
  #filename_2 = paste0(save_path,"tmsf_iter_", i, ".har")
  #write_har(tmsf, filename_2 , maxSize = 1e4)

  l = i-1
  
  filename_3 = paste0(save_path,"NATDEF_iter_", i, ".har")
  write_har(shock, filename_3 , maxSize = 1e4)
  
# Write the vector to a file. Include the iteration number in the file name.
  
  luc <- forest_data(i)
  
  write.table(luc, file = paste0(save_path,"Forest_LU_Region_Ha_",l, ".txt"), row.names = FALSE, col.names = FALSE)
  
  write.table(reset_region, file = paste0(save_path,"Reset_Region_",l, ".txt"), row.names = FALSE, col.names = FALSE)
  write.table(iter_region, file = paste0(save_path,"Iter_Region_",l, ".txt"), row.names = FALSE, col.names = FALSE)
  write.table(iter_region_wo_producer, file = paste0(save_path,"Iter_Region_wo_producer_",l, ".txt"), row.names = FALSE, col.names = FALSE)
  write.table(iter_region_producer, file = paste0(save_path, "Iter_Region_producer_",l, ".txt"), row.names = FALSE, col.names = FALSE)
  write.table(reset_region_wo_producer, file = paste0(save_path, "Reset_Region_wo_producer_",l, ".txt"), row.names = FALSE, col.names = FALSE)
  write.table(reset_region_producer, file = paste0(save_path, "Reset_Region_producer_",l, ".txt"), row.names = FALSE, col.names = FALSE)
  
  if (parameter == "forest" && bau_horizon > 0) {                                            # V21: one solve, members pinned by the CMF lines
    outputs[[i + 1]] <- run_Gtap(i + 1, bound_cells = bau_txt$pinned, label = paste0("iter_", i), targets = bau_txt$targets)   # V23: every BAU cell checked
    pinned <- bau_txt$pinned
    if (start_from == "bau") {                                                                 # V30: non-members' forest is endogenous - its change vs the BAU world is the leakage, in hectares
      luc_i <- read_forest_change_by_aez() * 1000                                              # aez x region, ha
      rs <- tolower(region_sets)
      lk <- data.frame(region = rs, status = ifelse(rs %in% tolower(members_i), "member", "outsider"),
                       forest_change_trop_ha = colSums(luc_i[paste0("aez", 1:6), rs, drop = FALSE]), forest_change_all_ha = colSums(luc_i[, rs, drop = FALSE]), stringsAsFactors = FALSE)
      bau_imp <- tapply(-bau_baseline$shock_pct / 100 * bau_baseline$forest_cover_ha, tolower(bau_baseline$region), sum)
      lk$bau_clearing_all_ha <- as.numeric(bau_imp[rs]); lk$bau_clearing_all_ha[is.na(lk$bau_clearing_all_ha)] <- 0
      lk$leakage_pct_of_bau <- ifelse(lk$status == "outsider" & lk$bau_clearing_all_ha > 0, -100 * lk$forest_change_all_ha / lk$bau_clearing_all_ha, NA)
      write.table(lk, file = paste0(save_path, "Forest_leakage_", i, ".txt"), row.names = FALSE)
      print(paste0("V30 round ", i, ": members' tropical forest vs the BAU world ", round(sum(lk$forest_change_trop_ha[lk$status == "member"]) / 1e3), " kha; outsiders' ",
                   round(sum(lk$forest_change_trop_ha[lk$status == "outsider"]) / 1e3), " kha (negative = leakage)"))
    }
    if (bau_outsiders == "cover" && length(bau_txt$out_cells) > 0) {                          # V23: wedge holding non-members on the BAU path vs the baseline's tinc*
      pr <- data.frame(cell = bau_txt$out_cells, tinc_bau = bau_baseline$tinc_solved[match(bau_txt$out_cells, bau_baseline$cell)],
                       tinc_iter = read_forest_subsidy(bau_txt$out_cells))
      pr$ratio <- pr$tinc_iter / pr$tinc_bau                                                  # < 1: the market would clear more than BAU (leakage pressure); > 1: less
      write.table(pr, file = paste0(save_path, "Forest_pressure_", i, ".txt"), row.names = FALSE)
    }
    info <- if (length(pinned) > 0) data.frame(cell = pinned, tinc_forest = read_forest_subsidy(pinned),
                                               tinc_bau = bau_baseline$tinc_solved[match(pinned, bau_baseline$cell)])
            else data.frame(cell = "none", tinc_forest = NA, tinc_bau = NA)
    info$passes <- 1; info$still_falling <- ""
    write.table(info, file = paste0(save_path, "Forest_commitment_", i, ".txt"), row.names = FALSE)
  } else if (parameter == "forest" && length(iter_area_producer[[i]]) > 0) {                # V15
    members_p <- iter_area_producer[[i]]
    bound <- character(0)
    for (pass in 1:max_pass) {
      ev_pass <- run_Gtap(i + 1, bound_cells = bound, label = paste0("iter_", i, "_pass_", pass))   # V19: checked solve
      falling <- setdiff(forest_cells_falling(members_p, read_forest_change_by_aez()), bound)
      if (length(falling) == 0 || pass == max_pass) break
      bound <- c(bound, falling)
      update_cmf_file(generate_text_for_forest(bound), i)
    }
    outputs[[i + 1]] <- ev_pass                          # the last solve is the iteration's solution
    info <- if (length(bound) > 0) data.frame(cell = bound, tinc_forest = read_forest_subsidy(bound)) else data.frame(cell = "none", tinc_forest = NA)
    info$passes <- pass; info$still_falling <- paste(falling, collapse = " ")
    write.table(info, file = paste0(save_path, "Forest_commitment_", i, ".txt"), row.names = FALSE)
  } else {
    outputs[[i + 1]] <- run_Gtap(i + 1, label = paste0("iter_", i))   # V19: checked solve
  }
  if (dynamics == "off") {                                                                 # V22: the seed is the coalition - write this run's files (the next iteration would have) and stop
    write.table(cbind(region_sets, outputs[[i]], outputs[[i + 1]], i + 1), file = paste0(save_path, "Equivalent_Variation_round_", i, ".txt"), row.names = FALSE, col.names = FALSE)
    if (!is.null(last_welfare)) write.table(last_welfare, file = paste0(save_path, "Welfare_decomp_round_", i, ".txt"), row.names = FALSE)   # V31: the round's solution (the last solve read)
    qg <- get_sol()[["qgdp"]]; if (length(dim(qg)) == 2) qg <- qg[, 1]
    write.table(cbind(region_sets, as.numeric(qg[tolower(region_sets)])), file = paste0(save_path, "GDP_round_", i, ".txt"), row.names = FALSE, col.names = FALSE)
    write.table(forest_data(i + 1), file = paste0(save_path, "Forest_LU_Region_Ha_", i, ".txt"), row.names = FALSE, col.names = FALSE)
    sign_check <- TRUE; converged <- TRUE
  }
  
  # if (4<i && i<25){
  #   # Calculate the difference measure between the current output and the previous one
  #   # For example, you can use the sum of absolute differences. Depending on your needs, you might want to use a different measure.
  #   #sign_check <- all(outputs[[i + 1]] > outputs[[i]] | outputs[[i + 1]] > outputs[[1]])
  #   
  #   #sign_check <- length(setdiff(iter_area[i], iter_area[i-1])) == 0
  #   #comparing with the last 4 iterations 
  #     for (j in 1:3) {
  #       if ((length(setdiff(iter_area[[i]], iter_area[[i - j]])) == 0) && (length(setdiff(iter_area[[i-j]], iter_area[[i]])) == 0)) {
  #         sign_check <- TRUE
  #         break  # Exit the loop if a match is found
  #       }
  #     }
  # }
  
  if (2 < i && i < max_rounds - 1){   # V28: max_rounds (25 in V13-V27)
    # Calculate the difference measure between the current output and the previous one
    # For example, you can use the sum of absolute differences. Depending on your needs, you might want to use a different measure.
    #sign_check <- all(outputs[[i + 1]] > outputs[[i]] | outputs[[i + 1]] > outputs[[1]])
    
    #sign_check <- length(setdiff(iter_area[i], iter_area[i-1])) == 0
    #comparing with the last 4 iterations 
      if ((length(setdiff(iter_area[[i]], iter_area[[i - 1]])) == 0) && (length(setdiff(iter_area[[i-1]], iter_area[[i]])) == 0)) {
        sign_check <- TRUE; converged <- TRUE   # V22: converged
        break  # Exit the loop if a match is found
    }
  }
  if (3 < i && i < max_rounds - 1 && !sign_check) {   # V27: a cycle of period k (the memberships of rounds i and i-1 repeat those of i-k and i-k-1) never converges - stop, keep the last coalition, report it
    same_set <- function(a, b) length(setdiff(a, b)) == 0 && length(setdiff(b, a)) == 0
    for (k in 2:min(6, floor((i - 1) / 2))) {
      if (same_set(iter_area[[i]], iter_area[[i - k]]) && same_set(iter_area[[i - 1]], iter_area[[i - k - 1]])) {
        cycle <- TRUE; sign_check <- TRUE
        moving <- unique(unlist(lapply(1:k, function(j) setdiff(union(iter_area[[i - j + 1]], iter_area[[i - j]]), intersect(iter_area[[i - j + 1]], iter_area[[i - j]])))))
        print(paste0("V27: the membership cycles with period ", k, " (rounds ", i - k - 1, " to ", i, "; moving: ", paste(moving, collapse = " "), ") - stopped, not converged"))
        break
      }
    }
    if (cycle) break
  }
  
  if (i == max_rounds){   # V28
    # Calculate the difference measure between the current output and the previous one
    # For example, you can use the sum of absolute differences. Depending on your needs, you might want to use a different measure.
    #sign_check <- all(outputs[[i + 1]] > outputs[[i]] | outputs[[i + 1]] > outputs[[1]])
    sign_check <- TRUE
  } 
  
  # Clear the region to reset and Increase the iteration number
  reset_region <- NULL
  iter_region <- NULL
  reset_area_producer[i+1] <- list(NULL)
  reset_area_wo_producer[i+1] <- list(NULL)
  reset_area[i+1] <- list(NULL)
  iter_area_producer[i+1] <- list(NULL)      # V17: an iteration where nobody joins no longer crashes
  iter_area_wo_producer[i+1] <- list(NULL)   # V17
  iter_area[i+1] <- list(NULL)               # V17
  
  sl4 <-"NATDEF.sl4"
  
  source_tracker <- file.path(parent_folder, "2_Model", sl4)
  destination_tracker <- file.path(save_path, paste0(sub("\\.([^.]+)$", paste0("_", i, ".\\1"), sl4)))
  
  result_tracker <- file.copy(source_tracker, destination_tracker, overwrite = TRUE)
  
  if (result_tracker) {
    print(paste("File copy successful for", bu_file))
  } else {
    print(paste("File copy failed for", bu_file))
  }
  
  i <- i + 1
}

## V27: outcome of the membership process, written for every run (Run_summary.txt in the run folder) and printed
run_outcome <- if (converged) "converged" else if (cycle) "cycle (not converged)" else "stopped at the round cap (not converged)"
writeLines(c(paste0("run: ", run_tag), paste0("seed: ", paste(seed, collapse = " "), " | dynamics: ", dynamics, " | join rule: ", join_rule, " | safeguard: ", safeguard, " | round cap: ", max_rounds),
             paste0("V30: start_from = ", start_from, if (start_from == "bau") paste0(" (", bl("data"), ") | eudr_outsiders = ", eudr_outsiders, " | member_pin = ", member_pin, " | welfare = ", welfare) else paste0(" | eudr_in_loop = ", eudr_in_loop)),
             paste0("outcome: ", run_outcome, " | solves: ", length(outputs) - 1),
             paste0("final coalition (", length(members_final), "): ", paste(sort(members_final), collapse = " "))),
           paste0(save_path, "Run_summary.txt"))
print(paste0("V27: ", run_outcome, " after ", length(outputs) - 1, " solves - final coalition: ", paste(sort(members_final), collapse = " ")))

## ---- V22: one-deviation stability check of the final coalition ---------------------------------------
##  S = the coalition the loop stopped at (members_final), solved last. Every test starts again from S and moves
##  ONE region: each member (the EU excepted) is taken out alone, each outsider of stability_scope is put in
##  alone; one solve per test, the charge / EUDR cost / pinned forest of the others exactly as in S.
##    member m wants to leave  if EV_m(S \ m) > EV_m(S)      -> S internally stable if nobody does
##    outsider o wants to join if EV_o(S + o) > EV_o(S)      -> S externally stable if nobody does
##  gain_from_moving = EV_deviation - EV_in_S; transfer_needed = max(0, gain) of a member (what keeps it in);
##  wants_to_move_with_friction uses the thresholds of the run as a moving cost; revenue_charge = duty the charge
##  (+ tau) raises on the member's imports from outsiders at the trade of S (VMSB x s / (100 + s), gdata.upd).
if (stability && parameter == "forest" && bau_horizon > 0) {
  S_final <- members_final
  O_final <- setdiff(region_sets, S_final)
  O_scope <- if (identical(stability_scope, "all")) O_final else intersect(tolower(trimws(strsplit(stability_scope, ",")[[1]])), O_final)
  O_scope <- setdiff(O_scope, locked_out)   # V29: a locked-out region is not tested for joining
  ev_S <- setNames(outputs[[length(outputs)]], region_sets)     # EV in S (the last solve)
  ev_0 <- setNames(outputs[[1]], region_sets)                   # EV in the baseline (EUDR + BAU, no coalition)
  thr_leave <- setNames(as.numeric(thresholds[[1]]), region_sets)
  thr_join  <- setNames(as.numeric(thresholds_down[[1]]), region_sets)
  tropical_forest_kha <- function() { luc <- get_sol()[["del_luc"]]; if (length(dim(luc)) == 4) luc <- luc[, , , 1]; sum(luc[paste0("aez", 1:6), "forestland", ]) }
  trop_S <- tropical_forest_kha()
  luc0 <- read.table(bl("luc"), header = FALSE); trop_0 <- sum(luc0[, 2:7]) / 1000     # V30: Stage B's forest (relative to the BAU world) in bau mode
  revenue <- tryCatch({                                          # duty raised by the charge on each member's imports from outsiders ($M), from the updated data of the last solve
    v <- read_har('gdata.upd')[["vmsb"]]
    g <- expand.grid(cm = dimnames(v)[[1]], o = O_final, m = S_final, stringsAsFactors = FALSE)
    sh <- as.numeric(shock[["0101"]][as.matrix(g)]); sh[is.na(sh)] <- 0
    tapply(as.numeric(v[as.matrix(g)]) * sh / (100 + sh), g$m, sum)[S_final]
  }, error = function(e) { print(paste("charge revenue not computed:", conditionMessage(e))); setNames(rep(NA_real_, length(S_final)), S_final) })
  solve_coalition <- function(members, label) {                 # one solve of an arbitrary coalition, same CMF rules as the loop
    members <- unique(c("eu27", members)); outsiders <- setdiff(region_sets, members)
    sh <- read_har('NATDEF.har'); sh[["0101"]] <- original_shock[["0101"]]
    sh <- shock_outsiders_into_members(sh, members, outsiders)
    write_har(sh, 'NATDEF.har', maxSize = 1e4)
    lines <- readLines(cmf_path, warn = FALSE)
    lines <- lines[1:which(lines == "! Part for productivity shocks;")]
    lines <- set_data_line(lines)                                                    # V30
    bau_k <- generate_text_for_bau(members, outsiders)
    lines <- c(lines, 'Shock tms_f =  file NATDEF.har header "0101";', generate_text_for_eudr(outsiders), bau_k$lines, '! Part for productivity shocks from R;')
    writeLines(set_solver_lines(lines, solve_mode), cmf_path)
    setNames(run_Gtap(0, bound_cells = bau_k$pinned, label = label, targets = bau_k$targets), region_sets)   # V23
  }
  M_scope <- setdiff(S_final, "eu27")                            # V32 (4 Oct): the members tested for leaving
  if (!identical(stability_members, "all")) M_scope <- if (identical(stability_members, "none")) character(0) else intersect(tolower(trimws(strsplit(stability_members, ",")[[1]])), M_scope)
  tests <- rbind(data.frame(region = "eu27",                    status = "eu27_anchor", stringsAsFactors = FALSE),
                 data.frame(region = M_scope,                   status = rep("member", length(M_scope)),   stringsAsFactors = FALSE),   # rep(): an empty scope is a 0-row frame
                 data.frame(region = O_scope,                   status = rep("outsider", length(O_scope)), stringsAsFactors = FALSE))
  tests$EV_baseline <- ev_0[tests$region]; tests$EV_in_S <- ev_S[tests$region]; tests$EV_in_S_vs_baseline <- tests$EV_in_S - tests$EV_baseline
  tests$EV_deviation <- NA_real_; tests$world_EV_deviation <- NA_real_; tests$tropical_forest_kha_deviation <- NA_real_; tests$solve_ok <- NA
  ev_dev <- matrix(NA_real_, length(region_sets), nrow(tests), dimnames = list(region_sets, paste0(c(eu27_anchor = "S_", member = "out_", outsider = "in_")[tests$status], tests$region)))
  ev_dev[, 1] <- ev_S
  print(paste("V22 stability check of", approach, run_tag, ":", nrow(tests) - 1, "one-deviation solves"))
  for (k in seq_len(nrow(tests))[-1]) {
    rg <- tests$region[k]
    ev_k <- tryCatch(solve_coalition(if (tests$status[k] == "member") setdiff(S_final, rg) else c(S_final, rg), label = paste0("dev_", rg)),
                     error = function(e) { print(paste("deviation solve failed:", rg, "-", conditionMessage(e))); NULL })
    tests$solve_ok[k] <- !is.null(ev_k)
    if (is.null(ev_k)) next
    ev_dev[, k] <- ev_k
    tests$EV_deviation[k] <- ev_k[rg]; tests$world_EV_deviation[k] <- sum(ev_k); tests$tropical_forest_kha_deviation[k] <- tropical_forest_kha()
  }
  tests$gain_from_moving <- tests$EV_deviation - tests$EV_in_S
  tests$threshold <- ifelse(tests$status == "member", thr_leave[tests$region], ifelse(tests$status == "outsider", thr_join[tests$region], NA))
  tests$wants_to_move <- tests$gain_from_moving > 0
  tests$wants_to_move_with_friction <- tests$gain_from_moving > tests$threshold
  tests$transfer_needed <- ifelse(tests$status == "member", pmax(0, tests$gain_from_moving), 0)
  tests$revenue_charge <- ifelse(tests$status %in% c("member", "eu27_anchor"), revenue[tests$region], 0)
  leavers  <- tests$region[tests$status == "member"   & tests$wants_to_move %in% TRUE]
  joiners  <- tests$region[tests$status == "outsider" & tests$wants_to_move %in% TRUE]
  leavers_f <- tests$region[tests$status == "member"   & tests$wants_to_move_with_friction %in% TRUE]
  joiners_f <- tests$region[tests$status == "outsider" & tests$wants_to_move_with_friction %in% TRUE]
  surplus <- -sum(pmin(0, tests$gain_from_moving[tests$status == "member"]), na.rm = TRUE)
  summary_txt <- c(
    paste0("V22 one-deviation stability check - ", approach, " / ", parameter, "_", run_tag),
    paste0("seed: ", paste(seed, collapse = " "), if (length(locked_out) > 0) paste0(" | locked out: ", paste(locked_out, collapse = " ")) else "", " | dynamics: ", dynamics, " | converged: ", converged, if (cycle) " (cycle)" else "", " | safeguard: ", safeguard, " | iterations: ", length(outputs) - 1),   # V27; V29: locked regions
    paste0("final coalition S (", length(S_final), "): ", paste(S_final, collapse = " ")),
    paste0("tested - members out alone: ", if (length(M_scope) == length(S_final) - 1) "all" else if (length(M_scope) == 0) "none" else paste(M_scope, collapse = " "), " | outsiders in alone: ", paste(O_scope, collapse = " ")),   # V32 (4 Oct)
    paste0("EV in S vs baseline ($M/yr) - members: ", round(sum(ev_S[S_final] - ev_0[S_final])), " | outsiders: ", round(sum(ev_S[O_final] - ev_0[O_final])),
           " | world: ", round(sum(ev_S - ev_0)), " | members losing vs baseline: ", paste(S_final[ev_S[S_final] < ev_0[S_final]], collapse = " ")),
    paste0("tropical forest change (kha, AEZ1-6, world): baseline ", round(trop_0), " | S ", round(trop_S), " | difference ", round(trop_S - trop_0)),
    paste0("internally stable (no member gains by leaving alone): ", length(leavers) == 0, if (length(leavers) > 0) paste0(" - would leave: ", paste(leavers, collapse = " ")) else ""),
    paste0("externally stable (no outsider gains by joining alone): ", length(joiners) == 0, if (length(joiners) > 0) paste0(" - would join: ", paste(joiners, collapse = " ")) else ""),
    paste0("with the thresholds as moving cost - would leave: ", paste(leavers_f, collapse = " "), " | would join: ", paste(joiners_f, collapse = " ")),
    paste0("transfers to keep the leavers ($M/yr): ", round(sum(tests$transfer_needed, na.rm = TRUE)), " | what the members who prefer S could pay: ", round(surplus),
           " | duty raised by the charge in S: ", if (all(is.na(revenue))) "not computed" else round(sum(revenue, na.rm = TRUE))),
    paste0("deviation solves failed: ", sum(tests$solve_ok %in% FALSE)))
  cat(summary_txt, sep = "\n")
  writeLines(summary_txt, paste0(save_path, "Stability_summary.txt"))
  write.table(tests, file = paste0(save_path, "Stability_tests.txt"), row.names = FALSE)
  write.table(data.frame(region = region_sets, EV_baseline = ev_0, ev_dev), file = paste0(save_path, "Stability_EV_by_test.txt"), row.names = FALSE)
  writeLines(c(summary_txt, "", capture.output(print(tests, row.names = FALSE, digits = 4))),
             file.path(parent_folder, "4_DB", paste0("Stability_", approach, "_", parameter, "_", run_tag, ".txt")))
} else if (stability) print("V22: stability check skipped (needs parameter = forest and bau_horizon > 0)")

## Last, restore the BU from the original RunGTAP
# List of BU files to copy
bu_files <- c("NATDEF.har", "NATDEF.sl4", "NATDEF.cmf")

# Source and destination folders are as per your setup
source_folder_copy <- file.path(parent_folder, "2_Model", "BU/")
destination_folder_paste <- GTAPAEZ_path

# Loop to iterate through each BU file
for (bu_file in bu_files) {
  
  # Full path of the source and destination files
  source_file_path_copy <- file.path(source_folder_copy, bu_file)
  destination_file_path_paste <- file.path(destination_folder_paste, bu_file)
  
  # Check if the source file exists
  if (!file.exists(source_file_path_copy)) {
    print(paste("Source file does not exist:", bu_file))
    next
  }
  
  # Check if the destination folder exists
  if (!dir.exists(destination_folder_paste)) {
    print("Destination folder does not exist.")
    next
  }
  
  # Attempt to copy and overwrite if the file already exists
  result <- file.copy(source_file_path_copy, destination_file_path_paste, overwrite = TRUE)

  
  # Check the result
  if (result) {
    print(paste("File copy successful for", bu_file))
  } else {
    print(paste("File copy failed for", bu_file))
  }
  # Check the result
  
}

print(paste( scenario,"Processed"))
}
}
}



tableau_db <- data.frame()

for (approach in list_approach){
  for (p in list_parameter){  
    for (name in length(scenarios)) {
      
      #approach = "Diplomatic"
      #p = "qes"
      #name = 1
      
      iter_db <- data.frame()
      reset_db <- data.frame() 
      ev_db <- data.frame()# Create an empty data frame to store the aggregated data
      luc_db <- data.frame()
      
      scenario_path <- file.path(parent_folder, "3_Output",approach, paste0(p, "_", run_tag), scenarios[[name]])   # V14
      
      file_iter_names <- list.files(path = scenario_path, pattern = "Iter_Region_\\d+\\.txt", full.names = TRUE)
      file_reset_names <- list.files(path = scenario_path, pattern = "Reset_Region_\\d+\\.txt", full.names = TRUE)
      file_ev_names <- list.files(path = scenario_path, pattern = "Equivalent_Variation_round_\\d+\\.txt", full.names = TRUE)
      file_luc_names <- list.files(path = scenario_path, pattern = "Forest_LU_Region_Ha_\\d+\\.txt", full.names = TRUE)
      
      for(file in file_iter_names) {
        # Read the txt file into a data frame
        iter_raw <- read.table(file, header = FALSE, sep = "\t", col.names= "Country")  # Assuming the files are tab-separated
        if(nrow(iter_raw) == 0) {
          warning(paste("File is empty:", file))
          next
        }
        # Extract the iteration number from the filename
        iteration_number <- gsub(".*Iter_Region_([0-9]+)\\.txt$", "\\1", file)
        # Add new columns to iter_raw with the iteration number and scenario
        iter_raw$Iteration <- as.integer(iteration_number) + 1   # V20: the sets in Iter_Region_<l> produce run l+1
        iter_raw$Scenario <- scenarios[[name]]
        iter_raw$Club <- "inside"
        # Append the data to the aggregated data frame
        iter_db <- bind_rows(iter_db, iter_raw)
      }
      
      for(file in file_reset_names) {
        # Read the txt file into a data frame
        reset_raw <- read.table(file, header = FALSE, sep = "\t", col.names= "Country")  # Assuming the files are tab-separated
        if(nrow(reset_raw) == 0) {
          warning(paste("File is empty:", file))
          next
        }
        # Extract the iteration number from the filename
        reset_number <- gsub(".*Reset_Region_([0-9]+)\\.txt$", "\\1", file)
        # Add new columns to iter_raw with the iteration number and scenario
        reset_raw$Iteration <- as.integer(reset_number) + 1      # V20: the sets in Reset_Region_<l> produce run l+1
        reset_raw$Scenario <- scenarios[[name]]
        reset_raw$Club <- "outside"
        # Append the data to the aggregated data frame
        reset_db <- bind_rows(reset_db, reset_raw)
      }
      
      for(file in file_luc_names) {
        # Read the txt file into a data frame
        
        #file = "C:/runGTAP375/Game_theory_2024/3_Output/Diplomatic/qes/Scenario_D/Forest_LU_Region_Ha_0.txt"
        
        luc_raw <- read.table(file, header = FALSE, sep = " ",)  # Assuming the files are tab-separated
        
        # Add new columns to iter_raw with the iteration number and scenario
        luc_number <- gsub(".*Forest_LU_Region_Ha_([0-9]+)\\.txt$", "\\1", file)
        
        luc_raw$Iteration <- as.integer(luc_number)
        luc_raw$Scenario <- scenarios[[name]]
        
        luc_raw <- luc_raw %>% rename (Country = V1, 
                                       aez1 = V2,aez2 = V3,aez3 = V4,aez4 = V5,aez5 = V6,aez6 = V7,
                                       aez7 = V8,aez8 = V9,aez9 = V10,aez10 = V11,aez11 = V12,aez12 = V13,
                                       aez13 = V14,aez14 = V15,aez15 = V16,aez16 = V17,aez17 = V18,aez18 = V19)
        
        # Append the data to the aggregated data frame
        luc_db <- bind_rows(luc_db, luc_raw)
      }
      
      for(file in file_ev_names) {
        # Read the txt file into a data frame
        
        #file  = "C:/runGTAP375/Game_theory_2024/3_Output/Diplomatic/qes/Scenario_D/Equivalent_Variation_round_0.txt" 
        
        ev_raw <- read.table(file, header = FALSE, sep = " ", col.names= c("Country", "EV_previous_round", "EV","Iteration"))  # Assuming the files are tab-separated
        # Add new columns to iter_raw with the iteration number and scenario
        ev_raw$Scenario <- scenarios[[name]]
        # Append the data to the aggregated data frame
        ev_db <- bind_rows(ev_db, ev_raw)
      }
    
      db_df <- rbind(iter_db, reset_db)
      db_df <- rbind(data.frame(Country = as.character(region_sets), Iteration = 0L, Scenario = scenarios[[name]], Club = "outside",
                                stringsAsFactors = FALSE), db_df)   # V20: run 0 is the baseline, no coalition
      ev_db['Iteration'] <- (ev_db['Iteration']-1)
      gdp_db <- data.frame()                                                                                   # V20: real GDP
      for (file in list.files(path = scenario_path, pattern = "GDP_round_\\d+\\.txt", full.names = TRUE)) {
        gdp_raw <- read.table(file, header = FALSE, sep = " ", col.names = c("Country", "GDP_pct"))
        gdp_raw$Iteration <- as.integer(gsub(".*GDP_round_([0-9]+)\\.txt$", "\\1", file)); gdp_raw$Scenario <- scenarios[[name]]
        gdp_db <- bind_rows(gdp_db, gdp_raw)
      }
      if (nrow(gdp_db) > 0) ev_db <- left_join(ev_db, gdp_db, by = c('Country' = 'Country', 'Iteration' = 'Iteration', 'Scenario' = 'Scenario')) else ev_db$GDP_pct <- NA_real_
    
      ev_db <- inner_join( luc_db, ev_db, by=c('Country'='Country', 'Iteration'='Iteration', 'Scenario'='Scenario'))
    
      db <- inner_join(db_df, ev_db, by=c('Country'='Country', 'Iteration'='Iteration', 'Scenario'='Scenario'))
    
      df_producer <- data.frame(Country = list_producer_countries, tag = "producer")
      df_non_producer <- data.frame(Country = list_non_producer_countries, tag = "non-producer")
    
      # Combine the two data frames
      df_combined <- rbind(df_producer, df_non_producer)
      #tag tehm
      db_tagged <- merge(db, df_combined, by = "Country", all.x = TRUE)
      db_tagged['parameter'] <- p
      db_tagged['Approach'] <- approach
      
      condition <- db_tagged$Iteration == 0
      condition_2 <- db_tagged$Country == 'eu27'
      # # Use a temporary variable to swap values
      temp <- db_tagged$EV[condition]
      db_tagged$EV[condition] <- db_tagged$EV_previous_round[condition]
      db_tagged$EV_previous_round[condition] <- temp
      db_tagged$Club[condition_2] <- 'inside'
      
      
      #save them
      #save_path <- file.path(parent_folder, "4_DB",approach,p,"Database_GTAPAEZ_results_2024.xlsx")
      #write_xlsx(db_tagged, save_path)
      
      tableau_db <- bind_rows(tableau_db,db_tagged)
      
      iter_db <- NULL
      reset_db <- NULL
      ev_db <- NULL
      file_iter_names <- NULL
      file_reset_names <- NULL
      file_ev_names <- NULL
      db_tagged <- NULL
    }
  }
}

tableau_db_agg <- tableau_db

# 
 tableau_db_agg $Tropical  <- rowSums(tableau_db_agg [, paste0("aez", 1:6)])     # V20: AEZ1-6 are tropical (labels were swapped)
 tableau_db_agg $Temperate <- rowSums(tableau_db_agg [, paste0("aez", 7:12)])
 tableau_db_agg $Boreal    <- rowSums(tableau_db_agg [, paste0("aez", 13:18)])
# 
 tableau_db_agg <- tableau_db_agg[, setdiff(names(tableau_db_agg), paste0("aez", 1:18))]   # V20: by name, not by position
# 
# 
# #save the tableau db
 save_path <- file.path(parent_folder, "4_DB",paste0("Database_GTAPAEZ_all_results_2024_agg_", paste(list_parameter, collapse = "-"), "_", run_tag, ".csv"))   # V15
 write.csv(tableau_db_agg , save_path, row.names = FALSE)

mapping <- list(
  angola = c('AGO'),
  drc = c('COD'),
  argentina = c('ARG'),
  bolivia = c('BOL'),
  brasil = c('BRA'),
  canada = c('CAN'),
  china = c('CHN'),
  colombia = c('COL'),
  eastasia = c('HKG', 'MAC', 'PRK', 'TWN', 'MNG', 'BRN'),
  EFTA = c('ISL', 'NOR', 'CHE'),
  eu27 = c('AUT', 'BEL', 'BGR', 'HRV', 'CYP', 'CZE', 'DNK', 'EST', 'FIN', 
           'FRA', 'DEU', 'GRC', 'HUN', 'IRL', 'ITA', 'LVA', 'LTU', 'LUX', 'MLT', 'NLD', 
           'POL', 'PRT', 'ROU', 'SVK', 'SVN', 'ESP', 'SWE', 'REU', 'GLP', 'MTQ'),
  
  ghana = c('GHA'),
  india = c('IND'),
  indonesia = c('IDN'),
  ivorycoast = c('CIV'),
  japan = c('JPN'),
  korea = c('KOR'),
  latinamer = c('AIA', 'ATG', 'ABW', 'BHS', 'BRB', 'VGB', 'CYM', 'CUB', 'DMA', 
                'DOM', 'GRD', 'HTI', 'JAM', 'MSR', 'PRI', 'KNA', 'LCA', 'VCT', 
                'TTO', 'TCA', 'VIR', 'BLZ', 'CRI', 'SLV', 'GTM', 'HND', 'NIC', 'PAN', 
                'CHL', 'ECU', 'FLK', 'GUF', 'GUY', 'SGS', 'SUR', 'URY'),  
  
  madagascar = c('MDG'),
  malasya = c('MYS'),
  mena = c( 'IRN', 'IRQ', 'ISR', 'JOR',
           'KWT', 'LBN', 'OMN', 'QAT', 'SAU', 'SYR', 'TUR', 'ARE', 'YEM'),
  mexico = c('MEX'),
  mozambique = c('MOZ'),
  myanmar = c('MMR'),
  newzealand = c('NZL'),
  nigeria = c('NGR'),
  oceania = c('AUS', 'FJI', 'NCL', 'PNG', 'SLB', 'VUT', 'GUM', 'KIR', 'MHL', 
              'FSM', 'NRU', 'MNP', 'PLW', 'UMI', 'ASM', 'COK', 'PYF', 'NIU', 'PCN',
              'WSM', 'TKL', 'TON', 'TUV', 'WLF'),
  paraguay = c('PRY'),
  peru = c('PER'),
  restofworld = c('IOT', 'ATF', 'BVT', 'BMU', 'GRL', 'SPM', 'ATA', 'KAZ', 
                  'KGZ', 'TJK', 'TKM', 'UZB', 'ARM', 'AZE', 'GEO', 'BLR', 
                  'MDA', 'UKR', 'GGY', 'JEY', 'FRO', 'IMN', 'ALB', 'AND',
                  'BIH', 'GIB', 'VAT', 'MNE', 'MKD', 'SMR', 'SRB', 'LIE', 'MCO'),
  russia = c('RUS'),
  seasia = c('KHM', 'LAO', 'PHL', 'SGP', 'THA', 'TLS', 'VNM'),
  southasia = c('AFG', 'BGD', 'BTN',  'MDV', 'NPL', 'PAK', 'LKA'),
  nafr = c('DZA', 'EGY','MAR','TUN','LBY','ESH','MRT'),
  wafr = c('BEN', 'BFA','GIN','SEN','TGO','CPV','GMB',  
           'GNB', 'LBR', 'MLI','NER','SHN','SLE'),
  cafr = c('CMR','CAF','TCD', 'COG', 
           'GNQ','GAB','STP','BDI'),
  eafr = c('ETH','KEN','MUS','RWA','UGA','TZA','COM','DJI',
           'ERI','MYT','SYC','SOM','SDN','SSD'),
  safr = c('MWI', 'ZMB', 'ZWE', 'BWA','NAM','ZAF','SWZ', 'LSO'),
  uk = c('GBR'),
  efta = c('NOR','ISL','CHE','LIE'),
  uruguay = c('URY'),
  us = c('USA'),  
  venezuela = c('VEN')
)

#Function to split country groups into separate rows
 split_countries <- function(row) {
   countries <- mapping[[row$Country]]
   data.frame(
     ISO = countries,
     country_group = rep(row$Country, length(countries)),
     Boreal_High1Humidity = rep(row$aez18, length(countries)),
     Boreal_Normal1Humidity = rep(row$aez17, length(countries)),
     Boreal_Low1Humidity = rep(row$aez16, length(countries)),
     Boreal_Moist1Semiarid = rep(row$aez15, length(countries)),
     Boreal_Dry1Semiarid = rep(row$aez14, length(countries)),
     Boreal_Arid1Arid= rep(row$aez13, length(countries)),

     Temperate_High1Humidity = rep(row$aez12, length(countries)),
     Temperate_Normal1Humidity = rep(row$aez11, length(countries)),
     Temperate_Low1Humidity = rep(row$aez10, length(countries)),
     Temperate_Moist1Semiarid = rep(row$aez9, length(countries)),
     Temperate_Dry1Semiarid = rep(row$aez8, length(countries)),
     Temperate_Arid1Arid= rep(row$aez7, length(countries)),

     Tropical_High1Humidity = rep(row$aez6, length(countries)),
     Tropical_Normal1Humidity = rep(row$aez5, length(countries)),
     Tropical_Low1Humidity = rep(row$aez4, length(countries)),
     Tropical_Moist1Semiarid = rep(row$aez3, length(countries)),
     Tropical_Dry1Semiarid = rep(row$aez2, length(countries)),
     Tropical_Arid1Arid= rep(row$aez1, length(countries)),

     Approach = rep(row$Approach, length(countries)),
     Iteration = rep(row$Iteration, length(countries)),
     Scenario = rep(row$Scenario, length(countries)),
     Club = rep(row$Club, length(countries)),
     EV_previous_round = rep(row$EV_previous_round, length(countries)),
     EV = rep(row$EV, length(countries)),
     GDP_pct = rep(row$GDP_pct, length(countries)),   # V20
     tag = rep(row$tag, length(countries)),
     parameter = rep(row$parameter, length(countries))
   )
 }

 # Apply the function to each row and concatenate the results
 split_df <- do.call(rbind, lapply(1:nrow(tableau_db), function(i) split_countries(tableau_db[i, ])))

 split_df <- split_df %>%
   rename(Country = country_group)

 split_df  <- split_df %>%
   pivot_longer(
     cols = starts_with("Boreal_") | starts_with("Temperate_") | starts_with("Tropical_"),
     names_to = c("Climate_Type", "Humidity_Level"),
     names_sep = "_",
     values_to = "Value"
   )

save_path <- file.path(parent_folder, "4_DB",paste0("Database_GTAPAEZ_all_results_2024_", paste(list_parameter, collapse = "-"), "_", run_tag, ".csv"))   # V15
write.csv(split_df , save_path, row.names = FALSE)
