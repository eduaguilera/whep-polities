#!/usr/bin/env python3
"""Does one layer-B item series draw on several raw PRODUCTS, switching back and forth?

`20_item_provenance.py` asks which raw LABEL a series came from -- a territory question. This is a
different failure: the territory can be right, the item name constant and the source unchanged, and
the series still be a patchwork of different commodities.

`australia / sugar raw centrifugal / tonnes` alternates `sugar: cane` and `sugar: BEET` -- 1912
131,961 (cane), 1913 922 (beet, x0.01), 1920 165,616 (cane, x105), 1939 6,400 (beet), 1944 611,300
(cane, x873). Australia's beet industry was negligible, so 12 of its 33 cells sit at about 1/300 of the
series around them. `sweden / p` runs calcium superphosphate 1909-1920, BASIC SLAG 1930-1932 (x0.08),
superphosphate again 1933 (x28) -- which is why a `p` series is a patchwork of fertilizer MATERIALS and
not a P2O5 total, and why half the convention registered for `p`/`n`/`k` in issue 369 was refuted.

NOTHING ELSE HERE CAN SEE THIS. The source never changes, so `validate_source_splices.py` has no seam.
Each value is plausible FOR THE PRODUCT IT CAME FROM, so no magnitude screen fires. The item name is
constant, so nothing keyed on the item notices. It is also part of the mechanism behind issue 360's
level-shift confound.

THE CRITERION IS OSCILLATION, BECAUSE THE OBVIOUS TEST IS CONFOUNDED. Comparing each product's median
level reports a gap for any GROWING series that happens to draw on an early product and a late one --
that is growth, not a defect, and it inflated the first count from 9 to 28. So a series is recorded
only when a product RECURS after another has intervened (A...B...A), which no trend can produce.

Three signals:
  A. COUNT + IDENTITY  the 9 are pinned and the count is bidirectional, so a new one fails and a
                       repaired one must be removed with a note.
  B. RATIO RE-DERIVED  `worst_switch` embeds both values, so `worst_switch_ratio` is checked against
                       them. It is the number every judgement here rests on and it rots silently.
  C. FILTER INTACT     the thresholds are restated here, not imported, so relaxing the generator's
                       constants and regenerating cannot quietly refill the table.

Usage:
  python3 scripts/validate_item_product_switches.py
"""
from __future__ import annotations

import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/item_product_switches.csv")

# Restated, never imported: relaxing these in the generator is the realistic regression.
MIN_CELLS = 8
MIN_PER_PRODUCT = 2
LEVEL = 3.0

BASELINE_SWITCHING = frozenset({
    ('australia', 'sugar raw centrifugal', 'tonnes'),
    ('austria', 'p', 'tonnes'),
    ('czech republic', 'wheat', 'tonnes'),
    ('france', 'p', 'tonnes'),
    ('japan', 'n', 'tonnes'),
    ('japan', 'p', 'tonnes'),
    ('paraguay', 'sugar raw centrifugal', 'tonnes'),
    ('spain', 'sugar raw centrifugal', 'tonnes'),
    ('sweden', 'p', 'tonnes'),
})


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"SKIP: {os.path.relpath(TABLE, REPO)} missing — run 21_item_product_switches.py --write")
        return 0
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    problems = []
    seen = {(r["layer_b_label"], r["item"], r["unit"]) for r in rows}
    print(f"series switching raw product: {len(rows)} (pinned {len(BASELINE_SWITCHING)})")

    for k in sorted(seen - BASELINE_SWITCHING):
        problems.append(
            f"A NEW switching series: {k[0]} / {k[1]} ({k[2]}). One item series is drawing on more "
            f"than one raw product and returning to an earlier one, so its level shifts are the "
            f"yearbook changing table, not output changing")
    for k in sorted(BASELINE_SWITCHING - seen):
        problems.append(
            f"A {k[0]} / {k[1]} ({k[2]}) is pinned as switching raw products but is not any more — "
            f"remove its entry, saying what was repaired or which threshold moved")

    for r in rows:
        tag = f"{r['layer_b_label']} / {r['item']} ({r['unit']})"
        # --- B: the ratio must follow from the two values in worst_switch ---
        nums = re.findall(r":(\d+(?:\.\d+)?)\s*\[", r["worst_switch"])
        if len(nums) != 2:
            problems.append(f"B {tag}: worst_switch {r['worst_switch']!r} does not carry two values")
        else:
            a, b = float(nums[0]), float(nums[1])
            if a <= 0 or b <= 0:
                problems.append(f"B {tag}: worst_switch carries a non-positive value")
            else:
                derived = max(a / b, b / a)
                if abs(derived - float(r["worst_switch_ratio"])) > 0.01 * max(1.0, derived):
                    problems.append(
                        f"B {tag}: worst_switch_ratio {r['worst_switch_ratio']} does not match its "
                        f"own two values ({derived:.2f})")
        # --- C: the filter ---
        if int(r["n_traced"]) < MIN_CELLS:
            problems.append(
                f"C {tag}: recorded on {r['n_traced']} traced cells, below MIN_CELLS={MIN_CELLS}")
        counts = [int(x.rsplit("=", 1)[1]) for x in r["products"].split(";") if "=" in x]
        if len(counts) < 2:
            problems.append(f"C {tag}: recorded as switching but names {len(counts)} product(s)")
        if counts and min(counts) < MIN_PER_PRODUCT:
            problems.append(
                f"C {tag}: a product supplies only {min(counts)} cell(s), below "
                f"MIN_PER_PRODUCT={MIN_PER_PRODUCT}. One cell of a product is as likely to be a "
                f"value collision as a real switch")
        if float(r["worst_switch_ratio"]) < LEVEL:
            problems.append(
                f"C {tag}: worst switch is {r['worst_switch_ratio']}x, below LEVEL={LEVEL}")
        if int(r["n_products"]) != len(counts):
            problems.append(
                f"C {tag}: n_products={r['n_products']} but the products column names {len(counts)}")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS: every switching series accounted for, each ratio re-derived, filter intact")
    return 0


if __name__ == "__main__":
    sys.exit(main())
