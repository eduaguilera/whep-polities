#!/usr/bin/env python3
"""Check that a polity's measured area resembles its own family's other periods.

Check A in validate_polygons.py compares a polity's RECORDED area against its measured one, and it
is the check that found eight polities carrying another country's polygon — San Marino with
Albania's, 470x too large. But it can only run where a recorded area exists, and 520 of the 684 live
polities claiming a polygon (76%) have none. For those, a mis-binding has nothing to contradict it.

This needs no external reference. A polity that has picked up the wrong country's geometry will
usually be wildly out of scale with the OTHER periods of its own family, which is a comparison the
database can make against itself. It covers every row with geometry, including the 520.

Two families exceed 5x today and both are legitimate, which is why they are baselined rather than
fixed:

  COG-1900-1906   2,234,449 km2 against a family median of 343,962. All six COG rows bind to the
                  same CShapes feature 484 at DIFFERENT vintage years — 1886, 1898, 1900, 1906,
                  1919, 1960 — and this row uses the 1898 vintage, when French Congo still included
                  what became Chad, CAR and Gabon. The large extent is historically right; the
                  median is dominated by the later, smaller periods.
  ERI-1885-1889   19,031 km2 against 120,803. The row is named "Eritrea (Italian coastal,
                  1885-1889)" and is deliberately just the coastal strip.

Both explanations are visible in the data — a vintage year and a polity name — which is the point:
the check flags a scale anomaly and the reason is then one field away.

Usage:
  python3 scripts/validate_family_areas.py [--ratio 5.0]
"""
import argparse
import csv
import os
import re
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES_CSV = os.path.join(REPO, "data/final/polities_database.csv")
POLITIES_GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")

DEAD_STATUS = ("retired", "superseded")

# Family periods whose area is legitimately out of scale. See the docstring.
#
# COG-1900-1906 -> COG-1898-1900 on 2026-08-05 (issue 123). The anomaly did not go away, it
# MOVED -- and where it moved to is the point. All four Congo rows from 1898 to 1919 were
# bound to their PREDECESSOR's CShapes step, so the 2.23M km2 French-Congo-at-its-widest
# polygon sat on the 1900-1906 row and this baseline recorded it there. With the lag fixed
# it sits on COG-1898-1900, which is the period that genuinely covered the whole
# Congo-Ubangi basin before the 1900s reorganisation.
#
# So this entry was previously pinning a real anomaly to the WRONG ROW, and reading it as
# "1900-1906 is legitimately large" would have been reading a binding error as history.
BASELINE = frozenset({"COG-1898-1900", "ERI-1885-1889"})

CODE_RE = re.compile(r"^(.*)-\d{4}-\d{4}$")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ratio", type=float, default=5.0)
    args = ap.parse_args()

    try:
        import geopandas as gpd
        from shapely.validation import make_valid
    except ImportError as exc:
        print(f"FAIL: geopandas/shapely unavailable ({exc})")
        return 2
    if not os.path.exists(POLITIES_GPKG):
        print(f"FAIL: {POLITIES_GPKG} missing; run scripts/build_database.py first")
        return 2

    dead = {
        r["polity_code"]
        for r in csv.DictReader(open(POLITIES_CSV, encoding="utf-8"))
        if (r.get("wiki_status") or "").strip() in DEAD_STATUS
    }

    frame = gpd.read_file(POLITIES_GPKG)
    frame = frame[~frame.geometry.isna() & ~frame.geometry.is_empty].copy()
    frame["geometry"] = frame.geometry.map(make_valid)
    equal_area = frame.to_crs("ESRI:54034")
    measured = dict(zip(frame["polity_code"], equal_area.geometry.area / 1e6))

    families = defaultdict(list)
    for code, km2 in measured.items():
        if code in dead:
            continue
        m = CODE_RE.match(code)
        if m:
            families[m.group(1)].append((code, km2))

    multi = {k: v for k, v in families.items() if len(v) > 1}
    observed = set()
    detail = {}
    for items in multi.values():
        areas = sorted(a for _, a in items)
        median = areas[len(areas) // 2]
        if median <= 0:
            continue
        for code, km2 in items:
            ratio = max(km2, median) / max(min(km2, median), 1e-9)
            if ratio >= args.ratio:
                observed.add(code)
                detail[code] = (ratio, km2, median, len(items))

    print(f"families with more than one geometry: {len(multi)}")
    print(f"periods at least {args.ratio}x from their family median: {len(observed)}")
    for code in sorted(observed, key=lambda c: -detail[c][0]):
        ratio, km2, median, n = detail[code]
        print(
            f"   {ratio:>7.1f}x  {code:<18}{km2:>12,.0f} km2  vs median {median:>12,.0f}"
            f"  ({n} periods)"
        )

    problems = []
    for code in sorted(observed - BASELINE):
        ratio, km2, median, _ = detail[code]
        problems.append(
            f"NEW area anomaly: {code} measures {km2:,.0f} km2 against a family median of "
            f"{median:,.0f} ({ratio:.1f}x) — check its polygon_feature_id and "
            f"polygon_feature_year before assuming the geometry is right"
        )
    for code in sorted(BASELINE - observed):
        problems.append(
            f"{code} is baselined as an area anomaly but no longer is — remove it from the baseline"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: family area anomalies match the baseline exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
