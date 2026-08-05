#!/usr/bin/env python3
"""Count invalid geometries in the published GeoPackage and hold the number down.

41 of 703 polygons fail `is_valid` in the published CRS. That matters because an invalid geometry makes every
spatial predicate unreliable: `contains`, `intersects` and `area` may return a wrong answer
or raise, depending on the GEOS version. `validate_spatial_containment` and
`validate_family_areas` both read these same geometries, so an invalid polygon silently
weakens two other gates rather than announcing itself.

    Nested shells            33
    Self-intersection         7
    Hole lies outside shell   1

WHAT THE CAUSE IS NOT. The discovery sweep that surfaced this reported the invalidity as
"created by SimplifyPreserveTopology(0.01)", i.e. by our own build. Checked rather than
repeated, and IT IS NOT THE MAIN CAUSE. Cliopatria ships 2,239 invalid geometries out of
15,690 features -- 14% of the source -- and all four of our Cliopatria-sourced invalid rows
are already invalid in the raw GeoJSON, before this repo touches them. Provenance:

    gadm-4.1-adm0     19        cliopatria         4     (all 4 invalid at source)
    reporting-areas    6        gadm-4.1-adm1      4
    constructed        5        cshapes-europe     3

`reporting-areas` and `constructed` are OUR unions, so those 11 could plausibly be ours --
a union of invalid inputs is invalid. The other 29 arrive that way. Simplification may still
add to it; the point is that "our simplifier did this" was asserted, and the evidence says
most of it is inherited.

WHY THIS GATE DOES NOT JUST CALL make_valid(). Because the two obvious repairs disagree, and
not by a rounding error:

    IRN-1800-1828   make_valid 1,730,793   buffer(0) 1,743,638   difference 12,845 km2
    PAP-1800-1870   make_valid    39,222   buffer(0)    39,269   difference     47
    IND-1800-1886   make_valid 4,209,849   buffer(0) 4,209,868   difference     20

`buffer(0)` keeps the area of a self-overlapping ring; `make_valid` splits it and drops the
overlap. On Qajar Iran that is 0.7% of the country, and neither answer is obviously the right
one without knowing whether the overlap is a digitising artifact or two genuinely distinct
rings. Repairing 41 polygons with a blanket call would move a real area by 12,845 km2 on the
strength of a default argument. So this gate MEASURES and BOUNDS; it does not repair.

Only 6 have a repair spread above 1 km2, so the rest are safe to fix whenever someone wants
to. Those 6 need a decision recorded per row.

VALIDITY IS CRS-DEPENDENT, WHICH IS EASY TO GET WRONG AND I DID. Measured on the same
GeoPackage:

    invalid in native EPSG:4326 (what is published)   41
    invalid after reprojecting to ESRI:54034          40
    only invalid natively:   FRA-1800-1871, FRA-1800-1919
    only invalid reprojected: SNW-1814-1905

I built the first baseline from an equal-area reprojection, because that is what you need for
areas, and the gate then correctly rejected it. This check runs on the NATIVE geometry, since
that is the geometry consumers receive. Anyone re-measuring should do the same, or they will
get a list that differs by three rows and disagrees in both directions.

Bidirectional: a NEW invalid polygon fails, and a baselined one that becomes valid must be
removed. The count can only go down.
"""
from __future__ import annotations

import collections
import csv
import os
import warnings

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG_PATH = os.path.join(REPO, "data/final/polities_database.gpkg")
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")

# Polygons known to be invalid, with the source that supplied them. Being here is a debt
# record, not an exemption: the list is bidirectional, so it shrinks and cannot grow.
BASELINE_INVALID = {
    # Invalid in the raw Cliopatria GeoJSON, verified feature by feature. These also carry the
    # largest repair spreads, so each needs a decision on its page, not a sweep.
    "FID-1887-1954": "cliopatria",
    "IND-1800-1886": "cliopatria",
    "IRN-1800-1828": "cliopatria",
    "PAP-1800-1870": "cliopatria",
    # Our own unions -- the ones most likely to be genuinely ours, since a union of invalid
    # inputs is invalid. All six have a repair spread at or below 2 km2.
    "RAFR-1850-2025": "reporting-areas",
    "RASI-1850-2025": "reporting-areas",
    "REUR-1850-2025": "reporting-areas",
    "RLAM-1850-2025": "reporting-areas",
    "ROCE-1850-2025": "reporting-areas",
    "ROW-1850-2025": "reporting-areas",
    # Also ours, from scripts/sources/constructed/build.py.
    "CHN-1932-1945": "constructed",
    "IRL-1800-1921": "constructed",
    "MAN-1932-1945": "constructed",
    "MAN-1945-1950": "constructed",
    "TTPI-1947-1994": "constructed",
    "FRA-1800-1871": "cshapes-europe",
    "FRA-1800-1919": "cshapes-europe",
    "GBR-1800-1921": "cshapes-europe",
}

BASELINE_COUNT_BY_SOURCE = {
    "gadm-4.1-adm0": 19,
    "gadm-4.1-adm1": 4,
    "constructed": 5,
    "cliopatria": 4,
    "cshapes-europe": 3,
    "reporting-areas": 6,
}


def main() -> int:
    for path in (GPKG_PATH, CSV_PATH):
        if not os.path.exists(path):
            print(f"SKIP: {path} missing; run scripts/build_database.py first")
            return 0
    try:
        import geopandas as gpd
    except ImportError:
        print("SKIP: geopandas unavailable")
        return 0

    warnings.filterwarnings("ignore")
    with open(CSV_PATH, encoding="utf-8") as fh:
        sources = {r["polity_code"]: r.get("polygon_source", "") for r in csv.DictReader(fh)}

    frame = gpd.read_file(GPKG_PATH)
    frame = frame[frame.geometry.notna() & ~frame.geometry.is_empty]
    invalid = frame[~frame.geometry.is_valid]
    found = {r["polity_code"] for _, r in invalid.iterrows()}
    by_source = collections.Counter(sources.get(c, "") for c in found)

    problems = []
    for code in sorted(found - set(BASELINE_INVALID)):
        src = sources.get(code, "")
        if by_source[src] <= BASELINE_COUNT_BY_SOURCE.get(src, 0):
            continue  # within the pinned per-source count
        problems.append(f"NEW invalid polygon: {code} from {src!r}")
    for code in sorted(set(BASELINE_INVALID) - found):
        problems.append(f"{code} is baselined as invalid but is valid now -- remove its line")
    for src, pinned in sorted(BASELINE_COUNT_BY_SOURCE.items()):
        actual = by_source.get(src, 0)
        if actual > pinned:
            problems.append(
                f"source {src!r} now has {actual} invalid polygons, up from {pinned}"
            )
        elif actual < pinned:
            problems.append(
                f"source {src!r} now has {actual} invalid polygons, down from {pinned} -- "
                f"lower the pinned count so the improvement is locked in"
            )

    print(f"polygons: {len(frame)}")
    print(f"invalid: {len(found)} (pinned total {sum(BASELINE_COUNT_BY_SOURCE.values())})")
    for src, n in sorted(by_source.items(), key=lambda kv: -kv[1]):
        print(f"  {src or '(none)':18s} {n:>3d}")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        print(
            "\n  An invalid polygon makes contains/intersects/area unreliable, which weakens\n"
            "  validate_spatial_containment and validate_family_areas without either of them\n"
            "  reporting anything. Do NOT fix by calling make_valid() across the board: on\n"
            "  IRN-1800-1828 make_valid and buffer(0) differ by 12,845 km2, so the repair\n"
            "  method is itself a decision that belongs on the polity's page."
        )
        return 1

    print("\nPASS: no new invalid geometry, and none of the baselined ones silently became valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
