#!/usr/bin/env python3
"""Do the recorded component under-selections still satisfy the criterion that made them findings?

`pipelines/polity-autoimprove/33_component_underselection.py` records layer-B `iia` nutrient series
that consistently publish the SMALLEST of several raw materials the source prints side by side (issue
490). The raw extract is not in this repo and absent in CI, so the tool writes
`state/component_underselection.csv` and this gate reads the committed table.

WHY THIS CLASS NEEDS ITS OWN GATE. Issue 379 already gates raw-product switching, on OSCILLATION
(A...B...A), because a one-way switch cannot be told from growth. A series that never switches -- that
picks the smallest material every time -- produces no oscillation, no level shift and no seam, and
every value is plausible for the product it came from. Only ONE of the eight rows here (`japan / p`)
appears in 379's table; the other seven are invisible to it by construction.

  A  THE UNDER-SELECTION CONDITION. `worst_picked_value` must be under half `worst_max_value`, and
     `worst_ratio` must equal their quotient. This is the finding itself: a cell whose picked product
     is most of the same-year maximum is not an under-selection.
  B  THE SHARE AND THE FLOOR, restated here and not imported, so relaxing the generator and
     regenerating cannot quietly admit weaker rows: at least 4 attributable cells, and at least 60%
     of them under-selected.
  C  ARITHMETIC. `n_underselected` <= `n_attributable`, and `share_underselected` equals their
     quotient.
  D  VOCABULARY. `source` is `iia`, `item` is one of p/n/k, `unit` is tonnes -- the restriction that
     makes "several materials stand side by side in one cell" the source's own structure rather than
     an ambiguity. `worst_picked_product` must name a raw product, not a layer-B item.

NO FLOOR ON THE ROW COUNT, DELIBERATELY, AND THE OBVIOUS ALTERNATIVE IS ALSO WRONG. This defect is
fixable in this repo, so pinning the defect count would make a correct fix fail CI. Flooring the
DENOMINATOR instead looks safe -- "how many cells are attributable" sounds like a property of the data
-- but it is not: attribution works by matching a published value to exactly one raw material, so if
the remedy publishes a real P2O5 total the value matches no single material and the denominator
collapses to zero as well. Both floors break on the fix.

The residual risk is therefore stated rather than hidden: a regeneration that silently returns zero
rows passes this gate. It is the same bargain `validate_cross_label_duplication.py` makes, for the same
reason -- a new instance is a finding, not a regression.

WHAT IS NOT ASSERTED. Any remedy. Summing the materials double-counts, since superphosphate is
manufactured FROM phosphate rock, and the item is a nutrient category while the raw figures are
material gross weights at different P2O5 contents. Issue 490 holds that decision.
"""
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/component_underselection.csv")

FIELDS = ["source", "label", "item", "unit", "verdict", "n_attributable", "n_underselected",
          "share_underselected", "worst_ratio", "worst_year", "worst_picked_product",
          "worst_picked_value", "worst_max_value"]

ITEMS = {"p", "n", "k"}
MIN_CELLS = 4            # B: restated, not imported
UNDERSEL_SHARE = 0.60    # B: restated, not imported
SMALLER_THAN = 0.50      # A: the under-selection condition
VERDICTS = {"underselects_minor_component", "attributable_no_underselection",
            "too_few_attributable_cells"}

# THE TABLE IS A CENSUS OF IN-SCOPE SERIES, NOT A LIST OF FINDINGS, and that is what makes a floor
# possible. This gate previously recorded, correctly, that neither the defect count nor
# `n_attributable` can be floored: a remedy publishing a genuine P2O5 total makes the published value
# match no raw material, so attribution collapses alongside the fix and both counts go to zero. That
# left "a regeneration silently returning zero rows passes" as a stated, unresolved risk.
#
# The SERIES survive a remedy -- iia still publishes a `p` series for spain, with different values --
# so the census row count is the one quantity a correct fix leaves alone and a broken regeneration
# destroys. 81 today; the floor is well below it because the scope moves when routing changes.
BASELINE_MIN_SERIES = 65

# POTASSIUM IS CLEAN, AND THAT IS A SCOPE CLAIM WORTH CHECKING RATHER THAN RESTATING. The table
# carries 8 `k` series and not one under-selected cell among them (`germany / k` has 4 attributable
# cells and 0 under-selected; the other 7 have none), so the defect is confined to `n` and `p`. That
# matters for the remedy: a fix framed as "nutrient series publish the smallest material" would imply
# potash needs the same treatment, and it does not.
#
# Unlike the defect count, this pin is safe against a correct remedy. A remedy collapses attribution
# for the affected series and drives their counts to zero -- which is exactly why the comment above
# refuses to floor them -- but `k` is already at zero, so a remedy cannot move it. Only a NEW finding
# can, and catching that is the point.
K_UNDERSELECTED = 0


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} missing — "
              f"run 33_component_underselection.py --write", file=sys.stderr)
        return 1
    with open(TABLE, newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        if rdr.fieldnames != FIELDS:
            print(f"FAIL: {TABLE} header is {rdr.fieldnames}, expected {FIELDS}", file=sys.stderr)
            return 1
        rows = list(rdr)

    problems = []
    bad_rows = [r for r in rows if r.get("verdict") == "underselects_minor_component"]
    for r in rows:
        who = f"{r['source']}/{r['label']}/{r['item']}"
        try:
            na, nu = int(r["n_attributable"]), int(r["n_underselected"])
        except (TypeError, ValueError) as e:
            problems.append(f"{who}: unparseable count ({e})")
            continue
        flagged = r.get("verdict") == "underselects_minor_component"
        if r.get("verdict") not in VERDICTS:                                        # D
            problems.append(f"{who}: verdict {r.get('verdict')!r} not in {sorted(VERDICTS)}")
        # E. THE VERDICT MUST FOLLOW FROM THE COUNTS. Without this the census could carry a series
        # that meets every criterion while labelled clean, which is the one way a defect could hide
        # inside a table whose whole point is to enumerate them.
        want = ("underselects_minor_component" if na >= MIN_CELLS and nu >= na * UNDERSEL_SHARE
                else "attributable_no_underselection" if na >= MIN_CELLS
                else "too_few_attributable_cells")
        if r.get("verdict") in VERDICTS and r["verdict"] != want:
            problems.append(
                f"{who}: verdict {r['verdict']!r} but {nu}/{na} attributable cells make it {want!r}")
        if not flagged:
            if nu > na:                                                             # C
                problems.append(f"{who}: n_underselected {nu} exceeds n_attributable {na}")
            continue
        try:
            share, ratio = float(r["share_underselected"]), float(r["worst_ratio"])
            picked, mx = float(r["worst_picked_value"]), float(r["worst_max_value"])
        except (TypeError, ValueError) as e:
            problems.append(f"{who}: flagged row with unparseable numeric field ({e})")
            continue

        if r["source"] != "iia":                                                    # D
            problems.append(f"{who}: source {r['source']!r} is not iia")
        if r["item"] not in ITEMS:                                                  # D
            problems.append(f"{who}: item {r['item']!r} is not one of {sorted(ITEMS)}")
        if r["unit"] != "tonnes":                                                   # D
            problems.append(f"{who}: unit {r['unit']!r} is not tonnes")
        if r["worst_picked_product"] in ITEMS or not r["worst_picked_product"].strip():   # D
            problems.append(
                f"{who}: worst_picked_product {r['worst_picked_product']!r} is not a raw product "
                f"name — the column must name the MATERIAL that was picked, not the nutrient item")
        if not (picked > 0 and mx > 0):
            problems.append(f"{who}: worst_picked_value {picked} / worst_max_value {mx} not positive")
        elif picked >= mx * SMALLER_THAN:                                           # A
            problems.append(
                f"{who}: worst_picked_value {picked:,.0f} is not under half worst_max_value "
                f"{mx:,.0f}. That is the finding itself — a cell whose picked product is most of the "
                f"same-year maximum is not an under-selection and does not belong in this table")
        elif abs(ratio - mx / picked) > max(0.01, 1e-4 * ratio):                     # A
            problems.append(f"{who}: worst_ratio {ratio} != worst_max/worst_picked = {mx / picked:.4f}")
        if nu > na:                                                                  # C
            problems.append(f"{who}: n_underselected {nu} exceeds n_attributable {na}")
        elif abs(share - nu / na) > 1e-4:                                            # C
            problems.append(f"{who}: share_underselected {share} != {nu}/{na} = {nu / na:.4f}")
        if na < MIN_CELLS:                                                           # B
            problems.append(
                f"{who}: {na} attributable cell(s), below the floor of {MIN_CELLS}. Below it a share "
                f"is not evidence — `canada / p` shows a 446x gap on 3 cells and is deliberately out")
        if nu < na * UNDERSEL_SHARE:                                                 # B
            problems.append(
                f"{who}: {nu}/{na} under-selected is below the {UNDERSEL_SHARE:.0%} share this table "
                f"requires; an occasional small pick is a switch, which issue 379's gate owns")

    tot_u = sum(int(r["n_underselected"]) for r in bad_rows)
    tot_a = sum(int(r["n_attributable"]) for r in bad_rows)
    print(f"{len(rows)} iia fertilizer series in scope (floor {BASELINE_MIN_SERIES}); "
          f"{len(bad_rows)} publish a minor component as the nutrient category "
          f"({tot_u} of {tot_a} attributable non-zero cells) — that count is printed, NOT pinned, "
          f"because a correct remedy empties it and collapses its denominator too")
    k_bad = [r for r in rows if r["item"] == "k" and int(r["n_underselected"] or 0) > 0]
    if len(k_bad) != K_UNDERSELECTED:
        problems.append(
            f"{len(k_bad)} `k` series now show an under-selected cell, recorded {K_UNDERSELECTED} "
            f"({', '.join(r['label'] for r in k_bad)}). The class has been confined to `n` and `p`, "
            f"and that is a published scope claim (issue 490); potash joining it is a new finding "
            f"and must not land silently. A remedy cannot cause this, because `k` is already at zero")

    if len(rows) < BASELINE_MIN_SERIES:
        problems.append(
            f"only {len(rows)} series in scope, below the floor of {BASELINE_MIN_SERIES}. This is a "
            f"CENSUS of iia p/n/k series, so it shrinks only when routing changes or the "
            f"regeneration broke -- and it is the one count a correct remedy does NOT move, which is "
            f"why it can carry a floor where the defect count cannot")
    for r in bad_rows:
        print(f"  {r['label'][:18]:19}{r['item']:3}{r['n_underselected']:>4}/{r['n_attributable']:<4}"
              f" worst {float(r['worst_ratio']):>7.0f}x  {r['worst_year']}: "
              f"{r['worst_picked_product'][:32]:34}{float(r['worst_picked_value']):>10,.0f}"
              f" vs {float(r['worst_max_value']):>10,.0f}")

    if problems:
        print(f"FAIL: {len(problems)} component-under-selection problem(s)", file=sys.stderr)
        for p in problems[:25]:
            print("  - " + p, file=sys.stderr)
        return 1
    print(f"PASS: {len(rows)} iia p/n/k series checked; the {len(bad_rows)} flagged ones each pick a "
          f"material under half the same-year maximum in at least {UNDERSEL_SHARE:.0%} of at least "
          f"{MIN_CELLS} attributable cells, every row's share and ratio agrees with its own counts, "
          f"and no `k` series under-selects")
    return 0


if __name__ == "__main__":
    sys.exit(main())
