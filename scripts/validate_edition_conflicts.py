#!/usr/bin/env python3
"""Does one IIA yearbook VOLUME contradict another about the same cell?

Every other check here compares the panel against a polity, an area, a sibling series or a second
SOURCE. This compares one edition of one source against another edition of the same source -- the
only comparison available that can convict a specific extracted cell of being wrong, because the
same publisher printed both numbers for the same territory, commodity and year.

`pipelines/polity-autoimprove/26_edition_conflicts.py` builds it from the raw IIA extract's
`yearbook` column, which nothing in this repo had used. The extract lives outside the repo and is
absent in CI, so this gate reads the committed table -- the same arrangement as
`validate_constant_runs.py`, `validate_isolated_spikes.py` and `validate_same_polity_overlaps.py`.

WHAT THE FIRST RUN MEASURED (issue 414):

    production+area zero rate, by volume
      iia_1909_21   0.82%     iia_1933_34   0.14%
      iia_1925_26   0.04%     iia_1938_39   6.30%   <- 14x to 150x the others
      iia_1929_30   0.07%     iia_1939_45   0.45%

    cells carried by more than one volume that disagree   1141
      a zero contradicted by a real value                   83   ALL of them in iia_1938_39
      a non-zero value revised                            1058   median 1.032x, 189 above 2x

Austria's 1933 meslin area is 0 in `iia_1938_39` and 8,588 ha in `iia_1933_34`; Czechoslovakia's is
0 against 6,610. A blank or dash read as `0` explains both the volume-level rate and the fact that
every contradicted zero sits in that one volume.

THE COVERAGE LIMIT IS ALSO THE MECHANISM. Only 1933 is covered by a second volume, so most of
`iia_1938_39`'s 770 zeros cannot be tested here -- and that is exactly why they reach layer B. Where
a second opinion exists the pipeline already prefers it (1933: 179 raw zeros -> 61 in layer B); where
none exists the zeros pass through (1935: 148 -> 120).

Three signals:
  A. VOLUME ASYMMETRY  every contradicted zero must still sit in the volume this was traced to. A
     zero contradicted in a DIFFERENT volume means a new extraction defect, not this one.
  B. COUNT CEILINGS    both conflict classes are pinned. Bidirectional: repairing cells must lower
     them with a note, so the table cannot quietly refill.
  C. INTERNAL SHAPE    a `zero_contradicted` row must actually carry a zero, a `revised` row must
     not, and the recorded ratio must match the two values it sits beside.

Usage:
  python3 scripts/validate_edition_conflicts.py
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/edition_conflicts.csv")

# Measured 2026-08-19 on the first run. BIDIRECTIONAL: setting false zeros to missing must lower
# ZERO_CONTRADICTED with a note saying which cells were repaired.
BASELINE_ZERO_CONTRADICTED = 83
BASELINE_REVISED = 959
# Measured 2026-08-19 (issue 424). 99 revisions differ by a clean power of ten, and 98 of the 99 hold
# the SMALLER value in iia_1933_34. The control is what makes that significant rather than a property
# of the volume: across all 1,032 revisions between the two volumes, iia_1933_34 is the smaller side
# 55% of the time -- a coin flip. BIDIRECTIONAL, because unlike the zero class these are repairable
# from the data: the other volume prints the other figure.
BASELINE_POWER_OF_TEN = 99
# Of the 99, this many must still hold the smaller value in iia_1933_34. A drop means a value moved.
BASELINE_POW10_SMALLER_IN_1933 = 98
POW10_VOLUME = "iia_1933_34"

# Every contradicted zero traced to this one volume. Not a threshold -- an observed 83 of 83.
ZERO_VOLUME = "iia_1938_39"

KINDS = {"zero_contradicted", "revised", "power_of_ten"}


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} missing — run 26_edition_conflicts.py --write",
              file=sys.stderr)
        return 1
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    zc = [r for r in rows if r["kind"] == "zero_contradicted"]
    rev = [r for r in rows if r["kind"] == "revised"]
    p10 = [r for r in rows if r["kind"] == "power_of_ten"]
    print(f"edition conflicts: {len(rows)}  "
          f"(zero_contradicted {len(zc)}/{BASELINE_ZERO_CONTRADICTED}, "
          f"power_of_ten {len(p10)}/{BASELINE_POWER_OF_TEN}, "
          f"revised {len(rev)}/{BASELINE_REVISED})")

    problems = []

    # --- B: ceilings ---
    if len(zc) > BASELINE_ZERO_CONTRADICTED:
        problems.append(
            f"B {len(zc)} cells read 0 in one volume and a real value in another, above the ceiling "
            f"of {BASELINE_ZERO_CONTRADICTED}. A zero publishes as 'produced none of this' and "
            f"biases every aggregate over the series downward")
    elif len(zc) < BASELINE_ZERO_CONTRADICTED:
        problems.append(
            f"B only {len(zc)} contradicted zeros remain, below the pinned ceiling of "
            f"{BASELINE_ZERO_CONTRADICTED} — lower the baseline and say which cells were repaired "
            f"and whether they were set to missing or to the other volume's value")
    if len(rev) > BASELINE_REVISED:
        problems.append(
            f"B {len(rev)} cells carry different non-zero values in two volumes, above the ceiling "
            f"of {BASELINE_REVISED}. The source revising itself is normal; MORE of it means either "
            f"a new extraction defect or a volume newly double-counted into the extract")
    elif len(rev) < BASELINE_REVISED:
        problems.append(
            f"B only {len(rev)} revisions remain, below the pinned ceiling of {BASELINE_REVISED} — "
            f"lower the baseline and say what was reconciled")

    # --- D: the power-of-ten class and its direction ---
    if len(p10) != BASELINE_POWER_OF_TEN:
        problems.append(
            f"D {len(p10)} revisions differ by a clean power of ten, against the pinned "
            f"{BASELINE_POWER_OF_TEN}. A source does not restate an estimate by exactly a "
            f"hundredfold — these are dropped digits or a units column read as absolute (issues 416, "
            f"424) — so a change here means a value moved or the extraction did")
    smaller = 0
    for r in p10:
        try:
            a, b = float(r["value_a"]), float(r["value_b"])
        except ValueError:
            continue
        if (r["volume_a"] if a < b else r["volume_b"]) == POW10_VOLUME:
            smaller += 1
    print(f"power-of-ten revisions holding the smaller value in {POW10_VOLUME}: "
          f"{smaller}/{len(p10)} (pinned {BASELINE_POW10_SMALLER_IN_1933})")
    if smaller != BASELINE_POW10_SMALLER_IN_1933:
        problems.append(
            f"D {smaller} of {len(p10)} power-of-ten revisions hold the smaller value in "
            f"{POW10_VOLUME}, against the pinned {BASELINE_POW10_SMALLER_IN_1933}. THE DIRECTION IS "
            f"THE EVIDENCE: across all revisions between the two volumes {POW10_VOLUME} is the "
            f"smaller side only 55% of the time, so a near-unanimous split here is what distinguishes "
            f"a systematic dropped digit from ordinary revision. Losing it means the class has "
            f"stopped being one phenomenon")

    # --- A: the asymmetry that identifies the defect ---
    for r in zc:
        holder = r["volume_a"] if r["value_a"] == "0" else r["volume_b"]
        if holder != ZERO_VOLUME:
            problems.append(
                f"A {r['label']}/{r['product']} {r['year']}: a zero contradicted by another volume "
                f"sits in {holder!r}, not {ZERO_VOLUME!r}. Every one of the {len(zc)} known cases is "
                f"in that one volume, so this is a DIFFERENT extraction defect and needs its own "
                f"diagnosis rather than being absorbed into issue 414's")

    # --- C: internal shape ---
    for r in rows:
        if r["kind"] not in KINDS:
            problems.append(f"C unknown kind {r['kind']!r} for {r['label']}/{r['product']}")
            continue
        try:
            a, b = float(r["value_a"]), float(r["value_b"])
        except ValueError:
            problems.append(f"C {r['label']}/{r['product']} {r['year']}: unparseable values")
            continue
        has_zero = (a == 0 or b == 0)
        if r["kind"] == "zero_contradicted" and not has_zero:
            problems.append(
                f"C {r['label']}/{r['product']} {r['year']} is classed zero_contradicted but "
                f"neither value is zero — the class that makes a cell provably wrong has been "
                f"diluted with ordinary revisions")
        if r["kind"] == "revised" and has_zero:
            problems.append(
                f"C {r['label']}/{r['product']} {r['year']} is classed revised but carries a zero — "
                f"a provably wrong cell is hiding in the class the ceiling treats as normal")
        if a == b:
            problems.append(
                f"C {r['label']}/{r['product']} {r['year']}: the two volumes agree, so this is not "
                f"a conflict and should not be in the table")
        if r["ratio"] != "inf":
            hi, lo = max(abs(a), abs(b)), min(abs(a), abs(b))
            want = hi / lo if lo else None
            if want is None or abs(float(r["ratio"]) - want) > 1e-3:
                problems.append(
                    f"C {r['label']}/{r['product']} {r['year']}: recorded ratio {r['ratio']} does "
                    f"not match its own two values ({a:g}, {b:g}) — the column every judgement here "
                    f"rests on no longer describes the row it sits in")

    for p in problems:
        print(f"FAIL: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
