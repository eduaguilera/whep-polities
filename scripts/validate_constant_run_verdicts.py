#!/usr/bin/env python3
"""Is each constant run a limit of its source's reporting grid, or is it not? Gate the answer.

`validate_constant_runs.py` gates the runs themselves: 246 series that repeat one value for years in a
way their OWN series refutes. What it cannot say is whether the repetition is innocent, and that is the
whole of issue 366's history -- its headline argument was WITHDRAWN because the finer evidence proving
"this series resolves finer than its constant" turned out to be cross-era in 169 of 170 runs, which is
what a change of reporting resolution looks like rather than evidence against one.

`state/source_value_precision.csv` (#446, #528) is the table that settles it, per (source, unit, era),
and `17_constant_runs.py` now joins the two and writes a `verdict` per run. THAT JOIN IS THE THING THIS
GATE EXISTS FOR. It was first measured by hand and published only in a comment on issue 366 -- 68
EXPLAINED / 153 UNDETERMINED / 11 REFUTED / 4 OFF-GRID / 10 NOT ATTRIBUTABLE -- where it could not be
re-run, diffed or gated, and nothing anywhere would have noticed if the counts moved. The 15 REFUTED and
OFF-GRID runs are the residue the issue exists to isolate: the runs where the innocent explanation
demonstrably fails.

The panel both tables derive from is gitignored and absent in CI, so this reads the two committed
tables -- the same arrangement as `validate_constant_runs.py` and `validate_source_splices.py`.

Five arms:

  A  SCHEMA. The three verdict columns exist and are populated, and `verdict` holds one of the five
     words. A column silently added and never filled would leave every other arm vacuous.

  B  THE VERDICT IS RE-DERIVED from the two tables, independently of the generator. RESTATED HERE
     RATHER THAN IMPORTED, deliberately: the failure this guards against is one table being edited out
     from under the other, and a gate importing the generator's own `judge()` would move with it. The
     era partition is recovered from the precision table's own `<year>+` labels, exactly as the
     generator does, so a moved boundary is a finding in both places rather than a silent reclassing.

  C  THE FIVE COUNTS ARE PINNED, bidirectionally, the way every other census here is. A run crossing
     from UNDETERMINED to REFUTED is a NEW FINDING -- the source turned out to report finer in that
     unit and era after all -- and the point of a baseline is that such a move must be read, not
     absorbed.

  D  THE 15-RUN RESIDUE IS PINNED BY IDENTITY. Counts alone can stay at 11 and 4 while the membership
     rotates, and membership is what a repair or a source-page lookup would act on.

  E  CROSS-CHECK AGAINST THE IN-VOLUME WITNESS, which is the other half of issue 366 already in this
     table. `finer_in_volume_year` names a year where the SAME yearbook volume records a value off the
     run's own grid. Three runs carry such a witness AND are EXPLAINED, and that is not a contradiction
     as long as the witness sits on the ERA's grid: `australia wine` repeats 20,000 ha (its own grid is
     10,000) beside a 19,000 in the same volume, and 19,000 is on the era's 1,000-grid, so the era
     explains both values. `algeria rye`'s 2,000-beside-1,000 is the same trap one level down, and
     getting it wrong is how an earlier count of 27 became 17. But a witness OFF the era's grid while
     the run is called EXPLAINED is a real contradiction: that volume printed a figure the era's grid
     cannot express, so the grid is not available as the run's explanation.

WHAT THIS GATE DOES NOT ASSERT. Not that an EXPLAINED run is correct: `coarse_1000` is a share (96.3%
for `iia` `ha` from 1934), not a rule, so EXPLAINED means "consistent with the grid", never "measured".
And not that a REFUTED run is a fabrication -- it may be a real plateau or a carried-forward figure.
The verdict separates the runs that need a source page from the runs that do not.

Usage:
  python3 scripts/validate_constant_run_verdicts.py
"""
from __future__ import annotations

import collections
import csv
import os
import re
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/constant_runs.csv")
PRECISION = os.path.join(REPO, "pipelines/polity-autoimprove/state/source_value_precision.csv")

VERDICTS = ("EXPLAINED", "UNDETERMINED", "REFUTED", "OFF-GRID", "NOT ATTRIBUTABLE")

# The precision table's verdict word -> the grid it asserts, in the series' own unit. `mixed` and
# `fine` assert no single grid and are deliberately absent rather than mapped to 1.
ERA_GRID = {"coarse_1000": 1000, "coarse_100": 100}

SCALE = 10 ** 6      # scaled integers, because float modulo cannot be trusted on 5.390 vs 100

# Measured 2026-08-31, reproducing by code the classification that had lived only in a comment on issue
# 366. BIDIRECTIONAL: a run moving between buckets is a finding either way and must move this with a
# note saying which run moved and why.
BASELINE_COUNTS = {
    "EXPLAINED": 68,
    "UNDETERMINED": 153,
    "REFUTED": 11,
    "OFF-GRID": 4,
    "NOT ATTRIBUTABLE": 10,
}

# The residue: every run whose innocent explanation demonstrably fails. GENERATED FROM THE TABLE, never
# hand-typed. All 15 are `iia`; the 11 REFUTED are all pre-1934, where `ha` sits at 9.8% on a 1000-grid
# and `tonnes` carries 53.1% sub-unit precision -- a source reporting to the hectare and the tenth of a
# tonne, printing one figure for five to nine consecutive years.
BASELINE_RESIDUE = frozenset({
    ('iia', 'australia', 'hops', 'ha', '500.000', '1939'),
    ('iia', 'austria', 'n', 'tonnes', '24000.000', '1914'),
    ('iia', 'fiji', 'tea', 'ha', '80.000', '1911'),
    ('iia', 'france', 'eggs hen in shell', 'tonnes', '5.390', '1939'),
    ('iia', 'guadeloupe', 'cacao beans', 'ha', '5000.000', '1918'),
    ('iia', 'guadeloupe', 'coffee green', 'ha', '7000.000', '1918'),
    ('iia', 'madagascar', 'wine', 'tonnes', '291.000', '1934'),
    ('iia', 'mauritius', 'tea', 'ha', '150.000', '1911'),
    ('iia', 'mauritius', 'tea', 'tonnes', '38.000', '1911'),
    ('iia', 'new zealand', 'hops', 'ha', '200.000', '1939'),
    ('iia', 'saint lucia', 'cacao beans', 'ha', '2400.000', '1910'),
    ('iia', 'saint lucia', 'cacao beans', 'ha', '2400.000', '1922'),
    ('iia', 'saint vincent and the grenadines', 'cacao beans', 'ha', '400.000', '1909'),
    ('iia', 'trinidad and tobago', 'coffee green', 'ha', '1700.000', '1909'),
    ('iia', 'united states of america', 'n', 'tonnes', '58000.000', '1914'),
})


def key(r):
    return (r["source"], r["country"], r["item"], r["unit"], r["constant"], r["year_first"])


def who(r):
    return (f"{r['source']} {r['country']} / {r['item']} ({r['unit']}) "
            f"{r['year_first']}-{r['year_last']}")


def load_precision(path):
    """-> {(source, unit, era): verdict}, {source: era cut}. The cut is read off the era labels."""
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    prec = {(r["source"], r["unit"], r["era"]): r["verdict"] for r in rows}
    cuts = collections.defaultdict(set)
    for r in rows:
        m = re.fullmatch(r"(\d{4})\+", r["era"])
        if m:
            cuts[r["source"]].add(int(m.group(1)))
    return prec, cuts


def rederive(r, prec, cuts):
    """(verdict, precision_era, precision_grid) for one run, from the two tables alone."""
    src, unit = r["source"], r["unit"]
    cs = cuts.get(src, set())
    if len(cs) > 1:
        return None, None, None      # reported once, by the caller, rather than per run
    if not cs:
        era = "all"
    else:
        cut = next(iter(cs))
        if int(r["year_first"]) < cut <= int(r["year_last"]):
            return "NOT ATTRIBUTABLE", f"straddles-{cut}", ""
        era = f"{cut}+" if int(r["year_first"]) >= cut else f"pre-{cut}"
    word = prec.get((src, unit, era))
    if word is None:
        return "UNDETERMINED", era, "unmeasured"
    grid = ERA_GRID.get(word)
    if grid is None:
        return ("UNDETERMINED" if word == "mixed" else "REFUTED"), era, word
    on_grid = int(round(float(r["constant"]) * SCALE)) % (grid * SCALE) == 0
    return ("EXPLAINED" if on_grid else "OFF-GRID"), era, str(grid)


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"SKIP: {os.path.relpath(TABLE, REPO)} missing — run 17_constant_runs.py --write")
        return 0
    if not os.path.exists(PRECISION):
        print(f"FAIL {os.path.relpath(PRECISION, REPO)} is missing, so the verdicts in "
              f"{os.path.relpath(TABLE, REPO)} rest on a table that is no longer here and nothing "
              f"can re-derive them", file=sys.stderr)
        return 1
    with open(TABLE, newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        cols = tuple(rdr.fieldnames or ())
        rows = list(rdr)
    prec, cuts = load_precision(PRECISION)

    problems = []
    # --- A: schema ---
    for c in ("verdict", "precision_era", "precision_grid"):
        if c not in cols:
            print(f"FAIL {os.path.relpath(TABLE, REPO)} has no `{c}` column: the classification "
                  f"issue 366 turns on is not in the table, so it cannot be diffed or gated. Run "
                  f"17_constant_runs.py --write", file=sys.stderr)
            return 1
    multi = sorted(s for s, cs in cuts.items() if len(cs) > 1)
    if multi:
        print(f"FAIL {os.path.relpath(PRECISION, REPO)}: {multi} carry more than one era cut, so a "
              f"run has no single grid to be judged against and every verdict here is ambiguous",
              file=sys.stderr)
        return 1

    counts = collections.Counter()
    for r in rows:
        if r["verdict"] not in VERDICTS:
            problems.append(f"{who(r)}: verdict {r['verdict']!r} is not one of {VERDICTS}")
            continue
        counts[r["verdict"]] += 1
        if not r["precision_era"]:
            problems.append(f"{who(r)}: verdict {r['verdict']} with an empty `precision_era`, so "
                            f"nothing records which row of the precision table it was read from")
        # --- B: re-derive ---
        want_v, want_era, want_grid = rederive(r, prec, cuts)
        if (r["verdict"], r["precision_era"], r["precision_grid"]) != (want_v, want_era, want_grid):
            problems.append(
                f"{who(r)}: the table says verdict={r['verdict']} era={r['precision_era']} "
                f"grid={r['precision_grid']}, but re-deriving from source_value_precision.csv gives "
                f"verdict={want_v} era={want_era} grid={want_grid}. One of the two tables moved "
                f"without the other; regenerate with 17_constant_runs.py --write, or if the "
                f"precision row changed, say what changed about the source")
        # --- E: the in-volume witness must not contradict an EXPLAINED verdict ---
        wv = (r.get("finer_in_volume_value") or "").strip()
        if wv and r["verdict"] == "EXPLAINED" and r["precision_grid"].isdigit():
            g = int(r["precision_grid"])
            if int(round(float(wv) * SCALE)) % (g * SCALE) != 0:
                problems.append(
                    f"{who(r)}: called EXPLAINED by a grid of {g}, yet its in-volume witness "
                    f"{r['finer_in_volume_year']}={wv} is OFF that grid — the same yearbook volume "
                    f"printed a figure the grid cannot express, so the grid is not available as this "
                    f"run's explanation and the verdict contradicts its own row")

    print(f"{len(rows)} constant run(s) judged against their source's reporting grid:")
    for v in VERDICTS:
        print(f"  {counts[v]:>4}  {v:17} (pinned {BASELINE_COUNTS[v]})  "
              f"{dict(collections.Counter(r['source'] for r in rows if r['verdict'] == v).most_common())}")

    # --- C: the census, bidirectionally ---
    for v in VERDICTS:
        if counts[v] == BASELINE_COUNTS[v]:
            continue
        problems.append(
            f"{v}: {counts[v]} run(s) against the pinned {BASELINE_COUNTS[v]}. This is the split issue "
            f"366 turns on, so a move is a finding in either direction — a run leaving UNDETERMINED "
            f"for REFUTED means its source reports finer in that unit and era after all, and one "
            f"leaving REFUTED means the innocent reading now covers it. Update BASELINE_COUNTS in the "
            f"same commit and name the run that moved")

    # --- D: the residue, by identity ---
    residue = {key(r) for r in rows if r["verdict"] in ("REFUTED", "OFF-GRID")}
    for k in sorted(residue - BASELINE_RESIDUE):
        problems.append(
            f"NEW un-explained run: {k[1]} / {k[2]} ({k[3]}) = {k[4]} from {k[5]}, {k[0]}. Its source "
            f"is not coarse enough in that unit and era to produce the constant by rounding, so the "
            f"flat years are a carried-forward or placeholder figure being read as data — add it to "
            f"BASELINE_RESIDUE only with a reading of the run")
    for k in sorted(BASELINE_RESIDUE - residue):
        problems.append(
            f"{k[1]} / {k[2]} = {k[4]} from {k[5]} is pinned as un-explained but is not any more. "
            f"Either its source's measured precision changed or the run did; remove its entry saying "
            f"which, because these 15 are the residue issue 366 exists to isolate")

    n_wit = sum(1 for r in rows
                if (r.get("finer_in_volume_year") or "").strip() and r["verdict"] == "EXPLAINED")
    print(f"  {n_wit} EXPLAINED run(s) also carry an in-volume witness, each on the era's own grid")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS: every run's verdict re-derives from the precision table, the five-way split is "
          "where it was pinned, and the 15-run residue is unchanged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
