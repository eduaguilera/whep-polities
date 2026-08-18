#!/usr/bin/env python3
"""Where a series-year carries several rows nothing can tell apart, is a TOTAL sitting beside its parts?

1,130 `(country, item, unit, source, indicator, year)` groups hold more than one row -- 3,081 rows, all
`fao1952` -- with NO column distinguishing the members: `item_code`, `source_detail`, `period`,
`polity_code` and `iso3c` are identical across every one. The item labels are collapsed multi-commodity
ranges (`horses mules asses`, `item_code` = the range `110_117`), so which row is which commodity is not
recoverable from the panel.

In 239 of those groups the largest value equals the sum of the rest to within 2%, i.e. a TOTAL is sitting
beside its own parts and summing the group returns exactly double:

    united states  meat    1000 t  1950   10,015 == 4,884 + 4,860 + 271
    italy          grapes  1000 t  1951    7,318 == 4,435 + 2,883

NONE OF THE USUAL DEFENCES APPLIES, which is why this needs its own gate. `is_aggregate` is `False` on
every row and correctly so -- the COUNTRY is not an aggregate; the aggregation is on the ITEM axis, which
that flag does not describe. `validate_composition_sums.py` reasons about part/whole POLITIES.
`05_magnitude_screen.py` screens series medians. And the panel is gitignored, so
`24_item_axis_aggregates.py` writes the table and this reads it.

EVERY CLASSIFICATION IS RE-DERIVED HERE FROM THE ROW'S OWN VALUES rather than trusted, because the
verdict is the whole content of the table and a threshold change would silently reclassify hundreds of
groups while every count still looked plausible.

Four signals:
  A. COUNTS            the group total and the `total_beside_parts` count are bidirectional ceilings.
  B. VERDICT DERIVED   largest, sum_of_rest, ratio and verdict are all recomputed from `values`.
  C. THRESHOLDS        restated here, not imported, so relaxing the generator cannot refill the table.
  D. WELL-FORMED       n_rows matches the value list, every group has at least two rows, and the
                       verdict is one the generator can produce.

Usage:
  python3 scripts/validate_item_axis_aggregates.py
"""
from __future__ import annotations

import csv
import os
import sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/item_axis_aggregates.csv")

TOTAL_TOL = 0.02
NEAR_TOL = 0.10
VERDICTS = ("total_beside_parts", "near_total", "siblings_only", "inconclusive")

# Measured 2026-08-18. BIDIRECTIONAL: repairing groups upstream must lower these, with a note, so the
# table cannot quietly refill. The right repair is to un-collapse the item ranges, which would remove
# groups entirely rather than reclassify them.
BASELINE_GROUPS = 1130
BASELINE_TOTAL_BESIDE_PARTS = 239


def classify(vals):
    v = sorted(vals, reverse=True)
    rest = sum(v[1:])
    if rest <= 0:
        return "inconclusive", rest, None
    ratio = v[0] / rest
    if abs(v[0] - rest) / rest <= TOTAL_TOL:
        return "total_beside_parts", rest, ratio
    if abs(v[0] - rest) / rest <= NEAR_TOL:
        return "near_total", rest, ratio
    return "siblings_only", rest, ratio


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"SKIP: {os.path.relpath(TABLE, REPO)} missing — run 24_item_axis_aggregates.py --write")
        return 0
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    problems = []
    by = Counter(r["verdict"] for r in rows)
    print(f"groups: {len(rows)} (ceiling {BASELINE_GROUPS})   "
          f"total_beside_parts: {by['total_beside_parts']} (ceiling {BASELINE_TOTAL_BESIDE_PARTS})")
    print("  " + "  ".join(f"{k}={v}" for k, v in sorted(by.items())))

    # --- A ---
    if len(rows) > BASELINE_GROUPS:
        problems.append(
            f"A {len(rows)} indistinguishable groups, above the ceiling of {BASELINE_GROUPS}. A new one "
            f"means another series-year where the panel cannot tell its own rows apart")
    elif len(rows) < BASELINE_GROUPS:
        problems.append(
            f"A only {len(rows)} groups remain, below the pinned {BASELINE_GROUPS} — lower the baseline "
            f"and say what was un-collapsed upstream")
    n_tot = by["total_beside_parts"]
    if n_tot > BASELINE_TOTAL_BESIDE_PARTS:
        problems.append(
            f"A {n_tot} groups have a total sitting beside its own parts, above the ceiling of "
            f"{BASELINE_TOTAL_BESIDE_PARTS}. Summing any of them returns double")
    elif n_tot < BASELINE_TOTAL_BESIDE_PARTS:
        problems.append(
            f"A only {n_tot} total-beside-parts groups remain, below the pinned "
            f"{BASELINE_TOTAL_BESIDE_PARTS} — lower the baseline and say what changed")

    for r in rows:
        tag = f"{r['source']}/{r['country']}/{r['item']} ({r['unit']}) {r['year']}"
        # --- D ---
        if r["verdict"] not in VERDICTS:
            problems.append(f"D {tag}: unknown verdict {r['verdict']!r}, not in {VERDICTS}")
            continue
        try:
            vals = [float(x) for x in r["values"].split(";") if x != ""]
        except ValueError:
            problems.append(f"D {tag}: values {r['values']!r} do not parse")
            continue
        if len(vals) < 2:
            problems.append(
                f"D {tag}: only {len(vals)} value(s). A group with one row is not indistinguishable "
                f"from anything and should not be in this table")
            continue
        if len(vals) != int(r["n_rows"]):
            problems.append(f"D {tag}: n_rows={r['n_rows']} but {len(vals)} values are listed")
        # --- B/C: re-derive the whole classification ---
        want_verdict, want_rest, want_ratio = classify(vals)
        if abs(max(vals) - float(r["largest"])) > 1e-3:
            problems.append(f"B {tag}: largest is {r['largest']} but the values give {max(vals)}")
        if abs(want_rest - float(r["sum_of_rest"])) > 1e-3:
            problems.append(
                f"B {tag}: sum_of_rest is {r['sum_of_rest']} but the values give {want_rest:.4f}")
        if want_ratio is not None and r["ratio"]:
            if abs(want_ratio - float(r["ratio"])) > 5e-4:
                problems.append(
                    f"B {tag}: ratio is {r['ratio']} but the values give {want_ratio:.4f}")
        if want_verdict != r["verdict"]:
            problems.append(
                f"C {tag}: recorded `{r['verdict']}` but its own values give `{want_verdict}` at "
                f"TOTAL_TOL={TOTAL_TOL} / NEAR_TOL={NEAR_TOL}. A total beside its parts read as "
                f"siblings is a double count waved through")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems[:40]:
            print(f"  {p}")
        if len(problems) > 40:
            print(f"  ... and {len(problems) - 40} more")
        return 1
    print("\nPASS: every group is well-formed and every verdict re-derives from its own values")
    return 0


if __name__ == "__main__":
    sys.exit(main())
