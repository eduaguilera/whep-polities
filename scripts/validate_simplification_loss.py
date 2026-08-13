#!/usr/bin/env python3
"""Check every shipped polygon against the UNSIMPLIFIED source polygon it was cut from.

WHY THIS EXISTS (issue 71). `polygon_area_km2` is compared, by `validate_polygons` check A,
against the geometry this repository SHIPS -- and the shipped geometry is not the source
polygon. `build_database.py` runs three passes over it before writing: Douglas-Peucker
simplification (to bound the GeoPackage's size), densification of planar edges (so a
spherical consumer sees the border the source drew), and a conditional validity repair.
Only the first of those was ever capable of moving real area, and it did:

    MDV-1800-2025   GADM 4.1 adm0, 791 atolls   299.68 km2 at source, 172.62 km2 shipped

That is -42% on a polygon that is correct. Nothing detected it, because check A skips rows
where both the claimed and the measured area are under --min-km2 200 -- which is every
archipelago small enough for 0.01 degrees of thinning to matter, by construction. So the
Maldives page could declare 299.68 and fail check A on a correct polygon, or declare
172.62 and understate the country by 42%. Issue 71's phrasing: the field was unfillable.

THE GEOMETRY HALF IS ALREADY FIXED, by the area budget in `build_database.py`
(`SIMPLIFY_MAX_AREA_CHANGE`, 2026-08-10): simplification now walks down a ladder of
tolerances and keeps the original if even the finest step costs too much. Measured across
all 735 shipped polygons on 2026-08-13, shipped against source: max loss 2.1%, nothing
above 5%, the Maldives at 0.0%.

THIS GATE IS THE ASSERTION THAT IT STAYS FIXED. The budget is a constant in a build
script, enforced nowhere, and a regression in it is invisible to every other gate here:
the loss is silent in the plane, conserves nothing detectable, and lands exactly on the
rows check A exempts. What makes the check possible without `data/geodata` -- which is
gitignored, so CI never has it -- is that `data/final/polygon_feature_index.csv` already
publishes each source feature's area, computed by `write_feature_index.py` straight from
the raw source BEFORE any of the build's three passes. That is the reference.

WHAT IT DOES NOT DO. It says nothing about whether the binding is the right feature (check
B and `validate_spatial_containment` do), and nothing about whether `polygon_area_km2` is
a good figure (checks A and A2 do). It asserts one thing: THE POLYGON WE PUBLISH IS THE
POLYGON WE READ. With that guaranteed to 5%, check A's 25% tolerance tests the territory
rather than the rendering, which is what issue 71 asked to be decided.

THE TOLERANCE IS NOT THE BUILD'S BUDGET, and the difference is measured rather than
assumed. `SIMPLIFY_MAX_AREA_CHANGE` is 2% enforced on `OGRGeometry.GetArea()` -- PLANAR
degrees squared -- while this gate measures km2 in an equal-area projection, and the two
disagree: RNAM-1850-2025 loses 2.11% here against a 2% budget it passed. Densification
also moves area the other way, by bowing each straight edge onto the great circle a
spherical consumer draws (LIE-1800-2025 +1.9%, AND-1800-2025 +1.9%). So the gate is set
at 5%: above every legitimate movement measured today with margin for both effects, an
order of magnitude below the 42% the defect produced, and well inside check A's 25%.

Usage:
  python3 scripts/validate_simplification_loss.py [--tolerance 0.05]
"""
import argparse
import collections
import csv
import os
import sys
import warnings

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
INDEX = os.path.join(REPO, "data/final/polygon_feature_index.csv")

# THE SAME PROJECTION STRING write_feature_index.py USES, deliberately, not ESRI:54034.
# The reference areas in the index were computed with this proj4 definition; measuring the
# shipped geometry in a different equal-area projection would fold a datum difference into
# every row's "loss". The two happen to agree here to three decimals on all 735 rows
# (checked 2026-08-13), but agreeing by measurement is not the same as agreeing by
# construction, and only the second is safe to gate on.
EQUAL_AREA = "+proj=cea +lat_ts=0 +lon_0=0 +units=m"

# The index rounds each area to one decimal (`round(area/1e6, 1)`), so a small polygon's
# reference figure carries up to half a unit of quantisation. On VAT-1929-2025 -- 0.53 km2
# published against 0.5 recorded -- that alone is 5.3%, which would have been this gate's
# largest "loss" and is entirely an artefact of the file it reads. Allowed for explicitly
# rather than papered over with a minimum-size cutoff, because a cutoff would exempt the
# microstates that are the whole point of issue 71.
INDEX_ROUNDING_KM2 = 0.05


def load_index():
    """Source areas by (source, feature_id). A key can hold several candidates: a temporal
    source lists one feature per time-step under the same id."""
    idx = collections.defaultdict(list)
    if not os.path.exists(INDEX):
        return idx
    with open(INDEX, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            a = (r.get("area_km2") or "").strip()
            if not a:
                continue
            try:
                idx[((r.get("source") or "").strip(), (r.get("feature_id") or "").strip())
                    ].append(float(a))
            except ValueError:
                continue
    return idx


def candidates(idx, source, fid):
    """Every recorded source area for this binding, tolerating the `.0` that a float-typed
    id column leaves on an integer feature id."""
    out = list(idx.get((source, fid), ()))
    if not out and fid.endswith(".0"):
        out = list(idx.get((source, fid[:-2]), ()))
    if not out:
        try:
            out = list(idx.get((source, str(int(float(fid)))), ()))
        except (TypeError, ValueError):
            pass
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tolerance", type=float, default=0.05,
                    help="fractional area movement tolerated between the source polygon "
                         "and the one we ship")
    A = ap.parse_args()

    try:
        import geopandas as gpd
    except ImportError as exc:
        print(f"SKIP: geopandas unavailable ({exc})")
        return 0
    if not os.path.exists(GPKG):
        print(f"FAIL: {GPKG} missing; run scripts/build_database.py first")
        return 1
    idx = load_index()
    if not idx:
        print(f"FAIL: {INDEX} missing or carries no areas; run "
              f"scripts/write_feature_index.py")
        return 1

    g = gpd.read_file(GPKG)
    g = g[g.geometry.notna() & ~g.geometry.is_empty].copy()
    g["shipped_km2"] = g.to_crs(EQUAL_AREA).geometry.area / 1e6

    rows = []
    unreferenced = []
    for r in g.itertuples():
        src = str(getattr(r, "polygon_source", "") or "").strip()
        fid = str(getattr(r, "polygon_feature_id", "") or "").strip()
        cands = candidates(idx, src, fid) if src and src != "none" and fid else []
        if not cands:
            unreferenced.append((r.polity_code, src, fid))
            continue
        # "There EXISTS a source candidate this polygon could be": a temporal source lists
        # several features under one id and this gate is not the one that decides which was
        # chosen (validate_polygon_binding_determinism is). Taking the closest keeps a
        # genuinely ambiguous binding from reading as an area defect.
        best = min(cands, key=lambda a: abs(r.shipped_km2 - a) / a if a > 0 else 9e9)
        if best <= 0:
            continue
        dev = (r.shipped_km2 - best) / best
        allowed = A.tolerance + INDEX_ROUNDING_KM2 / best
        rows.append((r.polity_code, src, fid, best, r.shipped_km2, dev, allowed))

    over = sorted((t for t in rows if abs(t[5]) > t[6]), key=lambda t: -abs(t[5]))
    print(f"{len(rows)} shipped polygon(s) compared against their source area; "
          f"{len(unreferenced)} not present in the feature index")
    for t in (0.25, 0.10, 0.05, 0.02, 0.01):
        n = sum(1 for x in rows if abs(x[5]) > t)
        print(f"   |movement| > {t:>4.0%}: {n}")

    worst = sorted(rows, key=lambda t: -abs(t[5]))[:8]
    print("\n   largest movements (source -> shipped), all within tolerance unless "
          "marked FAIL:")
    for code, src, fid, s, sh, dev, allowed in worst:
        print(f"     {dev*100:+7.2f}%  {code:18s} {s:>12,.1f} -> {sh:>12,.1f} km2  "
              f"({src}/{fid})")

    if over:
        print(f"\nFAIL: {len(over)} polygon(s) moved more than the tolerance between the "
              f"source and the file we publish")
        for code, src, fid, s, sh, dev, allowed in over:
            print(f"   FAIL {dev*100:+7.2f}%  {code:18s} source {s:>12,.1f} km2, "
                  f"shipped {sh:>12,.1f} km2  ({src}/{fid}), allowed {allowed:.1%}")
        print("\n  A polygon that does not measure what its source measures makes "
              "`polygon_area_km2`\n"
              "  unfillable: the page can state the truth about the territory and fail "
              "check A, or\n"
              "  state what the rendering measures and understate the territory. That is "
              "issue 71.\n"
              "  Usual cause: the simplification budget in build_database.py "
              "(SIMPLIFY_MAX_AREA_CHANGE\n"
              "  / SIMPLIFY_LADDER) no longer holds for this feature. Do not raise this "
              "tolerance to\n"
              "  accommodate it -- fix the build, or publish the geometry unsimplified.")

    if unreferenced:
        print(f"\nFAIL: {len(unreferenced)} shipped polygon(s) have no entry in "
              f"data/final/polygon_feature_index.csv, so no source area exists to compare "
              f"them against")
        for code, src, fid in unreferenced[:12]:
            print(f"   FAIL {code:18s} ({src}/{fid})")
        print("\n  Run python3 scripts/write_feature_index.py with the polygon sources "
              "fetched. This\n"
              "  arm exists because write_feature_index.py --check SKIPS in CI, where "
              "data/geodata is\n"
              "  absent -- so a new binding added without regenerating the index is "
              "otherwise unseen.")

    if not over and not unreferenced:
        print(f"\nPASS: every shipped polygon is within {A.tolerance:.0%} of the source "
              f"polygon it was cut from")
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
