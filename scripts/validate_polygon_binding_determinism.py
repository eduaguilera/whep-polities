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

    # FIXED and removed 2026-08-05 (issue 100):
    #   ROU-1940-1947  the one entry no polygon_feature_year could have fixed: its step spans
    #                  exactly {1940} and both neighbours contain 1940. Resolved instead by
    #                  BUILDING the polygon it needed -- post-war Romania MINUS an
    #                  eight-county Northern Transylvania proxy -- which measures 193,855 km2
    #                  against its declared 194,000 (0.07%). It is no longer cshapes-bound,
    #                  so it leaves this check's population entirely. Issues 12, 106.
    #   NAM-1886-1915  picked 699,762 of {699,762, 824,760}; German South West Africa was
    #                  825,615 km2, so it was short by 124,998. feature_year 1886 -> 1887.
    #   ROU-1918-1919  picked 251,719 of {148,934, 251,719, 296,087} while its own page and
    #                  its polygon_area_km2 both said ~295,000 -- a 15% shortfall against
    #                  its documented intent. feature_year 1920 -> 1921.
    # Both were chosen because TWO candidates started in the queried year, which is the
    # tie the tie-break cannot break.
    #
    # ---- candidates DIFFER: a re-fetch could hand back another polygon ----
    # Enumerated with the spread and what was actually picked. Issue 100.
    # ROU-1920-1940 removed 2026-08-05: order-dependence RESOLVED by moving
    # polygon_feature_year 1920 -> 1921, which falls inside exactly one candidate span.
    # The row order had been picking 251,719 km2 over the correct 296,087 -- Bessarabia
    # missing for all 20 interwar years and 1,087 data rows. This baseline entry recorded
    # the non-determinism for 21 rows; it turned out to also be recording a live 15% error.
    "POL-1919-1920": "3 candidates at year 1919 spanning 130,205-256,575 km2 (1.97x); picked 177,762, declared 177,754",
    "F51-1938-1945": "3 candidates at year 1938 spanning 100,822-140,398 km2 (1.39x); picked 116,616, no declared area",
    "KEN-1907-1924": "2 candidates at year 1907 spanning 635,868-772,550 km2 (1.21x); picked 772,550, no declared area",
    "USA-1959-2025": "3 candidates at year 1959 spanning 7,939,971-9,462,898 km2 (1.19x); picked 9,446,212, no declared area",
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

    # PREFER THE COMMITTED INDEX (issue 103). data/geodata/** is gitignored, so reading the
    # shapefiles makes this gate inert in CI -- it verified nothing there, exited 0, and had
    # to lose its selftest case because the harness rightly called that a gate that cannot
    # fail. data/final/polygon_feature_index.csv carries the same candidates with their file
    # order, written by scripts/write_feature_index.py and kept honest by its --check.
    #
    # The shapefile is still used when the index lacks a source, so a newly fetched source
    # is covered before anyone regenerates the index.
    index = {}
    index_path = os.path.join(REPO, "data/final/polygon_feature_index.csv")
    if os.path.exists(index_path):
        with open(index_path, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                def num(v):
                    try:
                        return int(float(v))
                    except (TypeError, ValueError):
                        return None
                index.setdefault(row["source"], []).append(
                    (row["feature_id"], num(row["start_year"]), num(row["end_year"]))
                )

    # Cache each source's features as (id_value, start_year, end_year), in FILE ORDER --
    # the order is the whole point, so it must not be sorted.
    cache = {}
    missing_sources = set()

    def features(slug):
        if slug in index:
            entry = cfg.get(slug)
            if entry is not None:
                return index[slug], entry, (entry.get("temporal") or {})
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

    if checked == 0:
        print("SKIP: no polygon source is fetched, so no binding could be resolved.")
        print("  This gate needs data/geodata/**, which is GITIGNORED -- it verifies each")
        print("  declared binding against the features it could have matched, and the")
        print("  committed GeoPackage holds only the feature that WAS chosen, which is")
        print("  exactly the information this check cannot use. Run it locally after")
        print("  scripts/sources/cshapes-2.0/fetch.sh.")
        return 0

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

    if unverifiable:
        # Do NOT print a clean PASS while part of the population could not be looked at.
        # Caught by simulating CI locally: with only cshapes-2.0 hidden, 192 bindings from
        # other sources still resolved, so the SKIP above did not fire and the gate printed
        # "every binding is decided by the data" with 25 of them unexamined.
        print(f"\nPARTIAL PASS: the {checked} bindings that could be resolved are all "
              f"decided by the data,")
        print(f"  but {len(unverifiable)} baselined binding(s) could not be examined at all "
              f"because their")
        print(f"  source is not fetched. This is NOT a statement about those.")
        return 0

    print("\nPASS: every binding is decided by the data, not by row order")
    return 0


if __name__ == "__main__":
    sys.exit(main())
