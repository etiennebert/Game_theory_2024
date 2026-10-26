#!/usr/bin/env python3
"""HILDA+ v2.1-crop land-use transitions and states by country x GTAP agro-ecological zone x year, from the netCDF files.

Replaces the Alteryx spatial match (B-1_Spatial-match_HILDA_AEZ.yxmd) with one script, for every country in the window.
Everything is located relative to this file (…\\1. HILDA data\\1. Extracting_ntcdf_data\\1. HILDA_NTCDF_data\\):

    hildaplus_GLOB-2-1-crop_transitions.nc, hildaplus_GLOB-2-1-crop_states.nc   next to this file
    ..\\Ext_World_Countries_Shp_Files\\World_Countries.shp                      the country polygons (COUNTRY names)
    World_Countries_iso3.csv                                                   COUNTRY -> ISO3, next to this file
    ..\\..\\3. Split_AEZ\\GAEZ_from_FAO_data\\mc3_CRUTS32_Hist_8110.tif, lgd_CRUTS32_Hist_0010.tif   FAO GAEZ v4 thermal climate and
                                                                               length of growing period (5 arc-minutes)
    outputs: country_AEZ_tables\\HILDA_v2.1_transitions_country_AEZ.csv  (country, iso3, year, aez, from_class, to_class, cells, area_ha)
             country_AEZ_tables\\HILDA_v2.1_states_country_AEZ.csv       (country, iso3, year, aez, lulc, cells, area_ha)

Method. Each 0.01-degree HILDA+ cell is assigned to the country whose polygon contains its centre (coastal cells whose centre falls
in the sea are given the country whose polygon touches them) and to the GTAP AEZ of the GAEZ 5-arc-minute cell it falls in,
AEZ = 6 x zone + moisture class, zone = tropical (thermal class 1, tropics lowland), temperate (classes 2-18: tropics highland,
subtropics and temperate) or boreal (19+), moisture class from the growing period (0-59 days = 1 arid, 60-119 = 2, 120-179 = 3,
180-239 = 4, 240-299 = 5, 300+ = 6). This reproduces the FAO GAEZ 18-class AEZ map (..\\3. Split_AEZ\\GAEZ_from_FAO_data\\GAEZ.shp,
the one the Alteryx match used) cell for cell, and it is the map the GTAP-AEZ land cover of the model follows (checked against the
LCOV totals by AEZ: Bolivia's Altiplano and the Andes are temperate AEZs). 23 Oct 2026: the first version counted thermal class 2 as
tropical; that moved the highlands of Peru, Bolivia, Colombia, Mexico and the Angolan plateau into tropical AEZs. Cell areas are geodetic (WGS84), in hectares. Transitions kept: from a forest class
(40-45), unmanaged grass/shrubland (55) or sparse vegetation (66) to annual crops (22), tree crops (23), agroforestry (24) or pasture
(33); the from-class is kept in the output so that forest-only and forest+55 definitions can both be built. States kept: 22, 23, 24,
33, 40-45, 55, 66 (areas by country x AEZ x year, e.g. forest cover by AEZ).

Usage (Spyder: run the file; or a prompt):  python hilda_country_aez_tables.py [--years 2008 2020] [--lat -56 84] [--lon -180 180] [--no-states] [--band 400]
Zones instead of countries (23 Oct 2026): --zones <polygon file> --zone-field <name column> [--out-suffix <tag>] aggregates by the polygons
of that file (e.g. the IBGE biomes of Brazil, biomes_2019_simplified.gpkg, field name_biome) instead of the countries; cells outside the
polygons are skipped, the output is HILDA_v2.1_transitions_<tag>_AEZ.csv with a "zone" column. --lat / --lon limit the window (Brazil:
--lat -34 6 --lon -74 -34), which makes such a run a few minutes.
Needs numpy, pandas, netCDF4, geopandas, rasterio (pip install rasterio). Runtime: tens of minutes (the two netCDF files are 8 GB).
"""
import argparse, os, sys, time
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--years", nargs=2, type=int, default=[2008, 2020], help="first and last year (HILDA+ v2.1 runs to 2020)")
ap.add_argument("--lat", nargs=2, type=float, default=[-56.0, 84.0], help="latitude window (default: all land except Antarctica; -56 40 for the tropics and subtropics only)")
ap.add_argument("--lon", nargs=2, type=float, default=[-180.0, 180.0], help="longitude window")
ap.add_argument("--zones", default=None, help="polygon file (shp, gpkg, geojson) whose features replace the countries, e.g. the IBGE biomes")
ap.add_argument("--zone-field", default=None, help="the name column of --zones")
ap.add_argument("--out-suffix", default=None, help="tag of the output files: HILDA_v2.1_transitions_<tag>_AEZ.csv (default country, or the stem of --zones)")
ap.add_argument("--band", type=int, default=400, help="rows (0.01 degree) read at a time")
ap.add_argument("--no-states", action="store_true", help="skip the states file")
ap.add_argument("--transitions", default=os.path.join(HERE, "hildaplus_GLOB-2-1-crop_transitions.nc"))
ap.add_argument("--states", default=os.path.join(HERE, "hildaplus_GLOB-2-1-crop_states.nc"))
ap.add_argument("--countries", default=os.path.join(HERE, "..", "Ext_World_Countries_Shp_Files", "World_Countries.shp"))
ap.add_argument("--iso", default=os.path.join(HERE, "World_Countries_iso3.csv"))
ap.add_argument("--gaez", default=os.path.join(HERE, "..", "..", "3. Split_AEZ", "GAEZ_from_FAO_data"))
ap.add_argument("--out", default=os.path.join(HERE, "country_AEZ_tables"))
args = ap.parse_args()
for p in (args.transitions, args.countries, args.iso, os.path.join(args.gaez, "mc3_CRUTS32_Hist_8110.tif"), os.path.join(args.gaez, "lgd_CRUTS32_Hist_0010.tif")) + (() if args.no_states else (args.states,)):
    if not os.path.exists(p): sys.exit(f"not found: {p}")
os.makedirs(args.out, exist_ok=True)
import netCDF4, geopandas as gpd, rasterio
from rasterio import features
from rasterio.transform import from_origin

# ---------------------------------------------------------------- the GTAP AEZ of every GAEZ 5-arc-minute cell (2160 x 4320, north up)
mc = rasterio.open(os.path.join(args.gaez, "mc3_CRUTS32_Hist_8110.tif")).read(1).astype(int)
lg = rasterio.open(os.path.join(args.gaez, "lgd_CRUTS32_Hist_0010.tif")).read(1).astype(int)
moist = np.select([lg < 0, lg < 60, lg < 120, lg < 180, lg < 240, lg < 300], [0, 1, 2, 3, 4, 5], default=6)
zone = np.where(mc == 1, 0, np.where(mc == 0, -1, np.where(mc >= 19, 2, 1)))   # 23 Oct 2026: class 2 (tropics highland) is temperate, 19+ boreal (= GAEZ.shp, = GTAP LCOV)
AEZ = np.where((zone >= 0) & (moist > 0), zone * 6 + moist, 0).astype(np.uint8)       # 0 = no zone (water, ice)
GRES = 1.0 / 12.0

# ---------------------------------------------------------------- countries, or zones
if args.zones:
    if not os.path.exists(args.zones): sys.exit(f"not found: {args.zones}")
    cty = gpd.read_file(args.zones).to_crs(4326); field = args.zone_field or [c for c in cty.columns if c != "geometry"][0]
    cty = cty[cty[field].notna()]; names = [str(v) for v in cty[field]]; iso = {}; unit = "zone"
    tag = args.out_suffix or os.path.splitext(os.path.basename(args.zones))[0]
    print(f"zones: {len(names)} polygons of {args.zones} ({field}): {', '.join(names[:12])}{'...' if len(names) > 12 else ''}", flush=True)
else:
    cty = gpd.read_file(args.countries).to_crs(4326)
    iso = pd.read_csv(args.iso).set_index("COUNTRY")["iso3"].fillna("").to_dict()
    names = list(cty["COUNTRY"]); unit = "country"; tag = args.out_suffix or "country"
shapes = [(geom, i + 1) for i, geom in enumerate(cty.geometry) if geom is not None]

# ---------------------------------------------------------------- the HILDA grid
nc_t = netCDF4.Dataset(args.transitions, "r")
lat = np.array(nc_t.variables["latitude"][:]); lon = np.array(nc_t.variables["longitude"][:]); years_nc = np.array(nc_t.variables["time"][:]).astype(int)
south_up = lat[0] < lat[-1]
res = abs(float(lat[1] - lat[0]))
rows = np.where((lat >= args.lat[0]) & (lat <= args.lat[1]))[0]; r_lo, r_hi = int(rows.min()), int(rows.max()) + 1
cols = np.where((lon >= args.lon[0]) & (lon <= args.lon[1]))[0]; c_lo, c_hi = int(cols.min()), int(cols.max()) + 1; lon_w = lon[c_lo:c_hi]
years = [y for y in range(args.years[0], args.years[1] + 1) if y in set(years_nc)]
print(f"grid {len(lat)} x {len(lon)} at {res:g} deg, {'south' if south_up else 'north'} up; rows {r_lo}:{r_hi} ({lat[rows].min():.2f} to {lat[rows].max():.2f}), columns {c_lo}:{c_hi} ({lon_w.min():.2f} to {lon_w.max():.2f}); years {years[0]}-{years[-1]}", flush=True)
R = 6371007.181   # authalic Earth radius, m
def cell_area_ha(lat_c):   # geodetic area of a res x res cell centred at lat_c, in hectares
    p1 = np.radians(lat_c - res / 2); p2 = np.radians(lat_c + res / 2)
    return R * R * np.radians(res) * (np.sin(p2) - np.sin(p1)) / 1e4

FROM = [40, 41, 42, 43, 44, 45, 55, 66]; TO = [22, 23, 24, 33]
T_CODES = np.array([f * 100 + t for f in FROM for t in TO]); S_CODES = np.array([22, 23, 24, 33, 40, 41, 42, 43, 44, 45, 55, 66])

def band_geo(r0, r1):
    """country index and AEZ for the rows r0:r1 (in the array's own orientation), and the cell areas by row."""
    lat_b = lat[r0:r1]; top = lat_b.max() + res / 2; left = lon_w.min() - res / 2
    T = from_origin(left, top, res, res); shp = (r1 - r0, len(lon_w))
    c = features.rasterize(shapes, out_shape=shp, transform=T, fill=0, dtype="uint16", all_touched=False)
    c2 = features.rasterize(shapes, out_shape=shp, transform=T, fill=0, dtype="uint16", all_touched=True)
    c = np.where(c == 0, c2, c)
    if south_up: c = np.flipud(c)                      # rasterize paints north up; match the array orientation
    gr = np.clip(((90.0 - lat_b) / GRES).astype(int), 0, AEZ.shape[0] - 1); gc = np.clip(((lon_w + 180.0) / GRES).astype(int), 0, AEZ.shape[1] - 1)
    a = AEZ[gr[:, None], gc[None, :]]
    return c, a, cell_area_ha(lat_b)

def aggregate(var, codes_keep, acc, r0, r1, c, a, area, yi, year):
    codes = np.asarray(var[yi, r0:r1, c_lo:c_hi]); codes = np.where(np.ma.getmaskarray(codes), 0, np.ma.getdata(codes)).astype(np.int32)
    m = np.isin(codes, codes_keep) & (c > 0)
    if not m.any(): return
    ri, ci = np.nonzero(m)
    key = (c[ri, ci].astype(np.int64) * 32 + a[ri, ci]) * 10000 + codes[ri, ci]
    w = area[ri]
    u, inv = np.unique(key, return_inverse=True)
    n = np.bincount(inv); s = np.bincount(inv, weights=w)
    for k, nn, ss in zip(u, n, s):
        acc[(year, int(k))] = acc.get((year, int(k)), (0, 0.0)); acc[(year, int(k))] = (acc[(year, int(k))][0] + int(nn), acc[(year, int(k))][1] + float(ss))

def to_frame(acc, kind):
    rec = []
    for (year, k), (n, s) in acc.items():
        code = k % 10000; ca = k // 10000; aez = ca % 32; ci = ca // 32; name = names[ci - 1]
        if kind == "transitions": rec.append((name, iso.get(name, ""), year, aez, code // 100, code % 100, n, round(s, 2)))
        else: rec.append((name, iso.get(name, ""), year, aez, code, n, round(s, 2)))
    cols = [unit, "iso3", "year", "aez", "from_class", "to_class", "cells", "area_ha"] if kind == "transitions" else [unit, "iso3", "year", "aez", "lulc", "cells", "area_ha"]
    return pd.DataFrame(rec, columns=cols).sort_values(cols[:5]).reset_index(drop=True)

# ---------------------------------------------------------------- the loop: bands outside, years inside
vt = nc_t.variables["LULC_transitions"]; yidx = {int(y): i for i, y in enumerate(years_nc)}
nc_s = None if args.no_states else netCDF4.Dataset(args.states, "r"); vs = None if nc_s is None else nc_s.variables["LULC_states"]
acc_t, acc_s = {}, {}; t0 = time.time(); nb = int(np.ceil((r_hi - r_lo) / args.band))
for b, r0 in enumerate(range(r_lo, r_hi, args.band)):
    r1 = min(r0 + args.band, r_hi); c, a, area = band_geo(r0, r1)
    for y in years:
        aggregate(vt, T_CODES, acc_t, r0, r1, c, a, area, yidx[y], y)
        if vs is not None: aggregate(vs, S_CODES, acc_s, r0, r1, c, a, area, yidx[y], y)
    print(f"  band {b + 1}/{nb} (lat {lat[r0:r1].min():.1f} to {lat[r0:r1].max():.1f}) done, {time.time() - t0:.0f} s", flush=True)
nc_t.close(); nc_s and nc_s.close()

out_t = os.path.join(args.out, f"HILDA_v2.1_transitions_{tag}_AEZ.csv"); out_s = os.path.join(args.out, f"HILDA_v2.1_states_{tag}_AEZ.csv")
dt = to_frame(acc_t, "transitions"); dt.to_csv(out_t, index=False, encoding="utf-8")
print("transitions:", len(dt), "rows ->", out_t)
if acc_s:
    ds = to_frame(acc_s, "states"); ds.to_csv(out_s, index=False, encoding="utf-8")
    print("states:", len(ds), "rows ->", out_s)

# ---------------------------------------------------------------- a first look: forest-to-agriculture by country and year, kha, forest classes vs class 55
f = dt[dt.from_class.between(40, 45)].groupby([unit, "year"]).area_ha.sum().unstack() / 1000
g = dt[dt.from_class == 55].groupby([unit, "year"]).area_ha.sum().unstack() / 1000
top = f.sum(axis=1).sort_values(ascending=False).head(25).index
pd.set_option("display.width", 250)
print(f"\nforest (40-45) to crops/pasture, kha per year, 25 largest {unit}s:"); print(f.loc[top].round(0).to_string())
print("\nthe same from unmanaged grass/shrubland (55), kha per year:"); print(g.reindex(top).fillna(0).round(0).to_string())
