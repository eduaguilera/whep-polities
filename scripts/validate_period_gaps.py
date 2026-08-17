#!/usr/bin/env python3
"""Check that no family leaves a year covered by nothing.

The twin of validate_period_overlaps.py. That one catches two live periods of one
family covering the SAME year, where a matcher gets two answers and picks by row
order. This catches the complement: consecutive periods with a year between them,
where a matcher gets NO answer.

A hole is harder to notice than an overlap. An overlap produces a wrong attribution
someone may eventually query; a hole produces a dropped row, or worse a fallback to
a neighbouring period, which attributes a figure to a polity that did not hold the
territory in that year.

`end_year` is EXCLUSIVE, so TCD-1912-1919 covers 1912-1918 and TCD-1920-1960 covers
1920-1959: 1919 is in neither.

GAPS ARE SPLIT BY SEVERITY as of 2026-08-17 (issue 252): see SHORT_GAP_MAX. A gap of two
years or less is presumed an ERROR and fails whatever the baseline says, because every one
this gate has ever recorded was a boundary written as if `end_year` were inclusive or a
source step WHEP never transcribed. A longer gap is presumed intentional and needs a
baseline entry naming who holds the territory. There are ZERO short gaps today; the
shortest surviving one is 11 years.

IT CANNOT ASSERT ZERO, and that is the point of the baseline. 6 of the 6 gaps on the
current database name a coverer -- they are periods when the entity did not exist as
itself and another family holds the territory:

    MNE-1913-1918 -> MNE-2006-2025   88y, Montenegro inside Yugoslavia
    CZE-1804-1918 -> CZE-1993-2025   75y, inside Czechoslovakia

Those two are the pair issue 82 named as UNREACHABLE, and they were, until the coverage
lookup started reading the published successor map -- see covered_elsewhere().

Two of the SHORT gaps are also correct, and they are why this check reports coverage
rather than only listing gaps:

    SYR 1945   covered by SYL-1944-1953, the "Syria and Lebanon" unit from fao1952

    The LBY 1949 entry that stood here was WRONG and is gone. It read "covered by
    CYR-1949-1951 and TRP-1943-1951 ... Libya was split into Cyrenaica and
    Tripolitania". Libya was split into THREE: Fezzan, about 550,000 km2 or a third of
    the country, was under FRENCH military administration and has no row at all. Two
    thirds of a country is not coverage, and 28 rows labelled `Libya` for 1949 were
    landing on Cyrenaica alone as a result. Fixed on 2026-08-05 by starting
    LBY-1949-1951 in 1949 -- the year of UN Resolution 289 -- which is what that row's
    own summary always claimed it did.
    SYR 1945   covered by SYL-1944-1953, the "Syria and Lebanon" unit from fao1952

THE FOUR UNCOVERED YEARS ISSUE 77 LISTED ARE ALL FIXED as of 2026-08-13: TCD 1919,
SEN 1959, LAO 1953 and CIV 1900-1901, each by moving one boundary of one row so the
two spans meet. Their baseline entries are deleted above with the measurement that
retired them. Two things the issue said about them turned out to be wrong:

  * "No source currently has data in any of the four ... they are latent, not live."
    Half true. mitchell has 14 Senegal observations for 1959 and 2 Lao observations
    for 1953, and matched.csv showed them already routed to spans that formally ended
    the year before, because the matcher reads end_year as INCLUSIVE. The dangerous
    fallback the issue predicted was already happening; it was invisible because the
    two candidate polygons are identical in both cases. TCD 1919 and CIV 1900-1901
    were latent as claimed.

  * "Each is a real historical question rather than a transcription slip." Not for
    Chad or Côte d'Ivoire. Both were dropped CShapes 2.0 steps -- Chad's 1919-06-28
    to 1920-03-16, Côte d'Ivoire's 1900-11-15 to 1902-03-19 -- with the same area as
    their neighbours, so absorbing them was arithmetic, not judgement.

What remains open is the one genuinely historical part: the MALI FEDERATION has no
polity, so Federation-labelled data for 1959-1960 still has nowhere to go even though
Senegal-labelled data now does.

    The cross-family lookup added for issue 82 is what makes that checkable: when this
    check said "no cover found" it was reporting the LOOKUP's reach, not the database's --
    AOF-1895-1960 held Senegal 1959 and FID-1887-1954 held Laos 1953 all along. Those two
    are no longer baselined, because issue 77 closed the spans outright; the lesson stands
    for whatever lands here next.

Usage:
  python3 scripts/validate_period_gaps.py
"""
from __future__ import annotations

import csv
import os
import re
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(REPO, "data/final/polities_database.csv")
ALIAS = os.path.join(REPO, "data/final/label_alias_map.csv")
SUCCESSOR_MAP = os.path.join(REPO, "data/final/iso3_successor_map.csv")
DEAD_STATUS = ("retired", "superseded")
CODE_RE = re.compile(r"^(.*)-(\d{4})-(\d{4})$")

# (earlier_code, later_code) pairs with a known gap between them. See the docstring:
# most are correct, four are issue 77.
BASELINE = frozenset({
    # ("ANT-1816-1960", "ANT-1961-2010") removed 2026-08-17 (issue 252): the gap is CLOSED, by
    # moving ANT-1816-1960's exclusive end_year to 1961 (renamed ANT-1816-1961). The page said in
    # so many words "End year 1960 is the final year before the existing ANT-1961-2010 row
    # begins" -- an inclusive reading of an exclusive column. This gate had annotated the gap
    # "source reaches it", and it was right for a reason worth recording: all nine published
    # `Netherlands W Indies`-family aliases carry the inclusive `year_end: 1960`, so they claimed
    # a year their target did not cover and sat in validate_alias_year_baseline.txt for it. One
    # boundary move cleared both gates at once. No territory changes; the polygon is the same
    # composed-union island proxy for every year of the span.
    ("BFA-1919-1932", "BFA-1947-1960"),
    # ("CHL-1810-1883", "CHL-1884-1899") removed 2026-08-06: the gap is CLOSED, by moving
    # CHL-1810-1883's exclusive end_year to 1884 so the two spans meet. It had sat here as an
    # accepted one-year gap; whep_crops v1.0 put 7 observed crop rows into 1883, which turned an
    # accepted hole into a routing failure. The gate was right that a gap existed and gave no
    # reason to think it mattered -- external data is what settled that.
    # ("GHA-1898-1956", "GHA-1957-2025") removed 2026-08-17 (issue 252): the gap is CLOSED, by
    # moving GHA-1898-1956's exclusive end_year to 1957 (renamed GHA-1898-1957). The alias
    # `Gold Coast` [fao1952] already claimed to 1956 with 36 observed rows behind it. This gate
    # had annotated the year "covered by BTL-1920-1957", which is TRUE and IRRELEVANT: British
    # Togoland is a ~33,771 km2 slice of the Gold Coast's east, not a stand-in for the colony, so
    # Gold-Coast-labelled 1956 data landing there would have been off by 7x in the wrong
    # direction. The direction of the fix was chosen against CShapes 2.0, which opens a
    # 1956-03-06 step at 239,046.81 km2 (Gold Coast WITH Togoland integrated): starting
    # GHA-1957-2025 in 1956 instead would have published that polygon for a year in which
    # BTL-1920-1957 still holds Togoland, double-counting the same ground.
    # ("HUN-1918-1919", "HUN-1920-1938") removed 2026-08-17 (issue 252): the gap is CLOSED, by
    # moving HUN-1918-1919's exclusive end_year to 1920 (renamed HUN-1918-1920). This one was
    # SELF-INFLICTED and recently: on 2026-06-30 the row's end_year was moved 1920 -> 1919 to stop
    # harvest-year 1920 data landing on the 325,421 km2 pre-Trianon polygon. Under the exclusive
    # convention end_year=1920 already excluded 1920, so the shortening went one year too far and
    # left the row covering 1918 alone -- contradicting its own page, whose data-routing table has
    # always said 1919 routes here. Restoring end_year=1920 keeps year-1920 data on
    # HUN-1920-1938 (~93,000 km2) and gives 1919 back its row.
    # ("KEN-1902-1906", "KEN-1907-1924") removed 2026-08-17 (issue 252): the gap is CLOSED, by
    # moving KEN-1902-1906's exclusive end_year to 1907 (renamed KEN-1902-1907). CShapes 2.0
    # decides it without judgement: gwcode 501 runs 1902-05-15 to 1906-12-31 and the next step
    # opens 1907-01-01, so the row's own step ends with the calendar year 1906. Both steps
    # measure 772,553.06 km2, so absorbing the year moves no territory. Latent, as this gate
    # said: no Kenyan observation in the layer B before 1907.
    # ("CIV-1893-1900", "CIV-1902-1932") removed 2026-08-13 (issue 77): the gap is CLOSED. The
    # cause was not "an error in one of the two end dates" as the issue guessed but a CShapes 2.0
    # step WHEP never transcribed -- 1900-11-15 to 1902-03-19, the move of the capital from
    # Grand Bassam to Bingerville, at the same 321,307.9 km2 as the steps on either side. Absorbed
    # by moving CIV-1893-1900's exclusive end_year to 1902 (renamed CIV-1893-1902), which loses no
    # territory. Latent: the layer B has no Ivorian observation for 1900 or 1901.
    ("CZE-1804-1918", "CZE-1993-2025"),
    ("ERI-1889-1952", "ERI-1993-2025"),
    # ("LAO-1893-1953", "LAO-1954-2025") removed 2026-08-13 (issue 77): the gap is CLOSED, by
    # moving LAO-1893-1953's exclusive end_year to 1954 (renamed LAO-1893-1954). NOT latent, which
    # is where the issue was wrong: mitchell has 2 Lao observations for 1953 (rice paddy area and
    # production) and data/compiled/pre1961/matched.csv shows both already routed to a row whose
    # span formally ended in 1952, because the matcher reads end_year as inclusive. Independence
    # fell on 22 October 1953, so the colonial row holds ten months of the year; every CShapes Laos
    # step measures 229,904.6 km2, so the direction costs no precision.
    # ("LBY-1943-1949", "LBY-1949-1951") removed 2026-08-05: the gap is CLOSED, not
    # re-explained. LBY-1949-1951 previously started in 1950 while its own summary claimed to
    # "close the 1949-1951 gap", leaving 1949 uncovered and sending 28 rows labelled `Libya`
    # to Cyrenaica alone. Moving its start to 1949 -- the year of UN Resolution 289 -- closed
    # it, and this gate then required the baseline entry to be deleted rather than kept.
    ("MNE-1913-1918", "MNE-2006-2025"),
    # MOR pair removed 2026-08-05: MOR-1956-1958 is retired (it duplicated 1956-1957,
    # which MAR-1911-1958 covers), leaving family MOR with a single period and so no
    # consecutive pair to gap.
    #
    # THE HOLE IT REPRESENTED IS STILL THERE and this check can no longer see it.
    # MOR-1800-1904 ends 1903, MAR-1911-1958 begins 1911, so 1904-1910 is covered by
    # nothing. It is now a CROSS-FAMILY hole, and this check is per-family by
    # construction. Exactly the blind spot issue 82 is about.
    #
    # Sharpened 2026-08-05 after joining against the observations: the "French Morocco"
    # alias claims from 1904 and carries 261 rows, which I first cited here as if they
    # landed in the hole. They do not -- every one is 1937-1951, inside MAR-1911-1958.
    # The hole routes ZERO rows today. Real as coverage, empty in practice, and the
    # alias's 1904 records when French influence began rather than where data is.
    #
    # STILL TRUE ON 2026-08-13, and now measurable rather than remembered. The alias no
    # longer claims 1904 either -- issue 54 clipped it to 1911-1956 on 2026-08-11 -- so the
    # sentence above describes a range that is gone. What survives is the coverage hole:
    # the published successor map resolves MAR for 1850-1903 (to MOR-1800-1904) and MAR's
    # own rows begin 1911, leaving 1904-1910 resolved by nothing. 7 years, in a map that
    # otherwise answers 74 modern codes. Still a CROSS-FAMILY hole and still unseen here,
    # because this check pairs CONSECUTIVE PERIODS OF ONE FAMILY. Issue 82.
    # ("SEN-1886-1959", "SEN-1960-2025") removed 2026-08-13 (issue 77): the gap is CLOSED, by
    # moving SEN-1886-1959's exclusive end_year to 1960 (renamed SEN-1886-1960). NOT latent either:
    # mitchell has 14 Senegal observations for 1959 and matched.csv shows all 14 already routed to
    # the colonial row. Senegal entered the Mali Federation on 4 April 1959 and its boundaries did
    # not move -- both CShapes Senegal steps measure 195,995.8 km2 -- so the earlier row takes the
    # year. The Mali Federation itself still has no polity; see oq-sen-mali-federation-entity.
    # SER pair removed 2026-08-05: SER-2006-2008 is retired (a duplicate of
    # SRB-2006-2008, issue 43), so family SER ends at SER-1918-1945 and has no
    # consecutive pair to gap.
    #
    # THIS ENTRY CLAIMED A HOLE THAT DOES NOT EXIST, and the claim is withdrawn here
    # rather than deleted. It read: "the 1945-2006 hole is still there -- SER-1918-1945
    # ends 1944, SRB-2006-2008 begins 2006, and no polity covers the Serbian republic
    # within SFR Yugoslavia in between".
    #
    # Measured against data/final/iso3_successor_map.csv on 2026-08-13, EVERY year of
    # 1945-2005 resolves for modern code SRB:
    #     1945-1946  F248-1920-1947      1991       F248-1991-1992
    #     1947-1990  F248-1947-1991      1992-2005  SCG-1992-2006
    # Nothing is uncovered. The gap was never a hole in the DATABASE; it was a hole in
    # the LOOKUP, which compared iso3_code (SER/SRB) against a holder coded YUG. The MOR
    # 1904-1910 hole above is the real one, and it is the only one of issue 82's three
    # examples that survives measurement.
    # ("SYR-1922-1945", "SYR-1946-1967") removed 2026-08-17 (issue 252): the gap is CLOSED, by
    # moving SYR-1922-1945's exclusive end_year to 1946 (renamed SYR-1922-1946). The page's own
    # prose always said the row ran "to the end of 1945" and cited the CShapes step 1922-12-02 to
    # 1945-12-31, whose successor opens 1946-01-01; only the columns said otherwise. Both steps
    # measure 187,993.23 km2. The "covered by SYL-1944-1953" annotation this gate printed was a
    # true statement about a LARGER unit (fao1952's joint "Syria and Lebanon"), which cannot serve
    # Syria-labelled data without overstating its area -- see the note in
    # validate_period_overlaps.py, where closing this hole also removed the SYR<->SYL family link
    # and with it that gate's view of a real containment.
    # ("TCD-1912-1919", "TCD-1920-1960") removed 2026-08-13 (issue 77): the gap is CLOSED, by
    # moving TCD-1920-1960's start_year back to 1919 (renamed TCD-1919-1960). The three AEF
    # siblings decided it: GAB-1919-1960, CAF-1919-1960 and COG-1919-1960 all start at the same
    # 28 June 1919 post-Versailles restoration, and Chad is the only one of the four whose CShapes
    # record is split again at 1920-03-17 (its separation from Oubangui-Chari). WHEP transcribed
    # the second half of that split and dropped the first, which is why Chad alone had a 1919 hole.
    # Both steps measure 1,271,888 km2, so nothing territorial is lost -- while extending
    # TCD-1912-1919 instead would have published the 1911 Neukamerun cession dip (1,220,971 km2)
    # for a year in which it had already been reversed. Latent: no Chad observation before 1953.
    ("VNM-1887-1954", "VNM-1975-2025"),
    ("ZWE-1900-1953", "ZWE-1964-1980"),
})


# SEVERITY SPLIT, added 2026-08-17 for issue 252.
#
# A LONG gap and a SHORT gap are different animals, and until now the baseline treated them
# alike. A multi-year gap is normally a territory genuinely held by someone else --
# Montenegro inside Yugoslavia, Czechia inside Czechoslovakia -- and it needs a note naming
# the holder. A one- or two-year gap asserts an interregnum of a year or two, which almost
# never happened: every one of the nine short gaps this gate has ever recorded turned out to
# be a boundary written as if `end_year` were inclusive, or a CShapes step WHEP never
# transcribed. TCD 1919, SEN 1959, LAO 1953 and CIV 1900-1901 (issue 77), CHL 1883, LBY 1949,
# and ANT 1960 / GHA 1956 / HUN 1919 / KEN 1906 / SYR 1945 (issue 252). None survived contact
# with its source.
#
# So a short gap is presumed an ERROR and fails even if someone baselines it; only an entry
# in SHORT_GAP_ACCEPTED, which has to say why, keeps it. That set is EMPTY today: after issue
# 252 the shortest surviving gap is 11 years (ZWE inside the Rhodesian federation). An
# accepted short gap must be argued in the entry, not merely listed.
SHORT_GAP_MAX = 2
SHORT_GAP_ACCEPTED: dict = {
    # code_pair -> why a gap of <= SHORT_GAP_MAX years is genuinely correct here.
    # Empty on purpose. If you add one, name the polity that holds the territory in the
    # missing year and say why the boundary cannot simply move.
}


def live_rows() -> list:
    with open(DB, encoding="utf-8") as fh:
        return [
            r
            for r in csv.DictReader(fh)
            if (r.get("wiki_status") or "") not in DEAD_STATUS
        ]


def successor_map() -> dict:
    """(modern_iso3, year) -> [(polity_code, hop_depth)] from the published successor map.

    THIS IS THE CROSS-FAMILY TERRITORY LINK, and it is published rather than inferred here:
    `scripts/write_iso3_successor_map.py` derives it from the database's own predecessor and
    successor edges. `hop_depth` 1 means the database asserts the relation directly; 2+ is an
    inference through intermediate rows and should be read as one.

    Missing file -> empty, so the annotation degrades to iso3 equality rather than crashing.
    """
    out = defaultdict(list)
    if not os.path.exists(SUCCESSOR_MAP):
        return out
    with open(SUCCESSOR_MAP, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                out[(r["modern_iso3"], int(r["year"]))].append(
                    (r["polity_code"], int(r["hop_depth"]))
                )
            except (KeyError, TypeError, ValueError):
                continue
    return out


def covered_elsewhere(rows: list, smap: dict, keys: tuple, year: int, exclude: set) -> list:
    """Who else holds this territory in this year: same-iso3 rows, plus the successor map.

    This is what separates a correct gap from a hole. Libya's 1949 looks identical to
    Chad's 1919 until you ask who else holds the territory: Cyrenaica and Tripolitania
    do for Libya, nothing does for Chad.

    iso3 EQUALITY ALONE GOT TWO OF THESE WRONG, which is issue 82, and the wrong answers
    were not the ones that issue and an earlier version of this docstring recorded. Both
    claimed the aggregates carry no iso3 at all -- "`F51-1947-1993` (Czechoslovakia) and
    `F248-1947-1991` (Yugoslavia) both have `iso3_code = ''`". Measured on the current
    database they carry `CSK` and `YUG`. The defect is not an EMPTY code, it is a
    DIFFERENT one: the family whose gap is being tested carries `CZE`/`MNE` and the family
    that holds the territory carries `CSK`/`YUG`, so equality matches nothing. Same shape
    as the local-versus-ISO case (`MOR-*` beside `MAR-*`) rather than a second failure mode.

    The fix is to consult the successor map, which links exactly those pairs and is derived
    from the chain graph, so it cannot drift from the database:

        CZE 1918-1992 -> F51-1947-1993 at depth 1   (was "no cover found")
        MNE 1918-2005 -> F248/SCG                   (was "no cover found")
        ERI 1952-1992 -> ETH-1952-1993 at depth 1   (was "no cover found")

    STILL ADVISORY, and the gate still does not act on it -- only the baseline comparison
    decides pass or fail. The remaining reason not to promote it: the map answers "who held
    this territory" for the years it resolves, and its silence is not proof of absence (109
    (iso3, year) pairs are unresolved for want of rows, not for want of traversal). Treat
    the annotation as a triage hint and check the specific case.
    """
    out = set()
    for r in rows:
        if r["polity_code"] in exclude or (r.get("iso3_code") or "") not in keys:
            continue
        try:
            if int(r["start_year"]) <= year < int(r["end_year"]):
                out.add(r["polity_code"])
        except (TypeError, ValueError):
            continue
    for key in keys:
        for code, depth in smap.get((key, year), []):
            if code not in exclude:
                out.add(f"{code} (map depth {depth})" if depth > 1 else code)
    return sorted(out)


def alias_claims(year: int, iso3: str) -> int:
    """Alias rows claiming this year for a polity that itself spans it.

    Answers "does any source actually reach this year", which is what makes a hole
    latent rather than live.
    """
    if not os.path.exists(ALIAS):
        return 0
    with open(ALIAS, encoding="utf-8") as fh:
        n = 0
        for r in csv.DictReader(fh):
            code = r.get("polity_code") or ""
            if not code.startswith(iso3):
                continue
            try:
                if int(r["year_start"]) <= year <= int(r["year_end"]):
                    n += 1
            except (KeyError, TypeError, ValueError):
                continue
        return n


def main() -> int:
    rows = live_rows()
    fam = defaultdict(list)
    for r in rows:
        m = CODE_RE.match(r["polity_code"])
        if m:
            fam[m.group(1)].append(
                (int(m.group(2)), int(m.group(3)), r["polity_code"], r.get("iso3_code") or "")
            )

    observed = {}
    for periods in fam.values():
        if len(periods) < 2:
            continue
        periods.sort()
        for i in range(1, len(periods)):
            prev_end = periods[i - 1][1]
            start = periods[i][0]
            if start > prev_end:
                observed[(periods[i - 1][2], periods[i][2])] = (
                    prev_end,
                    start - 1,
                    periods[i][3],
                )

    multi = sum(1 for v in fam.values() if len(v) > 1)
    print(f"live polities: {len(rows)} | multi-period families: {multi}")
    print(f"families with a gap between consecutive periods: {len(observed)}")

    short = {p for p, v in observed.items() if v[1] - v[0] + 1 <= SHORT_GAP_MAX}
    print(
        f"of which {len(short)} are {SHORT_GAP_MAX} years or shorter, which this gate "
        f"presumes to be an error rather than an interregnum"
    )

    smap = successor_map()
    for pair, (lo, hi, iso3) in sorted(observed.items(), key=lambda kv: -(kv[1][1] - kv[1][0])):
        span = hi - lo + 1
        # Look the territory up under BOTH the row's iso3 and its family prefix. They are
        # usually equal, but the successor map is keyed by the prefix, and a row with an
        # empty iso3 (71 of them today, all aggregates and pre-ISO states) would otherwise
        # be unlookupable -- which is the shape issue 82 mis-diagnosed as the whole defect.
        m = CODE_RE.match(pair[1])
        keys = tuple(k for k in {iso3, m.group(1) if m else ""} if k)
        others = covered_elsewhere(rows, smap, keys, lo, {pair[0], pair[1]}) if keys else []
        if others:
            tag = f"covered by {', '.join(others[:2])}"
        else:
            claims = alias_claims(lo, iso3) if iso3 else 0
            tag = "no cover found, source reaches it" if claims else "no cover found, seems latent"
        print(f"   {span:>4}y  {pair[0]:<20} -> {pair[1]:<20} ({lo}-{hi})  {tag}")

    problems = []
    for pair in sorted(short - set(SHORT_GAP_ACCEPTED)):
        lo, hi, _ = observed[pair]
        span = hi - lo + 1
        problems.append(
            f"SHORT gap: {pair[0]} ends before {pair[1]} begins, leaving {lo}-{hi} "
            f"({span}y) in no polity of that family. A gap of {SHORT_GAP_MAX} years or less "
            f"asserts an interregnum that almost never happened — read it as a boundary "
            f"written with an INCLUSIVE end_year, or as an untranscribed source step, and "
            f"move one boundary so the spans meet. Baselining it is not enough: add it to "
            f"SHORT_GAP_ACCEPTED with the polity that holds the territory if the gap is real"
        )
    for pair in sorted(set(observed) - BASELINE - short):
        lo, hi, _ = observed[pair]
        problems.append(
            f"NEW gap: {pair[0]} ends before {pair[1]} begins, leaving {lo}-{hi} in no "
            f"polity of that family — a year-aware matcher gets no answer"
        )
    for pair in sorted(BASELINE - set(observed)):
        problems.append(
            f"{pair[0]} -> {pair[1]} is baselined as gapped but no longer is — "
            f"remove the pair from BASELINE in this script"
        )
    for pair in sorted(set(SHORT_GAP_ACCEPTED) - set(observed)):
        problems.append(
            f"{pair[0]} -> {pair[1]} is in SHORT_GAP_ACCEPTED but is not gapped — "
            f"remove the entry (baselines here are bidirectional)"
        )
    for pair in sorted(BASELINE & short):
        problems.append(
            f"{pair[0]} -> {pair[1]} is a short gap sitting in BASELINE — short gaps are "
            f"governed by SHORT_GAP_ACCEPTED, which requires a reason; move it or fix it"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: family period gaps match the baseline exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
