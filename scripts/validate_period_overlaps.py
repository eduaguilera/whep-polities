#!/usr/bin/env python3
"""Check that no two live polities in the same family cover the same year.

A polity code is `PREFIX-start-end`, and the family is the prefix. Within one family the
periods are meant to TILE time, not overlap: a year-aware matcher asked "which polity was
this territory in 1930" must get one answer. When two periods of the same prefix overlap,
the matcher's answer depends on tie-break order rather than on history, so the same label
and year can route to different polities depending on which matcher is asked — and the two
matchers in this repo are already known to disagree in exactly that way.

Found by asking the consumer's crosswalk which area-years resolve to more than one polity,
then checking the whole database rather than only the areas. Four pairs, three families:

  BLX-1850-1999 / BLX-1921-1999   78 years. The known Belgium-Luxembourg overlap
                                  (issue 40). BLX-1850-1999 carries 156,557 observed
                                  rows and BLX-1921-1999 carries none, so the shorter
                                  row is the inert one.
  PER-1825-1884 / PER-1825-1909   59 years, and
  PER-1825-1909 / PER-1884-1909   25 years. Note the shape: PER-1825-1884 and
                                  PER-1884-1909 TILE 1825-1909 exactly, so
                                  PER-1825-1909 is a redundant un-split row that
                                  duplicates both. No aliases and no FAOSTAT mappings
                                  point at any of the three.
  MNE-1913-1915 / MNE-1913-1918   2 years. Two readings of when Montenegro ended —
                                  Austro-Hungarian occupation in 1916 versus joining
                                  Yugoslavia in 1918. Both are defensible, so which one
                                  survives is a historical decision, not a mechanical one.

Baselined bidirectionally rather than asserted to zero: a NEW overlap fails, and a
baselined one that is resolved fails until it leaves the baseline. Dead rows are excluded,
since a retired polity receives no data and cannot make a matcher ambiguous.

Usage:
  python3 scripts/validate_period_overlaps.py
"""
import csv
import os
import re
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")

DEAD_STATUS = ("retired", "superseded")

# Each entry is the pair of codes, sorted, that may overlap. See the docstring.
BASELINE = {
    ("BLX-1850-1999", "BLX-1921-1999"),
    # Both PER pairs removed 2026-08-05: PER-1825-1909 is superseded by the 1884 split,
    # so neither pair overlaps any more. Issue 62's sibling case.
    # MNE-1913-1915 / MNE-1913-1918 removed 2026-08-05: the 1913-1915 row is retired as
    # a duplicate, so the pair no longer overlaps. Issue 62.
}

CODE_RE = re.compile(r"^(.*)-(\d{4})-(\d{4})$")


def faostat_mapped() -> set:
    """Polity codes a consumer can reach through the published FAOSTAT area map.

    Whether a finding is LIVE or merely LATENT turns on this, and it is cheap to compute here rather
    than by querying the consumer. Two findings on this branch were written up as live and had to be
    downgraded after checking: the Tanzania and Morocco period overlaps, whose inert twins are
    unmapped, and area 240's two-era mapping, which is correctly folded. Printing reachability next
    to each case makes the distinction visible instead of remembered.
    """
    path = os.path.join(REPO, "data/final/faostat_area_polity_map.csv")
    if not os.path.exists(path):
        return set()
    with open(path, encoding="utf-8") as fh:
        return {
            (r.get("polity_code") or "").strip()
            for r in csv.DictReader(fh)
            if (r.get("polity_code") or "").strip()
        }


def main() -> int:
    families = defaultdict(list)
    live = 0
    for r in csv.DictReader(open(POLITIES, encoding="utf-8")):
        if (r.get("wiki_status") or "").strip() in DEAD_STATUS:
            continue
        live += 1
        m = CODE_RE.match(r["polity_code"])
        if not m:
            # build_database.py gates the code shape, so this should be unreachable.
            continue
        families[m.group(1)].append(
            (int(m.group(2)), int(m.group(3)), r["polity_code"])
        )

    observed = {}
    for items in families.values():
        items.sort()
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                a, b = items[i], items[j]
                lo, hi = max(a[0], b[0]), min(a[1], b[1])
                if hi > lo:
                    observed[tuple(sorted((a[2], b[2])))] = (lo, hi, hi - lo)

    print(f"live polities: {live}")
    print(f"exact-prefix families: {len(families)}")
    print(f"overlapping same-family pairs: {len(observed)}")
    mapped = faostat_mapped()
    for pair, (lo, hi, n) in sorted(observed.items(), key=lambda kv: -kv[1][2]):
        reach = sum(1 for c in pair if c in mapped)
        tag = {0: "latent (neither mapped)", 1: "latent (one mapped)", 2: "LIVE (both mapped)"}[reach]
        print(
            f"   {n:>4}y  {pair[0]:<20} overlaps {pair[1]:<20} ({lo}-{hi})  {tag}"
        )

    problems = []
    for pair in sorted(set(observed) - BASELINE):
        lo, hi, n = observed[pair]
        problems.append(
            f"NEW overlap: {pair[0]} and {pair[1]} both cover {lo}-{hi} ({n} years) — "
            f"a year-aware matcher cannot choose between them on history alone"
        )
    for pair in sorted(BASELINE - set(observed)):
        problems.append(
            f"{pair[0]} and {pair[1]} are baselined as overlapping but no longer do — "
            f"remove the pair from the baseline"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: same-family period overlaps match the baseline exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
