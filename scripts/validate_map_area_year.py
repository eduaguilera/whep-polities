#!/usr/bin/env python3
"""Check that no (area_code, year) in the published FAOSTAT map has two live answers.

`validate_period_overlaps.py` asks the same question of the polity TABLE, where a
code's `end_year` is EXCLUSIVE. This asks it of `data/final/faostat_area_polity_map.csv`,
where `year_start`/`year_end` are INCLUSIVE. Those two conventions meet at every
handover year, and nothing was comparing the map's ranges against each other.

The gap is not theoretical. Two areas assign a transfer year to BOTH the outgoing and
the incoming polity:

    area 205  year 1975   RESOLVED 2026-08-11 -- it was not a convention question at all.
                          The registry route wrote `year_end = pmin(end_year, 2025)`, copying the
                          polity code's EXCLUSIVE end year into an INCLUSIVE column, so area 205's
                          first row claimed 1975 while ESH-1975-2025 already owned it. Fixed in
                          match.R; ambiguity went 1 -> 0 with no data moved (both rows had
                          rows_observed = 0).
    area 240  year 1917   DWI-1800-1917  and  VIR-1917-2025

Both are real mid-year handovers -- Spanish Sahara's 1975 Madrid Accords, and the 1917
sale of the Danish West Indies to the United States. A consumer joining on year
containment gets two candidates and picks by row order, which is the same failure mode
as a duplicated polity period but originating in the map rather than in the table.

`validate_period_overlaps` cannot see these: read from the database, with the exclusive
convention, `DWI-1800-1917` covers through 1916 and genuinely does not overlap
`VIR-1917-2025`. The ambiguity exists only in the published ranges.

BASELINED rather than asserted to zero. Both pairs need a convention decided -- does a
handover year belong to the outgoing polity, the incoming one, or is it split? -- and
that is issue 74. This gate exists so a THIRD one cannot appear unnoticed while that is
open, and so the list shrinks when it is settled.

Dead polities are excluded: a retired or superseded row is not a resolution candidate,
so it cannot make an answer ambiguous.

Usage:
  python3 scripts/validate_map_area_year.py
"""
from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(REPO, "data/final/faostat_area_polity_map.csv")
DB = os.path.join(REPO, "data/final/polities_database.csv")
DEAD_STATUS = ("retired", "superseded")

# (area_code, year) pairs known to have two live answers. See the module docstring.
BASELINE = frozenset({
    # area 240 year 1917 cleared 2026-08-05 by the Group A alias clip (issue 90): the earlier
    # alias stopped claiming 1917, which its successor covers. Left as a set with one entry
    # rather than emptied so a regression still names the pair.
})


def live_polity_codes() -> set:
    with open(DB, encoding="utf-8") as fh:
        return {
            r["polity_code"]
            for r in csv.DictReader(fh)
            if (r.get("wiki_status") or "") not in DEAD_STATUS
        }


# THE MAP MAY DECLARE A FINAL REPORTING YEAR THE POLITY DOES NOT COVER, for exactly four areas.
#
# `end_year` is exclusive here and the map's `year_end` is inclusive, so a consistent row has
# `end_year == year_end + 1`. Measured over the 281 published mappings, by match_route:
#
#     iso-equal        {0: 2, 1: 243, 2: 1, 12: 1, 19: 2}
#     manual-replace   {0: 2, 1: 3}
#     manual-route     {1: 6, 19: 2}
#     manual-span      {1: 1}
#     registry         {0: 16, 1: 2}   <- a generator bug, fixed in match.R on 2026-08-11
#
# The registry block was mechanical and is gone. The four below are not: each is a FINAL REPORTED
# YEAR for a dissolved entity, and each is a year the successor polities already claim.
#
#     area  15  1961-1999  BLX-1850-1999    covers ..1998   Belgium-Luxembourg
#     area 151  1961-2010  ANT-1961-2010    covers ..2009   Netherlands Antilles
#     area 206  1961-2011  SUD-1956-2011    covers ..2010   Sudan (former)
#     area 228  1961-1991  F228-1945-1991   covers ..1990   USSR
#
# ACCEPTED RATHER THAN FIXED, which is issue 164's third option and what WHEP now assumes. The
# alternatives are worse: moving the polity end years is invasive (the year is embedded in
# polity_code, and each successor already starts in the current end_year, so it would create an
# overlap), and dropping the map's year_end loses a reported year -- for areas 15 and 151 the
# target is an `aggregate`, which WHEP's nearest-period fallback deliberately skips, so the row
# would go to NA and be dropped rather than relabelled.
#
# So the disagreement is data, and this pins it at exactly these four. Bidirectional: a fifth
# fails, and one that gets resolved fails until it is removed.
# frozenset, not a bare {...}: an empty set literal is a DICT, and once these four are resolved
# the set arithmetic below would raise TypeError. validate_constants enforces this, and caught it.
BASELINE_YEAR_END_PAST_COVERAGE = frozenset({
    ("15", "BLX-1850-1999"),
    ("151", "ANT-1961-2010"),
    ("206", "SUD-1956-2011"),
    ("228", "F228-1945-1991"),
})
CEILING = 2025


def year_end_past_coverage(mappings, spans):
    """(area_code, polity_code) pairs whose inclusive year_end reaches past the polity's coverage.

    Open-ended rows are excluded: a live polity whose exclusive end_year IS the 2025 ceiling has
    no real last year, so `year_end == 2025` is the ceiling showing through rather than an
    overshoot, and 13 registry rows sat there for that reason alone.
    """
    out = set()
    for m in mappings:
        span = spans.get(m.get("polity_code"))
        if not span:
            continue
        try:
            end_year, year_end = int(span[1]), int(m["year_end"])
        except (TypeError, ValueError):
            continue
        if end_year >= CEILING:
            continue
        if end_year - year_end <= 0:
            out.add((str(m["area_code"]), m["polity_code"]))
    return out


def polity_spans() -> dict:
    """polity_code -> (start_year, end_year) for every row, dead included.

    Dead rows are kept here deliberately, unlike live_polity_codes(): the ambiguity check asks
    which polities a consumer could RESOLVE to and so excludes them, but this check asks whether
    a map row's declared years fit the row it names, and a mapping pointing at a dead polity with
    the wrong years is still wrong.
    """
    out = {}
    with open(DB, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                out[r["polity_code"]] = (int(r["start_year"]), int(r["end_year"]))
            except (KeyError, TypeError, ValueError):
                continue
    return out


def main() -> int:
    live = live_polity_codes()
    with open(MAP, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    # Expand each mapping to the years it claims. `year_end` is INCLUSIVE here, which is
    # the whole point of this check -- reading it as exclusive would hide the very rows
    # it exists to find.
    claims = defaultdict(set)
    skipped = 0
    for r in rows:
        code = (r.get("polity_code") or "").strip()
        if code not in live:
            skipped += 1
            continue
        try:
            start = int(r["year_start"])
            end = int(r["year_end"])
        except (KeyError, TypeError, ValueError):
            continue
        area = (r.get("area_code") or "").strip()
        for year in range(start, end + 1):
            claims[(area, year)].add(code)

    observed = {k: sorted(v) for k, v in claims.items() if len(v) > 1}

    print(f"{len(rows)} mappings, {skipped} to dead polities (excluded)")
    print(f"{len(claims)} (area, year) pairs claimed")
    print(f"ambiguous: {len(observed)}")
    for (area, year), codes in sorted(observed.items()):
        print(f"   area {area:<5} {year}  {', '.join(codes)}")

    # --- year_end past the polity's coverage -------------------------------------------
    spans = polity_spans()
    over = year_end_past_coverage(rows, spans)
    print(f"\nmap rows whose inclusive year_end reaches past their polity's coverage: {len(over)} "
          f"(open-ended rows at the {CEILING} ceiling excluded)")
    for area, code in sorted(over):
        end_year = spans[code][1]
        print(f"   area {area:<5} {code:16s} covers ..{int(end_year) - 1}, map declares the year after")

    problems = []
    for key in sorted(over - BASELINE_YEAR_END_PAST_COVERAGE):
        problems.append(
            f"NEW year_end past coverage: area {key[0]} -> {key[1]} declares a reporting year the "
            f"polity does not cover. Either the map's year_end is one too high, or a successor "
            f"should take that year (issue 164)"
        )
    for key in sorted(BASELINE_YEAR_END_PAST_COVERAGE - over):
        problems.append(
            f"area {key[0]} -> {key[1]} is baselined as declaring a year past its polity's "
            f"coverage but no longer does — remove it from BASELINE_YEAR_END_PAST_COVERAGE"
        )

    for key in sorted(set(observed) - BASELINE):
        codes = ", ".join(observed[key])
        problems.append(
            f"NEW ambiguity: area {key[0]} year {key[1]} resolves to {codes} — "
            f"a consumer joining on year containment picks by row order"
        )
    for key in sorted(BASELINE - set(observed)):
        problems.append(
            f"area {key[0]} year {key[1]} is baselined as ambiguous but no longer is — "
            f"remove it from BASELINE in this script"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: map (area, year) ambiguity matches the baseline exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
