#!/usr/bin/env python3
"""Flag polygons that geometrically swallow other contemporaneous polities.

Why this is a distinct check: `validate_polygons.py` compares a polygon against
its recorded `polygon_area_km2`, so it is opt-in via a hand-entered field. Roughly
590 of 740 rows carry no area and are therefore never compared, and the worst
polygon error in the database sits in that blind spot:

  RUS-1991-2014 uses CShapes feature 365 — the same feature as every F228 (Russian
  Empire / USSR) row — and measures 21,824,142 km2 against Russia's 17,098,242. It
  geometrically contains Kazakhstan, Ukraine, Uzbekistan, Turkmenistan, the
  Baltics, Georgia and Azerbaijan. It has no recorded area, so nothing compared it
  to anything (issue 45).

This check needs no reference data and no hand-entered value. It asks only whether
two polities that COEXIST in time overlap in space, which for two separate
territories is a contradiction the geometry itself reveals.

Containment is frequently legitimate, so the check reports CONTAINERS rather than
pairs: a polity whose polygon holds three or more contemporaneous polities of other
families. Empires and federations do exactly that — and `polity_type` cannot
distinguish them, since French West Africa and its member colonies are all
`national` — so the legitimate ones are enumerated below rather than inferred.

Usage:
  python3 scripts/validate_spatial_containment.py [--min-contained 3]
"""
import argparse
import os
import sys
from collections import defaultdict

import geopandas as gpd
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
EQUAL_AREA = "ESRI:54034"
DEAD_STATUS = ("retired", "superseded")

# Polities that legitimately contain others, because they WERE the larger entity:
# empires containing their possessions, colonial federations containing their
# member colonies, and the statistical aggregates that exist to hold small
# territories. Enumerated because the database cannot express it — AOF-1895-1960
# and every colony inside it are all typed `national`.
LEGITIMATE_CONTAINERS = {
    # Statistical / reporting aggregates
    "ROW-1850-2023", "RAFR-1850-2021", "RASI-1850-2021", "REUR-1850-2021",
    "RLAM-1850-2013", "ROCE-1850-2021",
    # Empires
    "F228-1800-1856", "F228-1856-1905", "F228-1905-1914", "F228-1914-1917",
    "F228-1917-1918", "F228-1918-1920", "F228-1945-1991",
    "AUH-1800-1859", "AUH-1859-1866", "AUH-1866-1908", "AUH-1908-1918",
    "OTT-1800-1886", "JPN-1895-1945",
    # Colonial federations and their groupings
    "AOF-1895-1960", "CODRU-1922-1960", "FRN-1953-1964", "MASG-1946-1963",
    "MLI-1890-1960", "SEN-1854-1886", "SEN-1886-1959", "KEN-1891-1894",
    "NGA-1886-1914", "ZWE-1891-1900",
    # A federation over its pre-1901 colonies
    "AUS-1800-1901",
}

# Containers that are DEFECTS, tracked so the gate stays useful while they are
# open. Bidirectional: one that stops containing must be removed from this set, so
# the list shrinks as the polygons are fixed.
TRACKED_DEFECTS = {
    "RUS-1991-2014",  # issue 45: carries the USSR polygon (CShapes feature 365)
}

ap = argparse.ArgumentParser()
ap.add_argument("--min-contained", type=int, default=3,
                help="report a polity that contains at least this many others")
ap.add_argument("--overlap", type=float, default=0.90,
                help="fraction of the smaller polity that must lie inside")
A = ap.parse_args()

g = gpd.read_file(GPKG)
g = g[g.geometry.notna() & ~g.geometry.is_empty]
g = g[~g["wiki_status"].isin(DEAD_STATUS)].copy()
for col in ("start_year", "end_year"):
    g[col] = pd.to_numeric(g[col], errors="coerce")

eq = g.to_crs(EQUAL_AREA).copy()
# buffer(0) heals self-intersections that would otherwise make .area unreliable.
eq["geometry"] = eq.geometry.buffer(0)
eq["area_km2"] = eq.geometry.area / 1e6

pairs = gpd.sjoin(
    eq[["polity_code", "geometry"]], eq[["polity_code", "geometry"]],
    how="inner", predicate="intersects",
)
pairs = pairs[pairs.polity_code_left != pairs.polity_code_right]

meta = eq.set_index("polity_code")[["start_year", "end_year", "area_km2"]]
geo = eq.set_index("polity_code")["geometry"]

contains = defaultdict(list)
for outer, inner in zip(pairs.polity_code_left, pairs.polity_code_right):
    # Same prefix = successive periods of one territory, not two places.
    if outer.split("-")[0] == inner.split("-")[0]:
        continue
    mo, mi = meta.loc[outer], meta.loc[inner]
    # A shared transition year (one ends where the other starts) is not coexistence.
    if not (mo.start_year < mi.end_year and mi.start_year < mo.end_year):
        continue
    if mi.area_km2 <= 0 or mi.area_km2 >= mo.area_km2:
        continue
    if geo.loc[inner].intersection(geo.loc[outer]).area / geo.loc[inner].area > A.overlap:
        contains[outer].append(inner)

observed = {k for k, v in contains.items() if len(v) >= A.min_contained}
print(f"{len(eq)} live polities with geometry")
print(f"containers holding >={A.min_contained} contemporaneous polities of other "
      f"families: {len(observed)}")

for code in sorted(observed & TRACKED_DEFECTS):
    inside = sorted(contains[code])
    print(f"\n  TRACKED DEFECT {code} contains {len(inside)}: "
          f"{', '.join(inside[:6])}{' ...' if len(inside) > 6 else ''}")

problems = []
for code in sorted(observed - LEGITIMATE_CONTAINERS - TRACKED_DEFECTS):
    inside = sorted(contains[code])
    problems.append(
        f"NEW container {code} holds {len(inside)} contemporaneous polities of "
        f"other families: {', '.join(inside[:6])}"
        + (" ..." if len(inside) > 6 else "")
    )
for code in sorted((LEGITIMATE_CONTAINERS | TRACKED_DEFECTS) - observed):
    problems.append(
        f"{code} is listed as a container but no longer contains "
        f">={A.min_contained} others — remove it from the list"
    )

if problems:
    print(f"\nFAIL: {len(problems)} change(s)\n")
    for p in problems:
        print(f"  {p}")
    print("\n  A polygon that swallows a coexisting polity double-counts its "
          "territory in any spatial or area-weighted use.")
    sys.exit(1)

print("\nPASS: every container is either documented history or a tracked defect")
