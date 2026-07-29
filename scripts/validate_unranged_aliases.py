#!/usr/bin/env python3
"""Check that no alias can resolve a year AFTER its target polity ended.

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

  viet nam -> VNM-1887-1954
      a current name pointing at a long-ended polity, so it looks like the Syria defect. It is
      not: its recorded basis is "sub-territory routing for IIA year=NA rows", and an alias with
      no range is the only thing that can match a row whose year is missing. Deliberate, and
      baselined with that as the reason.

I first wrote that both this and "italy" were safe because they are scoped to source `iia`, a
historical source. That was not the actual reason for either, and checking rather than asserting
it is what showed the check itself was too blunt: "italy" is not unranged at all. It has
year_end 1860 against a target ending 1860 — bounded exactly where it matters — and only tripped
the first version of this gate because that version demanded BOTH bounds be present. The rule is
now about the UPPER bound alone, which is what determines whether an alias can fire after its
target stopped existing.

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
        y1 = (r.get("year_end") or "").strip()
        m = CODE_END.search(r["polity_code"])
        if not m:
            continue
        target_end = int(m.group(1))
        # What matters is the UPPER bound, not whether both are present. A half-open alias
        # with an empty start and an end at the target's own end is bounded exactly where it
        # needs to be — "italy" ends at 1860 against SAR-1800-1860, which is correct and was
        # a false positive in the first version of this check. The risk is an alias that can
        # still fire AFTER its target stopped existing.
        if y1.isdigit() and int(y1) <= target_end:
            continue
        unranged += 1
        if target_end >= 2025:
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
