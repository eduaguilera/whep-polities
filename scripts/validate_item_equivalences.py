#!/usr/bin/env python3
"""Is every (layer-B item, raw IIA product) mapping explicitly adjudicated?

Three defects found by hand share one shape: a layer-B item carrying a raw product it is not named for.
`wheat` is spelt and meslin, and the source has NO wheat production rows at all (#375/#376).
`flax fibre and tow` is majority LINSEED -- the seed, not the fibre -- with 19 cells also under the
`linseed` item (#380). A `p` series is a patchwork of fertiliser MATERIALS, not a P2O5 total (#378).

`22_item_equivalences.py` turns that into a registry: every mapping carrying at least 2 cells in some
series must have a VERDICT. This gate refuses an unadjudicated one, so the fourth instance fails CI
instead of waiting to be noticed. Building the registry immediately produced one:
`other sugar crops n e c` <- `citrus fruits: other`, 21 cells over 7 series -- citrus is not a sugar
crop, and both are "other" buckets.

VERDICTS
  approved_rename       the same thing renamed -- `cotton seed` <- `cottonseed`
  approved_aggregation  several products deliberately mapped to one category. Legitimate as a MAPPING;
                        whether the resulting SERIES is coherent is a separate question that
                        validate_item_product_switches.py answers
  defect                the item is not the product
  unresolved            genuinely unclear and NOT waved through -- `fertilizer mixed` <- `sulphur`,
                        since sulphur is a fungicide rather than a mixed fertiliser

17 pairs are `unresolved` and that is deliberate. The largest is `yarn of true hemp` <- `hemp: fibre`
at 333 cells: fibre is not yarn, and `hemp tow waste` also draws on `hemp: fibre`, so one raw product
feeds two items. Recording it as unresolved keeps it visible without asserting a conclusion I cannot
support from the panel.

Four signals:
  A. EVERY PAIR ADJUDICATED  a blank or unknown verdict fails. This is the point of the gate, and it
                             also catches the generator overwriting the hand-maintained column --
                             regenerating MERGES, and a wipe would show up as blanks.
  B. DEFECT/UNRESOLVED PINNED bidirectional, so a repaired one must be removed with a note and a new
                             one cannot hide among the approvals.
  C. REASON RECORDED         a `defect` or `unresolved` pair with no note is not an adjudication.
  D. SELF-CONSISTENT         names_share_word is re-derived, and counts must be positive.

Usage:
  python3 scripts/validate_item_equivalences.py
"""
from __future__ import annotations

import csv
import os
import re
import sys
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/item_equivalences.csv")

VERDICTS = ("approved_rename", "approved_aggregation", "defect", "unresolved")
MIN_NOTE = 40


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


BASELINE_DEFECT = frozenset({
    ('flax fibre and tow', 'linseed'),
    ('other sugar crops n e c', 'citrus fruits: other'),
    ('wheat', 'meslin'),
    ('wheat', 'spelt'),
})

BASELINE_UNRESOLVED = frozenset({
    ('butter cow milk', 'butter: whey, factory'),
    ('fertilizer mixed', 'fertilizers: copper(ii) sulfate'),
    ('fertilizer mixed', 'sulphur'),
    ('grapes', 'grapes: raisins, table'),
    ('grapes', 'grapes: table'),
    ('grapes', 'grapes: wine'),
    ('grapes', 'vineyards'),
    ('grapes', 'vineyards: all'),
    ('milk whole fresh cow', 'milk: buffalo, cow, ewe, angora goat, goat, other'),
    ('milk whole fresh cow', 'milk: buffalo, cow, ewe, goat'),
    ('milk whole fresh cow', 'milk: cow, ewe'),
    ('milk whole fresh cow', 'milk: cow, goat'),
    ('oranges', 'citrus fruits: lemons, mandarins, oranges'),
    ('oranges', 'citrus fruits: lemons, oranges'),
    ('oranges', 'citrus fruits: mandarins, oranges'),
    ('oranges', 'citrus fruits: oranges, other'),
    ('yarn of true hemp', 'hemp: fibre'),
})


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"SKIP: {os.path.relpath(TABLE, REPO)} missing — run 22_item_equivalences.py --write")
        return 0
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    problems = []
    by = defaultdict(int)
    for r in rows:
        by[r["verdict"] or "(blank)"] += 1
    print("pairs: %d   " % len(rows) + "  ".join(f"{k}={v}" for k, v in sorted(by.items())))

    for r in rows:
        key = (r["item"], r["raw_product"])
        tag = f"{r['item']} <- {r['raw_product']}"
        # --- A ---
        if not r["verdict"]:
            problems.append(
                f"A {tag} ({r['cells']} cells) has NO verdict. Every item/product mapping must be "
                f"adjudicated: is it the same thing renamed, a deliberate aggregation, a defect, or "
                f"genuinely unclear? An unadjudicated mapping is how `wheat` came to mean spelt")
            continue
        if r["verdict"] not in VERDICTS:
            problems.append(f"A {tag}: unknown verdict {r['verdict']!r}, not in {VERDICTS}")
            continue
        # --- C ---
        if r["verdict"] in ("defect", "unresolved") and len((r["note"] or "").strip()) < MIN_NOTE:
            problems.append(
                f"C {tag} is `{r['verdict']}` with no substantive note. The reason is the one thing a "
                f"reader cannot re-derive from the counts")
        # --- D ---
        derived = "yes" if set(norm(r["item"]).split()) & set(norm(r["raw_product"]).split()) else "no"
        if r["names_share_word"] != derived:
            problems.append(
                f"D {tag}: names_share_word is {r['names_share_word']!r} but the names say {derived!r}")
        try:
            if int(r["cells"]) <= 0 or int(r["series"]) <= 0:
                problems.append(f"D {tag}: non-positive cells/series")
        except ValueError:
            problems.append(f"D {tag}: cells/series not integers")

    # --- B ---
    for name, baseline in (("defect", BASELINE_DEFECT), ("unresolved", BASELINE_UNRESOLVED)):
        seen = {(r["item"], r["raw_product"]) for r in rows if r["verdict"] == name}
        for k in sorted(seen - baseline):
            problems.append(
                f"B NEW `{name}` mapping: {k[0]} <- {k[1]}. Record it in the baseline with what it "
                f"means for consumers")
        for k in sorted(baseline - seen):
            problems.append(
                f"B {k[0]} <- {k[1]} is pinned as `{name}` but is not any more — remove its baseline "
                f"entry, saying whether it was repaired or reclassified and why")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS: every item/product mapping is adjudicated, with defects and open cases pinned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
