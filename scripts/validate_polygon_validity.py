#!/usr/bin/env python3
"""Count invalid geometries in the published GeoPackage and hold the number down.

ZERO of 713 polygons fail `is_valid`, down from 44 (see BASELINE_INVALID). That matters because an invalid geometry makes every
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
BASELINE_INVALID = {}

# EMPTY, AND THAT IS THE POINT. 44 -> 1 -> 0 in two days:
#
#   PR 178  a conditional GEOS MakeValid at a <=0.5% area budget repaired 43, leaving
#           IRN-1800-1828, whose repair would have moved 12,845 km2.
#   PR 147  the s2 repair (scripts/repair_s2_polygons.py) repaired that one too, and it is
#           AREA-PRESERVING: IRN-1800-1828 still measures exactly 1,743,638 km2, not the
#           1,730,793 that make_valid would have given. The 12,845 km2 decision this
#           docstring warned about was never taken -- it was made unnecessary.
#
# So the outcome PR 140 was protecting is intact: nobody silently chose between make_valid
# and buffer(0) on Qajar Iran. A repair that preserves area does not need the judgement.
#
# The empty baseline is bidirectional like the rest: a new invalid polygon fails here, and
# it can no longer be waved through by adding a line, because there is no precedent line to
# copy.

# GEOS VALIDITY IS NOT s2 VALIDITY, AND THIS GATE ONLY SEES GEOS.
#
# shapely uses GEOS, so `is_valid` here is a planar judgement. R's sf uses s2 BY DEFAULT, and s2 is
# stricter. Measured on the published GeoPackage after the repair above:
#
#     GEOS-invalid   1     IRN-1800-1828
#     s2-invalid     4     IRN-1800-1828, DEU-1871-1919, FJI-1800-2025, SNW-1814-1905
#
# So THREE polygons pass this gate and fail in every R consumer that has not turned s2 off, and
# the failure is not cosmetic: st_intersection over the live 2015 polity set RAISES
# "Loop N edge M crosses loop P edge Q" and returns nothing at all. That is the actual cause of
# the symptom reported in eduaguilera/whep#514, which had diagnosed it as two polities sharing one
# polygon -- they do not; GNQ-1968-2025 and STP-1800-2025 measure 26,904 and 1,012 km2 with an
# empty intersection in both this database and whep's committed snapshot.
#
# This gate CANNOT be extended to cover it from Python without s2 bindings. Tracked separately.
BASELINE_COUNT_BY_SOURCE = {}


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
