#!/usr/bin/env python3
"""Check that an alias with no year range does not target a polity that has ended.

An alias with an empty `year_start`/`year_end` applies to EVERY year. If its target is a polity
that ended, the alias silently resolves modern data to a historical entity — and unlike an inert
alias, which validate_aliases.py catches, this one works. It just works wrongly.

Found via "Syria", which had no source and no year range and pointed at SYR-1946-1967. Every
year, including 2020, resolved to a polity that ended in 1967, across 162 observed rows. The
canonical FAOSTAT label "Syrian Arab Republic" was already split at 1967; the short label was
not, so it has been split the same way.

Thirteen unranged aliases target an ended polity, and twelve of them are FINE, which is why this
gate baselines rather than forbids. The distinction is whether the LABEL is still in use:

  Belgian Congo, French West Africa, French Equatorial Africa, Cape of Good Hope, indochina,
  rwanda and burundi, Netherlands West Indies
      historical names no present-day source writes. An unranged alias cannot mis-fire, because
      the label itself carries the era.

  italy -> SAR-1800-1860, viet nam -> VNM-1887-1954
      current names pointing at long-ended polities, which WOULD be the Syria defect — except
      both are scoped to source `iia`, a historical source. Left alone, and flagged here so the
      scoping is a deliberate reason rather than an accident nobody noticed.

So the rule enforced is: no NEW unranged alias may target an ended polity, and a baselined one
that gains a year range must leave the list.

Usage:
  python3 scripts/validate_unranged_aliases.py
"""
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAP = os.path.join(REPO, "data/final/label_alias_map.csv")

# (source_label, source) pairs allowed to be unranged against an ended polity.
BASELINE = frozenset({
    ("Belgian Congo", ""),
    ("Belgian Congo (fao1952)", ""),
    ("Cape of Good Hope", ""),
    ("French Equat Africa", ""),
    ("French W Africa", ""),
    ("French West Africa", ""),
    ("NetherlandsWest Indies", "fao1952"),
    ("indochina", ""),
    ("italy", "iia"),
    ("netherlandswest indies", "fao1952"),
    ("rwanda and burundi", ""),
    ("viet nam", "iia"),
})

CODE_END = re.compile(r"-(\d{4})$")


def main() -> int:
    rows = list(csv.DictReader(open(MAP, encoding="utf-8")))
    if not rows:
        print("FAIL: alias map is empty", file=sys.stderr)
        return 2

    observed = set()
    unranged = 0
    for r in rows:
        y0 = (r.get("year_start") or "").strip()
        y1 = (r.get("year_end") or "").strip()
        if y0 and y1:
            continue
        unranged += 1
        m = CODE_END.search(r["polity_code"])
        if not m or int(m.group(1)) >= 2025:
            continue
        observed.add(((r.get("source_label") or "").strip(), (r.get("source") or "").strip()))

    print(f"aliases published: {len(rows)}")
    print(f"with no year range: {unranged}")
    print(f"of those, targeting an ended polity: {len(observed)}")
    for label, source in sorted(observed):
        print(f"   {label!r} (source {source or 'any'})")

    problems = []
    for pair in sorted(observed - BASELINE):
        problems.append(
            f"NEW unranged alias to an ended polity: {pair[0]!r} (source {pair[1] or 'any'}) — "
            f"it will resolve modern years to a polity that no longer existed. Give it the "
            f"year range of its target, and add a second alias for the successor period if the "
            f"label is still in use."
        )
    for pair in sorted(BASELINE - observed):
        problems.append(
            f"{pair[0]!r} (source {pair[1] or 'any'}) is baselined as unranged-to-ended but no "
            f"longer is — remove it from the baseline"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} change(s) against the baseline\n")
        for p in problems:
            print(f"  {p}")
        return 1

    print("\nPASS: unranged aliases to ended polities match the baseline exactly")
    return 0


if __name__ == "__main__":
    sys.exit(main())
