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

RE-MEASURED 2026-08-17 (issue 155 again): 8 polities, 352 rows. AOI-1936-1941 left the
baseline because its polygon was built. The other eight were re-checked against the
FETCHED sources rather than against their own baseline comments, and every blocker held:
GADM 4.1 as fetched here has adm0 for 99 countries and adm1 for 80, and neither set
contains ITA, SVN, HRV (TRS-1947-1954), VNM (FCC-1862-1887) or PAN (CZN-1903-1979);
adm2 covers IDN alone, 502 features, so Trieste is unreachable above adm1 in any case.
CShapes 2.0's country names contain no Trieste, no Berlin and no Saar feature at all.
GADM's Saarland DEU.12_1 re-measures 2,571 km2 against SAC-1935-1947's 1,912 — still the
same 34% overstatement. So AOI was the ONLY member of this class fixable without
fetching new source data, which is the finding: what is left is a data-acquisition
task, not a rebinding one.

RE-MEASURED AGAIN 2026-08-17, LATER THE SAME DAY (issue 155, third pass): 6 polities, 327
rows. THE PARAGRAPH ABOVE WAS WRONG, and wrong in a way worth keeping visible rather than
deleting. Its conclusion — "what is left is a data-acquisition task, not a rebinding one" —
rested on asking each blocked polity's OWN sources one more time. Two of the eight fell to
asking a DIFFERENT source a different question:

  * CZN-1903-1979 (5 rows). The Hay-Bunau-Varilla Treaty DEFINES the Canal Zone as five
    miles each side of the canal centreline, so the only missing ingredient was a
    centreline. Four sources had been queried for a Canal Zone feature and none has one —
    but Natural Earth 10m rivers, shipped inside the paine-2024 replication package,
    carries the "Panama Canal" as two line parts. A 5-statute-mile buffer measures
    1,176 km2 against the stated 1,432 (-17.9%, being Gatun Lake beyond the strip plus the
    sea approaches). Nobody had queried that file, and the page's own open question had
    asked for exactly this construction while declaring the source absent.
  * FCC-1862-1887 (20 rows). Cliopatria's Vietnam at 1855 MINUS Vietnam at 1860 is
    66,039 km2 of the Mekong delta against ~65,000 stated for Cochinchina (+1.6%) — the
    MMR-LWR-1852-1885 pattern, where what changed hands is the difference between the two
    steps bracketing the conquest. The earlier note is right that Cliopatria's "French
    Indochina" is the whole federation and useless here; it did not occur to it that the
    same source answers a different question.

The lesson generalises to the six that remain, so it is recorded here rather than in a PR:
"no source has a feature for X" is a weaker statement than it sounds. It can be true while
X is still constructible, either because X is DEFINED as an operation on something a source
does have (CZN), or because X is the DIFFERENCE between two states a source records (FCC).
Both remaining Canada rows, the Saar and West Berlin have all been tested against the first
form and fail it for stated reasons; TRS and the Saar have not been tested exhaustively
against the second.

RE-MEASURED A FOURTH TIME, 2026-08-17 (issue 155, fourth pass): 5 polities, 159 rows.
CHL-1810-1884 left the baseline, and it is the LARGEST single block the class ever had at 168
rows. The paragraph above ended by naming TRS and the Saar as the two cases not yet tested
against the difference form; both have now been tested, both fail, and the case that fell was
neither of them. It fell to the FIRST form, on a row whose own page had written the definition
down and then not used it: the 1866 Chile-Bolivia treaty parallel at 24 deg S bounds the entire
1883-1884 annexation, so pre-war Chile is CShapes' 1886 Chile clipped at that line -- 600,490 km2
against 600,325 from independent modern-region arithmetic, 0.03%. Issue 158 had declined
Cliopatria here on the grounds that a 2.4x step would be a mapping convention rather than
territory. That was right, and it is an argument for staying inside CShapes rather than for
leaving the row empty; the clip makes the step 1.24x, which is the annexation.

Two lessons, both about where the answer was:

  * A "deliberately empty" row is not a closed one. CHL had a documented decision, an issue
    number (158) and a baseline entry all agreeing it should stay empty, and all three were
    reasoning about which SOURCE to attach when the question was which OPERATION to apply to the
    source already attached to its own siblings.
  * The page said 24 deg S in its Summary and in its own polygon decision, and still estimated the
    area by subtracting a round ~240,000 km2 instead of measuring the clip. Measured, 145,607 km2
    lies north of the parallel, so the page's ~516,000-520,000 was ~85,000 too small and issue
    158's ~180,000 annexation figure too large. The recipe was in the prose; only the arithmetic
    was missing.

What remains is 5 polities and 159 rows, and every one has now been tested against BOTH forms
with the negative result recorded in its entry below: TRS (78) has no 1947 or 1954 step break in
any source and its Italy/Yugoslavia gap is 2,239 km2 of mostly Adriatic sea against a 738 km2
territory; both Canada rows (43) have no Cliopatria step before 1932-1948; SAC (14) is contained
in every CShapes-Europe German step, so nothing detaches it; WBL (24) has no sub-Berlin unit in
GADM at adm2, adm3 OR adm4. That is now a data-acquisition list, stated after testing rather
than before -- which is the distinction the third pass got wrong.

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
    # CHL-1810-1884 WAS HERE AND IS FIXED, 2026-08-17 (168 rows, the largest block in the class).
    # This entry said Cliopatria's pre-1884 Chile steps are settlement-extent rather than claimed
    # territory, so binding one would put a 2.4x step against this family's CShapes-sourced
    # siblings, and that CShapes has a 1886 floor whose earliest Chile polygon already contains the
    # territory annexed in 1883-1884. Both halves are TRUE and the conclusion did not follow, in
    # the CZN-1903-1979 shape: there is no pre-conquest CShapes FEATURE, but there is a
    # pre-conquest BOUNDARY. The 1866 Treaty of Mutual Benefits (reaffirmed 1874) fixed the
    # Chile-Bolivia border at 24 deg S, and Tarapaca, the Bolivian Litoral and the administered
    # Tacna-Arica all lie north of it, so the annexation is a clip rather than a different source.
    # `build_chl_1810_1884` clips CShapes 155's 1886-1899 step (746,276 km2) at that parallel:
    # 600,669 km2, less Easter Island (179, annexed September 1888) = 600,490 published. The
    # convention objection is not overturned, it is SATISFIED -- the family keeps one source and
    # the 1884 step becomes 1.24x, which is the annexation, instead of Cliopatria's 2.4x.
    # It also falsified two figures: this page said ~240,000 km2 was annexed and put the row at
    # ~516,000-520,000; issue 158 said ~180,000. Measured, 145,607 km2 is north of 24 deg S, and
    # independent arithmetic (modern Chile 756,096 - Tarapaca 42,226 - Antofagasta 126,049 + Taltal
    # 20,405, scaled onto the CShapes base) gives 600,325, 0.03% from the published figure. The
    # old estimate had subtracted the whole modern Antofagasta region without adding Taltal back.
    # `proxy`, for the EASTERN edge: the 1886 step is post-1881-treaty Patagonia, so the polygon
    # understates Chile's claims for 71 of the row's 74 years (oq-pre-1881-patagonian-claims).
    # 78 rows, the largest remaining. NO SOURCE HAS IT. The Free Territory of Trieste
    # (declared 737 km2, Zone A ~222 + Zone B ~515) needs adm2-level Italian, Slovenian
    # and Croatian units. Measured: CShapes 2.0 has zero features matching Trieste or
    # "Free Territory" and carries no city-level units at all; CShapes-Europe holds only
    # Italy, Italy/Sardinia and Yugoslavia for the region; Cliopatria has no Trieste
    # polity; and GADM 4.1's fetched set has no ITA/SVN/HRV file, with adm2 extracted for
    # IDN alone. Unblocking it means fetching new GADM countries, not rebinding.
    #
    # TESTED AGAINST THE DIFFERENCE FORM TOO, 2026-08-17, and it fails: no source in
    # data/geodata carries a 1947 or a 1954 step break for either neighbour, so there is no
    # before/after pair to subtract. CShapes 2.0 has Italy/Sardinia as ONE step 1919-2019 and
    # Yugoslavia as one 1920-1991; CShapes-Europe the same (Italy/Sardinia 1919-2023,
    # Yugoslavia 1920-1990); Cliopatria has Republic of Italy as one step 1946-2023 and its
    # SFRY steps at 1947 and 1949 differ by 479 km2 lost and 96 gained, neither of them near
    # Trieste. And there is no HOLE to lift either: the territory in the 13.2-14.1E/45.2-46.0N
    # envelope covered by neither Italy nor Yugoslavia measures 2,239 km2, three times the
    # FTT's 738, because it is mostly the Gulf of Trieste -- and no fetched source has an
    # Italian/Slovenian/Croatian coastline to clip the sea off with.
    "TRS-1947-1954",
    # 39 rows. The recipe EXISTS and was measured WRONG: build.py carries
    # build_can_1800_1866 unregistered because the five modern provinces give
    # 2,735,024 km2 against the page's 1,209,852 — Ontario and Quebec reach Hudson Bay
    # while the 1866 Province of Canada stopped at Rupert's Land. A different territory,
    # not a proxy. Needs a pre-Confederation source. RE-MEASURED 2026-08-17: the "pre-Confederation
    # source" is not in data/geodata under any name. Cliopatria's EARLIEST Canada step is
    # 1932-1948 -- it has no pre-1932 Canada at all, so the before/after difference form has no
    # "before" -- and the legacy data/geodata/polities_polygons.gpkg, which does carry a
    # CAN-1866-1948 feature, measures it at 9,553,644 km2, i.e. modern Canada.
    "CAN-1800-1866",
    # 24 rows. West Berlin's three western sectors (~480 km2) cannot be recovered from
    # any fetched source: CShapes has no Berlin feature.
    # Its predecessor BRL-1945-1949 is now bound to the whole city, which is deliberately
    # NOT reused here: 892 km2 for a 480 km2 territory would be an 86% overstatement.
    #
    # THIS ENTRY'S REASON WAS HYPOTHETICAL AND IS REPLACED BY A MEASUREMENT. It said Berlin's
    # 2001 district reform merged boroughs ACROSS the sector line (Mitte = Mitte + Tiergarten +
    # Wedding; Friedrichshain-Kreuzberg spans it) "so even GADM adm2 could not reproduce it".
    # True of the reform, but it never had to be argued: GADM 4.1's DEU file carries Berlin as a
    # SINGLE feature at adm2 (403 units nationally), adm3 (4,680) AND adm4 (11,302). There is no
    # sub-Berlin unit at any level to union, coarse or fine. Two further sources were queried and
    # neither helps: CShapes-Europe's German Federal Republic 1949-1989 is 247,632 km2 in ONE part
    # with no exclave near Berlin, and its GDR 1949-1989 (109,361) has no interior ring, so West
    # Berlin is absent from both rather than liftable as a hole; and the legacy
    # data/geodata/polities_polygons.gpkg does carry a "West Berlin" feature (GWB-1800-1982) at
    # 891.5 km2 -- byte-identical in area to its own East Berlin feature, i.e. both are the whole
    # city, which is the same 892 this entry already refuses.
    "WBL-1949-1990",
    # FCC-1862-1887 WAS HERE AND IS FIXED, 2026-08-17 (20 rows). This entry said French
    # Cochinchina "needs the six southern Vietnamese provinces of the 1860s-80s; GADM 4.1's
    # fetched set has no VNM file, and Cliopatria's 'French Indochina' is the whole federation
    # (753,049 km2 against Cochinchina's ~65,000)". Both halves are true and the conclusion did
    # not follow: the six provinces are what Cliopatria's Vietnam LOST between its 1834-1858 step
    # (300,525 km2) and its 1859-1867 step (234,392), and that difference is 66,277 km2 in four
    # parts. Clipped to the Mekong-delta envelope (104-108.5E, 8-12.5N) it is 66,039 km2 against
    # ~65,000 stated, +1.6%; the 238 km2 dropped is step-boundary jitter near Nha Trang and Qui
    # Nhon. `proxy`, because Cliopatria puts the whole loss at 1859 while France took the three
    # western provinces only in 1867, so the polygon overstates 1862-1867 (5 of 25 years).
    # 14 rows. The 1935-1947 Saar is the 1920 Saar Territory boundary, 1,912 km2.
    # GADM's Saarland (DEU.12_1) measures 2,571 km2 — 34% larger, because post-1947
    # additions are in it. Bindable only as a documented 34% overstatement, which is a
    # judgement this gate's baseline should record rather than a fix to slip in.
    #
    # TESTED AGAINST THE DIFFERENCE FORM, 2026-08-17, and it fails on containment before it gets
    # to arithmetic: CShapes-Europe's German steps ALL CONTAIN Saarbruecken (7.00E, 49.24N) --
    # 1886-1918, 1919, 1920-1937 and 1938-1944 alike -- so no step models the 1920-1935 Saar
    # Territory as detached from Germany, and there is nothing to subtract. The 1886-1918 minus
    # 1920-1937 difference clipped to the Saar box (6.2-7.6E, 49.0-49.8N) is 2,844 km2, but it is
    # northern LORRAINE, not the Saar, which is why Saarbruecken stays German across the pair.
    # The subtraction form is unavailable in the other direction too: the 1946-47 enlargement was
    # 142 named municipalities from the Rhine Province and the Palatinate, and modern Saarland's
    # six Landkreise (2,568 km2 total: Merzig-Wadern 555, St. Wendel 476, Saarlouis 459,
    # Saarpfalz 418, Regionalverband Saarbruecken 411, Neunkirchen 249) were redrawn in 1974 and
    # do not decompose into it -- dropping St. Wendel whole leaves 2,092 against 1,912 and cuts
    # territory that WAS in the 1920 Saar. So the 34% figure stands as the only reading.
    "SAC-1935-1947",
    # AOI-1936-1941 WAS HERE AND IS FIXED, 2026-08-17. It had declared `constructed` at
    # 1,700,000 km2 with no builder, and this baseline's own entry said the union of
    # Ethiopia + Eritrea + Italian Somaliland was buildable but deferred it because it
    # needed a LEGITIMATE_CONTAINERS entry and left the double-count question open.
    # Built: `build_aoi_1936_1941` unions CShapes step 530/1907-1952 (1,127,556 km2),
    # step 531/1900-1941 (120,897) and the constructed ITS-1908-1960 (464,743) =
    # 1,713,196 km2, the exact arithmetic sum because all three pairwise intersections
    # measure 0.000 km2. That is +0.78% on the declared 1,700,000 and -0.70% on the
    # 1,725,330 usually quoted for AOI. The containment entry was added (it holds
    # ETH-1907-1936, ERI-1889-1952, ITS-1908-1960, exactly as predicted); the
    # aggregate-vs-member double-count question is NOT settled and is now
    # oq-aoi-member-double-count on the page — geometry was attached anyway, because 10
    # rows with no territory is worse than 10 rows a hypothetical double-sum would
    # duplicate.
    # CZN-1903-1979 WAS HERE AND IS FIXED, 2026-08-17 (5 rows). This entry said "no fetched
    # source carries it as a feature", which is true of the Canal Zone and irrelevant: the 1903
    # treaty DEFINES the Zone as five statute miles each side of the canal centreline, so what was
    # needed was a centreline, not a Zone. Natural Earth 10m rivers (inside the paine-2024 bundle)
    # has the Panama Canal as two line parts; the 8,046.72 m buffer measures 1,176 km2 against the
    # stated 1,432, -17.9%, the gap being Gatun Lake beyond the five-mile line plus the
    # three-marine-mile sea approaches. `proxy` for that reason. It also falsified a claim on
    # PAN-1903-1979's page: 95.9% of the Zone polygon lies INSIDE CShapes feature 95, so that
    # feature does not exclude the Zone and the two rows double-count it (now an open question on
    # the Canal Zone page, and the sentence on PAN's page is corrected).
    # 4 rows. Same territory question as CAN-1800-1866 and the same measured answer: modern
    # Ontario and Quebec absorbed Rupert's Land, Keewatin and Ungava between 1870 and 1912,
    # which is precisely the territory this row exists to EXCLUDE, so their union
    # (2,729,293 km2) overstates the row by more than the row itself.
    #
    # THIS ENTRY'S SECOND SENTENCE WAS STALE AND IS DELETED. It said "additionally its
    # polygon_source is `gadm-4.1`, which is not a registry slug at all ... so the build
    # reports it as an unknown source rather than as a missing feature". Re-measured
    # 2026-08-17: polygon_source is `none`. The dangling slug was brought into line on
    # 2026-08-13 (the page's own Territorial extent records it), the same day this baseline
    # was written, so the comment was describing a state that had already gone. The
    # `sources: [gadm-4.1]` frontmatter list still names it, which is a bibliography entry
    # and not a polygon binding.
    #
    # RE-MEASURED 2026-08-17 alongside CAN-1800-1866: same negative result. Cliopatria has no
    # Canada step before 1932-1948; the legacy polities_polygons.gpkg's CAN-1866-1948 is modern
    # Canada at 9,553,644 km2. Both Canada rows need a source this repo does not have.
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
