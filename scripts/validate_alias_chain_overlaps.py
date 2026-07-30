#!/usr/bin/env python3
"""Check that consecutive aliases for one label do not both cover a year.

An alias `year_end` is INCLUSIVE while a polity `end_year` is EXCLUSIVE. So an alias
ending at a polity's last year and the next alias starting at its successor's first year
both cover that year, and which polity a value lands in is decided by whichever row the
matcher reaches first.

MEASURED FROM THE CONSUMER SIDE, which is where the effect shows. Sweeping every
(label, source) chain with more than one row, 25 have a year where two rows name
different polities, and the rate depends on how the aliases were written:

    (any)                        18 of 31 chains ambiguous   hand-entered
    fao1952                       3 of 18
    faostat                       2 of 43
    lassaletta-grassland-share    1 of 30   generated
    trade-sources                 0 of  7   generated

The generated sets are clean because they were built with `year_end = polity_end_year - 1`,
so consecutive ranges do not touch. That is not an arbitrary convention: it makes an alias
agree with the database's own exclusive `end_year`, so year Y resolves to the polity this
database says was live in Y.

WHY THIS GATES RATHER THAN FIXES. 91 rows would have their `year_end` moved back a year by
a mechanical pass. Each one changes which polity a boundary year's value lands in — from
undefined-by-match-order to defined — so it moves data, and one of the 91 is a deliberate
curation choice: the two Cape Verde rows overlap at 1975 on purpose, a decision about which
polity gets a mid-year independence. A bulk edit would erase that decision along with the
88 accidents. The recommendation and the measurement are on issue #54; this script makes
sure the count cannot grow while that is decided.

Most of the 25 are benign in effect — the two candidates are adjacent periods of ONE
family, so a boundary value lands in one of two neighbouring periods of the same territory.
Five are cross-family and are the ones that need a historical decision rather than a
convention:

    botswana                      1966   BEC-1885-1966 / BWA-1966-2025
    china manchuria               1945   CHN-1945-1947 / MAN-1932-1945
    china, manchuria province of  1932   CHN-1921-1932 / MAN-1932-1945
    israel                        1948   ISR-1948-1967 / PAL-1920-1948
    serbia                        2006   SCG-1992-2006 / SER-2006-2008

Usage:
  python3 scripts/validate_alias_chain_overlaps.py
"""
import csv
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALIAS_MAP = os.path.join(REPO, "data/final/label_alias_map.csv")

# Chains whose consecutive ranges touch today, keyed "label||source". Bidirectional: a new
# one fails, and a chain that stops overlapping must be removed from here.
#
# Cape Verde is in this list but is NOT waiting to be fixed — its overlap is the deliberate
# mid-year-independence choice described above. Kept in one list rather than two because
# the check is the same; the distinction lives in this comment and in the issue.
BASELINE_PATH = os.path.join(
    REPO, "scripts/validate_alias_chain_overlaps_baseline.txt"
)


def load_baseline() -> set:
    if not os.path.exists(BASELINE_PATH):
        return set()
    with open(BASELINE_PATH, encoding="utf-8") as fh:
        return {
            line.strip()
            for line in fh
            if line.strip() and not line.startswith("#")
        }


def main() -> int:
    if not os.path.exists(ALIAS_MAP):
        print(f"FAIL: {ALIAS_MAP} missing; run scripts/write_label_alias_map.py")
        return 2

    chains = defaultdict(list)
    with open(ALIAS_MAP, encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            label = (row.get("source_label") or "").strip()
            source = (row.get("source") or "").strip()
            start = (row.get("year_start") or "").strip()
            end = (row.get("year_end") or "").strip()
            if not label:
                continue
            # An UNRANGED alias matches every year, so it overlaps every ranged row in its
            # chain by definition. Treating a missing bound as unbounded rather than
            # skipping the row is what catches that: the first version filtered NA years
            # out and missed "turkey", where an unranged row targeting TUR-1920-2025 sits
            # alongside a ranged 1913-1914 row targeting TUR-1913-1914, so 1913 resolves
            # by match order. Found by reconciling this count against the consumer's,
            # which swept year by year and reported 25 against this script's 24.
            try:
                lo = int(start) if start else -10**6
                hi = int(end) if end else 10**6
            except ValueError:
                continue
            chains[f"{label.lower()}||{source}"].append(
                (lo, hi, row.get("polity_code", ""))
            )

    overlapping = {}
    multi = 0
    for key, rows in chains.items():
        if len(rows) < 2:
            continue
        multi += 1
        rows.sort()
        for (s1, e1, p1), (s2, _e2, p2) in zip(rows, rows[1:]):
            if s2 <= e1 and p1 != p2:
                overlapping[key] = f"{s1}-{e1} and {s2}- both cover {s2}"
                break

    print(f"(label, source) chains with more than one alias: {multi}")
    print(f"chains whose consecutive ranges touch: {len(overlapping)}")

    baseline = load_baseline()
    problems = []
    new = sorted(set(overlapping) - baseline)
    if new:
        for key in new:
            print(f"   NEW  {key:<50}{overlapping[key]}")
        problems.append(
            f"{len(new)} chain(s) whose consecutive ranges touch and are not baselined. "
            f"Set year_end to the polity's end_year minus one so the boundary year "
            f"resolves to the polity this database says was live in it: {new}"
        )
    fixed = sorted(baseline - set(overlapping))
    if fixed:
        problems.append(
            f"baselined chains that no longer overlap — remove them: {fixed}"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print(
        f"\nPASS: overlapping alias chains match the baseline exactly "
        f"({len(baseline)} tracked)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
