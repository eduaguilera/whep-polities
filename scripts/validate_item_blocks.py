#!/usr/bin/env python3
"""Do four or more items share one value in a single label-year? That is a broadcast cell, not data.

Every other repetition guard here looks along the YEAR axis. `validate_constant_runs.py` covers one
value repeated across years within one series, `validate_isolated_spikes.py` and
`validate_series_collapses.py` a year out of line with its own neighbours. None can see one value
repeated across ITEMS within one year, and the cause is different: not a carried-forward estimate but
a single cell broadcast over a row, or a placeholder for a table nobody filled.

WHY THE CROSS-ITEM VIEW IS THE DIAGNOSIS. `validate_series_collapses.py` already pins
`mitchell india / swine` at 1947 — 3,000 between 3,653,000 and 4,420,000. What a per-series test
cannot say is that asses, buffalo, camels, cattle, goats, horses, sheep AND swine all read exactly
3,000 that year. Eight independent errors landing on one number is not a hypothesis worth weighing;
one broadcast cell is.

`pipelines/polity-autoimprove/28_item_blocks.py` measures it from the layer-B panel, which is
gitignored and absent in CI, so this gate reads the committed table.

WHAT IT FOUND — five blocks in the whole panel, and every one is a defect:

    mitchell india    heads 1947   8 items all      3,000   other years' median 20,895,500  (6,965x)
    mitchell somalia  heads 1959   4 items all     15,000   other years' median  1,286,000  (   86x)
    iia      belgium  ha    1934   4 items all          0
    iia      belgium  ha    1935   4 items all          0
    iia      belgium  ha    1936   4 items all          0

India's cattle reads 3,000 in a year it reads 160,220,000 (1936) and 155,295,000 (1951), so no
external source is needed. The belgium blocks are issue 414's blank-read-as-0 arriving as a block
rather than a cell, inside the iia_1938_39 window.

THE VALUE ITSELF IS NOT THE SIGNAL. `3,000` occurs 148 times across 48 mitchell labels and 23 items,
legitimately — plenty of small producers report 3,000 head. The coincidence WITHIN a label-year is
what carries it, so the check is on the block, never on the number.

Three signals:
  A. COUNT CEILING   blocks may not grow. Bidirectional: repairing one must lower it with a note.
  B. EVERY BLOCK pinned by identity, so one cannot be swapped for another at a constant total.
  C. INTERNAL SHAPE  the item count must match the item list, and must clear the generator's floor.

Usage:
  python3 scripts/validate_item_blocks.py
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/item_blocks.csv")

# Measured 2026-08-19. BIDIRECTIONAL: repairing a block must lower this with a note saying which
# label-year was fixed and whether the value became real data or a missing value.
BASELINE_BLOCKS = 5

# The generator's floor, restated so this gate does not depend on its constant to know what the
# table means.
MIN_ITEMS = 4

BASELINE_KEYS = frozenset({
    ("iia", "belgium", "ha", "1934"),
    ("iia", "belgium", "ha", "1935"),
    ("iia", "belgium", "ha", "1936"),
    ("mitchell", "india", "heads", "1947"),
    ("mitchell", "somalia", "heads", "1959"),
})


def key(r):
    return (r["source"], r["country"], r["unit"], r["year"])


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} missing — run 28_item_blocks.py --write",
              file=sys.stderr)
        return 1
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    print(f"broadcast-cell blocks: {len(rows)} (ceiling {BASELINE_BLOCKS}, "
          f"pinned {len(BASELINE_KEYS)})")

    problems = []
    if len(rows) > BASELINE_BLOCKS:
        problems.append(
            f"A {len(rows)} label-years have >={MIN_ITEMS} items sharing one value, above the ceiling "
            f"of {BASELINE_BLOCKS}. Four unrelated commodities do not agree to the digit by accident — "
            f"that is one cell broadcast over a row, or a placeholder for a table nobody filled")
    elif len(rows) < BASELINE_BLOCKS:
        problems.append(
            f"A only {len(rows)} blocks remain, below the pinned ceiling of {BASELINE_BLOCKS} — lower "
            f"the baseline and say which label-year was repaired and how")

    seen = {key(r) for r in rows}
    for k in sorted(seen - BASELINE_KEYS):
        problems.append(
            f"B NEW block: {k[1]} / {k[2]} at {k[3]}, {k[0]} — several items reading one identical "
            f"value, which is not data")
    for k in sorted(BASELINE_KEYS - seen):
        problems.append(
            f"B {k[1]} / {k[2]} at {k[3]} is pinned as a block but is not one any more — remove its "
            f"entry, saying what was repaired")

    for r in rows:
        items = [i for i in r["items"].split(";") if i]
        try:
            n = int(r["n_items"])
        except ValueError:
            problems.append(f"C {r['country']} {r['year']}: unparseable n_items")
            continue
        if n != len(items):
            problems.append(
                f"C {r['country']} / {r['unit']} {r['year']}: n_items={n} but the items column names "
                f"{len(items)} — the count every judgement here rests on no longer describes the row")
        if n < MIN_ITEMS:
            problems.append(
                f"C {r['country']} / {r['unit']} {r['year']}: {n} items is below the floor of "
                f"{MIN_ITEMS}, where commodities really can agree by coincidence")

    for p in problems:
        print(f"FAIL: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
