#!/usr/bin/env python3
"""Do any iia labels mix TERRITORIES at the item level, and is the filter that finds them intact?

`15_label_provenance.py` asks which raw label a whole layer-B label came from.
`20_item_provenance.py` asks it per (label, item, unit), because a label can be right for one
commodity and wrong for another -- and no label-level decision can fix that, since the alias key is
(label, source, years) with no item dimension. The panel and the raw extract are both gitignored and
absent in CI, so the generator commits `state/item_provenance.csv` and this gate reads it, the same
arrangement as the splice, constant-run, spike and composition-overlap tables.

WHAT THE FIRST RUN FOUND (issue 372): 11 labels mixing more than one raw label across their item
series, out of 1,918 series of which 804 are attributable. The two most diagnostic are phosphate:
`australia`'s `p` series is CHRISTMAS ISLAND's output and `french polynesia`'s is MAKATEA's, the great
Pacific deposits worked as dependencies. `syrian arab republic` carries Lebanon in its COTTON series
only, its hempseed and beans being Syria alone -- issue 315's Levant entry made precise.

THE FILTER GUARD IS THE POINT OF THIS GATE, not the count. Everything here rests on requiring a series
to have enough DISTINCT values before its fingerprint means anything: a handful of round values matches
any label containing them, the same pathology `17_constant_runs.py` measures. Unfiltered, the method
returns 43 labels including `cameroon <- new zealand` at full agreement, plus `egypt <- yugoslavia` and
`zambia <- uruguay`; filtered it returns 11 and every geographic absurdity disappears. So signal C
refuses any `attributable` row that does not clear the thresholds -- because loosening them and
regenerating would repopulate this table with noise while every count still looked plausible.

Three signals:
  A. MIXED LABELS    the 11 are pinned by identity and the count is bidirectional, so a new mixture
                     fails and a repaired one must be removed with a note.
  B. SELF-CONSISTENT `label_is_mixed` is re-derived from the table's own attributable rows. The
                     generator writes it, so it can drift from the rows it describes.
  C. FILTER INTACT   an `attributable` row must clear MIN_VALUES, MIN_DISTINCT and SHARE_FLOOR, and
                     every status must be one the generator can actually produce.

Usage:
  python3 scripts/validate_item_provenance.py
"""
from __future__ import annotations

import csv
import os
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/item_provenance.csv")

# Restated here rather than imported, so the gate does not inherit a loosened generator constant --
# the whole result rests on these, and signal C exists to stop them being relaxed unnoticed.
MIN_VALUES = 8
MIN_DISTINCT = 6
SHARE_FLOOR = 0.60

STATUSES = {"attributable", "ambiguous", "unattributable", "too_few_distinct", "too_few_values"}

# Measured 2026-08-18. BIDIRECTIONAL: repairing a mixture must remove its entry with a note.
BASELINE_MIXED = frozenset({
    'australia',
    'austria',
    'china, mainland',
    'indonesia',
    'malaysia',
    'niger',
    'papua new guinea',
    'russian federation',
    'syrian arab republic',
    'timor-leste',
    'united states of america',
})


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"SKIP: {os.path.relpath(TABLE, REPO)} missing — run 20_item_provenance.py --write")
        return 0
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    problems = []
    counts = defaultdict(int)
    for r in rows:
        counts[r["status"]] += 1

    # --- B: the flag must follow from the rows ---
    attributed = defaultdict(set)
    for r in rows:
        if r["status"] == "attributable":
            attributed[r["layer_b_label"]].add(r["raw_label"])
    derived = {k for k, v in attributed.items() if len(v) > 1}
    flagged = {r["layer_b_label"] for r in rows if r["label_is_mixed"] == "yes"}
    for label in sorted(derived - flagged):
        problems.append(
            f"B {label!r}: its attributable series name {len(attributed[label])} different raw "
            f"labels but label_is_mixed says `no` — the flag has drifted from the rows"
        )
    for label in sorted(flagged - derived):
        problems.append(
            f"B {label!r}: label_is_mixed says `yes` but its attributable series all name one raw "
            f"label — re-run 20_item_provenance.py --write"
        )

    # --- C: the filter that makes any of this meaningful ---
    for r in rows:
        if r["status"] not in STATUSES:
            problems.append(f"C {r['layer_b_label']}/{r['item']}: unknown status {r['status']!r}")
            continue
        if r["status"] != "attributable":
            continue
        n, d = int(r["n_values"]), int(r["n_distinct"])
        if n < MIN_VALUES:
            problems.append(
                f"C {r['layer_b_label']}/{r['item']} ({r['unit']}): attributed to "
                f"{r['raw_label']!r} on {n} values, below MIN_VALUES={MIN_VALUES}"
            )
        if d < MIN_DISTINCT:
            problems.append(
                f"C {r['layer_b_label']}/{r['item']} ({r['unit']}): attributed to "
                f"{r['raw_label']!r} on only {d} DISTINCT values, below MIN_DISTINCT="
                f"{MIN_DISTINCT}. A few round values match any label containing them, so this "
                f"attribution is a chance collision and not a measurement"
            )
        if not r["share"] or float(r["share"]) < SHARE_FLOOR:
            problems.append(
                f"C {r['layer_b_label']}/{r['item']} ({r['unit']}): attributed on share "
                f"{r['share'] or '(blank)'}, below SHARE_FLOOR={SHARE_FLOOR}"
            )
        if not r["raw_label"]:
            problems.append(
                f"C {r['layer_b_label']}/{r['item']}: status is `attributable` with no raw_label"
            )

    # --- A: the mixtures themselves ---
    print(f"series: {len(rows)}   " + "  ".join(f"{k}={counts[k]}" for k in sorted(counts)))
    print(f"labels mixed at the item level: {len(flagged)} (pinned {len(BASELINE_MIXED)})")
    for label in sorted(flagged - BASELINE_MIXED):
        problems.append(
            f"A {label!r} now mixes more than one raw label across its item series and is not "
            f"pinned. A label-level reroute cannot fix an item-level mixture — the alias key has no "
            f"item dimension — so record what it mixes and route the upstream fix"
        )
    for label in sorted(BASELINE_MIXED - flagged):
        problems.append(
            f"A {label!r} is pinned as an item-level mixture but is not one any more — remove its "
            f"entry, saying what was repaired, or whether a threshold moved and hid it"
        )

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS: every mixture accounted for, the flag follows the rows, and the filter is intact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
