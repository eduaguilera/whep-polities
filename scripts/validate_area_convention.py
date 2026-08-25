#!/usr/bin/env python3
"""Hold the repo to ONE area convention, and keep the other one measurable (issue 569).

Two ways of measuring a polygon's area coexist here and neither was ever declared canonical:

  PROJECTED  planar `.area` in ESRI:54034, used by ~20 scripts including validate_stated_areas.py
             and write_stated_area_basis.py, and therefore by every published ratio
  GEODESIC   spherical area via s2/spherely (`repair_s2_polygons.geodesic_area_km2`), "by the same
             route sf::st_area() takes", used by the s2 repair/validate tooling

Both are spherical, so they ought to agree. They do not: a cylindrical equal-area projection
preserves a shape's area, but `.area` joins vertices with STRAIGHT LINES IN THE PLANE while s2 joins
them with GREAT CIRCLES. Those are different curves and the gap grows with latitude -- which is
exactly the signature arm B pins.

THIS GATE DOES NOT PREFER EITHER METHOD. It records that the published figures follow the projected
one and refuses to let that change silently, because switching would move `polygon_area_km2` and
`ratio_polygon_over_stated` for ~500 rows by up to 0.8% -- a decision about published numbers, not a
repair, and not one that should arrive as a side effect of editing a script.
"""
from __future__ import annotations

import os
import statistics
import sys
import warnings

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")

# Arm A. Measured 2026-08-25 over 758 polygons: median 0.99740, spread 0.99537-1.00772. The envelope
# is wider than the observation because adding or editing polygons moves the median a little; it is
# far narrower than the ~0.4% gap between the two conventions, so a switch cannot hide inside it.
MEDIAN_LO, MEDIAN_HI = 0.9950, 1.0000
MAX_SPREAD = 0.020

# Arm C. Declared areas follow the PROJECTED convention: median |declared/projected - 1| = 0.00105
# against 0.00417 for geodesic, and 112 of 232 land within 0.1% against 20. Requiring a factor of two
# states the choice without pinning the exact numbers, which move as declared areas are corrected.
MIN_CONVENTION_MARGIN = 2.0

LAT_BANDS = [(0, 10), (10, 20), (20, 30), (30, 40), (40, 50), (50, 60), (60, 90)]


def main() -> int:
    try:
        import geopandas as gpd
    except ImportError as exc:
        print(f"FAIL: geopandas unavailable ({exc})")
        return 1
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from repair_s2_polygons import geodesic_area_km2
    except ImportError as exc:
        print(f"FAIL: the geodesic side is unreachable ({exc}). Both conventions must be measurable "
              "here, or this gate cannot tell which one the published figures follow")
        return 1

    frame = gpd.read_file(GPKG)
    frame = frame[frame.geometry.notna() & ~frame.geometry.is_empty].copy()
    projected = frame.to_crs("ESRI:54034").geometry.area / 1e6
    lat = frame.geometry.centroid.y.abs()

    rows = []
    for idx, r in frame.iterrows():
        p = float(projected.loc[idx])
        try:
            g = float(geodesic_area_km2(r.geometry))
        except Exception:
            continue
        if p > 0 and g > 0:
            rows.append((float(lat.loc[idx]), p / g, r["polity_code"], p, g))
    if not rows:
        print("FAIL: no polygon could be measured both ways")
        return 1

    problems = []
    ratios = [x[1] for x in rows]
    med, lo, hi = statistics.median(ratios), min(ratios), max(ratios)
    print(f"{len(rows)} polygons measured both ways")
    print(f"A. projected/geodesic median {med:.5f} (envelope {MEDIAN_LO}-{MEDIAN_HI}), "
          f"spread {lo:.5f}-{hi:.5f}")
    if not MEDIAN_LO <= med <= MEDIAN_HI:
        problems.append(
            f"projected/geodesic median is {med:.5f}, outside {MEDIAN_LO}-{MEDIAN_HI}. One of the two "
            f"measurements has changed what it computes -- the gap between the conventions is about "
            f"0.4% and this envelope is wider than any polygon edit should move it")
    if hi - lo > MAX_SPREAD:
        problems.append(f"the two conventions now span {hi - lo:.4f}, above {MAX_SPREAD}")

    print("B. by |centroid latitude| -- the great-circle-versus-straight-line signature:")
    medians = []
    for b0, b1 in LAT_BANDS:
        v = [x[1] for x in rows if b0 <= x[0] < b1]
        if len(v) < 5:
            continue
        m = statistics.median(v)
        medians.append(((b0, b1), m, len(v)))
        print(f"     {b0:2}-{b1:2} deg  n={len(v):4}  median {m:.5f}")
    breaks = [f"{a[0][0]}-{a[0][1]} ({a[1]:.5f}) > {b[0][0]}-{b[0][1]} ({b[1]:.5f})"
              for a, b in zip(medians, medians[1:]) if a[1] > b[1]]
    if breaks:
        problems.append(
            "the ratio no longer rises monotonically with latitude, which is the signature that "
            "identifies this as a straight-line-versus-great-circle difference rather than a bug in "
            "either method: " + "; ".join(breaks[:3]))

    # DECLARED AREAS COME FROM THE GEOPACKAGE, not the CSV. Both numbers in this comparison must
    # come from the same artefact, or the gate can compare a declared area from one build against a
    # geometry from another and call the difference a convention. `validate_polygons.py` reads them
    # from the .gpkg for the same reason. Found by the selftest: the first version read the CSV, the
    # case rewrote the .gpkg, and the gate passed a mutation that changed every declared area.
    declared = {}
    for _, r in frame.iterrows():
        try:
            v = float(r.get("polygon_area_km2"))
        except (TypeError, ValueError):
            continue
        if v > 0:
            declared[r["polity_code"]] = v
    dp = [abs(declared[c] / p - 1) for _, _, c, p, _ in rows if c in declared]
    dg = [abs(declared[c] / g - 1) for _, _, c, _, g in rows if c in declared]
    if not dp:
        problems.append("no polity declares an area, so which convention they follow cannot be read")
    else:
        mp, mg = statistics.median(dp), statistics.median(dg)
        near_p = sum(1 for x in dp if x <= 0.001)
        near_g = sum(1 for x in dg if x <= 0.001)
        print(f"C. {len(dp)} declared areas: median deviation {mp:.5f} from PROJECTED, {mg:.5f} from "
              f"geodesic; within 0.1% {near_p} vs {near_g}")
        if mp <= 0 or mg / mp < MIN_CONVENTION_MARGIN:
            problems.append(
                f"declared areas no longer track the projected convention by a clear margin "
                f"({mg:.5f} geodesic vs {mp:.5f} projected, ratio {mg / max(mp, 1e-9):.2f}x, "
                f"needs {MIN_CONVENTION_MARGIN}x). Either the published figures were recomputed on "
                f"the other convention -- which moves polygon_area_km2 and ratio_polygon_over_stated "
                f"for hundreds of rows -- or the convention this repo means by `the polygon's area` "
                f"is no longer the one its scripts measure")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print("  " + p)
        return 1
    print("\nPASS: both conventions measurable, their difference is the documented latitude "
          "signature, and the published areas follow the projected one")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
