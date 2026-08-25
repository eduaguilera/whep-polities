#!/usr/bin/env python3
"""Guard the cross-source agreement surface (issue 375).

Different labels routing to the same polity make two independent publishers directly comparable.
Issue 360 recorded that cross-source validation was impossible here, keyed on the LABEL -- zero cells
carry two sources. Keyed on the POLITY there are 804, across 10 polities, and issue 375 called it "a
free validation surface that has never been used". `39_cross_source_agreement.py` publishes it; this
holds it.

WHAT MAKES IT A CHECK RATHER THAN A REPORT. Median agreement is 1.0011 -- two publishers matching to
four figures -- so the tail is meaningful rather than noise. Every cell of that tail is currently a
defect this repo has already recorded: wheat is spelt and meslin, tobacco and hops are the 1934 scale
break, `czech republic` and `serbia` are layer-B labels fed by several raw labels at different
territorial levels. So the ceiling on unexplained large disagreements is ZERO and it is reachable.

A cell that appears there with nothing behind it is one of: a routing change that put two
incompatible series on one polity, a new extraction defect, or a real disagreement between publishers
that nobody has looked at. All three are worth a look, and nothing else in this repo would surface
any of them -- every other check compares a series against itself, its neighbours, or its polygon.

NO REGENERATION CHECK, deliberately: the table is built from layer B, which is absent in CI, so a
`--check` could only compare nothing and report OK (issue 573). This gate reads the committed table.
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/cross_source_agreement.csv")
ERRORS = os.path.join(REPO, "pipelines/polity-autoimprove/state/data_errors.csv")

BIG_RATIO = 10.0
BASELINE_UNEXPLAINED = 0        # reachable today; a new one is a finding
BASELINE_MIN_CELLS = 700        # 804 today. A floor, so the surface cannot quietly disappear.

# Arm E. The key excludes `indicator` on purpose -- the column holds a measurement type for fao1952
# and iia (`crops:production`) and a PAGE REFERENCE for mitchell (`page_12_table_1`), so keying on it
# would split iia from mitchell on a field that does not mean the same thing in each and destroy the
# comparison. `unit` already separates production from area.
#
# What would genuinely invalidate a cell is both sides being annotated and DISAGREEING, which is a
# different test from "is the column in the key". Zero today: every mismatch is a null against a
# mitchell page string.
BASELINE_INDICATOR_CONFLICTS = 0


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} is missing -- run "
              "pipelines/polity-autoimprove/39_cross_source_agreement.py")
        return 1
    with open(TABLE, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    with open(ERRORS, newline="", encoding="utf-8") as fh:
        known_ids = {e["issue_id"] for e in csv.DictReader(fh)}

    problems = []
    big, unexplained, dangling, conflicts = [], [], [], []
    for r in rows:
        try:
            lo, hi, ratio = float(r["value_min"]), float(r["value_max"]), float(r["ratio"])
        except ValueError:
            problems.append(f"{r['polity_code']}/{r['item']}/{r['year']}: unparseable numbers")
            continue
        if lo <= 0:
            problems.append(f"{r['polity_code']}/{r['item']}/{r['year']}: value_min is not positive, "
                            "so the ratio is meaningless and the row should not have been written")
            continue
        # ARITHMETIC. The ratio is the whole content of a row; a stale one would let a large
        # disagreement present itself as a small one and never reach the ceiling below.
        if abs(ratio - hi / lo) > max(0.001, 0.001 * ratio):
            problems.append(f"{r['polity_code']}/{r['item']}/{r['year']}: ratio {ratio} != "
                            f"{hi:.4g}/{lo:.4g} = {hi / lo:.4f}")
        if ";" not in r["sources"]:
            problems.append(f"{r['polity_code']}/{r['item']}/{r['year']}: only one source "
                            f"({r['sources']!r}) -- this table exists for cells with two or more")
        for issue_id in filter(None, r["known_defect"].split(";")):
            if issue_id not in known_ids:
                dangling.append(f"{r['polity_code']}/{r['item']}/{r['year']} -> {issue_id}")
        # nulls are written as an empty segment, so a cell reads e.g. ";page_14_table_1"
        annotated = {x for x in r.get("indicators", "").split(";") if x}
        if len(annotated) > 1:
            conflicts.append(f"{r['polity_code']}/{r['item']}/{r['year']}: "
                             f"{sorted(annotated)} across {r['sources']}")
        if ratio >= BIG_RATIO:
            big.append(r)
            if not r["known_defect"]:
                unexplained.append(r)

    print(f"{len(rows):,} cross-source cells across {len({r['polity_code'] for r in rows})} polities "
          f"(floor {BASELINE_MIN_CELLS})")
    print(f"  disagreeing by >={BIG_RATIO:g}x: {len(big)}   "
          f"with NO recorded defect: {len(unexplained)} (ceiling {BASELINE_UNEXPLAINED})")

    if len(rows) < BASELINE_MIN_CELLS:
        problems.append(
            f"only {len(rows)} cells, below the floor of {BASELINE_MIN_CELLS}. The surface exists "
            f"because several labels route to one polity, so it SHRINKS when a reroute separates "
            f"them -- which may be correct, but it removes the only place two publishers are "
            f"comparable and should be a deliberate act")
    if len(unexplained) > BASELINE_UNEXPLAINED:
        for r in unexplained[:8]:
            print(f"   UNEXPLAINED {r['polity_code']:16}{r['item'][:22]:24}{r['unit'][:8]:10}"
                  f"{r['year']:6}{r['ratio']:>10}x  {r['sources']}  [{r['labels']}]")
        problems.append(
            f"{len(unexplained)} cell(s) disagree by >={BIG_RATIO:g}x with no entry in "
            f"data_errors.csv explaining them, above the ceiling of {BASELINE_UNEXPLAINED}. Two "
            f"independent publishers differing by an order of magnitude on the same polity, item, "
            f"unit and year is either a routing that put incompatible series together or a defect "
            f"nobody has recorded")
    elif len(unexplained) < BASELINE_UNEXPLAINED:
        problems.append(f"only {len(unexplained)} unexplained cell(s), below the ceiling of "
                        f"{BASELINE_UNEXPLAINED} -- lower it so the improvement is held")
    print(f"  cells whose sources give DIFFERENT non-null indicators: {len(conflicts)} "
          f"(ceiling {BASELINE_INDICATOR_CONFLICTS})")
    if len(conflicts) > BASELINE_INDICATOR_CONFLICTS:
        problems.append(
            f"{len(conflicts)} cell(s) compare two sources that annotate DIFFERENT indicators, so "
            f"the two numbers are not measuring the same thing and their ratio means nothing: "
            + "; ".join(conflicts[:4]))

    if dangling:
        problems.append(
            f"{len(dangling)} cell(s) cite a data_errors entry that no longer exists, so the "
            f"explanation is gone while the cell still reads as explained: " + "; ".join(dangling[:4]))

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems[:20]:
            print("  " + p)
        return 1
    print("\nPASS: every large cross-source disagreement is a recorded defect, every citation "
          "resolves, and every ratio matches its own two values")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
