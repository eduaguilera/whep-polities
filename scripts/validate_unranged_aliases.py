#!/usr/bin/env python3
"""Check that an alias cannot resolve a year OUTSIDE its target polity's span — both directions.

THE LATE DIRECTION was the original check and is described below. THE EARLY DIRECTION was added
2026-08-05 (issue 54) and is the mirror image: a blank `year_start` is unbounded BELOW, so the
alias also resolves years before its target began.

That half was genuinely ungated, and the reason is worth recording. An investigation of issue 54
proposed a gate testing `year_start < start_year` — which is UNEVALUABLE when year_start is
blank, so it flagged 4 aliases and silently skipped 18. Measured against layer B, those 18 put
66 rows on polities that did not yet exist:

  `Turkey`    (blank start) -> TUR-1920-2025   46 rows dated 1880-1919
  `indochina` (blank start) -> FID-1887-1954   20 rows dated 1866-1886

Both are fixed: `Turkey` is bounded to 1920 with three ranged siblings covering 1880-1919 across
the TUR periods, and `indochina` is bounded to 1887 with a sibling routing 1866-1886 to
FCC-1862-1887, French Cochinchina — the only French possession there before the 1887 federation.
The early count is now 0.

The check here is STRUCTURAL rather than data-driven, so it runs in CI: a blank year_start is
flagged when the target begins after the 1800 database floor, whether or not data happens to fall
in the exposed years today. Thirteen do, and all thirteen are baselined — none currently
misroutes anything, but each is one new observation away from doing so, which is precisely what
a baseline should record rather than what a passing gate should hide.

An alias with an empty `year_start`/`year_end` applies to EVERY year. If its target is a polity
that ended, the alias silently resolves modern data to a historical entity — and unlike an inert
alias, which validate_aliases.py catches, this one works. It just works wrongly.

Found via "Syria", which had no source and no year range and pointed at SYR-1946-1967. Every
year, including 2020, resolved to a polity that ended in 1967, across 162 observed rows. The
canonical FAOSTAT label "Syrian Arab Republic" was already split at 1967; the short label was
not, so it has been split the same way.

Thirteen unranged aliases target an ended polity, and twelve of them are FINE, which is why this
gate baselines rather than forbids. The distinction is whether the LABEL is still in use:

  Belgian Congo, French West Africa, French Equatorial Africa, indochina,
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

That reasoning was right about this gate and wrong about the repository. Both consumers of the
field keyed their year test on `year_start`, so a rule bounded only above skipped the test
altogether and matched EVERY year: `matchlib.match_alias` and WHEP's `resolve_polity_label()`
each resolved ("italy", iia, 2000) to SAR-1800-1860, a polity that ended in 1860. The bound this
gate called sufficient was not being read at all. Both now treat a missing bound as unbounded on
that side, which is what makes the sentence above true rather than merely intended — and it is
worth noting that the gate permitting the row and the matcher mishandling it lived in the same
repository, disagreeing about one field, until a consumer in another repository hit it.

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
    # ("Cape of Good Hope", "") removed 2026-08-14 (issue 22). It is no longer unranged:
    # CAP-1800-1910 was split at the 1895 British Bechuanaland annexation, so the label now
    # carries two ranged rows, 1800-1894 -> CAP-1800-1895 and 1895-1909 -> CAP-1895-1910.
    # Bounding it drops nothing: measured in layer B, all 205 rows labelled "Cape of Good
    # Hope" are dated 1854-1904 and none has a missing year, which is the only thing an
    # unranged alias was buying here.
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
# The START year, read off the code the same way this gate already reads the end year.
# validate_code_year_agreement holds only two rows whose code and columns disagree, and
# both differ on end_year, so the code's start is safe to trust here.
CODE_START = re.compile(r"-(\d{4})-\d{4}$")

# EARLY DIRECTION (issue 54). Blank year_start, target starting after the 1800 floor: the alias is
# unbounded below. Baselined by (label, source) with the reason each is currently harmless.
# Bidirectional: a new one fails, and one that gains a year_start must be removed.
BASELINE_EARLY = frozenset({
    # Historical names no present-day source writes, so the label itself carries the era and the
    # exposed years contain no data. Verified: 0 rows before the target's start, in layer B.
    ("Belgian Congo", ""), ("Belgian Congo (fao1952)", ""),
    ("French Equat Africa", ""), ("French W Africa", ""), ("French West Africa", ""),
    ("rwanda and burundi", ""), ("NetherlandsWest Indies", "fao1952"),
    ("netherlandswest indies", "fao1952"),
    # Current names whose target starts late, but whose sources begin later still.
    ("American Samoa", ""), ("British Borneo Brunei", ""), ("EI Salvador", ""),
    ("belgium", "iia"),
    # Deliberate: an unranged alias is the only thing that can match an IIA row whose year is
    # MISSING, which is this alias's recorded purpose. Bounding it would drop those rows.
    ("viet nam", "iia"),
})


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

    # ---------- EARLY DIRECTION ----------
    FLOOR = 1800
    observed_early = set()
    for row in rows:
        if (row.get("year_start") or "").strip():
            continue
        tgt = (row.get("polity_code") or "").strip()
        m = CODE_START.search(tgt)
        if not m:
            continue
        start = int(m.group(1))
        if start <= FLOOR:
            continue
        observed_early.add(((row.get("source_label") or "").strip(),
                            (row.get("source") or "").strip()))
    print(f"aliases with a BLANK year_start whose target begins after {FLOOR}: "
          f"{len(observed_early)} ({len(BASELINE_EARLY)} baselined)")

    problems = []
    for pair in sorted(observed_early - BASELINE_EARLY):
        problems.append(
            f"NEW unbounded-below alias: {pair[0]!r} (source {pair[1] or 'any'}) has a blank "
            f"year_start while its target begins after {FLOOR}, so it resolves years before that "
            f"polity existed. Give it the target's start year, and add a sibling alias for the "
            f"earlier period if data reaches back that far."
        )
    for pair in sorted(BASELINE_EARLY - observed_early):
        problems.append(
            f"{pair[0]!r} (source {pair[1] or 'any'}) is baselined as unbounded-below but no "
            f"longer is — remove it from BASELINE_EARLY"
        )

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
