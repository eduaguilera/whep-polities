#!/usr/bin/env python3
"""Check that an alias does not claim a year its target polity cannot cover.

A polity code's `end_year` is EXCLUSIVE: `BLX-1850-1999` covers 1850-1998. An alias
row's `year_end` is INCLUSIVE. So whenever an alias's `year_end` equals its target's
`end_year`, the alias claims one year the polity does not hold.

Measured when this was written: 265 alias rows do that, carrying 461,445 observed
rows between them. The four largest are entities whose FINAL REPORTING YEAR is the
disputed one, and FAOSTAT publishes a full year of data for each:

    156,557 rows  "Belgium-Luxembourg"  to 1999 -> BLX-1850-1999   covers to 1998
    139,921 rows  "Sudan (former)"      to 2011 -> SUD-1956-2011   covers to 2010
     91,616 rows  "USSR"                to 1991 -> F228-1945-1991  covers to 1990
     61,441 rows  "Netherlands Antilles" to 2010 -> ANT-1961-2010  covers to 2009

WHICH SIDE IS WRONG IS NOT SETTLED, which is why this gate baselines rather than
fails. Either the aliases overclaim by a year, or those polity codes end a year too
early and the aliases are right -- Belgium-Luxembourg did report as a unit FOR 1999.
Issue 79.

The failure is silent, which is the reason to gate it: a matcher that falls back to
the nearest period lands these rows on the ADJACENT polity rather than dropping them,
so 461k rows can be misattributed without anything looking broken.

Usage:
  python3 scripts/validate_alias_year_coverage.py [--list]
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIAS = os.path.join(REPO, "data/final/label_alias_map.csv")
DB = os.path.join(REPO, "data/final/polities_database.csv")
BASELINE = os.path.join(REPO, "scripts/validate_alias_year_baseline.txt")


def load_baseline() -> set:
    if not os.path.exists(BASELINE):
        return set()
    out = set()
    with open(BASELINE, encoding="utf-8") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) == 3:
                out.add(tuple(parts))
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="print every offender, not just new ones")
    args = ap.parse_args()

    with open(DB, encoding="utf-8") as fh:
        db = {r["polity_code"]: r for r in csv.DictReader(fh)}
    with open(ALIAS, encoding="utf-8") as fh:
        aliases = list(csv.DictReader(fh))

    observed = {}
    rows_at_risk = 0
    unknown_target = 0
    for r in aliases:
        code = (r.get("polity_code") or "").strip()
        target = db.get(code)
        if target is None:
            unknown_target += 1
            continue
        try:
            year_end = int(r["year_end"])
            polity_end = int(target["end_year"])
        except (KeyError, TypeError, ValueError):
            continue
        if year_end < polity_end:
            continue
        key = ((r.get("source_label") or ""), (r.get("source") or ""), code)
        try:
            n = int(r.get("observed_rows") or 0)
        except ValueError:
            n = 0
        if key not in observed:
            rows_at_risk += n
        observed[key] = (year_end, polity_end, n)

    baseline = load_baseline()
    print(f"{len(aliases)} alias rows, {unknown_target} pointing at no known polity")
    print(f"claiming a year past their polity's coverage: {len(observed)}")
    print(f"observed rows on those aliases: {rows_at_risk:,}")

    if args.list:
        for key, (ye, pe, n) in sorted(observed.items(), key=lambda kv: -kv[1][2]):
            print(f'   rows={n:>6}  "{key[0][:34]:34}" [{key[1][:12]:12}] to {ye} -> {key[2]} (covers to {pe - 1})')

    problems = []
    for key in sorted(set(observed) - baseline):
        ye, pe, n = observed[key]
        problems.append(
            f'NEW: "{key[0]}" [{key[1]}] claims to {ye} but {key[2]} covers only to '
            f"{pe - 1} ({n} observed rows)"
        )
    for key in sorted(baseline - set(observed)):
        problems.append(
            f'"{key[0]}" [{key[1]}] -> {key[2]} is baselined but no longer overclaims — '
            f"remove its line from scripts/validate_alias_year_baseline.txt"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: alias year coverage matches the baseline exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
