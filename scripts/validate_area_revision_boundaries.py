#!/usr/bin/env python3
"""Do the recorded stated-area revisions still line up (or fail to) with our period boundaries?

`pipelines/polity-autoimprove/34_area_revision_boundaries.py` records every case where a source revises
its own stated area by at least 50% and the label resolves to a polity (issue 503). The table has two
halves and BOTH are load-bearing:

  * `our_boundary_falls_between` -- the source revised and we already have a span boundary there. This
    is CORROBORATION of the periodisation from data rather than from historical reading, which nothing
    else in this repo supplies. 87,776 -> 247,916 km2 for Serbia becoming Yugoslavia against
    F248-1920-1947; Romania's Transylvania gains against ROU-1920-1940; Trianon against HUN-1920-1938.
  * `one_polity_spans_the_revision` -- one row carries a constant territory across a change the source
    records in its own area column.

  A  ARITHMETIC. `step_pct` must equal |area_after/area_before - 1| x 100, and clear the 50% floor.
     A row whose stated step disagrees with its own two areas is not measuring anything.
  B  THE VERDICT MUST FOLLOW FROM THE SPAN. `one_polity_spans_the_revision` exactly when the polity's
     span contains both data years. This is the finding, so it cannot be a free-text field.
  C  THE EXCLUSION MUST HOLD. No row may name a (polity, source) pair that `validate_stated_areas.py`
     already explains in BASELINE or SOURCE_NOTES. That filter is what makes this a self-clearing
     worklist: a diagnosed source defect leaves the table by being diagnosed. Without it, 4 of the
     spanning rows are MONACO's dropped decimal, GREENLAND's re-estimates and TIEN-TSIN, and the table
     reads as a false-positive generator.
  D  THE CORROBORATION HALF MUST NOT VANISH. At least MIN_AGREEING rows must agree. If that number
     goes to zero the periodisation did not suddenly stop matching the source -- the label resolution
     broke, which is the failure mode this whole area is prone to (issue 195: 1,190 of 2,225
     statements resolved to nothing until the lexicon was retargeted).

WHAT IS NOT ASSERTED. That any polity should move. `ALGÉRIE` is the clear case -- 575,289 km2 for the
three civil departments against 2,196,294 for the colony including the Southern Territories, with
DZA-1919-1962 spanning it -- and that is issue 400's case 2, a polity-creation decision. `EQUATEUR`
tracks Ecuador's CLAIMED Amazon before the 1942 Rio Protocol, so it is probably not ours at all. Of the
rest, one of the two figures is simply wrong (`LITHUANIE` 150,000 against a real 65,300;
`CÔTE DES SOMALIS` 120,000 against 23,000), and they belong in SOURCE_NOTES once diagnosed -- at which
point they leave here on their own.
"""
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/area_revision_boundaries.csv")
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")
BASIS = os.path.join(REPO, "data/final/source_stated_area_basis.csv")

FIELDS = ["label", "source", "step_pct", "year_before", "year_after", "area_before", "area_after",
          "polity_code", "polity_start", "polity_end", "verdict"]

VERDICTS = {"one_polity_spans_the_revision", "our_boundary_falls_between"}
MIN_STEP_PCT = 50.0     # restated, not imported
MIN_AGREEING = 6        # arm D: 11 today; a floor well below it, so a real change is a finding


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} missing — run "
              f"34_area_revision_boundaries.py --write", file=sys.stderr)
        return 1
    with open(TABLE, newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        if rdr.fieldnames != FIELDS:
            print(f"FAIL: {TABLE} header is {rdr.fieldnames}, expected {FIELDS}", file=sys.stderr)
            return 1
        rows = list(rdr)

    # The excluded set is read from the PUBLISHED artifact of that curation, not by importing
    # validate_stated_areas: write_stated_area_basis.py already copies every BASELINE/SOURCE_NOTES
    # explanation into the `note` column of source_stated_area_basis.csv. Reading the table keeps this
    # gate a data check with one input instead of a code import that drags in matchlib, the lexicon and
    # the polities CSV -- which is exactly what stopped it running in the selftest's scratch tree.
    explained = set()
    if os.path.exists(BASIS):
        with open(BASIS, newline="", encoding="utf-8") as fh:
            for b in csv.DictReader(fh):
                if (b.get("note") or "").strip():
                    explained.add((b["polity_code"], b["source"]))

    problems = []
    if not os.path.exists(BASIS):
        # Arm C cannot run without it, and a gate arm that silently skips is the failure mode this
        # repo has shipped three times (issues 407, 412, 420), so absence is a failure.
        print(f"FAIL: {os.path.relpath(BASIS, REPO)} missing — arm C cannot check the exclusion",
              file=sys.stderr)
        return 1
    n_span = n_agree = 0
    for r in rows:
        who = f"{r['label']} / {r['source']}"
        try:
            step = float(r["step_pct"])
            y0, y1 = int(r["year_before"]), int(r["year_after"])
            a0, a1 = float(r["area_before"]), float(r["area_after"])
            ps, pe = int(r["polity_start"]), int(r["polity_end"])
        except (TypeError, ValueError) as e:
            problems.append(f"{who}: unparseable field ({e})")
            continue
        if r["verdict"] not in VERDICTS:                                          # vocabulary
            problems.append(f"{who}: verdict {r['verdict']!r} not in {sorted(VERDICTS)}")
            continue
        n_span += r["verdict"] == "one_polity_spans_the_revision"
        n_agree += r["verdict"] == "our_boundary_falls_between"

        if not (a0 > 0 and a1 > 0):
            problems.append(f"{who}: non-positive stated area ({a0}, {a1})")
        else:
            exp = abs(a1 / a0 - 1) * 100
            if abs(step - exp) > 0.15:                                            # A
                problems.append(f"{who}: step_pct {step} != |{a1}/{a0} - 1| x 100 = {exp:.1f}")
            elif step < MIN_STEP_PCT:                                             # A
                problems.append(
                    f"{who}: a {step:.0f}% revision is below the {MIN_STEP_PCT:.0f}% floor. Below it a "
                    f"revision is re-measurement or a boundary survey, not an event")
        if y1 <= y0:
            problems.append(f"{who}: year_after {y1} does not follow year_before {y0}")
        spans = ps <= y0 and y1 <= pe
        want = "one_polity_spans_the_revision" if spans else "our_boundary_falls_between"
        if r["verdict"] != want:                                                  # B
            problems.append(
                f"{who}: verdict says {r['verdict']!r} but {r['polity_code']} spans {ps}-{pe} and the "
                f"revision runs {y0}->{y1}, so it should be {want!r}. The verdict is the finding and "
                f"must follow from the span, not be asserted beside it")
        if (r["polity_code"], r["source"]) in explained:                           # C
            problems.append(
                f"{who}: ({r['polity_code']}, {r['source']}) is already explained in "
                f"validate_stated_areas' BASELINE/SOURCE_NOTES, so this revision has a recorded cause "
                f"and must not be re-reported here — that exclusion is what keeps this a worklist "
                f"rather than a false-positive generator")

    print(f"{len(rows)} stated-area revision(s) of at least {MIN_STEP_PCT:.0f}% with a resolved polity")
    print(f"  our boundary falls between the figures: {n_agree} (corroboration, floor {MIN_AGREEING})")
    print(f"  ONE POLITY SPANS THE REVISION:          {n_span}")
    for r in rows[:8]:
        m = "SPANS" if r["verdict"] == "one_polity_spans_the_revision" else "boundary"
        print(f"  {r['label'][:26]:28}{float(r['step_pct']):>6.0f}%  {r['year_before']}->"
              f"{r['year_after']:<6}{r['polity_code']:20} {m}")

    if n_agree < MIN_AGREEING:                                                     # D
        problems.append(
            f"only {n_agree} revision(s) agree with a span boundary, below the floor of "
            f"{MIN_AGREEING}. The periodisation did not stop matching the source — far more likely the "
            f"label resolution broke, which is exactly what issue 195 found when 1,190 of 2,225 "
            f"statements resolved to nothing")

    if problems:
        print(f"FAIL: {len(problems)} area-revision problem(s)", file=sys.stderr)
        for p in problems[:25]:
            print("  - " + p, file=sys.stderr)
        return 1
    print(f"PASS: every revision's step matches its own two areas, every verdict follows from its "
          f"polity's span, none duplicates a recorded source-defect note, and {n_agree} still "
          f"corroborate a period boundary")
    return 0


if __name__ == "__main__":
    sys.exit(main())
