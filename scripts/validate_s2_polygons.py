#!/usr/bin/env python3
"""Check that every published polygon can be measured on the sphere.

The other geometry gates all reason in the PLANE. validate_polygons compares areas in
an equal-area projection, validate_spatial_containment intersects in lon/lat,
validate_family_areas projects to ESRI:54034. None of them can see a polygon that GEOS
accepts and s2 rejects -- and two of the ten that s2 rejected on this database were
GEOS-VALID, each carrying a pinch 4e-10 m wide that one representation self-intersects
on and the other does not, so `make_valid()` returned them unchanged and every planar
check passed.

That gap is not academic. WHEP's consumers ask spherical questions: a geodesic area,
an intersection against a 0.5-degree grid cell. Both go through s2, both ABORT rather
than return a wrong number, and the abort is what takes a territory out of a gridded
build. FJI-1800-2025 is live in the present day and FAOSTAT area 66 routes to it
across 203,519 observed rows; measured against the shipped copy before the fix,
sf::st_intersection() of that polygon with a 0.5-degree grid raised
"Loop 82 edge 4 crosses loop 332 edge 2" while the same call on live neighbour
TON-1800-2025 returned 20 cells.

The check uses spherely, which wraps the same s2geometry library that R's s2 package
wraps. That matters more than it looks: a gate that APPROXIMATES the spherical
predicates can pass while the consumer still aborts, so this asks the actual engine.
The failure messages it prints are character-for-character the ones an sf user sees.

WHAT IT ASSERTS
  A. Every polity carrying a non-empty geometry can be loaded by s2 and yields a
     finite, positive geodesic area. Dead rows (retired/superseded) are included:
     they must never receive data, but a consumer that reads the whole layer still
     aborts on one bad geometry regardless of whose it is.
  B. The regression pins below -- the ten rows that were unloadable, Fiji first --
     are still present, still non-empty and still measurable. A geometry gate that
     only forbids NEW breakage would pass if the repaired polygon were dropped
     altogether, which is the other way to make the failure go away.
  C. UNREPAIRABLE is bidirectional, like every baseline in this repo: a row listed
     there that has become measurable fails too, so the list cannot go stale. It is
     empty today, which is the target state -- all ten repaired.

Rows with NO geometry are out of scope here and are not silently tolerated either:
46 of the 749 have none, which the manifest tracks as polygon_gap_polity_codes and
validate_polygons check C gates. Reporting them again from here would put one fact
behind two gates with two baselines.

Usage:
  python3 scripts/validate_s2_polygons.py
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES_CSV = os.path.join(REPO, "data/final/polities_database.csv")
POLITIES_GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The ten rows s2 could not load before scripts/repair_s2_polygons.py ran, with the
# geodesic area each yields now, under the default `preserve` repair. Pinned so the repair
# cannot silently regress and so dropping a polygon does not count as fixing it. Note that
# these are the PRESERVE-method numbers: switching repair_s2_polygons.py to --method node
# moves four of them (IRN-1800-1828 by 12,845 km2), and this list is what would then have to
# be re-measured -- deliberately, since that switch is a decision. Tolerance is generous on
# purpose:
# the claim is "this territory is measurable and roughly this size", not a digit-exact
# reproduction of one GEOS version's snap-rounding.
#
# FJI-1800-2025 heads the list because it is the only one FAOSTAT-mapped (area 66,
# 203,519 observed rows) and the only one live today, so it is the only one whose
# breakage was costing a present-day build anything.
REGRESSION_PINS = {
    "FJI-1800-2025": 18_710.0,
    "DEU-1871-1919": 538_028.0,
    # 701_416 -> 755_602 on 2026-08-07, and the pin was stale rather than the geometry wrong.
    # This pin was recorded on 2026-08-05 against a polygon that CONTAINED NEW CALEDONIA, REUNION
    # AND KERGUELEN: Cliopatria's "French Indochina" feature is a record of French possessions east
    # of Africa, and all 35 of its steps carry those islands. PR 152 replaced it with the 1920 step
    # clipped to a mainland envelope (99-110.5E, 7.5-24.5N), which drops 11 parts totalling 36,992
    # km2 and keeps Guangzhouwan. The new figure being LARGER despite dropping territory is the
    # vintage moving 1900 -> 1920, into Cliopatria's stable 1908-1939 plateau.
    "FID-1887-1954": 755_602.0,
    "FRA-1800-1871": 532_627.0,
    "FRA-1800-1919": 532_627.0,
    "GBR-1800-1921": 312_224.0,
    "IND-1800-1886": 4_220_004.0,
    "IRN-1800-1828": 1_744_545.0,
    "PAP-1800-1870": 39_204.0,
    "SNW-1814-1905": 761_137.0,
}
PIN_TOLERANCE = 0.02  # 2%

# Polities whose polygon s2 still cannot load. Empty is the target state. An entry
# here is a declared, enumerated gap rather than an abort at call time -- which is
# what the issue asked for -- and it must carry the reason, so a reader can tell a
# known source defect from a repair that regressed.
UNREPAIRABLE: dict[str, str] = {}

DEAD_STATUS = ("retired", "superseded")


def main() -> int:
    try:
        import geopandas as gpd
        import spherely  # noqa: F401 - availability check; used via repair_s2_polygons
        from repair_s2_polygons import geodesic_area_km2, s2_failure
    except ImportError as exc:
        print(f"FAIL: geopandas/shapely/spherely unavailable ({exc})")
        print("  pip install -r requirements-ci.txt")
        return 2
    if not os.path.exists(POLITIES_GPKG):
        print(f"FAIL: {POLITIES_GPKG} missing; run scripts/build_database.py first")
        return 2

    with open(POLITIES_CSV, encoding="utf-8") as fh:
        status = {
            r["polity_code"]: (r.get("wiki_status") or "").strip()
            for r in csv.DictReader(fh)
        }

    frame = gpd.read_file(POLITIES_GPKG)
    n_empty = int((frame.geometry.isna() | frame.geometry.is_empty).sum())
    with_geom = frame[~frame.geometry.isna() & ~frame.geometry.is_empty]

    failures: dict[str, str] = {}
    areas: dict[str, float] = {}
    for _, row in with_geom.iterrows():
        code = row["polity_code"]
        reason = s2_failure(row.geometry)
        if reason is not None:
            failures[code] = reason
            continue
        km2 = geodesic_area_km2(row.geometry)
        if not (km2 > 0) or km2 != km2 or km2 == float("inf"):
            failures[code] = f"geodesic area is {km2!r}"
            continue
        areas[code] = km2

    print(f"features: {len(frame)}   with geometry: {len(with_geom)}   empty: {n_empty}")
    print(f"s2 loads and measures: {len(areas)}   s2 rejects: {len(failures)}")
    for code in sorted(failures):
        live = "live" if status.get(code) not in DEAD_STATUS else "dead"
        print(f"   {code:<18} ({live})  {failures[code]}")

    problems: list[str] = []

    # A + C: anything s2 rejects must be a declared entry, and every declared entry
    # must still be rejected.
    for code in sorted(set(failures) - set(UNREPAIRABLE)):
        live = status.get(code) not in DEAD_STATUS
        problems.append(
            f"s2 cannot measure {code} ({'LIVE' if live else 'dead'}): {failures[code]} "
            f"— run scripts/repair_s2_polygons.py, and if it cannot fix it add the row "
            f"to UNREPAIRABLE with the reason so consumers can report it"
        )
    for code in sorted(set(UNREPAIRABLE) - set(failures)):
        problems.append(
            f"{code} is listed in UNREPAIRABLE but s2 measures it fine now — remove it"
        )

    # B: the pinned rows must still be there, and still be roughly the right size.
    for code, expected in sorted(REGRESSION_PINS.items()):
        if code not in set(frame["polity_code"]):
            problems.append(f"regression pin {code} has vanished from the GeoPackage")
            continue
        if code not in areas:
            problems.append(
                f"regression pin {code} no longer yields a geodesic area "
                f"({failures.get(code, 'geometry is empty or absent')})"
            )
            continue
        got = areas[code]
        off = abs(got - expected) / expected
        status_word = "ok" if off <= PIN_TOLERANCE else "OFF"
        print(f"   pin {code:<18}{got:>13,.0f} km2  vs {expected:>13,.0f}  {status_word}")
        if off > PIN_TOLERANCE:
            problems.append(
                f"regression pin {code} measures {got:,.0f} km2 against a pinned "
                f"{expected:,.0f} ({100 * off:.1f}% off, tolerance "
                f"{100 * PIN_TOLERANCE:.0f}%) — the polygon binding changed, or the "
                f"repair did"
            )

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: every published polygon is measurable on the sphere")
    return 0


if __name__ == "__main__":
    sys.exit(main())
