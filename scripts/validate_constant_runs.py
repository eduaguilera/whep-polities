#!/usr/bin/env python3
"""Does any series repeat one value for years on end in a way its own resolution refutes?

A constant run breaks no magnitude bound, opens no year gap and crosses no source seam, so nothing
else here looks for it — yet the rows carry ZERO VARIANCE, and every trend, growth rate or
level-shift reading of them says "this did not change" when the truth is that nobody knew. The bias
lands on small producers and colonial reporting units, flattening the series that are already
weakest.

`pipelines/polity-autoimprove/17_constant_runs.py` measures the runs from the layer-B panel and
writes `state/constant_runs.csv`. The panel is gitignored and absent in CI, so this gate reads the
committed table — the same arrangement as `validate_source_splices.py`.

THE TABLE ONLY HOLDS RUNS THE SERIES ITSELF REFUTES. A long run of exactly 1,000 ha would be
innocent if the source reported in thousands: the run would be a resolution limit, not a filled gap.
So a run is recorded only when the SAME series carries a value off the run value's own power-of-ten
grid. `argentina / soybeans / ha` records 2 ha and then sits at exactly 1,000 for eleven years; a
source that can express 2 is not rounding to 1,000. The proof case is `denmark / potatoes / ha` --
exactly 54,000 for ten straight years in a series that elsewhere carries 54,100, so its grid resolves
100 ha. That test needs no external data and no judgement, which is what makes it gateable.

WHAT THE FIRST RUN MEASURED (issue filed alongside):

    constant runs of >=5 identical values                       459   (3,100 rows)
      refuted as rounding by their own series                   246   (1,619 rows, 210 series)
        by source     juan 1,035    iia 522    mitchell 62

`fao1952` contributes nothing, which is itself a check on the method: its values are mostly
non-integer, so it has no coarse grid to sit on and cannot produce this shape.

Two signals:
  A. COUNT CEILING   the number of refuted runs may not grow. Bidirectional: repair some and the
                     ceiling must come down with a note, so the table cannot quietly refill.
  B. LONG RUNS       every run of >= 10 identical values is pinned by identity. At that length the
                     rounding explanation is not available and each is one lookup on a source page.

Usage:
  python3 scripts/validate_constant_runs.py
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/constant_runs.csv")

# Measured 2026-08-18 on the first run. BIDIRECTIONAL: repairing runs must lower this, with a note
# saying which were repaired, so a later regression cannot hide inside the old headroom.
BASELINE_RUNS = 246

# At this length a coarse-grid reading is not available as an explanation.
LONG_RUN = 10


def key(r):
    return (r["source"], r["country"], r["item"], r["unit"], r["constant"], r["year_first"])


# Every run of >= LONG_RUN values on the first run. GENERATED FROM THE TABLE, never hand-typed.
BASELINE_LONG = frozenset({
    ('iia', 'australia', 'lemons and limes', 'ha', '2000.000', '1933'),
    ('iia', 'grenada', 'cotton lint', 'tonnes', '100.000', '1935'),
    ('iia', 'india', 'sesame seed', 'ha', '1000.000', '1934'),
    ('iia', 'new zealand', 'tobacco unmanufactured', 'ha', '1000.000', '1934'),
    ('iia', 'south africa', 'tea', 'ha', '1000.000', '1933'),
    ('iia', 'viet nam', 'cotton lint', 'tonnes', '100.000', '1934'),
    ('juan', 'argentina', 'soybeans', 'ha', '1000.000', '1950'),
    ('juan', 'colombia', 'cocoa beans', 'tonnes', '3000.000', '1901'),
    ('juan', 'costa rica', 'tobacco unmanufactured', 'ha', '1000.000', '1939'),
    ('juan', 'denmark', 'potatoes', 'ha', '54000.000', '1902'),
    ('juan', 'iceland', 'potatoes', 'ha', '1000.000', '1933'),
    ('juan', 'italy', 'sesame seed', 'ha', '1000.000', '1945'),
    ('juan', 'luxembourg', 'grain mixed', 'ha', '1000.000', '1939'),
    ('juan', 'luxembourg', 'grapes', 'ha', '1000.000', '1933'),
    ('juan', 'malta', 'barley', 'ha', '2000.000', '1943'),
    ('juan', 'malta', 'grapes', 'ha', '1000.000', '1933'),
    ('juan', 'malta', 'wheat', 'ha', '2000.000', '1944'),
    ('juan', 'norway', 'wheat', 'ha', '5000.000', '1900'),
    ('juan', 'switzerland', 'maize', 'ha', '1000.000', '1930'),
    ('juan', 'switzerland', 'tobacco unmanufactured', 'ha', '1000.000', '1933'),
    ('juan', 'switzerland', 'tobacco unmanufactured', 'ha', '1000.000', '1948'),
})


# THE IN-VOLUME WITNESS ARM (issue 366). `finer_in_volume_year` names the earliest year, in a volume
# window the run itself touches, where the same series records a value OFF the constant's grid. When it
# is set the grid cannot explain the run: that volume demonstrably could express the finer figure.
#
# Restated here rather than imported, so relaxing the generator and regenerating cannot quietly admit
# weaker witnesses. The overlap years are the load-bearing part: layer B carries no volume provenance,
# so a value at a year TWO volumes cover could have come from either and proves nothing. Allowing them
# takes the count from 17 to 39.
IIA_VOLUMES = ((1909, 1921), (1920, 1925), (1926, 1929), (1929, 1933), (1932, 1938), (1939, 1945))
IIA_AMBIGUOUS_YEARS = frozenset(
    y for y in range(1900, 1960) if sum(1 for a, b in IIA_VOLUMES if a <= y <= b) > 1
)
# Pinned in BOTH directions, like the row counts above: a new witness is a finding that wants reading,
# and a lost one means something was repaired and should be said out loud.
BASELINE_IN_VOLUME = 17


def _volumes_covering(year: int) -> set:
    return {i for i, (a, b) in enumerate(IIA_VOLUMES) if a <= year <= b}


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"SKIP: {os.path.relpath(TABLE, REPO)} missing — run 17_constant_runs.py --write")
        return 0
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    long_runs = {key(r) for r in rows if int(r["n_values"]) >= LONG_RUN}
    print(f"recorded runs: {len(rows)} (ceiling {BASELINE_RUNS})")
    print(f"  of >={LONG_RUN} values: {len(long_runs)} (pinned {len(BASELINE_LONG)})")

    problems = []
    if len(rows) > BASELINE_RUNS:
        problems.append(
            f"{len(rows)} constant runs are refuted as rounding by their own series, above the "
            f"ceiling of {BASELINE_RUNS}. A series that resolves finer than the value it repeats for "
            f"years is carrying a filled gap as if it were an observation")
    elif len(rows) < BASELINE_RUNS:
        problems.append(
            f"only {len(rows)} runs remain, below the pinned ceiling of {BASELINE_RUNS} — lower the "
            f"baseline and say which were repaired and how")

    for k in sorted(long_runs - BASELINE_LONG):
        problems.append(
            f"NEW run of >={LONG_RUN} identical values: {k[1]} / {k[2]} ({k[3]}) = {k[4]} from "
            f"{k[5]}, {k[0]}. At this length the value cannot be a rounding floor — the series "
            f"resolves finer — so it is a carried-forward or placeholder value being read as data")
    for k in sorted(BASELINE_LONG - long_runs):
        problems.append(
            f"{k[1]} / {k[2]} = {k[4]} from {k[5]} is pinned as a long constant run but is not one "
            f"any more — remove its entry, saying what was repaired")

    n_wit = 0
    for r in rows:
        wy, wv = r.get("finer_in_volume_year", ""), r.get("finer_in_volume_value", "")
        if not wy and not wv:
            continue
        who = f"{r['source']} {r['country']} / {r['item']} ({r['unit']})"
        if bool(wy) != bool(wv):
            problems.append(f"{who}: finer_in_volume_year and _value must be set together, "
                            f"got {wy!r} and {wv!r}")
            continue
        n_wit += 1
        if r["source"] != "iia":
            problems.append(
                f"{who}: carries an in-volume witness, but only `iia` has known volume windows — "
                f"for any other source this column cannot mean anything and must be empty")
            continue
        try:
            y = int(wy)
            wval = float(wv)
            y0, y1 = int(r["year_first"]), int(r["year_last"])
            grid = float(r["grid"])
        except (TypeError, ValueError) as e:
            problems.append(f"{who}: unparseable witness ({e})")
            continue
        if y0 <= y <= y1:
            problems.append(
                f"{who}: witness year {y} lies INSIDE the run {y0}-{y1}, where every value equals "
                f"the constant by definition, so it cannot be evidence against the grid")
        if y in IIA_AMBIGUOUS_YEARS:
            problems.append(
                f"{who}: witness year {y} is covered by two IIA volumes, so the value could have "
                f"come from either and proves nothing about the run's own volume. Layer B carries no "
                f"volume provenance, which is why these years are excluded")
        if not (_volumes_covering(y) & (_volumes_covering(y0) | _volumes_covering(y1))):
            problems.append(
                f"{who}: witness year {y} shares no volume window with the run {y0}-{y1}, so it is "
                f"cross-era evidence — exactly the reading issue 366 withdrew")
        if grid > 0:
            q = wval / grid
            if abs(q - round(q)) < 1e-9:
                problems.append(
                    f"{who}: witness value {wval} sits ON the constant's grid of {grid}, so it shows "
                    f"a different multiple rather than finer precision. `algeria rye` is the trap: a "
                    f"2,000 constant beside 1,000, both on a 1,000 grid, is no evidence at all")
    print(f"  with an in-volume witness: {n_wit} (pinned {BASELINE_IN_VOLUME})")
    if n_wit != BASELINE_IN_VOLUME:
        problems.append(
            f"{n_wit} runs carry an in-volume witness against the pinned {BASELINE_IN_VOLUME}. More "
            f"means a volume was shown to resolve finer for a series it flat-lines, which wants "
            f"reading; fewer means one was repaired, which wants saying")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS: no new constant run, and every long one is accounted for")
    return 0


if __name__ == "__main__":
    sys.exit(main())
