#!/usr/bin/env python3
"""Check that site/ still describes the database it is generated from.

`site/build_wiki.sh` trims and simplifies the master GeoPackage for in-browser display, and
`.github/workflows/pages.yml` DEPLOYS `site/**` whenever it changes. So `site/` is published
output -- and until this gate existed, nothing compared it to the database at all. The word
`site/` appeared in exactly one workflow, the one that publishes it.

WHAT THAT COST, measured on 2026-08-10 (issue 146):

    site/polities.geojson last regenerated   2026-06-11
    features it carried                      561
    live polities with geometry               681
    live codes missing from the site         194
    retired/superseded polities DRAWN          35

Two independent defects in one file, which is why one check is not enough:

  1. STALE. Two months of polygon work -- including every geometry repair, the s2 fixes, and
     four new polities -- never reached the site. A viewer looking at the map was reading June.

  2. WITHDRAWN ROWS WERE DRAWN. `build_wiki.sh` converted the whole GeoPackage, and the
     GeoPackage carries geometry for dead rows too. `index.html` reads `wiki_status` for the
     colour legend and the status badge but never FILTERS on it, so `ARG-1800-2025`
     (superseded) drew Argentina a second time over ARG's real periods, and three retired
     Canadas drew over Canada. The map claimed the same ground twice for a reason that has
     nothing to do with territory. Nobody would see this by reading either file: the CSV is
     correct, the GeoPackage is correct, and the defect is in what the converter chose to keep.

THE CONTRACT, asserted rather than described:

    A. site/polities.csv is byte-identical to data/final/polities_database.csv (it is a `cp`)
    B. site/polities.geojson holds EXACTLY the live rows carrying polygonal geometry
    C. no feature in site/polities.geojson is retired or superseded

B is an equality, not a subset in either direction, so it catches both directions of drift:
a stale site (missing live codes) and a site built from a newer database than the committed
one (codes the database no longer has).

Geometry is deliberately NOT compared. `build_wiki.sh` simplifies rings to 80 points, drops
parts under 0.1 square degrees and splits antimeridian polygons, all on purpose -- comparing
coordinates would fail on every run and teach people to ignore this. What must not drift is
WHICH polities the site claims to show.

Usage:
  python3 scripts/validate_site_outputs.py
"""
from __future__ import annotations

import csv
import json
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_CSV = os.path.join(REPO, "data/final/polities_database.csv")
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
SITE_CSV = os.path.join(REPO, "site/polities.csv")
SITE_GEOJSON = os.path.join(REPO, "site/polities.geojson")

DEAD = ("retired", "superseded")
REBUILD = "  rebuild: bash site/build_wiki.sh"


def live_with_geometry() -> set:
    """Codes the site is expected to draw: live rows whose GeoPackage geometry is polygonal."""
    import warnings

    warnings.filterwarnings("ignore")
    import geopandas as gpd

    g = gpd.read_file(GPKG)
    g = g[g.geometry.notna() & ~g.geometry.is_empty]
    g = g[~g.wiki_status.astype(str).str.strip().isin(DEAD)]
    return set(g.polity_code)


def main() -> int:
    for path in (DB_CSV, GPKG, SITE_CSV, SITE_GEOJSON):
        if not os.path.exists(path):
            print(f"FAIL: {os.path.relpath(path, REPO)} missing")
            return 2

    problems = []

    # A ------------------------------------------------------------------------------------
    with open(DB_CSV, encoding="utf-8") as fh:
        master = fh.read()
    with open(SITE_CSV, encoding="utf-8") as fh:
        shipped = fh.read()
    if master.replace("\r\n", "\n") != shipped.replace("\r\n", "\n"):
        m, s = len(master.splitlines()), len(shipped.splitlines())
        problems.append(
            f"site/polities.csv differs from the master CSV ({s} lines vs {m}) -- it is a "
            f"straight copy, so any difference means the site was built from another database"
        )

    # B and C -----------------------------------------------------------------------------
    with open(SITE_GEOJSON, encoding="utf-8") as fh:
        geo = json.load(fh)
    feats = geo.get("features", [])
    shown, withdrawn = set(), []
    for f in feats:
        props = f.get("properties") or {}
        code = props.get("polity_code")
        if code:
            shown.add(code)
        if (props.get("wiki_status") or "").strip() in DEAD:
            withdrawn.append(code)

    expected = live_with_geometry()
    missing = sorted(expected - shown)
    extra = sorted(shown - expected)

    print(f"site/polities.geojson features: {len(feats)}")
    print(f"live polities with geometry:     {len(expected)}")
    print(f"missing from the site:           {len(missing)}")
    print(f"present but not expected:        {len(extra)}")
    print(f"retired/superseded drawn:        {len(withdrawn)}")

    if missing:
        problems.append(
            f"{len(missing)} live polities with geometry are not in site/polities.geojson, "
            f"e.g. {', '.join(missing[:5])} -- the site is behind the database"
        )
    if extra:
        problems.append(
            f"{len(extra)} features are not live polities with geometry, e.g. "
            f"{', '.join(extra[:5])} -- the site is ahead of, or diverged from, the database"
        )
    if withdrawn:
        problems.append(
            f"{len(withdrawn)} retired/superseded polities are drawn on the map, e.g. "
            f"{', '.join(sorted(c for c in withdrawn if c)[:5])} -- index.html colours by "
            f"wiki_status but does not filter on it, so each one is rendered over the rows "
            f"that replaced it"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        print(f"\n{REBUILD}")
        return 1

    print("\nPASS: site/ shows exactly the live polities that carry geometry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
