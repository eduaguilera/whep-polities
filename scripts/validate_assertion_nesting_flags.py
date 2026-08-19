#!/usr/bin/env python3
"""Does the nesting-flag table still describe its own rows?

`state/assertion_nesting_flags.csv` is issue 273's table: 234 same-source assertion pairs whose
candidate polygons nest, with the panel's own extensive cells tested against inclusion. Its headline
is that **in 20 of them inclusion is arithmetically impossible** — the source reports the outer
territory EXCLUSIVE of the inner one, so the polity a label is routed to is larger than what the
numbers describe. Metropolitan Japan against Korea and Formosa is the largest case; Juan's UK against
Ireland the second.

Until 2026-08-19 no gate read it (issue 432 found 11 such tracked tables). That matters more here than
for most: 13 of the 20 impossible pairs contradict an already-BANKED verdict, so the table is evidence
against recorded decisions, and nothing checked that it still said what it says.

The `inclusion` verdict is FULLY RE-DERIVABLE from two of the row's own columns, using the generator's
own thresholds (`--min-violations 3`, `--min-violation-frac 0.1`):

    impossible_outer_excludes_inner   cells_outer_lt_inner >= 3  AND  / shared_cells > 0.10
    consistent_with_inclusion         cells_outer_lt_inner == 0
    few_violations                    otherwise

Verified: that rule reproduces all 84 rows carrying shared cells, with zero mismatches. The other 150
are `no_shared_cells` or `label_not_in_panel`, which the arithmetic cannot speak to and which this
gate therefore requires to carry NO violating cells rather than re-deriving them.

WHY THE 20 IS PINNED HERE, when validate_magnitude_outliers.py deliberately pins no count. The
distinction is what the number is. 2,718 screening rows shift with any panel refresh, so pinning them
would fail on a correct action and train the next person to edit baselines. **20 is a curated finding
count that issue 273 is about.** If it moves, someone should have to say why — including whoever
eventually fixes #273, whose remedy will move it on purpose. That is what a bidirectional pin is for.

Usage:
  python3 scripts/validate_assertion_nesting_flags.py
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/assertion_nesting_flags.csv")
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")

# The generator's own defaults, restated so this gate does not depend on its constants to know what
# the table means.
MIN_VIOLATIONS = 3
MIN_VIOLATION_FRAC = 0.1

# Measured 2026-08-19. BIDIRECTIONAL: issue 273's remedy will change this deliberately, and whoever
# changes it should have to say so.
BASELINE_IMPOSSIBLE = 20

VERDICTS = {"impossible_outer_excludes_inner", "consistent_with_inclusion", "few_violations",
            "no_shared_cells", "label_not_in_panel"}
# The two the arithmetic cannot speak to: no cells were comparable, so no verdict is derivable.
NO_CELL_VERDICTS = {"no_shared_cells", "label_not_in_panel"}


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} missing — run 12_triage_assertions.py",
              file=sys.stderr)
        return 1
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    live = None
    if os.path.exists(POLITIES):
        with open(POLITIES, encoding="utf-8") as fh:
            live = {r["polity_code"] for r in csv.DictReader(fh)}

    problems, orphans, derived, impossible = [], set(), 0, 0
    for i, r in enumerate(rows, start=2):
        where = f"line {i} {r.get('outer_code')} <- {r.get('inner_code')}"
        verdict = r.get("inclusion", "")
        if verdict not in VERDICTS:
            problems.append(f"unknown inclusion {verdict!r} at {where} — generator and gate "
                            f"disagree about the vocabulary")
            continue
        if verdict == "impossible_outer_excludes_inner":
            impossible += 1

        c, s = num(r.get("cells_outer_lt_inner")), num(r.get("shared_cells"))

        # --- A: the verdict must follow from the row's own two numbers ---
        if verdict in NO_CELL_VERDICTS:
            if c:
                problems.append(
                    f"A {where}: verdict {verdict!r} means no cells were comparable, but the row "
                    f"records {c:g} violating cells")
        elif c is None or s is None or not s:
            problems.append(f"A {where}: verdict {verdict!r} needs shared cells to be derivable, "
                            f"but shared_cells={r.get('shared_cells')!r}")
        else:
            want = ("impossible_outer_excludes_inner"
                    if (c >= MIN_VIOLATIONS and c / s > MIN_VIOLATION_FRAC)
                    else "consistent_with_inclusion" if c == 0 else "few_violations")
            derived += 1
            if want != verdict:
                problems.append(
                    f"A {where}: table says {verdict!r} but its own numbers "
                    f"({c:g} of {s:g} = {c / s:.1%}) give {want!r} under the generator's thresholds "
                    f"(>={MIN_VIOLATIONS} cells and >{MIN_VIOLATION_FRAC:.0%})")
            if c > s:
                problems.append(f"A {where}: {c:g} violating cells exceeds {s:g} shared cells")

        # --- B: both codes must still exist ---
        if live is not None:
            for k in ("outer_code", "inner_code"):
                if r.get(k) and r[k] not in live:
                    orphans.add(r[k])

        # --- C: nesting means the inner polygon is inside the outer ---
        oa, ia = num(r.get("outer_km2")), num(r.get("inner_km2"))
        if oa is not None and ia is not None and ia > oa + 1:
            problems.append(
                f"C {where}: inner_km2 {ia:,.0f} exceeds outer_km2 {oa:,.0f} — this table is by "
                f"definition pairs whose polygons NEST, so the pair does not belong in it")

        # --- D: a covered share is a share ---
        sh = num(r.get("inner_share_covered"))
        if sh is not None and not (-1e-9 <= sh <= 1.0 + 1e-9):
            problems.append(f"D {where}: inner_share_covered {sh:g} is outside [0, 1]")

    for code in sorted(orphans):
        problems.append(
            f"B {code} is not a polity in data/final/polities_database.csv — the database moved "
            f"under this table and rows on that code point at nothing. This is how six rows in "
            f"magnitude_outliers.csv survived on re-spanned codes (issue 432)")

    print(f"nesting flags: {len(rows)} pairs, {derived} verdicts re-derived from their own numbers, "
          f"impossible {impossible}/{BASELINE_IMPOSSIBLE}, orphaned codes {len(orphans)}")

    if impossible > BASELINE_IMPOSSIBLE:
        problems.append(
            f"{impossible} pairs are arithmetically impossible, above the pinned "
            f"{BASELINE_IMPOSSIBLE}. A new one means a label is routed to a polity larger than the "
            f"numbers describe — issue 273's class")
    elif impossible < BASELINE_IMPOSSIBLE:
        problems.append(
            f"only {impossible} impossible pairs remain, below the pinned {BASELINE_IMPOSSIBLE} — "
            f"lower the baseline and say which pair was resolved and how (issue 273)")

    for p in problems:
        print(f"FAIL: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
