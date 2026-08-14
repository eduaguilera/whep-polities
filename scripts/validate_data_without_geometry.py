#!/usr/bin/env python3
"""Does every polity that RECEIVES DATA carry a polygon?

Matching and geometry are checked separately everywhere else in this repo, and nothing
joined the two questions. The completeness harness counts a row as a success when its
label resolves to a polity; `validate_polygons` asks whether a polity's declared polygon
is attached. Neither asks the question a consumer actually has: *the rows that arrived
here — do they have any territory?*

A polity with data and no geometry is **matched but spatially unusable**. Every gate
reports those rows as routed, and every consumer doing anything area-weighted — density,
per-km2 intensity, dasymetric reallocation, the constant-territory back-casting in the
WHEP R package — silently drops them or divides by nothing. Silently is the problem: an
unmatched row is visible in a coverage figure, a matched row with no territory is not.

WHAT IT MEASURED WHEN IT WAS WRITTEN (2026-08-13, issue 155): 9 live polities receive
362 layer-B rows with no geometry, all nine judged and baselined below. On rebase
(2026-08-14) it briefly measured 8 polities and 194 rows, because the gitignored parquet the
counts derive from predated the recent re-spans; CHL-1810-1884 left the baseline for that
reason. Regenerating the parquet (issue 243) restored the original reading exactly — 9
polities, 362 rows — and CHL is baselined again.

Issue 155 filed the same class at 18 polities / 1,071 rows. Re-enumerating it from the
data rather than from the issue changed both the membership and the counts:

  * EIGHT of the issue's 18 had already acquired geometry from other PRs by the time this
    gate was written — SER-1918-1945, SAA-1947-1957, FTO-1920-1960, GCT-1919-1956,
    TRP-1943-1951, BWI-1833-1962, FRIN-1816-1954, CYR-1949-1951. The issue's own text
    said five (BWI, FRIN, GCT, TRP, CYR); it missed the three largest.
  * THREE were fixed in the PR that added this gate: TAN-1891-1920 (46 rows),
    TAN-1920-1922 (8), BRL-1945-1949 (2).
  * TWO MORE THE ISSUE NEVER LISTED were fixed in the same PR: TAS-1825-1900 at 195 rows
    — the single largest block in the entire class — and BRL-1938-1945 at 19.
  * SEVEN of the issue's 18 remain, and TWO it never listed (TRS-1947-1954 at 78 rows,
    WBL-1949-1990 at 24) are in the baseline below.

The per-polity counts also differ from the issue's throughout (SER 476 filed vs 573
measured, FTO 93 vs 182, TAN-1891-1920 38 vs 46), because the issue resolved labels
through matchlib directly while this gate reads the committed territory-basis column.
Which is the argument for the gate rather than against it: a hand-run measurement goes
stale the moment the next PR lands, and this one re-runs on every push.

INPUT, AND ITS ONE LIMITATION. The row counts come from
`pipelines/polity-autoimprove/state/territory_basis.csv`, whose `layerb_data_rows`
column stage 4 derives from the layer-B match. Layer B itself lives outside the repo
(~/Nextcloud, not redistributable), so this gate reads the COMMITTED counts rather than
recomputing them — which means a polity that started receiving data since that file was
last refreshed is invisible here until it is. The counts are therefore a floor, not a
census, and check C below fails if the column collapses to all-zero, because a gate whose
input has silently emptied prints PASS forever. That is the failure mode this repo has
already paid for once: `04_territory_basis.py --check` compares only the columns CI can
reproduce, and this column is not one of them.

The OTHER way the input goes wrong is subtler than emptying, and check C cannot see it: the
parquet keeps a re-spanned polity's old code, so its rows are attributed to a code that no
longer exists and the successor's committed count reads 0 while the total stays healthy.
That is issue 243, and it cost this baseline an entry. `04_territory_basis.py` now refuses to
write or validate the accounting while any such orphan code is present, which is upstream of
here and is why check C can stay the cheap non-empty test it is.

Three checks:
  A. DATA WITHOUT TERRITORY — a live polity with rows > 0 and no geometry, unbaselined.
  B. STALE BASELINE (bidirectional) — a baselined polity that now HAS geometry, or now
     receives no rows. Fixing a baselined defect must fail until the entry is removed,
     or the baseline becomes a list of things that used to be true.
  C. INPUT ALIVE — the row-count column must not be uniformly zero.

Usage:
  python3 scripts/validate_data_without_geometry.py
"""
import csv
import os
import sys

import geopandas as gpd
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
CSV = os.path.join(REPO, "data/final/polities_database.csv")
BASIS = os.path.join(REPO, "pipelines/polity-autoimprove/state/territory_basis.csv")
DEAD = ("retired", "superseded")

# Polities judged to receive data with no polygon, with the reason each one has none.
# Every entry below was checked against the actual sources in data/geodata rather than
# taken from its own page's prose — which is how issue 155's five already-fixed cases
# were found. Row counts are the layer-B figures measured on 2026-08-13.
BASELINE = frozenset({
    # CHL-1810-1884, 168 rows, RESTORED on 2026-08-14 (issue 243). It was removed earlier the
    # same day because committed state said `layerb_data_rows = 0` for it: the rows were real
    # but attributed to `CHL-1810-1883`, a code the database no longer contains, because the
    # gitignored matched_rows.parquet predated the re-spans. That parquet has now been
    # regenerated against the current polity set (orphan codes 5 -> 0, 799 rows re-attributed),
    # so the count is 168 again and check A flags it for the reason below rather than for
    # staleness. 04_territory_basis.py now refuses to write the accounting at all while any
    # orphan code remains, so this entry cannot silently become a lie a second time.
    #
    # The reason it had no polygon is unchanged and still on the page: Cliopatria's pre-1884
    # Chile steps (1866-1879: 314,287 km2) are settlement-extent rather than claimed territory, so
    # binding one would put a 2.4x step against this family's CShapes-sourced siblings
    # (~745,000 km2) that is a mapping convention and not a border. CShapes has a 1886
    # floor and its earliest Chile polygon already contains the ~240,000 km2 annexed in
    # 1883-1884. See wiki/polities/chl-1810-1884.md and issue 158.
    "CHL-1810-1884",
    # 78 rows, the largest remaining. NO SOURCE HAS IT. The Free Territory of Trieste
    # (declared 737 km2, Zone A ~222 + Zone B ~515) needs adm2-level Italian, Slovenian
    # and Croatian units. Measured: CShapes 2.0 has zero features matching Trieste or
    # "Free Territory" and carries no city-level units at all; CShapes-Europe holds only
    # Italy, Italy/Sardinia and Yugoslavia for the region; Cliopatria has no Trieste
    # polity; and GADM 4.1's fetched set has no ITA/SVN/HRV file, with adm2 extracted for
    # IDN alone. Unblocking it means fetching new GADM countries, not rebinding.
    "TRS-1947-1954",
    # 39 rows. The recipe EXISTS and was measured WRONG: build.py carries
    # build_can_1800_1866 unregistered because the five modern provinces give
    # 2,735,024 km2 against the page's 1,209,852 — Ontario and Quebec reach Hudson Bay
    # while the 1866 Province of Canada stopped at Rupert's Land. A different territory,
    # not a proxy. Needs a pre-Confederation source.
    "CAN-1800-1866",
    # 24 rows. West Berlin's three western sectors (~480 km2) cannot be recovered from
    # any fetched source: CShapes has no Berlin feature, and Berlin's 2001 district
    # reform merged boroughs ACROSS the sector line (Mitte = Mitte + Tiergarten + Wedding;
    # Friedrichshain-Kreuzberg spans it), so even GADM adm2 could not reproduce it.
    # Its predecessor BRL-1945-1949 is now bound to the whole city, which is deliberately
    # NOT reused here: 892 km2 for a 480 km2 territory would be an 86% overstatement.
    "WBL-1949-1990",
    # 20 rows. French Cochinchina needs the six southern Vietnamese provinces of the
    # 1860s-80s; GADM 4.1's fetched set has no VNM file, and Cliopatria's "French
    # Indochina" is the whole federation (753,049 km2 against Cochinchina's ~65,000).
    "FCC-1862-1887",
    # 14 rows. The 1935-1947 Saar is the 1920 Saar Territory boundary, 1,912 km2.
    # GADM's Saarland (DEU.12_1) measures 2,571 km2 — 34% larger, because post-1947
    # additions are in it. Bindable only as a documented 34% overstatement, which is a
    # judgement this gate's baseline should record rather than a fix to slip in.
    "SAC-1935-1947",
    # 10 rows. Italian East Africa declares `constructed` at 1,700,000 km2 with no
    # builder. A union of Ethiopia + Eritrea + Italian Somaliland is buildable, but it
    # would contain three coexisting polities and so needs a LEGITIMATE_CONTAINERS entry
    # in validate_spatial_containment plus the member-vs-aggregate double-count question
    # settled. Deliberately not done for 10 rows in a PR about the other 270.
    "AOI-1936-1941",
    # 5 rows. The Panama Canal Zone (1,432 km2) is a strip either side of the canal; no
    # fetched source carries it as a feature and GADM's Panamá/Colón provinces are not
    # it. polygon_source is empty, which at least does not lie about having one.
    "CZN-1903-1979",
    # 4 rows. Same territory question as CAN-1800-1866 and the same measured answer;
    # additionally its polygon_source is `gadm-4.1`, which is not a registry slug at all
    # (the registry has gadm-4.1-adm0 and gadm-4.1-adm1), so the build reports it as an
    # unknown source rather than as a missing feature.
    "CAN-1866-1870",
})


def main() -> int:
    if not os.path.exists(BASIS):
        print(f"FAIL: {BASIS} missing — run pipelines/polity-autoimprove/04_territory_basis.py")
        return 1

    basis = {}
    with open(BASIS) as fh:
        for r in csv.DictReader(fh):
            try:
                basis[r["polity_code"]] = int(float(r["layerb_data_rows"] or 0))
            except ValueError:
                basis[r["polity_code"]] = 0

    meta = pd.read_csv(CSV)
    dead = set(meta.loc[meta["wiki_status"].isin(DEAD), "polity_code"])

    g = gpd.read_file(GPKG)
    has_geom = set(g.loc[g.geometry.notna() & ~g.geometry.is_empty, "polity_code"])

    receiving = {c: n for c, n in basis.items() if n > 0 and c not in dead}
    bare = {c: n for c, n in receiving.items() if c not in has_geom}

    print(
        f"{len(basis)} polities in the territory-basis accounting; {len(receiving)} live "
        f"ones receive layer-B rows; {len(has_geom)} of {len(g)} rows carry geometry"
    )

    # ---------- C: the input must not have gone silent ----------
    problems = []
    if not receiving:
        problems.append(
            "layerb_data_rows is zero for every polity — the column collapsed (its input, "
            "state/matched_rows.parquet, is untracked), so checks A and B cannot fire and "
            "this gate would pass vacuously"
        )
        print("\nC. INPUT ALIVE — FAIL: no polity records any layer-B rows")
    else:
        print(
            f"\nC. INPUT ALIVE — OK: {sum(receiving.values()):,} rows recorded across "
            f"{len(receiving)} polities"
        )

    # ---------- A: data without territory ----------
    unbaselined = sorted(
        ((c, n) for c, n in bare.items() if c not in BASELINE),
        key=lambda t: -t[1],
    )
    print(
        f"\nA. DATA WITHOUT TERRITORY — {len(bare)} live polit(ies) receive "
        f"{sum(bare.values()):,} rows with no geometry; {len(BASELINE)} baselined, "
        f"{len(unbaselined)} not"
    )
    for code, n in unbaselined:
        src = meta.loc[meta.polity_code == code, "polygon_source"]
        src = (src.iloc[0] if len(src) else None)
        problems.append(
            f"{code} receives {n} layer-B rows and carries no geometry "
            f"(polygon_source={src!r}) — matched but spatially unusable"
        )
        print(f"   FAIL {code:18s} {n:>6} rows  polygon_source={src!r}")

    # ---------- B: baseline is bidirectional ----------
    fixed = sorted(c for c in BASELINE if c in has_geom)
    silent = sorted(c for c in BASELINE if basis.get(c, 0) == 0 or c in dead)
    print(
        f"\nB. STALE BASELINE — {len(fixed)} baselined polit(ies) now carry geometry, "
        f"{len(silent)} now receive no rows"
    )
    for code in fixed:
        problems.append(
            f"{code} is baselined here but now HAS geometry — delete its BASELINE entry "
            f"and replace it with a comment saying what was bound"
        )
        print(f"   FAIL {code:18s} now has geometry")
    for code in silent:
        problems.append(
            f"{code} is baselined here but records 0 layer-B rows (or is dead) — it no "
            f"longer belongs in this baseline"
        )
        print(f"   FAIL {code:18s} records no rows")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)")
        for line in problems:
            print(f"  {line}")
        return 1
    print("\nPASS: every live polity receiving layer-B rows carries geometry or is baselined")
    return 0


if __name__ == "__main__":
    sys.exit(main())
