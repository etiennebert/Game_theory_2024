"""The 4 Oct 2026 edits of the SI on the V32 runs: sections 6.1, 6.3-6.5 re-footed, Fig. S7 and Fig. S9 redrawn, section 7 rewritten
(Table S9 every run, Figs S10-S11 membership and welfare by round, Table S10 the one-deviation tests, Table S11 the welfare decomposition,
Table S12 Brazil's commodities, the suitability check restated). Writes ops_v32.json (redline.py), anchors_v32.json (accept_in_targets.py)
and images_v32.json (insert_images.py). Markup: *italic*  ^sup^  ~sub~  \\$ literal dollar."""
import json, os
AP = "’"; MN = "−"; X = "×"
FIGS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "figs")
ops = []; anchors = []; images = []
def rep(anchor, new, mode="diff"): ops.append({"op": "replace", "anchor": anchor, "new": new, "mode": mode}); anchors.append(anchor)
def ins_after(anchor, paras): ops.append({"op": "insert_after", "anchor": anchor, "paragraphs": paras})
def table_after(anchor, md_path): ops.append({"op": "insert_table_after", "anchor": anchor, "markdown": open(md_path).read().strip(), "style": "TableGrid"})
def body(t): return {"style": "body", "text": t}
def sub(t): return {"style": "subheading", "text": t}
def cap(t): return {"style": "caption", "text": t}
US = "US\\$"

# ---------------- 6.1: the surcharge at the lowest working charge
rep("Shocks are written for every bilateral flow with positive base imports",
    "where *t*^0^~c,s,d~ is the base tariff of the database (the ratio of the value of imports at domestic market prices, VMSB, to their CIF value, minus "
    "one); the adjustment matters where existing duties are high, for instance the EU" + AP + "s 32% most-favoured-nation tariff on beef, 23% on sugar and "
    "21% on paddy rice. The rate is origin- and product-specific but the same in every member, since the footprint is a property of the origin" + AP + "s "
    "production. Shocks are written for every bilateral flow with positive base imports and an AVE of at least 0.01% (643 origin–commodity rates and "
    "26,363 bilateral shocks at " + US + "100 tCO~2~^" + MN + "1^, 405 and 16,605 at " + US + "400 ha^" + MN + "1^; files *tms_f_shocks_bilateral_<scenario>.csv*). "
    "At " + US + "400 ha^" + MN + "1^ the surcharge is 1.5% on Brazilian live cattle, 0.8% on Brazilian beef, 0.14% on Brazilian soybeans, 0.1% on Indonesian "
    "palm oil and 0.9% on Ivorian cocoa and coffee; at " + US + "100 tCO~2~^" + MN + "1^ it is 198%, 104%, 11%, 22% and 0%, respectively (Ivorian cocoa has net "
    "negative emissions). The runs of the paper use the table built at " + US + "10,000 ha^" + MN + "1^, scaled linearly to the price per hectare of the "
    "scenario; at " + US + "4,000 ha^" + MN + "1^ the surcharge is 8.1% on Brazilian beef, 14.8% on live cattle, 1.4% on soybeans, 0.9% on Indonesian palm oil "
    "and 9.4% on Ivorian cocoa and coffee, and at " + US + "3,500 ha^" + MN + "1^, the lowest surcharge at which the club forms from the EU alone, 7.1%, 13.0%, "
    "1.2%, 0.8% and 8.2%.")

# ---------------- 6.3: the seeds, the runs
rep("The EU27 is the permanent member and initiator.",
    "The EU27 is the permanent member and initiator. The seed coalition is the EU alone, the EU with China, the EU with the four founding Mercosur countries "
    "(Brazil, Argentina, Paraguay and Uruguay), or the EU, Mercosur and China; as a check, Bolivia is added to the Mercosur seed.")
rep("Four starting coalitions are run",
    "Four starting coalitions are run: the EU alone, in which the club has to form by itself; the EU with China; the EU with the four founding Mercosur "
    "countries (Brazil, Argentina, Paraguay and Uruguay), representing an agreement built on the EU–Mercosur trade agreement; and the EU, Mercosur and "
    "China; as a check, Bolivia is added to the Mercosur seed. The seed members apply the rules from the first round, and the dynamics then run unchanged. "
    "The EU-alone seed is run at every charge of the searches of Section 6.4, the EU + China seed at the charges of its own search, and the Mercosur seeds "
    "with no charge; Table S9 (Section 7.1) lists every run.")

# ---------------- 6.4: the searches, the stability test, the supply responses
rep("Because joining is triggered by the charge and sustained by the payoff of membership",
    "Because joining is triggered by the charge and sustained by the payoff of membership, whether the club forms from a given seed depends on the level of "
    "the instrument. Starting from the EU alone, we search for the lowest price per hectare (footprint surcharge alone) and the lowest penalty (club penalty "
    "alone) at which Brazil, the pivotal producer, ends inside the final coalition, in steps of " + US + "500 ha^" + MN + "1^ and 0.25 percentage points; each "
    "run is a complete membership process (three to ten rounds, one solve each; one run reached the cap of 15 rounds). The same search is run from the EU + "
    "China seed, for the penalty at a fixed surcharge (the exchange rate between the instruments), with Brazil, the United States, the United States and "
    "China together, or Indonesia locked out (treated as a non-member at every decision), and at half and double the switching-cost share φ (script "
    "*Run_V32_all.R*, which runs every simulation of the paper). The 37 runs are listed in Table S9, and the brackets they give are in Table 2 of the main "
    "text and Extended Data Fig. 1: from the EU alone the club forms at 1.25% (not at 1.0%) and at " + US + "3,500 ha^" + MN + "1^, the first-round loss of "
    "Brazil being the decision that sets both thresholds.")
rep("Stability of the final coalition.",
    "*Stability of the final coalition.* The membership process stops at a rest point of the decision rule, at which no region moves; whether that coalition "
    "*S* is also self-enforcing is tested with a one-deviation check^34^: starting from *S*, each member (the EU excepted) is removed alone and each "
    "non-member of the test scope added alone, one solve per test, everything else unchanged. The scope holds the nineteen regions that can matter for the "
    "forest or the charge: Brazil, Argentina, Paraguay, Uruguay, Bolivia, Colombia, Venezuela, Ivory Coast, Ghana, Nigeria, DRC, Angola, Central Africa, "
    "Indonesia, Malaysia, Southeast Asia, India, China and the United States. *S* is internally stable if no member" + AP + "s welfare is higher outside than "
    "inside, and externally stable if no non-member" + AP + "s welfare is higher inside than outside; counting the switching cost as the cost of moving gives "
    "the regions that would still move. For members that would gain by leaving, the check reports the transfer that would retain them and, for comparison, "
    "the duty raised by the charge on each member" + AP + "s imports from non-members (from the updated database of the final solve); the files "
    "*Stability_<run>.txt* list, for every region tested, its welfare in *S* and after its deviation, the gain from moving and its switching cost. Four "
    "coalitions are tested: the club of the EU alone at 1.5%, the coalition of the EU alone at " + US + "4,000 ha^" + MN + "1^, the club of the EU and China "
    "at 1.12% and the EU–Mercosur club with no charge (Table S10, Section 7.3; Fig. 4c of the main text).")
rep("Coalition formation is driven by each region",
    "Coalition formation is driven by each region" + AP + "s comparison of its welfare with its own experience of the other status, not by strategic tariff "
    "optimization. A region moves only when the other status was better by more than its switching cost (Table S7) or, for a member, under the bounded-loss "
    "safeguard. These thresholds are intentionally small in macroeconomic terms, but they prevent membership decisions from being triggered by negligible "
    "welfare fluctuations and provide a reduced form representation of the political and distributional constraints emphasized in political economy models "
    "of trade agreements. Consistent with this design, the sectoral supply adjustments remain modest: Brazil" + AP + "s output of land-based goods changes by "
    "0.4–1.3% at the club equilibrium (wheat by 2.7%; Fig. 5 of the main text, Table S12), and across the 1,470 region–sector pairs of the model 1,260 move "
    "by less than 1% and every sector above " + US + "50 billion of output by less than 1%; the largest responses are in small land-based sectors, the "
    "forestry and wood products of the members whose held forest returns to timber production (Fig. S9).")
# Fig. S9: the old figure and caption out, the new caption in (the picture is inserted before it by insert_images.py)
ops.append({"op": "delete", "anchor": "Fig. S9 | Economy‑wide sectoral supply responses in GTAP‑AEZ", "preceding_figures": 1})
S9CAP = ("**Fig. S9 | Economy-wide sectoral supply responses at the club equilibrium (EU alone, penalty 1.5%).** Percentage change in sectoral output "
         "relative to the EUDR world (vertical axis) against the value of the sector" + AP + "s output in the base data (horizontal axis, million US dollars, "
         "log scale), one point per region–sector pair, for the twelve producer regions of the game script (**a**; four of them, Angola, Bolivia, Colombia "
         "and DRC, are outside the club at convergence) and the thirty other regions (**b**); the seventeen charged commodities and forestry in green, the "
         "other sectors in grey. Twelve points lie beyond ±10%: the forestry and wood products of Malaysia, Ivory Coast, Ghana, Peru, Paraguay and Nigeria (+11 to "
         "+48%), where the forest the member holds returns to timber production, and Paraguay" + AP + "s wool (" + MN + "12%). Every "
         "sector above US\\$50 billion of output moves by less than 1%.")
ins_after("Coalition formation is driven by each region", [cap(S9CAP)])
images.append({"before_anchor": "Fig. S9 | Economy-wide sectoral supply responses at the club equilibrium", "png": os.path.join(FIGS, "Fig_S9_supply_responses.png"), "width_in": 6.3})

# ---------------- Fig. S7: the baseline figure redrawn on the two stages
ops.append({"op": "delete", "anchor": "Fig. S7 | Baseline results of net national / zone forest area change", "preceding_figures": 1})
S7CAP = ("**Fig. S7 | Forest cover change in the two stages of the baseline, by region and climate zone.** **a**, Stage A: the business-as-usual clearing "
         "imposed on the 2019 data (22.2 Mha in the 174 cells of Table S6) together with the response of the forest elsewhere, which expands as agricultural "
         "prices fall (+2.7 Mha, almost all temperate and boreal forest, in Canada, the EU and Russia): a net change of " + MN + "19.5 Mha over five years. "
         "**b**, Stage B: the EUDR applied to the business-as-usual world, with forest cover endogenous everywhere: +12.6 kha of tropical forest (Brazil "
         "+10.8) against 26 kha of temperate and boreal forest lost in the EU (" + MN + "19) and Canada (" + MN + "10), a net " + MN + "13.6 kha. Regions "
         "with changes below 5 kha in both stages are omitted. Abbreviations: DRC, Democratic Republic of the Congo; EFTA, European Free Trade Association. "
         "Source: *NATDEF_A.sl4* and *NATDEF_B.sl4* (*del_luc*, Forestland).")
ins_after("We designed a counterfactual analysis in which the baseline is the current policy environment", [cap(S7CAP)])
images.append({"before_anchor": "Fig. S7 | Forest cover change in the two stages of the baseline", "png": os.path.join(FIGS, "Fig_S7_baseline_forest.png"), "width_in": 6.3})

# ---------------- 6.5
rep("The outputs are HAR",
    "The outputs are HAR‐formatted results and text-formatted results processed in R with the HARr package. Each round takes one accurate solve of five to "
    "ten minutes, and a membership process three to ten rounds (Table S9).")
rep("Finally, the results of every run",
    "Finally, the results of every run (the csv of EV, real GDP and forest change by climate zone, region and round; the welfare decomposition, leakage and "
    "commitment files of each round; the stability tables) are read by the Python scripts of the figure pipeline (*Figures_v2/scripts_v32*: "
    "*extract_all.py*, *tables.py*, the figure scripts and *si_figures.py*, run by *make_all.py*), which build every figure and table of the paper and of "
    "this section, and their source data; *si_v32_extract.R* reads the solution files of the headline runs for Tables S11 and S12 and Figs S7 and S9.")

# ---------------- Section 7: out with the old scenarios, in with the V32 results
ops.append({"op": "delete_range", "from_anchor": "7.1 Iterative process", "to_anchor": "Figure S18 illustrates the results from this procedure"})
P = []
P.append(sub("7.1 The runs of the paper"))
P.append(body("Table S9 lists the 37 membership processes behind the results: the searches from the EU alone at a switching cost of 0.1% of trade (the "
    "penalty from 0.75% to 5%, the surcharge from 3,500 to 6,000 " + US + " ha^" + MN + "1^, and five combinations of the two), the same searches at 0.05% "
    "and 0.2% of trade, the eight lock-outs, and the seeds with China, with Mercosur, and with Mercosur and China or Bolivia. Every run converged within ten "
    "rounds except the penalty of 0.5% at a switching cost of 0.05% of trade, which reached the cap of 15 rounds with 33 members and Brazil inside without "
    "settling; it is reported as unsettled and is neither a failing nor a working run of the brackets. For each run the SI files contain the result csv "
    "(*Database_GTAPAEZ_all_results_2024_agg_forest_<run>.csv*: EV, real GDP, forest cover by climate zone and membership, by region and round), the "
    "welfare decomposition, leakage and commitment files of every round (*Welfare_decomp_round_<i>.txt*, *Forest_leakage_<i>.txt*, "
    "*Forest_commitment_<i>.txt*), the CMF file of every solve and the run summary; the figure pipeline reads them into *all_data_V32.json*, from which "
    "every figure and table of the paper is drawn (*Figures_v2/scripts_v32*, Section 6.5). The thresholds bracketed by these runs are in Table 2 of the "
    "main text, the lock-outs in Table 3 and Fig. 3e, and the switching-cost sensitivity in Extended Data Fig. 1."))
P.append(cap("**Table S9. Every membership process of the paper.** Seed, region locked out, switching cost (share of trade), charge, rounds to convergence, "
    "outcome, members at convergence and whether Brazil is among them, tropical forest kept by the members (all zones in brackets) and lost by the "
    "non-members (the leakage) relative to the EUDR world over five years, and world welfare on the decision measure (GTAP" + AP + "s gross equivalent "
    "variation in brackets), million US dollars per year. A negative loss outside means that the non-members cleared less than in the EUDR world. "
    "Abbreviations: DRC, Democratic Republic of the Congo; US, United States."))
P.append(sub("7.2 Membership and welfare by round"))
P.append(body("Fig. S10 shows the membership of every run round by round and Fig. S11 the welfare of the members and of the non-members. The cascade has "
    "the same shape in every run in which the club forms: the producers whose first-round loss exceeds their switching cost join in the second round, the "
    "importers whose import bills the producers" + AP + " restraint has raised join in the third, the smaller forest regions in the fourth, and the importers "
    "without a footprint reconsider in the fifth, leaving the surcharge coalitions and staying in the penalty clubs, which charge their own exports; "
    "convergence comes two to three rounds later. Under the penalty the welfare of the members as a group falls as the club grows, because the gains of the "
    "producers are outweighed by the losses of the importers that join; under the surcharge the importers mostly stay out, the members" + AP + " welfare "
    "settles near zero and the non-members" + AP + " falls (Fig. S11). Where the club does not form, the process stops within three to five rounds with a "
    "handful of members and no more than 3.8 Mha of forest."))
P.append(cap("**Fig. S10 | Members of the Forest Club after each round, every run.** Bars: tropical forest regions (at least 0.1 Mha of business-as-usual "
    "clearing; dark) and other regions (light) inside the club after each round; round 0 is the EUDR world with the seed alone. The label gives the "
    "members at convergence and the tropical forest they keep, in orange when the club does not form (Brazil outside at convergence, or the 15-round cap "
    "reached without convergence)."))
P.append(cap("**Fig. S11 | Welfare of members and non-members after each round, every run.** Sum of the equivalent variation relative to the EUDR world on "
    "the decision measure (billion US dollars per year) over the members (green), over the non-members (orange) and the world (dashed), with the "
    "membership of each round."))
P.append(sub("7.3 One-deviation tests of the final coalitions"))
P.append(body("Table S10 summarizes the one-deviation tests of the four coalitions tested (Section 6.4; Fig. 4c of the main text). The club of the EU alone "
    "at 1.5% is stable in the strong sense: no member gains by leaving alone and no outsider by joining alone, whether or not the switching cost is "
    "counted. The coalition of the EU alone at " + US + "4,000 ha^" + MN + "1^ is held together by the switching cost at its margins: without it Madagascar, "
    "the rest of East Asia and Mozambique would leave and Uruguay and China would join; with it only Madagascar moves, by 0.7 million US dollars per "
    "year, and a transfer of 1 million against 201 million of duty retains it; China" + AP + "s gain from joining, 110 million, is half its switching cost. "
    "The club of the EU and China at 1.12%, which ends on the same 35 members as the EU alone at 1.5%, is stable once the cost is counted (Myanmar would "
    "leave without it). The EU–Mercosur club with no charge is internally stable once the cost is counted but not externally: India, Ivory Coast and "
    "Malaysia would each gain by joining alone, net of their switching costs, because forgoing their clearing raises the prices of the crops it would have "
    "grown; the membership dynamics do not find them, since a region that has never been a member moves only after a loss larger than its switching cost "
    "(Section 6.3), and none of the three loses that much in any round. Japan, outside the club at 1.5%, is not in the test scope."))
P.append(cap("**Table S10. One-deviation tests of the final coalitions.** For each coalition tested: the members that would gain by leaving alone and the "
    "non-members of the test scope that would gain by joining alone, before and after their switching cost is counted; the transfer that would retain "
    "the members that gain by leaving (the sum of their gains, million US dollars per year); what the members who prefer the coalition could pay (the sum, "
    "over the members that lose by leaving, of what each would lose); and the duty raised by the charge on the members" + AP + " imports from non-members. "
    "The complete tables are in the files *Stability_<run>.txt*."))
P.append(sub("7.4 Welfare decomposition at the headline equilibria"))
P.append(body("Table S11 decomposes the welfare change of every region at the two headline equilibria with the Huff–Hertel decomposition of the equivalent "
    "variation implemented in GTAP (Methods, Welfare measure): allocative efficiency, which contains the wedge term (the AEZ rows of the endowment-tax "
    "contribution, where the clearing incentives of Stage A sit; the decision measure removes it), technical change (the productivity of the forgone "
    "hectares, reversed in the members), the terms of trade and the investment–savings account. For Brazil four fifths of the gain is its terms of trade "
    "(+850 of +1,048 million US dollars per year in the club); for the EU the cost is its terms of trade (" + MN + "826) net of the ban" + AP + "s iceberg "
    "cost, which the members no longer pay (+152); for the United States the loss comes through the investment–savings account (" + MN + "812), for China "
    "through its terms of trade (" + MN + "978). For the world, GTAP" + AP + "s equivalent variation of " + MN + "349 million is an allocative gain of "
    "+1,824 (of which +2,369 is the wedge term and " + MN + "545 the other tax wedges, among them the charge) against a technical loss of " + MN + "2,223, the "
    "productivity of the hectares the members forgo; net of the wedge term the decision measure is " + MN + "2,718 million per year."))
P.append(cap("**Table S11. Decomposition of the welfare change at the headline equilibria, every region** (million US dollars per year, relative to the EUDR "
    "world). For the club of the EU alone at 1.5%: GTAP" + AP + "s equivalent variation, the forest-land wedge term, the decision measure (their "
    "difference), and the contributions of allocative efficiency (which contains the wedge term), technical change, the terms of trade and the "
    "investment–savings account; for the coalition of the EU alone at " + US + "4,000 ha^" + MN + "1^, the decision measure and the terms of trade. "
    "\"(out)\" marks a non-member. Regions in the order of their welfare in the club. Abbreviations: DRC, Democratic Republic of the Congo; EFTA, European "
    "Free Trade Association."))
P.append(sub("7.5 Brazil at the club equilibrium"))
P.append(body("Table S12 gives Brazil" + AP + "s output, exports and export prices by commodity at the two equilibria; Fig. 5 of the main text shows its land "
    "use by zone. Brazil exports 1.5–7.5% less of every land-based good except vegetable oils and processed rice, at prices 0.2–2.1% higher; its terms of "
    "trade improve by 0.37%, its real GDP by 0.015% and its GDP deflator by 0.2%, and the rents of its cropland, pasture and forest rise by 21–23%, "
    "13–14% and 42–109%, the forest rent most in the year-round humid zone (AEZ 6), where 5.3 of its 7.8 Mha of business-as-usual clearing would have "
    "taken place. The world prices of the land-based goods rise by 0.2–1.4% (oilseeds, other crops, sugar crops and paddy rice the most, beef and dairy the least) and the world price of "
    "forestry falls by 4%, as the held forest returns to timber production."))
P.append(cap("**Table S12. Brazil" + AP + "s land-based commodities at the two headline equilibria.** Value of output in the 2019 database (million US "
    "dollars) and, relative to the EUDR world, the percentage change in output, in export volume and in the export price at the club of the EU alone at "
    "1.5% and at the coalition of the EU alone at " + US + "4,000 ha^" + MN + "1^ (*qo*, *qxw*, *pxw* of GTAP–AEZ). Land rents at the club equilibrium "
    "(percentage change, zones with cover): cropland +21 to +23% in AEZs 2–6 and 12, pasture +13 to +14%, forest +42% (AEZs 4, 5 and 12) to +109% (AEZ 6)."))
P.append(sub("7.6 Agronomic suitability of the land that changes use"))
P.append(body("At the club equilibrium the members forgo the expansion of their cropland and pasture rather than expanding it (Brazil: 6.7 Mha less pasture "
    "and 1.1 Mha less cropland than in the EUDR world, Fig. 5 of the main text), so the question of whether newly cultivated land is agronomically "
    "suitable now concerns two areas: the 0.28 Mha of cropland that shifts into the semi-arid and sub-humid zones of Brazil (AEZs 2–4: +22, +75 and +187 "
    "kha, Fig. 5b), and the 0.6 Mha of forest that the non-members convert (the leakage, Fig. 2d of the main text; by region and AEZ in "
    "*Forest_leakage_<i>.txt*). The cropland that shifts within Brazil goes to zones that already grow the same crops (soybeans, maize and sugar cane in "
    "the sub-humid Cerrado), and the converted forest of the non-members lies in the cells where they clear on their business-as-usual path. The check "
    "of these areas against the crop-suitability layers of Zabel (2022)^28^, which rank suitability from 0 to 100 for 23 crops under rainfed conditions "
    "over 1980–2019, follows the procedure of the first submission: the suitability scores are aggregated by crop and AEZ and compared with the zones "
    "that gain cropland."))
ins_after("Additional results from the counterfactual analysis", P)
table_after("Table S9. Every membership process of the paper.", os.path.join(FIGS, "Table_S9_runs.md"))
table_after("Table S10. One-deviation tests of the final coalitions.", os.path.join(FIGS, "Table_S10_stability.md"))
table_after("Table S11. Decomposition of the welfare change at the headline equilibria", os.path.join(FIGS, "Table_S11_welfare_decomposition.md"))
table_after("Table S12. Brazil", os.path.join(FIGS, "Table_S12_brazil.md").replace(".md", "_table.md"))
images.append({"before_anchor": "Fig. S10 | Members of the Forest Club after each round, every run.", "png": os.path.join(FIGS, "Fig_S10_members_by_round.png"), "width_in": 6.3})
images.append({"before_anchor": "Fig. S11 | Welfare of members and non-members after each round, every run.", "png": os.path.join(FIGS, "Fig_S11_welfare_by_round.png"), "width_in": 6.3})
ops.append({"op": "comment", "anchor": "At the club equilibrium the members forgo the expansion of their cropland and pasture",
            "text": "Etienne: the Zabel check of the first submission was on the old scenario (2.13 Mha of new cropland, Fig. S18). The areas to check on the V32 "
                    "equilibrium are Brazil AEZ 2-4 (+284 kha of cropland: +22, +75, +187 kha) and the non-members' converted forest by AEZ (Forest_leakage_7.txt "
                    "of the 1.5 % run, 0.59 Mha). I did not have the Zabel layers here, so the last sentence describes the procedure, not a result; either run it "
                    "or cut the subsection."})

here = os.path.dirname(os.path.abspath(__file__))
json.dump(ops, open(os.path.join(here, "ops_v32.json"), "w"), ensure_ascii=False, indent=0)
json.dump(anchors, open(os.path.join(here, "anchors_v32.json"), "w"), ensure_ascii=False, indent=0)
json.dump(images, open(os.path.join(here, "images_v32.json"), "w"), ensure_ascii=False, indent=0)
print(len(ops), "ops,", len(anchors), "target paragraphs,", len(images), "images")
