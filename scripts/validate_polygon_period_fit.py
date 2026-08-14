#!/usr/bin/env python3
"""Does each polity's polygon binding actually belong to the period the row covers?

Two signals, both derived from the committed `data/final/polygon_feature_index.csv` and the
committed GeoPackage, so this runs in CI. Between them they found EIGHT wrong bindings across
five families in one session, none of which any area check could see.

  A. OUT-OF-SPAN VINTAGE. The row's `polygon_feature_year` falls outside its own
     [start_year, end_year), and the source offers a differently-sized step INSIDE that span.
     Nearly always the predecessor's step, i.e. the whole family lagged by one.

  B. IDENTICAL GEOMETRY WITH AN ALTERNATIVE. Two consecutive periods of one family share the
     same (source, feature_id, feature_year) and therefore byte-identical geometry, while the
     source offers a differently-sized step covering the later row's start year.

WHY BOTH, AND WHY NEITHER SUFFICES ALONE — this is the part worth reading:

  Signal B found ANG-1800-1890 / ANG-1890-1891. Fixing it revealed that ANG-1891-1905 was
  ALSO wrong, and B was structurally blind to it: a UNIFORM LAG makes every row wrong and no
  two identical, so there is no collision to detect. Signal A finds lags.

  Signal A in turn cannot see a duplicated binding where both rows legitimately sit inside
  their spans. Signal B finds those.

WHAT THEY FOUND, so the value is not hypothetical:
  CHN-1950-2025   1.81M km2 too small for 75 years -- the largest polygon error in this
                  database, on the largest agricultural producer in it (issue 120)
  COG x4          the Congo family lagged by one across four rows, worst case a 6.5x
                  overstatement (issue 124)
  ANG x2          Angola lagged by one across two rows (issue 122)
  SNI-1906-1913   bound to the pre-Lagos-merger polygon (issue 51)
  SWA, TCD        the 1911 Neukamerun cession, lagged in two more families (issue 125)
  ITA x2          both pre-1870 rows on the 1886 vintage, +13.8% and +5.9% against external
                  figures, while CShapes-Europe's own 1862-1866 and 1867-1870 steps were
                  sitting unused in the same feature (issue 121)
  SUD-1934-1956   published the 1914-1934 step, so the 1934 Sarra Triangle cession to Italian
                  Libya (-92,582 km2) never reached the map; the page had described the
                  correct step all along (issue 121)

WHY AN AREA CHECK FINDS NONE OF THEM: every one of those rows declared no
`polygon_area_km2`, so `validate_polygons`' comparison -- opt-in via that hand-entered field
-- never examined it. Roughly 590 of 742 rows are in that blind spot (issue 59). These two
signals need no declared area, because they compare the binding against the SOURCE'S OWN
alternatives rather than against a number someone typed.

BOTH SIGNALS ARE NOISY WITHOUT THEIR SECOND CLAUSE, and the clauses are what make them
usable:
  - 72 live rows have an out-of-span feature_year; most are inherent, because GADM and
    `constructed` are modern-only and a historical row MUST use a modern vintage. Requiring
    a TEMPORAL source and a differently-sized in-span step gives 3.
  - 107 consecutive pairs share geometry, 53 of them from the same binding, and most are
    correct: decolonisation usually preserves borders (BDI-1922-1962 -> BDI-1962-2025), as
    does independence (SUD-1934-1956 -> SUD-1956-2011). Requiring an available alternative
    as well gives 1.
    (Counted 2026-08-13, after issue 121. The figures this paragraph carried before -- 83 /
    8 and 115 / 5 -- were measured before issues 120-125 were fixed; the fixes both removed
    flags and removed rows from the raw populations.)

Usage:
  python3 scripts/validate_polygon_period_fit.py
"""
import csv
import os
import re
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")
INDEX = os.path.join(REPO, "data/final/polygon_feature_index.csv")
GPKG = os.path.join(REPO, "data/final/polities_database.gpkg")
WIKI = os.path.join(REPO, "wiki/polities")
DEAD = ("retired", "superseded")
TEMPORAL = {"cshapes-2.0", "cshapes-europe", "cliopatria"}
TOL = 0.02          # a step counts as "differently sized" beyond 2%

# Bindings judged and accepted. Two kinds, and the distinction is deliberate:
#
#   "documented"  the page states a proxy or vintage choice, so an out-of-span year is
#                 intentional. ROU-1918-1919's 1921 vintage was chosen on DATA evidence
#                 (maize production consistent only with Greater Romania) -- a check that
#                 failed on it would be failing on its own correct decision.
#   "undecided"   flagged, unexplained, and NOT yet judged. Tracked in issue 121.
#                 Listed here so the gate can run at zero without pretending these are fine.
#
# Re-measured on 2026-08-14 (issue 123). That issue named fourteen rows: five documented, nine
# undecided. EIGHT of the nine have since been rebound or re-labelled, and the only undecided
# signal-A entry left in this set is A:SUD-1934-1956 -- whose note below is measurably wrong and
# is corrected in place. Everything else here is a documented proxy or a signal-B pair from
# issue 121.
BASELINE = frozenset({
    # --- documented proxies (signal A) ---
    "A:F237-1954-1975",
    # A:ITA-1861-1866 and A:ITA-1866-1870 LEFT this list on 2026-08-13. They were filed as
    # "documented proxies", and the pages did document them -- both said the 1886 vintage
    # overstated the row and that "no such polygon exists in CShapes 2.0 or CShapes-Europe
    # (Italy has a single backdated polygon)". That sentence was false, and being documented
    # is what kept it unexamined for six weeks. CShapes-Europe Id 325 carries FIVE steps
    # (1862-1866 = 247,820; 1867-1870 = 272,655; 1871-1885 = 284,509; 1886-1918 = 284,718;
    # 1919-2023 = 300,106), and their capital fields read Turin / Florence / Rome / Rome /
    # Rome -- the actual sequence of Italian capitals. The two rows are now on 1862 and 1867,
    # both in span, so signal A no longer fires and "B:ITA-1861-1866 / ITA-1866-1870" and
    # "B:ITA-1866-1870 / ITA-1870-1919" below are gone with them.
    "A:ROU-1918-1919",
    "A:TUR-1800-1913",
    # --- cleared (signal A), issue 123 ---
    # The Congo four, SWA-1912-1958 and TCD-1912-1919 left this list on 2026-08-12 without leaving a
    # note behind, so it is recorded here. Each was bound to its PREDECESSOR's feature_year; each now
    # names its own step, and the published GeoPackage confirms it (ESRI:54034, km2):
    #
    #     COG-1898-1900  fy 1886 -> 1898     343,962 ->   2,234,499
    #     COG-1900-1906  fy 1898 -> 1900   2,234,449 ->     962,676
    #     COG-1906-1912  fy 1900 -> 1906     962,676 ->     343,962
    #     COG-1912-1919  fy 1906 -> 1912     343,962 ->     262,586
    #     SWA-1912-1958  fy 1900 -> 1912     176,369 ->     269,194
    #     TCD-1912-1919  fy 1900 -> 1912   1,271,772 ->   1,220,889
    #
    # Issue 123's own table of "bound km2" was OFF BY ONE for the Congo rows, and for the same reason
    # TUR-1913-1914's entry was wrong: it assumed a feature_year names the step CONTAINING it, while
    # find_feature prefers the step STARTING at it. So the issue reported COG-1906-1912 as carrying
    # 2,234,540 km2 ("a 6.5x overstatement"); it actually carried 962,676, and the 2.2 Mkm2 sat on
    # COG-1900-1906 instead. The lag diagnosis was right; the per-row areas attached to it were not.
    # The worst live error was COG-1900-1906 at +132% (2,234,449 for a row whose step is 962,676).
    # A:MOR-1800-1904 LEFT this list on 2026-08-12. The note here was right that it is "not a
    # one-step lag" and stopped there. The bound step is 1769-1860, which COVERS the row's first
    # 61 years -- the step was in span even though the year naming it was not. polygon_feature_year
    # is now 1800, which selects the identical step (387,614 km2, verified) and describes it
    # honestly, so the flag is gone with no geometry change.
    #
    # What the flag was standing in front of is a different issue: FIVE Cliopatria vintages fall
    # inside 1800-1903, and the territory drops 387,614 -> 358,422 across them, so one geometry
    # overstates the row's last two decades by 7.5%. That is issue 22's class, recorded in the
    # page's polygon_vintage_note, and splitting at 1885 would fix it.
    # A:SUD-1934-1956 LEFT this list on 2026-08-13, and its note -- "-3.6%, within
    # simplification and boundary-vintage noise" -- was a misreading. CShapes 625 dates the
    # step-down to 20 July 1934, the date of the Anglo-Italian agreement ceding the Sarra
    # Triangle to Italian Libya, and differencing the two steps gives 92,581 km2 lost, 0
    # gained, in ONE block bounded 19.07E-25.00E / 19.51N-22.00N -- the Sarra Triangle's own
    # corner. Simplification does not remove area on one side only, in one contiguous piece.
    # Worth generalising: a percentage on its own cannot distinguish simplification from a
    # cession, but the source's CHANGE DATE and the SHAPE of the difference can, and this
    # gate already has both in hand.
    #
    # The row's page had named the 1934-1955 step and its 2,486,943 km2 area all along while
    # the frontmatter said 1914, so the published geometry was the 1914-1934 step and was
    # byte-identical to SUD-1899-1934 (2,580,191 km2 measured). Declared recipe right,
    # binding wrong -- which is why "B:SUD-1899-1934 / SUD-1934-1956" below is gone too.
    # A:TUR-1913-1914 LEFT this list on 2026-08-12, and the note it carried -- "points FORWARD
    # (1914 for a 1913 row); every fixed case pointed back" -- described the symptom and drew the
    # wrong conclusion from it. Pointing forward was not a quirk to tolerate: fy=1914 resolved to
    # the `1914-1918` step, so the row published 1,705,971 km2 while declaring 1,785,218, and it
    # published the SAME geometry as TUR-1914-1918 (which is why "B:TUR-1913-1914 /
    # TUR-1914-1918" sat below). Neither 1913 step can be named by a feature_year -- both start in
    # 1913 -- so it is now a constructed row selecting the step by its bounds. See
    # build_tur_1913_1914 and _cshapes2_step.
    # WHERE ISSUE 123 STANDS, re-measured 2026-08-14 against the committed CSV, feature index and
    # GeoPackage: signal A flags six rows. Five are the documented proxies at the top of this set
    # -- the same five the issue itself named as "deliberate and documented" and excluded from
    # suspicion. The sixth is SUD-1934-1956, the one row of the nine undecided that is still
    # bound outside its own span. Eight of the nine are done; seven of those eight moved
    # geometry, and MOR-1800-1904 moved none because its 1769-1860 step already covered the
    # row's first 61 years.
    # --- documented / undecided (signal B), issues 121 and 123 ---
    # B:ITA-1861-1866 / ITA-1866-1870 and B:ITA-1866-1870 / ITA-1870-1919 LEFT this list on
    # 2026-08-13; see the A:ITA note above. All three rows published the SAME 284,847 km2,
    # and the fix moved the first two off it (247,820 and 272,655) while leaving
    # ITA-1870-1919 alone -- post-Rome Italy really is what the 1886 vintage shows.
    # B:HUN-1944-1947 / HUN-1947-2025 -- RESOLVED AS A DELIBERATE CHOICE on 2026-08-12, and the
    # old note's reading was back to front. It said "the LATER row is right: 93,004 km2 matches
    # modern Hungary, so the earlier row is the suspect". The earlier row is not a suspect; it is
    # on that step ON PURPOSE, and hun-1944-1947.md now carries a polygon_vintage_note saying so.
    #
    # CShapes 310 has ONE step for 1938-1947 (108,785 km2, the enlarged post-Vienna-Award Hungary)
    # and does not model the reversion. The January 1945 Armistice restored the Trianon borders, so
    # for 1945 and 1946 the Trianon step is right and CShapes' in-span step would overstate them by
    # 15,781 km2. For 1944 it is the other way round. Two of three years favour the choice made.
    #
    # The pair stays here because signal B does not read pages -- unlike signal A, which consults
    # declares_proxy(). Teaching B the same test would clear this entry automatically, and is worth
    # doing if a second documented duplicate appears; with one, the baseline entry is cheaper than
    # the code change.
    "B:HUN-1944-1947 / HUN-1947-2025",
    # B:SUD-1899-1934 / SUD-1934-1956 LEFT this list on 2026-08-13; see the A:SUD note above.
    # SUD-1934-1956 is now on the 1934 vintage, so its geometry is the post-Sarra-Triangle
    # 2,487,112 km2 and no longer matches its predecessor. It DOES still match its successor
    # SUD-1956-2011, which is correct and does not fire signal B: independence changed no
    # borders, and CShapes offers no differently-sized step inside 1956-2010.
})

PROXY_RE = re.compile(
    r"polygon_vintage_proxy:\s*true|polygon_vintage_note:|"
    r"polygon_status:\s*(proxy|estimate|polygon_vintage_drift)"
)


def declares_proxy(code: str) -> bool:
    p = os.path.join(WIKI, f"{code.lower()}.md")
    if not os.path.exists(p):
        return False
    with open(p, encoding="utf-8") as fh:
        return bool(PROXY_RE.search(fh.read()))


def num(v):
    try:
        return int(float(v))
    except (TypeError, ValueError):
        return None


def main() -> int:
    if not os.path.exists(INDEX):
        print(f"SKIP: {INDEX} missing; run scripts/write_feature_index.py")
        return 0

    steps = defaultdict(list)
    with open(INDEX, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            steps[(r["source"], r["feature_id"])].append(
                (num(r["start_year"]), num(r["end_year"]), float(r["area_km2"] or 0))
            )

    with open(CSV_PATH, encoding="utf-8") as fh:
        rows = [r for r in csv.DictReader(fh) if r["wiki_status"] not in DEAD]

    problems, observed = [], set()

    # ---------- SIGNAL A ----------
    for r in rows:
        src = (r.get("polygon_source") or "").strip()
        if src not in TEMPORAL:
            continue
        fy, s, e = (num(r["polygon_feature_year"]), num(r["start_year"]),
                    num(r["end_year"]))
        if None in (fy, s, e) or s <= fy < e:
            continue
        cand = steps.get((src, str(r["polygon_feature_id"]).strip()), [])
        chosen = [c for c in cand if c[0] is not None and c[0] <= fy <= c[1]]
        inspan = [c for c in cand if c[0] is not None and s <= c[0] < e]
        if not chosen or not inspan:
            continue
        ch = chosen[0][2]
        alt = [c for c in inspan if abs(c[2] - ch) / max(ch, 1) > TOL]
        if not alt:
            continue
        key = f"A:{r['polity_code']}"
        observed.add(key)
        if key in BASELINE:
            continue
        best = max(alt, key=lambda c: abs(c[2] - ch))
        problems.append(
            f"A {r['polity_code']}: covers {s}-{e - 1} but polygon_feature_year={fy} is "
            f"OUTSIDE that span, selecting {ch:,.0f} km2; the source offers "
            f"{best[0]}-{best[1]} = {best[2]:,.0f} km2 ({100 * (best[2] - ch) / max(ch, 1):+.1f}%) "
            f"inside it"
            + ("" if declares_proxy(r["polity_code"])
               else "  [the page declares no proxy or vintage note]")
        )

    # ---------- SIGNAL B ----------
    try:
        import geopandas as gpd
        import pandas as pd
    except ImportError as exc:
        print(f"  note: signal B skipped, geopandas unavailable ({exc})")
        gpd = None
    if gpd is not None and os.path.exists(GPKG):
        g = gpd.read_file(GPKG)
        g = g[~g.wiki_status.astype(str).isin(DEAD)]
        g = g[g.geometry.notna() & ~g.geometry.is_empty].copy()
        g["km2"] = g.to_crs("ESRI:54034").geometry.area / 1e6
        g["s"] = pd.to_numeric(g.start_year, errors="coerce")
        g["prefix"] = g.polity_code.str.rsplit("-", n=2).str[0]
        for _pre, fam in g.groupby("prefix"):
            if len(fam) < 2:
                continue
            rs = list(fam.sort_values("s").itertuples())
            for k in range(len(rs) - 1):
                a, b = rs[k], rs[k + 1]
                if not a.geometry.equals(b.geometry):
                    continue
                bind = (str(a.polygon_source), str(a.polygon_feature_id),
                        str(a.polygon_feature_year))
                if bind != (str(b.polygon_source), str(b.polygon_feature_id),
                            str(b.polygon_feature_year)):
                    continue
                cand = steps.get((bind[0], bind[1]), [])
                if len(cand) < 2:
                    continue
                cur = [c for c in cand
                       if c[0] is not None and c[0] <= (b.s or -1) <= (c[1] or 9999)]
                alt = [c for c in cur if abs(c[2] - b.km2) / max(b.km2, 1) > TOL]
                if not alt:
                    continue
                key = f"B:{a.polity_code} / {b.polity_code}"
                observed.add(key)
                if key in BASELINE:
                    continue
                best = max(alt, key=lambda c: abs(c[2] - b.km2))
                problems.append(
                    f"B {a.polity_code} / {b.polity_code}: identical geometry at "
                    f"{b.km2:,.0f} km2 from one binding, while {best[0]}-{best[1]} = "
                    f"{best[2]:,.0f} km2 ({100 * (best[2] - b.km2) / max(b.km2, 1):+.1f}%) "
                    f"covers the later row"
                )

    for key in sorted(BASELINE - observed):
        problems.append(f"{key} is baselined but no longer flagged — remove it")

    print(f"bindings on a temporal source checked against their period: {len(observed)} "
          f"flagged, {len(BASELINE)} baselined")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        print("\n  A row bound to a step from outside its own period measures the wrong\n"
              "  territory for every year it covers, and no area check will say so: these\n"
              "  rows typically declare no polygon_area_km2 at all (issue 59).")
        return 1

    print("\nPASS: every binding fits the period its row covers, or is baselined with a reason")
    return 0


if __name__ == "__main__":
    sys.exit(main())
