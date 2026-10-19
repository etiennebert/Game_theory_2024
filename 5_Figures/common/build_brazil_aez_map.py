"""brazil_aez.geojson: Brazil's GTAP agro-ecological zones as polygons, built the way GTAP-AEZ defines them, from the two FAO GAEZ v4
rasters in the Supplementary Materials (thermal climate mc3_CRUTS32_Hist_8110.tif, length of growing period lgd_CRUTS32_Hist_0010.tif):
zone = tropical (thermal classes 1-2), temperate (3-20) or boreal (21+); moisture class from the growing period, 0-59 days = 1 (arid),
60-119 = 2 (dry semi-arid), 120-179 = 3 (moist semi-arid), 180-239 = 4 (sub-humid), 240-299 = 5 (humid), 300+ = 6 (year-round humid);
AEZ = 6 x zone + moisture class. Clipped to Natural Earth's Brazil. Needs rasterio and geopandas; the result is kept in this folder, so
fig5_brazil_aez.py does not need this script or the rasters.  Usage: python build_brazil_aez_map.py <folder with the two tif files>"""
import sys, os, numpy as np, geopandas as gpd, rasterio, warnings
from rasterio import features
from rasterio.windows import from_bounds
from shapely.geometry import shape
from paths import here
warnings.filterwarnings("ignore")
D = sys.argv[1] if len(sys.argv) > 1 else "."
mc = rasterio.open(os.path.join(D, "mc3_CRUTS32_Hist_8110.tif")); lg = rasterio.open(os.path.join(D, "lgd_CRUTS32_Hist_0010.tif"))
win = from_bounds(-75, -35, -33, 6, mc.transform)
A = mc.read(1, window=win).astype(int); B = lg.read(1, window=win).astype(int); T = mc.window_transform(win)
moist = np.select([B < 0, B < 60, B < 120, B < 180, B < 240, B < 300], [0, 1, 2, 3, 4, 5], default=6)
zone = np.where(np.isin(A, [1, 2]), 0, np.where(A == 0, -1, np.where(A >= 21, 2, 1)))
aez = np.where((zone >= 0) & (moist > 0), zone * 6 + moist, 0).astype(np.int32)
bra = gpd.read_file(here(os.path.join("ne110", "ne_110m_admin_0_countries.shp"))); bra = bra[bra["ADM0_A3"] == "BRA"].to_crs(4326)
shapes = [(shape(g), int(v)) for g, v in features.shapes(aez, transform=T) if v > 0]
gdf = gpd.GeoDataFrame({"aez": [v for _, v in shapes]}, geometry=[g for g, _ in shapes], crs=4326)
gdf = gpd.clip(gdf, bra).dissolve(by="aez").reset_index()
gdf["area_Mha"] = gdf.to_crs("ESRI:54032").area / 1e10
gdf.to_file(here("brazil_aez.geojson"), driver="GeoJSON")
print(gdf[["aez", "area_Mha"]].round(1).to_string())
