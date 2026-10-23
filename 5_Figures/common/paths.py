"""Where things are. The layout of 5_Figures:

  common\            shared modules (this file, figstyle, mapping, v30) and the extraction scripts (extract_all, extract_plane, stats, extract_brazil_aez.R)
  data\              the extracted data of one generation of runs: all_data_<label>.json, stats_<label>.json, plane_runs_<label>.json, ..., brazil_aez_<label>.csv
  <Figure>_script\   one script per figure or table set; <Figure>_Output\ its png / pdf / source-data csv (the output folder is derived from the script's folder)

REPO     the model folder: the parent of 5_Figures when this folder sits in the repository, else the environment variable
         FOREST_CLUB_REPO, else C:\runGTAP375\Game_theory_2024
VERSION  the suffix the run tags carry after "..._frombau_eudrkeep_pinall": "_wnet_v33" (V33, the Miranda-calibrated elasticities, 20 Oct 2026),
         "_wnet_v32" (V32, the runs of 7 Oct), "_wnet" (V31), "" (V30);
         set with FOREST_CLUB_VERSION or `python make_all.py --version _wnet`
LABEL    the short name of that generation (V32, V31, V30): the data files are suffixed with it (all_data_V32.json)
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))              # 5_Figures\common
ROOT = os.path.abspath(os.path.join(HERE, ".."))                 # 5_Figures
_PARENT = os.path.abspath(os.path.join(ROOT, ".."))              # the model repository, when 5_Figures sits inside it
_IN_REPO = os.path.isdir(os.path.join(_PARENT, "4_DB"))
REPO = os.environ.get("FOREST_CLUB_REPO", _PARENT if _IN_REPO else r"C:\runGTAP375\Game_theory_2024")
DB   = os.path.join(REPO, "4_DB")
EXT  = os.path.join(REPO, "0_External_data")
OUT3 = os.path.join(REPO, "3_Output")
VERSION = os.environ.get("FOREST_CLUB_VERSION", "_wnet_v33")   # default moved to V33 on 22 Oct 2026 (the manuscript figures); set FOREST_CLUB_VERSION=_wnet_v32 to redraw the V32 generation
LABELS = {"_wnet_v33": "V33", "_wnet_v32": "V32", "_wnet": "V31", "": "V30"}
BASELINE_SUFFIX = {"_wnet_v33": "_v33"}.get(VERSION, "")   # V33 reads Baseline_2stage_bau5_eta0.66_v33; earlier generations the unsuffixed folder
LABEL = LABELS.get(VERSION, VERSION.strip("_") or "V30")
DATA = os.path.join(ROOT, "data"); os.makedirs(DATA, exist_ok=True)
FIG_ROOT = os.environ.get("FOREST_CLUB_FIGURES", os.path.join(ROOT, "figures"))   # only for a script that is not in a <Figure>_script folder
FIG = os.path.join(FIG_ROOT, LABEL)
def _script_dir():
    main = sys.argv[0] if sys.argv and sys.argv[0] else ""
    return os.path.dirname(os.path.abspath(main)) if main else ""
def out_dir():
    """The output folder of the running script: <Figure>_Output next to its <Figure>_script folder; FIG otherwise."""
    d = _script_dir(); b = os.path.basename(d)
    o = os.path.join(os.path.dirname(d), b[:-len("_script")] + "_Output") if b.endswith("_script") else FIG
    os.makedirs(o, exist_ok=True); return o
def db(name): return os.path.join(DB, name)
def fig(name): return os.path.join(out_dir(), name)
def here(name):
    """A data file of the generation (json, brazil_runs.txt, brazil_aez.csv) in data\, suffixed with the label; any other shared file in common\."""
    if name.endswith(".json") or name in ("brazil_runs.txt", "brazil_aez.csv"):
        stem, ext = os.path.splitext(name); return os.path.join(DATA, f"{stem}_{LABEL}{ext}")
    return os.path.join(HERE, name)
