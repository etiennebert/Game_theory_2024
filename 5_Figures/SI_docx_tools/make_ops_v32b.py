"""The 7 Oct 2026 edits of the SI on the completed V32 runs (the surcharge bracket closed at 1,500 / 2,000 USD/ha, the 0.2 %-of-trade
bracket at 8,000 / 9,000, the EU + China penalty bracket at 0.75 / 0.87, the Japan and coalition-outsider stability tests):
sections 6.1, 6.4, 6.5, 7.1, 7.2, 7.3 re-footed, Table S9 (8 new rows), Table S10 (3 cells), Figs S10 and S11 redrawn.
Writes ops_v32b.json (redline.py), anchors_v32b.json (accept_prior2.py), images_v32b.json (insert_images.py) and tables_v32b.json
(table_edit.py). Markup: *italic*  ^sup^  ~sub~  \\$ literal dollar."""
import json, os
AP = "’"; MN = "−"; X = "×"; EN = "–"
SIO = os.environ.get("FOREST_CLUB_SI_OUTPUT", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "SI_Output"))  # the regenerated SI figures and tables
ops = []; anchors = []; images = []; tables = []
def rep(anchor, new, mode="diff"): ops.append({"op": "replace", "anchor": anchor, "new": new, "mode": mode}); anchors.append(anchor)
US = "US\\$"
HA = " ha^" + MN + "1^"

# ---------------- 6.1: the ad valorem equivalents at the lowest working surcharge (2,000 USD/ha), and the 4,000 values made consistent
# (the 4 Oct text quoted the EU-specific shock for live cattle and palm oil, 14.8 % and 0.9 %, next to the origin AVE for the other three)
rep("Shocks are written for every bilateral flow with positive base imports",
    "where *t*^0^~c,s,d~ is the base tariff of the database (the ratio of the value of imports at domestic market prices, VMSB, to their CIF value, minus "
    "one); the adjustment matters where existing duties are high, for instance the EU" + AP + "s 32% most-favoured-nation tariff on beef, 23% on sugar and "
    "21% on paddy rice. The rate is origin- and product-specific but the same in every member, since the footprint is a property of the origin" + AP + "s "
    "production. Shocks are written for every bilateral flow with positive base imports and an AVE of at least 0.01% (643 origin–commodity rates and "
    "26,363 bilateral shocks at " + US + "100 tCO~2~^" + MN + "1^, 405 and 16,605 at " + US + "400" + HA + "; files *tms_f_shocks_bilateral_<scenario>.csv*). "
    "At " + US + "400" + HA + " the surcharge is 1.5% on Brazilian live cattle, 0.8% on Brazilian beef, 0.14% on Brazilian soybeans, 0.1% on Indonesian "
    "palm oil and 0.9% on Ivorian cocoa and coffee; at " + US + "100 tCO~2~^" + MN + "1^ it is 198%, 104%, 11%, 22% and 0%, respectively (Ivorian cocoa has net "
    "negative emissions). The runs of the paper use the table built at " + US + "10,000" + HA + ", scaled linearly to the price per hectare of the "
    "scenario; at " + US + "4,000" + HA + " the surcharge is 8.1% on Brazilian beef, 15.4% on live cattle, 1.4% on soybeans, 1.0% on Indonesian palm oil "
    "and 9.4% on Ivorian cocoa and coffee, and at " + US + "2,000" + HA + ", the lowest surcharge at which the coalition forms from the EU alone "
    "(Section 6.4), 4.1%, 7.7%, 0.7%, 0.5% and 4.7%.")

# ---------------- 6.4: the searches (the brackets closed; how the two thresholds are set), the stability scope extended
rep("Because joining is triggered by the charge and sustained by the payoff of membership",
    "Because joining is triggered by the charge and sustained by the payoff of membership, whether the club forms from a given seed depends on the level of "
    "the instrument. Starting from the EU alone, we search for the lowest price per hectare (footprint surcharge alone) and the lowest penalty (club penalty "
    "alone) at which Brazil, the pivotal producer, ends inside the final coalition, in steps of " + US + "500" + HA + " and 0.25 percentage points; each "
    "run is a complete membership process (three to ten rounds, one solve each; one run reached the cap of 15 rounds). The same search is run from the EU + "
    "China seed, for the penalty at a fixed surcharge (the exchange rate between the instruments), with Brazil, the United States, the United States and "
    "China together, or Indonesia locked out (treated as a non-member at every decision), and at half and double the switching-cost share φ (script "
    "*Run_V32_all.R*, which runs every simulation of the paper). The 45 runs are listed in Table S9, and the brackets they give are in Table 2 of the main "
    "text and Extended Data Fig. 1: from the EU alone the club forms at 1.25% (not at 1.0%) and the coalition at " + US + "2,000" + HA + " (not at 1,500). "
    "The two thresholds are set differently. Under the penalty the threshold is Brazil" + AP + "s own decision after the first round: the round in which the "
    "EU alone charges costs it 86 million US dollars per year at 1.25% and 69 million at 1.0%, against a switching cost of 73 million, so that it joins in "
    "the second round in the first case and never in the second. Under the surcharge Brazil" + AP + "s first-round loss is below its switching cost from "
    "3,000 " + US + HA + " down (64, 55 and 45 million at 3,000, 2,500 and 2,000), yet the coalition forms: the seven smaller producers whose loss "
    "exceeds their cost join in the second round, the importers whose import bills their restraint raises join in the third, and their charge on Brazilian "
    "beef and soybeans, added to the EU" + AP + "s, costs Brazil 0.19–0.23 billion in that round, more than its switching cost, so that it joins in the "
    "fourth. At 1,500 " + US + HA + " the chain breaks at its first link: Colombia and the DRC no longer lose more than their switching costs in the "
    "first round, only five producers join in the second, only Japan, Korea, the United Kingdom and EFTA follow in the third, their charge costs Brazil "
    "5 million, and the coalition stalls at ten members and 4.1 Mha (Table S9, Fig. S10).")
rep("Stability of the final coalition.",
    "*Stability of the final coalition.* The membership process stops at a rest point of the decision rule, at which no region moves; whether that coalition "
    "*S* is also self-enforcing is tested with a one-deviation check^34^: starting from *S*, each member (the EU excepted) is removed alone and each "
    "non-member of the test scope added alone, one solve per test, everything else unchanged. The scope holds the nineteen regions that can matter for the "
    "forest or the charge: Brazil, Argentina, Paraguay, Uruguay, Bolivia, Colombia, Venezuela, Ivory Coast, Ghana, Nigeria, DRC, Angola, Central Africa, "
    "Indonesia, Malaysia, Southeast Asia, India, China and the United States; for the two coalitions of the EU alone the test was extended to every outsider "
    "the scope does not cover (Japan at 1.5%; at " + US + "4,000" + HA + " Japan, Korea, the United Kingdom, Russia, the Middle East, North Africa, Southern "
    "and Western Africa, South Asia, Oceania, Myanmar and the rest of the world), so that no region is left untested there (the supplementary runs "
    "*SminclubYjapan* and *SmincoalitionXouts*). *S* is internally stable if no member" + AP + "s welfare is higher outside than "
    "inside, and externally stable if no non-member" + AP + "s welfare is higher inside than outside; counting the switching cost as the cost of moving gives "
    "the regions that would still move. For members that would gain by leaving, the check reports the transfer that would retain them and, for comparison, "
    "the duty raised by the charge on each member" + AP + "s imports from non-members (from the updated database of the final solve); the files "
    "*Stability_<run>.txt* list, for every region tested, its welfare in *S* and after its deviation, the gain from moving and its switching cost. Four "
    "coalitions are tested: the club of the EU alone at 1.5%, the coalition of the EU alone at " + US + "4,000" + HA + ", the club of the EU and China "
    "at 1.12% and the EU–Mercosur club with no charge (Table S10, Section 7.3; Fig. 4c of the main text).")

# ---------------- 6.5: the figure pipeline in its October layout
rep("Finally, the results of every run",
    "Finally, the results of every run (the csv of EV, real GDP and forest change by climate zone, region and round; the welfare decomposition, leakage and "
    "commitment files of each round; the stability tables) are read by the Python scripts of the figure pipeline (folder *5_Figures*: "
    "*common/extract_all.py* extracts the runs into *data/all_data_V32.json*, and one script per figure, in *Fig_2_script* to *ExtData_Fig_2_script*, "
    "*Tables_script* and *SI_script*, writes its figure, table and source data into the matching *_Output* folder; *make_all.py* runs them in order), "
    "which build every figure and table of the paper and of this section; *SI_script/si_v32_extract.R* reads the solution files of the headline runs for "
    "Tables S11 and S12 and Figs S7 and S9.")

# ---------------- 7.1: the runs
rep("Table S9 lists the 37 membership processes behind the results",
    "Table S9 lists the 45 membership processes behind the results: the searches from the EU alone at a switching cost of 0.1% of trade (the "
    "penalty from 0.75% to 5%, the surcharge from 1,500 to 6,000 " + US + HA + ", and five combinations of the two), the same searches at 0.05% "
    "and 0.2% of trade, the eight lock-outs, and the seeds with China, with Mercosur, and with Mercosur and China or Bolivia; the six one-deviation tests "
    "of Section 7.3 are single solves of the final coalitions and are not listed. Every run converged within ten rounds except the penalty of 0.5% at a "
    "switching cost of 0.05% of trade, which reached the cap of 15 rounds with 33 members and Brazil inside without settling; it is reported as unsettled "
    "and is neither a failing nor a working run of the brackets. For each run the SI files contain the result csv "
    "(*Database_GTAPAEZ_all_results_2024_agg_forest_<run>.csv*: EV, real GDP, forest cover by climate zone and membership, by region and round), the "
    "welfare decomposition, leakage and commitment files of every round (*Welfare_decomp_round_<i>.txt*, *Forest_leakage_<i>.txt*, "
    "*Forest_commitment_<i>.txt*), the CMF file of every solve and the run summary; the figure pipeline reads them into *all_data_V32.json*, from which "
    "every figure and table of the paper is drawn (*5_Figures*, Section 6.5). The thresholds bracketed by these runs are in Table 2 of the "
    "main text, the lock-outs in Table 3 and Fig. 3e, and the switching-cost sensitivity in Extended Data Fig. 1.")

# ---------------- 7.2: the cascade and the failing runs
rep("Fig. S10 shows the membership of every run round by round",
    "Fig. S10 shows the membership of every run round by round and Fig. S11 the welfare of the members and of the non-members. The cascade has "
    "the same shape in every run in which the club forms: the producers whose first-round loss exceeds their switching cost join in the second round, the "
    "importers whose import bills the producers" + AP + " restraint has raised join in the third, the remaining forest regions in the fourth (Brazil itself "
    "from 2,000 to 3,000 " + US + HA + " of surcharge, Section 6.4), and the importers without a footprint reconsider in the fifth, leaving the "
    "surcharge coalitions and staying in the penalty clubs, which charge their own exports; convergence comes two to three rounds later. Under the penalty "
    "the welfare of the members as a group falls as the club grows, because the gains of the producers are outweighed by the losses of the importers that "
    "join; under the surcharge the importers mostly stay out, the members" + AP + " welfare settles near zero and the non-members" + AP + " falls (Fig. S11). "
    "Where the club does not form, the process stops within three to seven rounds with four to thirteen members and no more than 4.1 Mha of tropical forest.")
# Figs S10 and S11 redrawn with the eight new runs: the old pictures out, the new ones in before the (unchanged) captions
ops.append({"op": "delete_figures_before", "anchor": "Fig. S10 | Members of the Forest Club after each round, every run.", "count": 1})
ops.append({"op": "delete_figures_before", "anchor": "Fig. S11 | Welfare of members and non-members after each round, every run.", "count": 1})
images.append({"before_anchor": "Fig. S10 | Members of the Forest Club after each round, every run.", "png": os.path.join(SIO, "Fig_S10_members_by_round.png"), "width_in": 6.3})
images.append({"before_anchor": "Fig. S11 | Welfare of members and non-members after each round, every run.", "png": os.path.join(SIO, "Fig_S11_welfare_by_round.png"), "width_in": 6.3})

# ---------------- 7.3: the one-deviation tests with Japan and the coalition's outsiders tested
rep("Table S10 summarizes the one-deviation tests of the four coalitions tested",
    "Table S10 summarizes the one-deviation tests of the four coalitions tested (Section 6.4; Fig. 4c of the main text). The club of the EU alone "
    "at 1.5% is stable once the switching cost is counted: no member gains by leaving alone, and the one outsider that would gain by joining alone, Japan, "
    "would gain 35 million US dollars per year, 5 million less than its switching cost (the membership dynamics agree: Japan joins in the third round and "
    "leaves in the fifth). The coalition of the EU alone at " + US + "4,000" + HA + " is held together by the switching cost at its margins: without it "
    "Madagascar, the rest of East Asia and Mozambique would leave and twelve outsiders would join, Uruguay and China among the producers and ten importers "
    "(Japan, Korea, the United Kingdom, Russia, the Middle East, North Africa, Southern Africa, South Asia, Oceania and the rest of the world); with it "
    "Madagascar still leaves, by 0.7 million per year (a transfer of 1 million, against 201 million of duty, retains it), China" + AP + "s gain from "
    "joining, 110 million, is half its switching cost, and one outsider still joins: Southern Africa, whose gain of 31 million is three times its switching "
    "cost of 11 million. The membership dynamics do not find it, since a region that has never been a member moves only after a loss larger than its "
    "switching cost (Section 6.3) and Southern Africa never loses that much in a round. The club of the EU and China at 1.12%, which ends on the same 35 "
    "members as the EU alone at 1.5%, is stable once the cost is counted (Myanmar would leave without it). The EU–Mercosur club with no charge is "
    "internally stable once the cost is counted but not externally: India, Ivory Coast and Malaysia would each gain by joining alone, net of their "
    "switching costs, because forgoing their clearing raises the prices of the crops it would have grown; as for Southern Africa, the dynamics do not find "
    "them, none of the three losing more than its switching cost in any round.")
rep("Table S10. One-deviation tests of the final coalitions.",
    "**Table S10. One-deviation tests of the final coalitions.** For each coalition tested: the members that would gain by leaving alone and the "
    "non-members tested (every outsider for the two coalitions of the EU alone, the test scope of Section 6.4 for the other two) that would gain by joining "
    "alone, before and after their switching cost is counted; the transfer that would retain the members that gain by leaving (the sum of their gains, "
    "million US dollars per year); what the members who prefer the coalition could pay (the sum, over the members that lose by leaving, of what each would "
    "lose); and the duty raised by the charge on the members" + AP + " imports from non-members. The complete tables are in the files *Stability_<run>.txt*.")

# ---------------- Table S9: the eight new rows, Table S10: the three cells that change
new_rows = {
    "1,500 USD/ha": (["EU", EN, "0.1", "3,500 USD/ha"], ["EU", EN, "0.1", "1,500 USD/ha", "7", "10 (out)", "4.11 (4.44)", "0.11 (0.59)", MN + "914 (504)"]),
    "2,000 USD/ha": (["EU", EN, "0.1", "3,500 USD/ha"], ["EU", EN, "0.1", "2,000 USD/ha", "7", "18 (in)", "12.29 (13.16)", "0.54 (1.82)", MN + "1,258 (738)"]),
    "2,500 USD/ha": (["EU", EN, "0.1", "3,500 USD/ha"], ["EU", EN, "0.1", "2,500 USD/ha", "7", "19 (in)", "12.65 (13.61)", "0.45 (1.81)", MN + "1,258 (777)"]),
    "3,000 USD/ha": (["EU", EN, "0.1", "3,500 USD/ha"], ["EU", EN, "0.1", "3,000 USD/ha", "6", "18 (in)", "12.65 (13.61)", "0.45 (1.81)", MN + "1,277 (760)"]),
    "0.75 % at 0.05": (["EU", EN, "0.05", "1 %"], ["EU", EN, "0.05", "0.75 %", "7", "33 (in)", "14.64 (16.49)", "0.54 (0.63)", MN + "2,622 (" + MN + "290)"]),
    "8,000 USD/ha": (["EU", "Brazil", "0.1", "1.5 %"], ["EU", EN, "0.2", "8,000 USD/ha", "5", "9 (out)", "3.79 (4.01)", MN + "0.12 (0.32)", MN + "1,069 (282)"]),
    "9,000 USD/ha": (["EU", "Brazil", "0.1", "1.5 %"], ["EU", EN, "0.2", "9,000 USD/ha", "4", "23 (in)", "13.46 (14.69)", "0.52 (1.95)", MN + "1,841 (208)"]),
    "EU + China 0.75 %": (["EU + China", EN, "0.1", "0.87 %"], ["EU + China", EN, "0.1", "0.75 %", "3", "10 (out)", "1.70 (1.96)", "0.04 (0.05)", MN + "883 (329)"]),
}
# check every new row against the regenerated table on the disk
disk = [[c.strip() for c in l.strip().strip("|").split("|")] for l in open(os.path.join(SIO, "Table_S9_runs.md"), encoding="utf8") if l.startswith("| EU")]
for name, (before, cells) in new_rows.items():
    assert cells in disk, f"row not on the disk: {name} {cells}"
tables.append({"table_after": "Table S9. Every membership process of the paper.",
               "insert_rows": [{"before_row_text": before, "cells": cells} for before, cells in new_rows.values()]})
s10 = [[c.strip() for c in l.strip().strip("|").split("|")] for l in open(os.path.join(SIO, "Table_S10_stability.md"), encoding="utf8") if l.startswith("| EU")]
club = [r for r in s10 if r[0].startswith("EU alone · penalty")][0]; coal = [r for r in s10 if r[0].startswith("EU alone · surcharge")][0]
tables.append({"table_after": "Table S10. One-deviation tests of the final coalitions.",
               "set_cells": [{"row_text": [club[0]], "col": 3, "text": club[3]},
                             {"row_text": [coal[0]], "col": 3, "text": coal[3]},
                             {"row_text": [coal[0]], "col": 4, "text": coal[4]}]})
assert club[3] == "Japan" and coal[4] == "Madagascar, Southern Africa", (club[3], coal[4])

here = os.path.dirname(os.path.abspath(__file__))
json.dump(ops, open(os.path.join(here, "ops_v32b.json"), "w"), ensure_ascii=False, indent=0)
json.dump(anchors, open(os.path.join(here, "anchors_v32b.json"), "w"), ensure_ascii=False, indent=0)
json.dump(images, open(os.path.join(here, "images_v32b.json"), "w"), ensure_ascii=False, indent=0)
json.dump(tables, open(os.path.join(here, "tables_v32b.json"), "w"), ensure_ascii=False, indent=0)
print(len(ops), "ops,", len(anchors), "target paragraphs,", len(images), "images,", sum(len(t.get('insert_rows', [])) for t in tables), "rows,",
      sum(len(t.get('set_cells', [])) for t in tables), "cells")
