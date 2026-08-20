#!/usr/bin/env python3
"""Do the recorded grid-ambiguous zeros still satisfy the condition that made them findings?

`pipelines/polity-autoimprove/32_grid_ambiguous_zeros.py` records published zeros that the source's
REPORTING GRID cannot distinguish from a small positive value (issue 446). The panel is gitignored and
absent in CI, so the tool writes `state/grid_ambiguous_zeros.csv` and this gate reads the committed
table.

WHY EACH CONDITION IS GATED RATHER THAN TRUSTED:

  A. `min_nonzero == grid` IS THE WHOLE CRITERION. Being on a coarse grid is not suspicious by itself:
     a series of 500,000-tonne harvests on a 1000-grid has a 0.1% rounding error and its zeros mean
     what they say. The zeros are ambiguous only where the quantity lives at the grid's resolution
     floor, so the step below the smallest observation is zero. Drop this and the table would grow to
     every coarse series in the panel and assert nothing. 227 zeros sit in a fully-coarse series; 201
     survive this condition.
  B. THE GRID MUST DIVIDE THE SERIES. `max_nonzero` must be a multiple of `grid`, and `grid` itself
     must be 100 or 1000. A row whose own extremes are off the grid it claims is not measuring a grid.
  C. THE ZERO ACCOUNTING MUST CLOSE. `zeros_dated + zeros_undated == zeros`, and `zero_years` must
     list exactly `zeros_dated` years. This arm exists because the first version of the generator
     listed only dated years while counting all of them: four rows carried a `zero_years` shorter
     than their own `zeros` and nothing said why, because a `.dropna()` had discarded the period rows
     silently. The split matters for exposure, not just tidiness -- a zero on a `period` row never
     reaches the R package (`build.R` filters `!is.na(year)`), so `zeros_dated` is the consumer-facing
     number and it is 197 of the 201.
  D. THE NON-ZERO FLOOR IS RESTATED HERE, NOT IMPORTED. With fewer than 3 non-zero values, "all of
     them are on a grid" is a coincidence. Restating means relaxing the generator and regenerating
     cannot quietly refill the table.
  E. A FLOOR ON THE TOTAL. `iceland / goats` alone carries 69 zeros over a vocabulary of {0, 1000,
     2000}; a regeneration that returns an empty or near-empty table has broken, not improved. The
     floor is what a correct rebuild produces, not the current row count, so a genuine new instance
     still passes.

The COUNT IS PRINTED, NOT PINNED above the floor: a new instance is a finding, not a regression.

WHAT THIS GATE DOES NOT ASSERT. It does not claim any particular zero is non-zero -- that needs a
source outside the panel. It asserts only that each recorded zero is UNINFORMATIVE, which is what the
criterion establishes. The remedy is issue 446's open schema question and deliberately not encoded.
"""
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/grid_ambiguous_zeros.csv")

FIELDS = ["source", "country", "item", "unit", "indicator", "grid", "zeros", "zeros_dated",
          "zeros_undated", "n_nonzero", "min_nonzero", "max_nonzero", "distinct_nonzero",
          "zero_share", "zero_years"]

ALLOWED_GRIDS = {100.0, 1000.0}
MIN_NONZERO = 3            # arm D: restated, not imported from the generator
MIN_TOTAL_ZEROS = 60       # arm E: iceland/goats alone carries 69
MIN_ROWS = 5


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"FAIL: missing {TABLE}", file=sys.stderr)
        return 1
    with open(TABLE, newline="") as fh:
        rdr = csv.DictReader(fh)
        if rdr.fieldnames != FIELDS:
            print(f"FAIL: {TABLE} header is {rdr.fieldnames}, expected {FIELDS}", file=sys.stderr)
            return 1
        rows = list(rdr)

    problems = []
    total = dated = 0
    for r in rows:
        who = f"{r['source']}/{r['country']}/{r['item']}/{r['unit']}"
        try:
            grid = float(r["grid"])
            z, zd, zu = int(r["zeros"]), int(r["zeros_dated"]), int(r["zeros_undated"])
            nnz, mn, mx = int(r["n_nonzero"]), float(r["min_nonzero"]), float(r["max_nonzero"])
            dnz, share = int(r["distinct_nonzero"]), float(r["zero_share"])
        except (TypeError, ValueError) as e:
            problems.append(f"{who}: unparseable numeric field ({e})")
            continue
        total += z
        dated += zd

        if grid not in ALLOWED_GRIDS:                                            # B
            problems.append(f"{who}: grid {grid} is not one of {sorted(ALLOWED_GRIDS)}")
        if mn != grid:                                                           # A
            problems.append(
                f"{who}: min_nonzero {mn} != grid {grid}. This is the entire criterion -- a series "
                f"whose smallest observation is above the reporting step has no rounding path to "
                f"zero, so its zeros are not ambiguous and it does not belong in this table")
        if grid and mx % grid != 0:                                              # B
            problems.append(f"{who}: max_nonzero {mx} is not a multiple of its own grid {grid}")
        if nnz < MIN_NONZERO:                                                    # D
            problems.append(
                f"{who}: {nnz} non-zero value(s), below the floor of {MIN_NONZERO}. Below it, "
                f"'every non-zero value is on the grid' is a coincidence rather than a convention")
        if dnz < 1 or dnz > nnz:
            problems.append(f"{who}: distinct_nonzero {dnz} outside 1..{nnz}")
        if z < 1:
            problems.append(f"{who}: recorded with {z} zeros")
        if zd + zu != z:                                                         # C
            problems.append(f"{who}: zeros_dated {zd} + zeros_undated {zu} != zeros {z}")
        listed = [y for y in (r["zero_years"] or "").split(";") if y.strip()]
        if len(listed) != zd:                                                    # C
            problems.append(
                f"{who}: zero_years lists {len(listed)} year(s) but zeros_dated is {zd}. A gap here "
                f"means undated zeros are being dropped silently instead of counted in "
                f"zeros_undated, which is how the first version of this table shipped")
        if len({y for y in listed}) != len(listed):
            problems.append(f"{who}: zero_years repeats a year")
        exp = round(z / (z + nnz), 4)
        if abs(share - exp) > 1e-4:
            problems.append(f"{who}: zero_share {share} != zeros/(zeros+n_nonzero) = {exp}")

    if len(rows) < MIN_ROWS or total < MIN_TOTAL_ZEROS:                           # E
        problems.append(
            f"table has {len(rows)} row(s)/{total} zero(s), below the floor of {MIN_ROWS}/"
            f"{MIN_TOTAL_ZEROS}. `iceland / goats` alone carries 69 zeros over a vocabulary of "
            f"{{0, 1000, 2000}}, so a table this small means the screen has broken, not that the "
            f"panel improved")

    by = {}
    for r in rows:
        k = (r["source"], r["unit"])
        by[k] = by.get(k, 0) + int(r["zeros"])
    print(f"{total} grid-ambiguous zero(s) in {len(rows)} series "
          f"({dated} dated and consumer-facing, {total - dated} on period rows the R package drops); "
          f"by source/unit: {by}")
    for r in rows[:8]:
        print(f"  {r['source']:9} {r['country'][:15]:16} {r['item'][:26]:27} {r['unit']:7} "
              f"grid={r['grid']:>5} zeros={r['zeros']:>3} non-zero range "
              f"{r['min_nonzero']}-{r['max_nonzero']} ({r['distinct_nonzero']} distinct)")

    if problems:
        print(f"FAIL: {len(problems)} grid-ambiguous-zero problem(s)", file=sys.stderr)
        for p in problems[:25]:
            print("  - " + p, file=sys.stderr)
        return 1
    print(f"PASS: all {len(rows)} series live at their grid's resolution floor "
          f"(min_nonzero == grid), the grid divides their extremes, every zero is accounted for as "
          f"dated or undated, and each clears the {MIN_NONZERO}-non-zero floor")
    return 0


if __name__ == "__main__":
    sys.exit(main())
