"""Rebuild every data file, figure and table of one generation of runs, in order. Run from anywhere:

  python make_all.py                      the V32 runs (tag suffix _wnet_v32): data\\ then every <Figure>_Output\\
  python make_all.py --version _wnet      another generation (V31; --version "" for V30) - its data files get their own label
  python make_all.py --figures            redraw the figures and tables from data\\ alone, without the model folder
  python make_all.py --no-r               skip the two R steps (Fig. 5 and the SI figures are then drawn from the last csv files)

Layout: common\\ holds the shared modules and the extraction scripts, data\\ the extracted json / csv of the generation, and each
figure has a <Figure>_script\\ folder (one script) and a <Figure>_Output\\ folder (png, pdf, source-data csv). The model folder is
the parent of 5_Figures when the folder sits in the repository (else FOREST_CLUB_REPO). The R steps (HARr) run with Rscript when it
is on the PATH; otherwise the command to run by hand is printed."""
import subprocess, sys, os, time, shutil
ROOT = os.path.dirname(os.path.abspath(__file__))
args = sys.argv[1:]
if "--version" in args:
    i = args.index("--version"); os.environ["FOREST_CLUB_VERSION"] = args[i + 1] if i + 1 < len(args) else ""; del args[i:i + 2]
only_figures = "--figures" in args; no_r = "--no-r" in args
sys.path.insert(0, os.path.join(ROOT, "common")); import paths
print(f"generation {paths.LABEL} (tag suffix '{paths.VERSION}'), model folder {paths.REPO}, data files in {paths.DATA}")
steps = [("common/extract_all.py", "data\\all_data_<L>.json: every run of the generation, the configurations the text quotes, thresholds, stability tests, GDP, switching costs; brazil_runs_<L>.txt"),
         ("common/extract_plane.py", "data\\plane_runs_<L>.json, top_deforesters_<L>.json, counterfactuals_<L>.json"),
         ("common/stats.py", "data\\stats_<L>.json and the printed digest of every run quoted in the Results"),
         ("Tables_script/tables.py", "Tables_Output: Table 1 (the club by starting point), Table 2 (thresholds by switching cost), Table 3 (lock-outs)"),
         ("common/extract_brazil_aez.R", "data\\brazil_aez_<L>.csv: Brazil's land use by AEZ from the GEMPACK solutions (R, HARr)"),
         ("Fig_2_script/fig2_forest.py", "Fig. 2: maps of forest kept, the cascade, forest kept by region, leakage"),
         ("Fig_3_script/fig3_plane.py", "Fig. 3: the instrument plane, the eight largest deforesters, the lock-outs"),
         ("Fig_4_script/fig4_welfare.py", "Fig. 4: welfare maps, region x starting point grid, one-deviation stability"),
         ("Fig_5_script/fig5_brazil_aez.py", "Fig. 5: Brazil's land use by agro-ecological zone at the club equilibrium"),
         ("ExtData_Fig_1_script/extdata_fig1_thresholds.py", "Extended Data Fig. 1: Brazil's first-round loss against the charge and the switching cost"),
         ("ExtData_Fig_2_script/extdata_fig2_deforesters.py", "Extended Data Fig. 2: the largest deforesters' first-round loss and joining round"),
         ("SI_script/si_v32_extract.R", "SI_script\\data\\*.csv: baseline forest change, welfare decomposition, supply responses, Brazil's commodities (R, HARr)"),
         ("SI_script/si_figures.py", "SI_Output: Figs S7, S9, S10, S11 and Tables S9-S12")]
for script, what in steps:
    if only_figures and (script.startswith("common/extract") or script.endswith("stats.py") or script.endswith(".R")): continue
    path = os.path.join(ROOT, *script.split("/")); cwd = os.path.dirname(path)
    if script.endswith(".R"):
        if no_r: print(f"\n== {script}: skipped (--no-r)"); continue
        rs = shutil.which("Rscript")
        if not rs: print(f"\n== {script}: Rscript not on the PATH - run it by hand: Rscript \"{path}\" \"{paths.REPO}\" {paths.LABEL}"); continue
        cmd = [rs, path, paths.REPO] + ([paths.LABEL] if "brazil" in script else [])
    else: cmd = [sys.executable, path]
    t0 = time.time(); print(f"\n== {script}: {what.replace('<L>', paths.LABEL)}")
    r = subprocess.run(cmd, cwd=cwd)
    print(f"   {'ok' if r.returncode == 0 else 'FAILED'} in {time.time() - t0:.0f} s")
    if r.returncode and not script.endswith("stats.py"): sys.exit(r.returncode)
print("\ndone: data files in data\\, figures and tables in the <Figure>_Output folders")
