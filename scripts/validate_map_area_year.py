#!/usr/bin/env python3
"""Check that no (area_code, year) in the published FAOSTAT map has two live answers.

`validate_period_overlaps.py` asks the same question of the polity TABLE, where a
code's `end_year` is EXCLUSIVE. This asks it of `data/final/faostat_area_polity_map.csv`,
where `year_start`/`year_end` are INCLUSIVE. Those two conventions meet at every
handover year, and nothing was comparing the map's ranges against each other.

The gap is not theoretical. Two areas assign a transfer year to BOTH the outgoing and
the incoming polity:

    area 205  year 1975   ESH-1958-1975  and  ESH-1975-2025
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
BASELINE = {
    ("205", 1975),
    ("240", 1917),
}


def live_polity_codes() -> set:
    with open(DB, encoding="utf-8") as fh:
        return {
            r["polity_code"]
            for r in csv.DictReader(fh)
            if (r.get("wiki_status") or "") not in DEAD_STATUS
        }


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

    problems = []
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
