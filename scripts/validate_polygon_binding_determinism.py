#!/usr/bin/env python3
"""Find polygon bindings whose chosen feature depends on shapefile row order.

THE MECHANISM. `build_database.find_feature()` collects every feature matching the
declared `polygon_feature_id`, filters by `polygon_feature_year` under the source's
`match_year` policy, then breaks ties:

    exact = [f for f, s in candidates if s == feature_year]
    if exact:
        return exact[0]        # <- FIRST of possibly several
    return candidates[0][0]    # <- FIRST of possibly several

So a binding is ORDER-DEPENDENT whenever more than one candidate survives and the
tie-break cannot single one out -- either two or more candidates start in the queried
year, or none does. The winner is then whichever the shapefile happens to list first,
which is not a modelling decision anybody made.

WHY IT MATTERS: this is the same bug three times, each found by hand and each after it
had shipped.

  issue 45  RUS-1991-2014 carried the USSR polygon. `polygon_feature_year: 1991`
            matched six CShapes steps for gwcode 365 and order picked the 21,824,142 km2
            one against Russia's 17,098,242. It geometrically contained Kazakhstan,
            Ukraine, the Baltics, Georgia and Azerbaijan.
  issue 92  SRB-2008-2025 carried Kosovo for seventeen years, double-counting 10,735 km2
            against a live KOS-2008-2025.
  issue 99  VNM-1887-1954 measured 379,770 km2 against its own declared 326,024.
            gwcode 815 has THREE steps containing 1893 and TWO of them start in 1893,
            so the tie-break could not decide. The page's Decisions section had asked
            for the post-Laos-transfer extent and the mechanism handed back the
            pre-transfer one.

Each was caught by a different accident -- a containment sweep, a sibling overlap, a
magnitude cross-check. None was caught by asking the only question that generalises:
COULD THIS BINDING HAVE GONE ANOTHER WAY?

WHAT THIS DOES NOT CHECK. Whether the chosen polygon is correct. A deterministic binding
can still be wrong, and `validate_polygons` and `validate_spatial_containment` are the
checks for that. This one asks only whether the choice was made by the data or by the
row order, because a binding decided by row order is not reproducible across a source
re-fetch.

Usage:
  python3 scripts/validate_polygon_binding_determinism.py
"""
import csv
import os
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")
SOURCES = os.path.join(REPO, "scripts/sources.yaml")
DEAD = ("retired", "superseded")

# Bindings known to be order-dependent and deliberately left so, each with the reason.
# Bidirectional: a new one fails, and one that becomes deterministic must be removed.
BASELINE = {
    # ---- candidates are IDENTICAL in area, so order-dependence is harmless today ----
    # These still deserve pinning eventually: an upstream re-fetch that changes one of
    # the duplicate steps would make them differ, silently and without a code change.
    "GNB-1879-1886": "2 identical candidates at year 1886, all 33,242 km2 -- no geometry at stake",
    "GNB-1886-1974": "2 identical candidates at year 1886, all 33,242 km2 -- no geometry at stake",
    "IRQ-1921-1932": "3 identical candidates at year 1932, all 436,255 km2 -- no geometry at stake",
    "IRQ-1932-2025": "3 identical candidates at year 1932, all 436,255 km2 -- no geometry at stake",
    "JOR-1918-1920": "2 identical candidates at year 1920, all 45,148 km2 -- no geometry at stake",
    "JOR-1920-1923": "2 identical candidates at year 1920, all 45,148 km2 -- no geometry at stake",
    "LBN-1920-1944": "2 identical candidates at year 1920, all 10,209 km2 -- no geometry at stake",
    "MWI-1964-2025": "2 identical candidates at year 1964, all 118,484 km2 -- no geometry at stake",
    "PAL-1920-1948": "2 identical candidates at year 1920, all 26,964 km2 -- no geometry at stake",

    # ---- candidates DIFFER: a re-fetch could hand back another polygon ----
    # Enumerated with the spread and what was actually picked. Issue 100.
    "ROU-1918-1919": "3 candidates at year 1920 spanning 148,934-296,087 km2 (1.99x); picked 251,719, declared 295,000",
    "ROU-1920-1940": "3 candidates at year 1920 spanning 148,934-296,087 km2 (1.99x); picked 251,719, no declared area",
    "POL-1919-1920": "3 candidates at year 1919 spanning 130,205-256,575 km2 (1.97x); picked 177,762, declared 177,754",
    "F51-1938-1945": "3 candidates at year 1938 spanning 100,822-140,398 km2 (1.39x); picked 116,616, no declared area",
    "ROU-1940-1947": "3 candidates at year 1940 spanning 237,379-296,087 km2 (1.25x); picked 245,066, declared 194,000",
    "KEN-1907-1924": "2 candidates at year 1907 spanning 635,868-772,550 km2 (1.21x); picked 772,550, no declared area",
    "USA-1959-2025": "3 candidates at year 1959 spanning 7,939,971-9,462,898 km2 (1.19x); picked 9,446,212, no declared area",
    "NAM-1886-1915": "2 candidates at year 1886 spanning 699,762-824,759 km2 (1.18x); picked 699,762, no declared area",
    "ROU-1919-1920": "3 candidates at year 1919 spanning 128,499-148,934 km2 (1.16x); picked 141,247, no declared area",
    "MLI-1960-2025": "3 candidates at year 1960 spanning 1,252,292-1,448,287 km2 (1.16x); picked 1,252,292, no declared area",
    "TUR-1918-1920": "3 candidates at year 1918 spanning 1,657,471-1,731,860 km2 (1.04x); picked 1,731,860, no declared area",
    "SYR-1920-1922": "2 candidates at year 1920 spanning 182,452-188,004 km2 (1.03x); picked 182,452, no declared area",
    "F228-1918-1920": "5 candidates at year 1918 spanning 21,405,134-21,760,482 km2 (1.02x); picked 21,676,599, no declared area",
    "F228-1920-1921": "4 candidates at year 1920 spanning 21,405,134-21,700,852 km2 (1.01x); picked 21,506,736, no declared area",
    "F228-1940-1945": "4 candidates at year 1940 spanning 21,552,704-21,828,529 km2 (1.01x); picked 21,606,391, no declared area",
    "F228-1945-1991": "3 candidates at year 1945 spanning 21,828,529-22,065,965 km2 (1.01x); picked 22,033,900, no declared area",
}


def main() -> int:
    try:
        from osgeo import ogr
        ogr.UseExceptions()
    except ImportError as exc:
        print(f"SKIP: GDAL unavailable ({exc})")
        return 0

    with open(SOURCES, encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh).get("sources", {})

    with open(CSV_PATH, encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["wiki_status"] not in DEAD]

    # Cache each source's features as (id_value, start_year, end_year), in FILE ORDER --
    # the order is the whole point, so it must not be sorted.
    cache = {}
    missing_sources = set()

    def features(slug):
        if slug in cache:
            return cache[slug]
        entry = cfg.get(slug)
        if entry is None:
            return None
        path = os.path.join(REPO, entry["file"])
        if not os.path.exists(path):
            missing_sources.add(slug)
            cache[slug] = None
            return None
        ds = ogr.Open(path)
        lyr = ds.GetLayer()
        temporal = entry.get("temporal") or {}
        out = []
        lyr.ResetReading()
        for feat in lyr:
            v = feat.GetField(entry["id_column"])
            s = e = None
            if temporal:
                sv = feat.GetField(temporal["start_column"])
                ev = feat.GetField(temporal["end_column"])
                if sv is not None and ev is not None:
                    s, e = int(str(sv)[:4]), int(str(ev)[:4])
            out.append((v, s, e))
        cache[slug] = (out, entry, temporal)
        return cache[slug]

    problems = []
    observed = {}
    checked = 0

    for r in rows:
        slug = (r.get("polygon_source") or "").strip()
        fid = (r.get("polygon_feature_id") or "").strip()
        if not slug or slug == "none" or not fid:
            continue
        got = features(slug)
        if got is None:
            continue
        feats, entry, temporal = got
        fyear = r.get("polygon_feature_year")
        try:
            fyear = int(float(fyear))
        except (TypeError, ValueError):
            fyear = None
        if entry.get("id_type") == "int":
            try:
                want = int(fid)
            except ValueError:
                continue
            same = [(v, s, e) for v, s, e in feats if v is not None and int(v) == want]
        else:
            same = [(v, s, e) for v, s, e in feats if str(v) == fid]
        checked += 1
        if not same:
            continue

        cands = same
        if temporal and fyear is not None:
            policy = temporal.get("match_year", "within")
            if policy == "within":
                cands = [(v, s, e) for v, s, e in same
                         if s is not None and e is not None and s <= fyear <= e]
            elif policy == "exact_start":
                cands = [(v, s, e) for v, s, e in same if s == fyear]
        if len(cands) < 2:
            continue

        exact = [c for c in cands if c[1] == fyear] if fyear is not None else []
        if len(exact) == 1:
            continue        # the tie-break resolves it

        why = ("no candidate starts in the queried year, so the FIRST of "
               f"{len(cands)} is taken"
               if not exact else
               f"{len(exact)} candidates start in the queried year, so the FIRST is taken")
        observed[r["polity_code"]] = why
        if r["polity_code"] not in BASELINE:
            spans = ", ".join(f"{s}-{e}" for _v, s, e in cands[:6])
            problems.append(
                f"{r['polity_code']}: {slug} id={fid!r} year={fyear} -- {why}. "
                f"Candidate spans: {spans}"
                + (" ..." if len(cands) > 6 else "")
            )

    # The reverse direction, but ONLY for rows whose source was actually readable.
    # Absence of an observation is not evidence of a fix: when data/geodata is not
    # fetched, every source returns nothing and every baselined code would be reported
    # as resolved. That is exactly what happened the first time this gate ran inside the
    # selftest's scratch repo -- it failed with 25 spurious "no longer order-dependent"
    # lines and named none of the real defect.
    checkable = {
        r["polity_code"] for r in rows
        if (r.get("polygon_source") or "").strip() not in missing_sources
    }
    for code in sorted((set(BASELINE) & checkable) - set(observed)):
        problems.append(
            f"{code} is baselined as order-dependent but is not any more -- remove it"
        )
    unverifiable = sorted(set(BASELINE) - checkable)
    if unverifiable:
        print(f"baselined but unverifiable, source not fetched: {len(unverifiable)}")

    print(f"bindings resolved against a source: {checked}")
    print(f"order-dependent: {len(observed)}")
    if missing_sources:
        print(f"sources not fetched, so unchecked: {sorted(missing_sources)}")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        print("\n  A binding decided by shapefile row order is not reproducible: a source\n"
              "  re-fetch can silently hand back a different polygon. Pin it by choosing a\n"
              "  polygon_feature_year that falls inside exactly one candidate span.")
        return 1

    print("\nPASS: every binding is decided by the data, not by row order")
    return 0


if __name__ == "__main__":
    sys.exit(main())
