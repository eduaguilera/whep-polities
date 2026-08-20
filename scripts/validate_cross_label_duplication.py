#!/usr/bin/env python3
"""Do the recorded cross-label duplications still satisfy the conditions that made them findings?

`pipelines/polity-autoimprove/31_cross_label_duplication.py` reports two labels of one source whose
values are byte-identical across a CONTIGUOUS BLOCK of years and plainly different outside it (issue
468). The panel is gitignored and absent in CI, so the tool writes `state/cross_label_duplication.csv`
and this gate reads the committed table.

WHY EACH CONDITION IS GATED RATHER THAN TRUSTED. Every one of them is load-bearing, and dropping any
turns the screen into a false-positive generator:

  A. THE DISTINCTNESS FLOOR. 89 pairs have a contiguous identical block; 6 survive a 4-distinct-value
     floor. The 83 rejected are `estonia`/`iceland` goats and `belgium`/`malta` mules -- small round
     numbers matching by chance. This is the single most important number in the file.
  B. CONTIGUITY AND SIZE. `block_last - block_first + 1` must equal `block_years`: a scattered set of
     equal years is coincidence, an unbroken run is a copied stretch.
  C. THE PAIR MUST DIFFER OUTSIDE THE BLOCK. Identical everywhere means synonyms, which
     `25_same_polity_overlaps.py` owns; `outside_ratio_median` must sit outside [0.67, 1.5].
  D. DIRECTION IS ONLY CLAIMED WHERE THE BLOCK HAS A LEVEL. `block_matches_level_of`, when set, must
     name one of the two labels, and must be empty when `block_spread` exceeds 5. The first version
     of the generator ignored that and answered `serbia` for the iia czech/serbia pair -- the one case
     whose direction is independently established, and it runs the other way (issue 433). Its block
     swings 35x, so it has no level to match; blocks that do swing 1.2x-2.4x.

ALL 5 ARMS WERE VERIFIED TO FIRE on 2026-08-20, by mutating this table to trigger each in turn.
An arm that cannot fire passes every run while asserting nothing, and this repo has shipped three of
those (issues 407, 412, 420), so "the gate is green" is only meaningful once each arm is known live.
Verified: a block below the distinctness floor (A); a non-contiguous block (B); a pair that does
not differ outside its block (C); a direction claimed on a block with no level (D, permanent
case); a smaller_label contradicting its own ratio (E, which shipped INVERTED in all six rows and
is why arm E exists at all).

The COUNT is printed, not pinned: a new instance is a finding, not a regression, and pinning it would
make an honest discovery fail CI.
"""
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/cross_label_duplication.csv")

FIELDS = ["source", "item", "unit", "label_a", "label_b", "shared_years", "block_years",
          "block_first", "block_last", "block_distinct", "outside_ratio_median", "block_spread",
          "smaller_label", "block_matches_level_of"]
MIN_DISTINCT, MIN_BLOCK, SAME_LO, SAME_HI, MAX_BLOCK_SPREAD = 4, 3, 0.67, 1.5, 5.0


def main() -> int:
    problems = []
    if not os.path.exists(TABLE):
        print(f"FAIL: missing {os.path.relpath(TABLE, REPO)}", file=sys.stderr)
        return 1
    with open(TABLE, newline="") as fh:
        rd = csv.DictReader(fh)
        if rd.fieldnames != FIELDS:
            print(f"FAIL: header is {rd.fieldnames}, expected {FIELDS}", file=sys.stderr)
            return 1
        rows = list(rd)

    for i, r in enumerate(rows, start=2):
        w = f"line {i} {r['source']}/{r['item']}/{r['label_a']}+{r['label_b']}"
        try:
            shared, blk = int(r["shared_years"]), int(r["block_years"])
            first, last = int(r["block_first"]), int(r["block_last"])
            distinct = int(r["block_distinct"])
            om = float(r["outside_ratio_median"])
        except ValueError:
            problems.append(f"A {w}: a numeric field is not numeric")
            continue
        # --- A: the floor ---
        if distinct < MIN_DISTINCT:
            problems.append(f"A {w}: block holds {distinct} distinct value(s), below the floor of "
                            f"{MIN_DISTINCT}. 83 of 89 candidate pairs are rejected by this floor "
                            f"alone -- small round numbers match anything, and a block of them is "
                            f"coincidence rather than a copied series")
        if blk < MIN_BLOCK:
            problems.append(f"A {w}: block of {blk} year(s) is below the minimum of {MIN_BLOCK}")
        if blk > shared:
            problems.append(f"A {w}: block_years {blk} exceeds shared_years {shared}")
        if blk == shared:
            problems.append(f"A {w}: identical in ALL {shared} shared years, so these labels are "
                            f"synonyms and belong to validate_same_polity_overlaps, not here")
        # --- B: contiguity ---
        if last - first + 1 != blk:
            problems.append(f"B {w}: {blk} equal years spanning {first}-{last} is not contiguous; a "
                            f"scattered set of equal years is coincidence, an unbroken run is not")
        # --- C: must differ outside ---
        if SAME_LO < om < SAME_HI:
            problems.append(f"C {w}: outside_ratio_median {om} sits inside [{SAME_LO}, {SAME_HI}], so "
                            f"the two labels do not differ outside the block either")
        # --- D: direction only where the block has a level ---
        m = (r["block_matches_level_of"] or "").strip()
        spread = (r["block_spread"] or "").strip()
        if m and m not in (r["label_a"], r["label_b"]):
            problems.append(f"D {w}: block_matches_level_of {m!r} names neither label")
        if m and spread:
            try:
                if float(spread) > MAX_BLOCK_SPREAD:
                    problems.append(
                        f"D {w}: direction claimed ({m}) on a block whose own values swing "
                        f"{spread}x, above {MAX_BLOCK_SPREAD}. A block that disagrees with itself by "
                        f"more than the two labels do has no level to match -- this is exactly how "
                        f"the first version answered `serbia` for the pair whose direction is known "
                        f"to run the other way (issue 433)")
            except ValueError:
                problems.append(f"D {w}: block_spread {spread!r} is not numeric")
        if (r["smaller_label"] or "").strip() not in (r["label_a"], r["label_b"]):
            problems.append(f"D {w}: smaller_label {r['smaller_label']!r} names neither label")
        # --- E: smaller_label must AGREE with the ratio it is derived from ---
        # `outside_ratio_median` is median(label_a / label_b) over the differing years, so a value
        # below 1 means label_a is the smaller series. The generator's first version wrote
        # `a if om > 1 else b` and shipped this column naming the LARGER label in all six rows. It
        # survived review because `block_matches_level_of` stayed correct -- names and levels were
        # swapped together, so the double swap cancelled and the column anyone would sanity-check read
        # right while this one was wrong. Checking a derived column against its own input is the only
        # thing that catches that.
        want_smaller = r["label_a"] if om < 1 else r["label_b"]
        if (r["smaller_label"] or "").strip() != want_smaller:
            problems.append(
                f"E {w}: smaller_label is {r['smaller_label']!r} but outside_ratio_median {om} says "
                f"{want_smaller!r} is the smaller series (the ratio is a/b, so below 1 means a). An "
                f"inverted direction column reads as authoritative and points remediation at the "
                f"wrong label")

    by_src = {}
    for r in rows:
        by_src[r["source"]] = by_src.get(r["source"], 0) + 1
    dirn = sum(1 for r in rows if (r["block_matches_level_of"] or "").strip())
    print(f"{len(rows)} cross-label duplication(s): {by_src}; direction attributed for {dirn}, "
          f"withheld for {len(rows) - dirn}")
    for r in rows:
        print(f"  {r['source']:9} {r['item'][:22]:22} {r['label_a'][:18]:18}/{r['label_b'][:18]:18} "
              f"{r['block_years']}/{r['shared_years']} eq {r['block_first']}-{r['block_last']} "
              f"({r['block_distinct']} distinct)")
    if problems:
        print(f"FAIL: {len(problems)} cross-label duplication problem(s)", file=sys.stderr)
        for p in problems[:25]:
            print("  - " + p, file=sys.stderr)
        return 1
    print("PASS: every recorded duplication still clears the distinctness floor, is contiguous, "
          "differs outside its block, and claims direction only where the block has a level")
    return 0


if __name__ == "__main__":
    sys.exit(main())
