#!/usr/bin/env python3
"""Does every constant run say what a consumer should DO with it, and are the filled ones registered?

`validate_constant_runs.py` gates that the runs exist and `validate_constant_run_verdicts.py` gates
whether the source's own reporting grid explains them. Neither says what a flat run IS -- which is what
issue 366 asked for in its last form: "for the long runs, which of carried-forward / interpolated /
placeholder is it, and what should the cells become?". `17_constant_runs.py` now answers that per run:

    shape         the run against its OWN series: PLACEHOLDER (>=10x off the series' median),
                  CARRIED_FORWARD (reproduces the last observation before it to within 5 percent),
                  STARTS_SERIES, BRIDGED (between the flanking observations), UNCLASSIFIED
    disposition   what a consumer does with it, from `shape` + `verdict`:
                  ROUNDING_GRID | CARRIED_FORWARD | PLACEHOLDER | BRIDGED | UNRESOLVED
    value_divisor the issue-416 value-scale divisor the run was measured under (1 where none)

The panel is gitignored and absent in CI, so this reads the committed table -- the same arrangement as
its two siblings. `shape` itself needs the panel, and `17_constant_runs.py --check` is what proves the
table still is what the panel produces; this gate pins what the table says and joins it to the registry.

Five arms:

  A  SCHEMA. The three columns exist and every cell is in its vocabulary. A column added and never
     filled would leave every other arm vacuous.

  B  `disposition` IS RE-DERIVED from `shape` and `verdict`, restated here rather than imported, so a
     relaxed generator cannot quietly relabel a run. PLACEHOLDER outranks a grid explanation: a
     constant 2,000x off its own series is not made innocent by sitting on a coarse grid.

  C  THE CENSUS IS PINNED, bidirectionally. A run entering CARRIED_FORWARD or PLACEHOLDER is a new
     filled gap; one leaving means something was repaired or the series moved. Either must be read.

  D  THE FILLED SET IS PINNED BY IDENTITY, because counts can hold while membership rotates.

  E  EVERY FILLED RUN IS REGISTERED in `data_errors.csv` entry `constant-runs-filled-carried-forward`,
     by identity, so the consumer-facing record cannot lag the table. A run with a divisor must carry
     a power of ten (above or below 1), because a divisor is a unit change and never a fitted factor.

WHAT THIS DOES NOT ASSERT. That a CARRIED_FORWARD run was seen reprinted in a yearbook: the signature is
that the constant matches the preceding observation, and the source page would confirm, not resolve. Nor
that UNRESOLVED runs are innocent: they match neither flank and need the page. For the iia runs a
per-cell precision/grid column is a separate product (issue 446) and is not duplicated here.

Usage:
  python3 scripts/validate_constant_run_dispositions.py
"""
from __future__ import annotations

import collections
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/constant_runs.csv")
ERRORS = os.path.join(REPO, "pipelines/polity-autoimprove/state/data_errors.csv")
ENTRY = "constant-runs-filled-carried-forward"

SHAPES = ("PLACEHOLDER", "CARRIED_FORWARD", "STARTS_SERIES", "BRIDGED", "UNCLASSIFIED")
DISPOSITIONS = ("ROUNDING_GRID", "CARRIED_FORWARD", "PLACEHOLDER", "BRIDGED", "UNRESOLVED")
FILLED = ("CARRIED_FORWARD", "PLACEHOLDER")

# Measured 2026-10-07 by 17_constant_runs.py on the layer-B panel after the value-scale divisors
# (issue 416) and item-scoped label corrections (issue 675) -- the same two steps 01_match_and_findings
# applies. BIDIRECTIONAL: a move is a finding either way and must move this with a note saying which run.
BASELINE_DISPOSITIONS = {
    "ROUNDING_GRID": 63,
    "CARRIED_FORWARD": 23,
    "PLACEHOLDER": 8,
    "BRIDGED": 52,
    "UNRESOLVED": 98,
}

# The runs a consumer must not read as observations. GENERATED FROM THE TABLE, never hand-typed.
BASELINE_FILLED = frozenset({
    ('iia', 'saint lucia', 'cacao beans', 'tonnes', '300.000', '1933'),
    ('iia', 'sri lanka', 'cacao beans', 'ha', '14000.000', '1930'),
    ('juan', 'argentina', 'soybeans', 'ha', '1000.000', '1950'),
    ('juan', 'austria', 'grapes', 'ha', '207000.000', '1878'),
    ('juan', 'austria', 'grapes', 'ha', '40000.000', '1941'),
    ('juan', 'brazil', 'tea', 'tonnes', '700.000', '1953'),
    ('juan', 'czechoslovakia', 'tobacco unmanufactured', 'ha', '10000.000', '1933'),
    ('juan', 'denmark', 'barley', 'ha', '233700.000', '1907'),
    ('juan', 'denmark', 'potatoes', 'ha', '52000.000', '1888'),
    ('juan', 'denmark', 'potatoes', 'ha', '54000.000', '1902'),
    ('juan', 'denmark', 'rye', 'ha', '276000.000', '1907'),
    ('juan', 'germany', 'grapes', 'ha', '120000.000', '1883'),
    ('juan', 'italy', 'oranges', 'ha', '33000.000', '1935'),
    ('juan', 'malta', 'wheat', 'ha', '4000.000', '1933'),
    ('juan', 'mexico', 'peas dry', 'ha', '7000.000', '1946'),
    ('juan', 'norway', 'barley', 'ha', '39500.000', '1901'),
    ('juan', 'paraguay', 'coffee green', 'tonnes', '100.000', '1940'),
    ('juan', 'spain', 'apricots', 'ha', '3700.000', '1939'),
    ('juan', 'spain', 'carobs', 'ha', '152000.000', '1950'),
    ('juan', 'spain', 'olives', 'ha', '1123000.000', '1891'),
    ('juan', 'spain', 'tangerines mandarins clementines satsumas', 'tonnes', '71900.000', '1939'),
    ('juan', 'switzerland', 'maize', 'tonnes', '4000.000', '1953'),
    ('juan', 'switzerland', 'sugar beet', 'ha', '6000.000', '1953'),
    ('iia', 'new zealand', 'tobacco unmanufactured', 'ha', '1000.000', '1934'),
    ('iia', 'saint lucia', 'lemons and limes', 'tonnes', '100.000', '1939'),
    ('juan', 'argentina', 'cotton lint', 'tonnes', '400.000', '1906'),
    ('juan', 'belgium', 'rapeseed', 'tonnes', '100.000', '1933'),
    ('juan', 'costa rica', 'sugar cane', 'tonnes', '3000.000', '1910'),
    ('juan', 'guatemala', 'groundnuts with shell', 'ha', '1000.000', '1939'),
    ('juan', 'paraguay', 'potatoes', 'ha', '1000.000', '1940'),
    ('mitchell', 'indonesia', 'tea', 'tonnes', '1000.000', '1858'),
})


def key(r):
    return (r["source"], r["country"], r["item"], r["unit"], r["constant"], r["year_first"])


def who(r):
    return (f"{r['source']} {r['country']} / {r['item']} ({r['unit']}) "
            f"{r['year_first']}-{r['year_last']}")


def derive(r):
    """The disposition for one run, from `shape` and `verdict` alone (restated, not imported)."""
    if r["shape"] == "PLACEHOLDER":
        return "PLACEHOLDER"
    if r["verdict"] == "EXPLAINED":
        return "ROUNDING_GRID"
    if r["shape"] in ("CARRIED_FORWARD", "BRIDGED"):
        return r["shape"]
    return "UNRESOLVED"


def is_power_of_ten(x):
    try:
        f = float(x)
    except (TypeError, ValueError):
        return False
    if f <= 0:
        return False
    # Divisors below 1 are multipliers (issue 424: eight 1933 cells printed ten times too small).
    import math
    e = round(math.log10(f))
    return e != 0 and abs(f - 10.0 ** e) < 1e-12 * max(1.0, f)


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"SKIP: {os.path.relpath(TABLE, REPO)} missing -- run 17_constant_runs.py --write")
        return 0
    with open(TABLE, newline="", encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        cols = tuple(rdr.fieldnames or ())
        rows = list(rdr)
    for c in ("shape", "disposition", "value_divisor"):
        if c not in cols:
            print(f"FAIL {os.path.relpath(TABLE, REPO)} has no `{c}` column: what a consumer should do "
                  f"with a flat run is not in the table. Run 17_constant_runs.py --write",
                  file=sys.stderr)
            return 1

    problems = []
    counts = collections.Counter()
    for r in rows:
        if r["shape"] not in SHAPES:
            problems.append(f"{who(r)}: shape {r['shape']!r} is not one of {SHAPES}")
        if r["disposition"] not in DISPOSITIONS:
            problems.append(f"{who(r)}: disposition {r['disposition']!r} is not one of {DISPOSITIONS}")
            continue
        counts[r["disposition"]] += 1
        want = derive(r)
        if r["disposition"] != want:
            problems.append(
                f"{who(r)}: disposition={r['disposition']} but shape={r['shape']} and "
                f"verdict={r['verdict']} give {want}. The table and its own two inputs disagree; "
                f"regenerate with 17_constant_runs.py --write")
        if r["value_divisor"] != "1" and not is_power_of_ten(r["value_divisor"]):
            problems.append(f"{who(r)}: value_divisor {r['value_divisor']!r} is not a power of ten; a "
                            f"divisor is a unit change, never a fitted factor")

    print(f"{len(rows)} constant run(s), by what a consumer should do with them:")
    for d in DISPOSITIONS:
        print(f"  {counts[d]:>4}  {d:16} (pinned {BASELINE_DISPOSITIONS[d]})  "
              f"{dict(collections.Counter(r['source'] for r in rows if r['disposition'] == d).most_common())}")
    for d in DISPOSITIONS:
        if counts[d] != BASELINE_DISPOSITIONS[d]:
            problems.append(
                f"{d}: {counts[d]} run(s) against the pinned {BASELINE_DISPOSITIONS[d]}. A run entering "
                f"CARRIED_FORWARD or PLACEHOLDER is a new filled gap read as data; one leaving means "
                f"something was repaired or its series moved. Update BASELINE_DISPOSITIONS in the same "
                f"commit and name the run")

    filled = {key(r) for r in rows if r["disposition"] in FILLED}
    for k in sorted(filled - BASELINE_FILLED):
        problems.append(
            f"NEW filled run: {k[1]} / {k[2]} ({k[3]}) = {k[4]} from {k[5]}, {k[0]}. It repeats a value "
            f"its own series resolves finer than, and no reporting grid explains it. Register it in "
            f"data_errors `{ENTRY}` and add it to BASELINE_FILLED with a reading of the run")
    for k in sorted(BASELINE_FILLED - filled):
        problems.append(
            f"{k[1]} / {k[2]} = {k[4]} from {k[5]} is pinned as filled but is not any more. Remove it "
            f"from BASELINE_FILLED and from the data_errors entry, saying what was repaired")

    # --- E: the registry names every filled run ---
    with open(ERRORS, newline="", encoding="utf-8") as fh:
        entry = next((e for e in csv.DictReader(fh) if e["issue_id"] == ENTRY), None)
    if entry is None:
        problems.append(f"data_errors.csv has no `{ENTRY}` entry, so the {len(filled)} filled runs have "
                        f"no consumer-facing record")
    else:
        for r in rows:
            if r["disposition"] not in FILLED:
                continue
            tag = (f"{r['source']} {r['country']} / {r['item']} ({r['unit']}) "
                   f"{r['year_first']}-{r['year_last']} = {float(r['constant']):g}")
            if tag not in entry["summary"]:
                problems.append(f"{who(r)}: filled but not named in data_errors `{ENTRY}` as {tag!r}")
        if entry["status"] not in ("confirmed", "resolved"):
            problems.append(f"data_errors `{ENTRY}` has status {entry['status']!r}; the filled runs are "
                            f"measured, not pending an audit")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"\nPASS: every run's disposition re-derives, the census is where it was pinned, and the "
          f"{len(filled)} filled runs are registered")
    return 0


if __name__ == "__main__":
    sys.exit(main())
