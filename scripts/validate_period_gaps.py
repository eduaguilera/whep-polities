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

IT CANNOT ASSERT ZERO, and that is the point of the baseline. 13 of the 19 gaps are
correct -- they are periods when the entity did not exist as itself and another
family holds the territory:

    MNE-1913-1918 -> MNE-2006-2025   88y, Montenegro inside Yugoslavia
    CZE-1804-1918 -> CZE-1993-2025   75y, inside Czechoslovakia

Two of the SHORT gaps are also correct, and they are why this check reports coverage
rather than only listing gaps:

    LBY 1949   covered by CYR-1949-1951 and TRP-1943-1951, both iso3 LBY --
               Libya was split into Cyrenaica and Tripolitania
    SYR 1945   covered by SYL-1944-1953, the "Syria and Lebanon" unit from fao1952

Four are genuinely uncovered and all are latent today, since no source reaches them:
TCD 1919, SEN 1959, LAO 1953, and CIV 1900-1901. Each is a real historical question
rather than a slip -- Senegal was in the Mali Federation in 1959, Laos gained
independence in October 1953 -- so they are baselined for issue 77 rather than
patched.

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
DEAD_STATUS = ("retired", "superseded")
CODE_RE = re.compile(r"^(.*)-(\d{4})-(\d{4})$")

# (earlier_code, later_code) pairs with a known gap between them. See the docstring:
# most are correct, four are issue 77.
BASELINE = frozenset({
    ("ANT-1816-1960", "ANT-1961-2010"),
    ("BFA-1919-1932", "BFA-1947-1960"),
    ("CHL-1810-1883", "CHL-1884-1899"),
    ("GHA-1898-1956", "GHA-1957-2025"),
    ("HUN-1918-1919", "HUN-1920-1938"),
    ("KEN-1902-1906", "KEN-1907-1924"),
    ("CIV-1893-1900", "CIV-1902-1932"),
    ("CZE-1804-1918", "CZE-1993-2025"),
    ("ERI-1889-1952", "ERI-1993-2025"),
    ("LAO-1893-1953", "LAO-1954-2025"),
    ("LBY-1943-1949", "LBY-1950-1951"),
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
    ("SEN-1886-1959", "SEN-1960-2025"),
    # SER pair removed 2026-08-05: SER-2006-2008 is retired (a duplicate of
    # SRB-2006-2008, issue 43), so family SER ends at SER-1918-1945 and has no
    # consecutive pair to gap.
    #
    # SAME BLIND SPOT AS THE MOR PAIR ABOVE. The 1945-2006 hole is still there --
    # SER-1918-1945 ends 1944, SRB-2006-2008 begins 2006, and no polity covers the
    # Serbian republic within SFR Yugoslavia in between. It is now a CROSS-FAMILY
    # hole (SER -> SRB) and this check is per-family, so it cannot see it. Issue 82.
    ("SYR-1922-1945", "SYR-1946-1967"),
    ("TCD-1912-1919", "TCD-1920-1960"),
    ("VNM-1887-1954", "VNM-1975-2025"),
    ("ZWE-1900-1953", "ZWE-1964-1980"),
})


def live_rows() -> list:
    with open(DB, encoding="utf-8") as fh:
        return [
            r
            for r in csv.DictReader(fh)
            if (r.get("wiki_status") or "") not in DEAD_STATUS
        ]


def covered_elsewhere(rows: list, iso3: str, year: int, exclude: set) -> list:
    """Live polities of ANOTHER family sharing this iso3 and spanning the year.

    This is what separates a correct gap from a hole. Libya's 1949 looks identical to
    Chad's 1919 until you ask who else holds the territory: Cyrenaica and Tripolitania
    do for Libya, nothing does for Chad.

    ADVISORY, NOT AUTHORITATIVE, and the gate does not act on it -- only the baseline
    comparison decides pass or fail. iso3 is the only cross-family link the data has and
    it fails two ways:

      * AGGREGATES CARRY NO iso3. `F51-1947-1993` (Czechoslovakia) and `F248-1947-1991`
        (Yugoslavia) both have `iso3_code = ''`, so the CZE 1918-1992 and SER 1945-2005
        gaps are reported uncovered when Czechoslovakia and Yugoslavia in fact hold
        that territory.
      * LOCAL AND ISO CODES FOR ONE TERRITORY DO NOT LINK. Morocco is `MOR-*` (a
        declared local code) and `MAR-*` (the ISO one), so the "French Morocco" alias
        -- 261 observed rows, pointing at `MAR-1911-1958` -- is invisible when testing
        the MOR family's gap, and that gap reads latent when it is live.

    Both are the same missing thing: nothing expresses "these families are the same
    territory". Treat the annotation as a triage hint and check the specific case.
    """
    out = []
    for r in rows:
        if r["polity_code"] in exclude or (r.get("iso3_code") or "") != iso3:
            continue
        try:
            if int(r["start_year"]) <= year < int(r["end_year"]):
                out.append(r["polity_code"])
        except (TypeError, ValueError):
            continue
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

    for pair, (lo, hi, iso3) in sorted(observed.items(), key=lambda kv: -(kv[1][1] - kv[1][0])):
        span = hi - lo + 1
        others = covered_elsewhere(rows, iso3, lo, {pair[0], pair[1]}) if iso3 else []
        if others:
            tag = f"covered by {', '.join(others[:2])}"
        else:
            claims = alias_claims(lo, iso3) if iso3 else 0
            tag = "no cover found, source reaches it" if claims else "no cover found, seems latent"
        print(f"   {span:>4}y  {pair[0]:<20} -> {pair[1]:<20} ({lo}-{hi})  {tag}")

    problems = []
    for pair in sorted(set(observed) - BASELINE):
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

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: family period gaps match the baseline exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
