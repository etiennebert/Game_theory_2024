import csv, os, geopandas as gpd, warnings
from paths import db, here
warnings.filterwarnings("ignore")
D = here("DB_GTAPAEZ_ISO-Code_2024.csv")   # a copy of 4_DB\DB_GTAPAEZ_ISO-Code_2024.csv kept here so the figures need no model folder
if not os.path.exists(D): D = db("DB_GTAPAEZ_ISO-Code_2024.csv")
iso2reg = {r["ISO"]: r["Country"] for r in csv.DictReader(open(D))}
iso2reg.update({"NGA": "nigeria", "PSE": "mena", "XKX": "restofworld"})
_world = None
def regions_gdf():
    global _world
    if _world is not None: return _world
    g = gpd.read_file(here(os.path.join("ne110", "ne_110m_admin_0_countries.shp")))
    g = g[g["ADM0_A3"] != "ATA"].copy()
    g["iso"] = g["ISO_A3"].where(g["ISO_A3"] != "-99", g["ADM0_A3"])
    fix = {"FRA": "FRA", "NOR": "NOR", "KOS": "XKX", "SDS": "SSD", "SOL": "SOM", "CYN": "CYP", "SAH": "ESH"}
    g["iso"] = g["iso"].replace(fix)
    g["region"] = g["iso"].map(iso2reg)
    miss = sorted(g.loc[g["region"].isna(), "NAME"].tolist())
    g = g.to_crs("ESRI:54030")
    _world = (g, miss)
    return _world
if __name__ == "__main__":
    g, miss = regions_gdf(); print("unmapped:", miss); print(g["region"].value_counts().head(45))
