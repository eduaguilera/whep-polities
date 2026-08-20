#!/usr/bin/env python3
"""Are the per-row verdicts on iia's post-1933 tobacco/hops era consistent with their own numbers?

`pipelines/polity-autoimprove/29_era_shift_verdicts.py` classifies every `iia` tobacco/hops production
row from 1934 -- the era issue 416 sized at 328 rows across 56 labels, against a pre-1934 median yield of
0.92 t/ha and a 1934+ median of 76.00. The layer-B panel is gitignored and absent in CI, so the tool
writes `state/era_shift_verdicts.csv` and this gate reads the committed table.

THE ARM THAT MATTERS IS D, AND IT EXISTS BECAUSE THE OBVIOUS CODE LOSES THE BEST EVIDENCE. 50 of these
rows carry production of 200 to 85,000 tonnes against an area of EXACTLY 0. Their implied yield is
infinite, which is the strongest thing any row here says. Written the natural way --

    if area > 0:  test the yield

-- all 50 fall through to the much weaker "is it 30x its own history" test. Measured by restoring the
guard and re-running: 36 of them are still convicted by that weaker test, and **14 are EXONERATED** --
11 classed `no_area_level_consistent` and 3 `untestable`, i.e. reported as fine. So the guard does not
merely weaken the evidence, it clears rows whose implied yield is infinite, and the convicted total falls
from 266 to 252. That is not hypothetical: those are exactly the counts the first pass at this measurement
reported (252 convicted, 92 level_shift, 28 consistent, 17 untestable), which is how the guard was found.
Issue 420 is the same shape -- an `area_ha > 0` filter before a division dropped 177 infinite-yield cells
from the tool built to find impossible yields. So arm D forbids a zero-area row from carrying any verdict
other than `impossible_yield_zero_area`.

Those zeros are almost certainly issue 414's defect surfacing in the AREA series -- `iia_1938_39` reads
blank cells as 0 and its window is exactly this era -- so two open defects interact here: a false-zero
area disables the yield test for the production row beside it.

Checks:
  A. VOCABULARY -- seven verdicts, and `convicted` agrees with which of them convict.
  B. ARITHMETIC -- `implied_yield` is production/area where area > 0, `ratio_to_own` is
     production/own_pre_era_median, and a row with no area carries no yield.
  C. THRESHOLD COHERENCE -- each verdict's own numbers must place it in that class: nothing called
     impossible below 20 t/ha, nothing called plausible above 3, nothing called a level shift below 30x.
     This is what stops a threshold being edited in the tool while the table keeps its old labels.
  D. ZERO AREA IS A VERDICT, NOT A SKIP (see above).
  E. THE ERA FLOOR -- every row is 1934 or later, since 1933 is the last year a second yearbook volume
     offers an opinion (issue 414) and a row before it belongs to a different question.

ALL 5 ARMS WERE VERIFIED TO FIRE on 2026-08-20, by mutating this table to trigger each in turn.
An arm that cannot fire passes every run while asserting nothing, and this repo has shipped three of
those (issues 407, 412, 420), so "the gate is green" is only meaningful once each arm is known live.
Verified: an unknown verdict (A); an implied_yield disagreeing with production/area (B); an
`impossible_yield` row pushed below the 20 t/ha line (C); a zero-area row reclassified (D, which
also carries the permanent selftest case); a row dated before 1934 (E).

The class COUNTS are printed, not pinned: they move whenever the panel or the matcher legitimately moves.
What is pinned is arithmetic and the zero-area rule, neither of which can legitimately break.
"""
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/era_shift_verdicts.csv")

FIELDS = ["source", "label", "whep_code", "item", "year", "period", "unit", "production", "area_ha",
          "implied_yield", "own_pre_era_median", "ratio_to_own", "verdict", "convicted"]
CONVICTING = {"impossible_yield_zero_area", "impossible_yield", "no_area_level_shift"}
NOT_CONVICTING = {"high_yield_3to20", "plausible_yield", "no_area_level_consistent", "untestable"}
IMPOSSIBLE_YIELD, HIGH_YIELD, LEVEL_SHIFT, ERA_FROM = 20.0, 3.0, 30.0, 1934


def _f(s):
    s = (s or "").strip()
    return None if s == "" else float(s)


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
        w = f"line {i} {r['label']}/{r['item']}/{r['year'] or r['period']}"
        v = r["verdict"]
        # --- A ---
        if v not in CONVICTING | NOT_CONVICTING:
            problems.append(f"A {w}: unknown verdict {v!r}")
            continue
        if r["convicted"] not in ("True", "False"):
            problems.append(f"A {w}: convicted {r['convicted']!r} is not True/False")
        elif (r["convicted"] == "True") != (v in CONVICTING):
            problems.append(f"A {w}: verdict {v} but convicted={r['convicted']}")
        prod, ar, yld = _f(r["production"]), _f(r["area_ha"]), _f(r["implied_yield"])
        base, ratio = _f(r["own_pre_era_median"]), _f(r["ratio_to_own"])
        # --- E: the era floor, for a dated row OR a period row ---
        # 341 of this source's production rows carry a period instead of a year, and 99 of those are
        # inside the era. The screen's first version compared `year >= 1934`, which is False for NaN,
        # so it dropped them silently and reported the era as 328 rows instead of 427. A row must
        # therefore carry EXACTLY ONE of `year` or `period`, and whichever it carries must reach the era.
        yr, per = (r["year"] or "").strip(), (r["period"] or "").strip()
        if bool(yr) == bool(per):
            problems.append(f"E {w}: carries year={yr!r} and period={per!r}; exactly one is required "
                            f"-- a five-year mean must never be readable as an observation of one year")
        elif yr:
            if int(yr) < ERA_FROM:
                problems.append(f"E {w}: year {yr} precedes the {ERA_FROM} boundary; 1933 is the "
                                f"last year a second volume offers an opinion (issue 414)")
        else:
            yy = re.findall(r"\d{4}", per)
            if not yy:
                problems.append(f"E {w}: period {per!r} carries no year")
            elif int(yy[-1]) < ERA_FROM:
                problems.append(f"E {w}: period {per} ENDS before the {ERA_FROM} boundary, so it "
                                f"belongs to the clean era, not this one")
        # --- B ---
        if ar is not None and ar > 0:
            if yld is None:
                problems.append(f"B {w}: area {ar} > 0 but no implied_yield")
            elif abs(yld - prod / ar) > 1e-4 * max(1.0, abs(yld)):
                problems.append(f"B {w}: implied_yield {yld} != production/area ({prod / ar:.6f})")
        elif yld is not None:
            problems.append(f"B {w}: implied_yield {yld} recorded with area {r['area_ha']!r}; a yield "
                            f"needs a positive area")
        if base is not None and base > 0 and ratio is not None:
            if abs(ratio - prod / base) > 1e-4 * max(1.0, abs(ratio)):
                problems.append(f"B {w}: ratio_to_own {ratio} != production/own_pre_era_median "
                                f"({prod / base:.6f})")
        # --- D: zero area is a verdict, not a skip ---
        if ar is not None and ar == 0.0 and prod and prod > 0 and v != "impossible_yield_zero_area":
            problems.append(
                f"D {w}: area is exactly 0 with production {prod}, so the implied yield is INFINITE "
                f"-- the strongest evidence in this table -- but the row is classed {v!r}. This is "
                f"the `if area > 0` guard reappearing: it sends all 50 such rows to the weaker "
                f"own-history test, which EXONERATES 14 of them outright and drops the convicted "
                f"count from 266 to 252 (issue 420 is the same shape)")
        # --- C: the numbers must place the row in its class ---
        if v == "impossible_yield" and (yld is None or yld <= IMPOSSIBLE_YIELD):
            problems.append(f"C {w}: classed impossible_yield with implied_yield {yld}, not above "
                            f"{IMPOSSIBLE_YIELD}")
        if v == "high_yield_3to20" and (yld is None or not (HIGH_YIELD < yld <= IMPOSSIBLE_YIELD)):
            problems.append(f"C {w}: classed high_yield_3to20 with implied_yield {yld}")
        if v == "plausible_yield" and (yld is None or yld > HIGH_YIELD):
            problems.append(f"C {w}: classed plausible_yield with implied_yield {yld}")
        if v == "no_area_level_shift" and (ratio is None or ratio < LEVEL_SHIFT):
            problems.append(f"C {w}: classed no_area_level_shift with ratio_to_own {ratio}, not at "
                            f"least {LEVEL_SHIFT}")
        if v == "untestable" and (yld is not None or ratio is not None):
            problems.append(f"C {w}: classed untestable but carries yield {yld} / ratio {ratio}")

    vc = {}
    for r in rows:
        vc[r["verdict"]] = vc.get(r["verdict"], 0) + 1
    conv = sum(1 for r in rows if r["convicted"] == "True")
    print(f"{len(rows)} iia tobacco/hops production row(s) from {ERA_FROM}, "
          f"{len({r['label'] for r in rows})} label(s); convicted {conv}")
    for k in sorted(vc, key=lambda k: (k not in CONVICTING, k)):
        print(f"  {k:28} {vc[k]:4}{'  <- convicted' if k in CONVICTING else ''}")

    if problems:
        print(f"FAIL: {len(problems)} era-shift verdict problem(s)", file=sys.stderr)
        for p in problems[:30]:
            print("  - " + p, file=sys.stderr)
        return 1
    print("PASS: every verdict is consistent with its own numbers, and a zero-area row is convicted "
          "rather than skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
