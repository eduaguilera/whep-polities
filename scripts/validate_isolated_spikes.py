#!/usr/bin/env python3
"""Does one year in an otherwise smooth series read many times its own neighbours?

`05_magnitude_screen.py` screens series MEDIANS against the polity's area, which is right for a series
carried on the wrong scale THROUGHOUT and blind to a single bad year by construction. `iia cameroon /
groundnuts, with shell / ha` runs 61,000 (1931), 620,004,098 (1932), 62,000 (1933); its median is
71,000, so the screen carries the series -- flagged at ratio 9.3, for intensity -- and never sees the
spike. Cameroon's whole land area is about 47.5M ha, so 1932 is thirteen times the country.
`16_source_splices.py` cannot see these either: spike and both neighbours come from ONE source, so
there is no seam. `17_constant_runs.py` looks for the opposite shape.

`pipelines/polity-autoimprove/18_isolated_spikes.py` measures them from the layer-B panel and writes
`state/isolated_spikes.csv`. The panel is gitignored and absent in CI, so this gate reads the committed
table -- the same arrangement as `validate_source_splices.py` and `validate_constant_runs.py`.

WHAT THE FIRST RUN MEASURED:

    isolated single-year spikes >=20x BOTH neighbours      21
      >=50x  11      >=100x  8      >=1000x  4
      by source   iia 16   juan 3   mitchell 1   sa_colonial 1

TWO TRAPS, AND THE FIRST ONE BIT BEFORE IT WAS FIXED. Run without `indicator` in the series key the
detector returns 110 hits, 89 of them `fao1952`, printing "neighbours" in the SAME YEAR as the spike --
that source packs several indicators under one item code, so the comparison was between indicators, not
years. And 342 series carry two rows for one year with nothing in the panel to order them (issue 367);
a series that cannot be ordered has no neighbours, so it is skipped and counted rather than guessed at.

IT DELIBERATELY MISSES ADJACENT SPIKES. The Czech beer series spikes in 1937, 1944 and 1945; only 1937
is here, because 1944's neighbour is 1945 -- also spiked -- and the ratio collapses. A RUN of bad years
belongs to the splice and constant-run detectors. Endpoints have one neighbour and are not tested.

Two signals:
  A. COUNT CEILING   the number of spikes may not grow. Bidirectional: repair some and the ceiling
                     must come down with a note, so the table cannot quietly refill.
  B. EVERY SPIKE     all 21 are pinned by identity. At 20x against both neighbours there is no
                     harvest, war or border reading available, and each is one lookup on a page.

Usage:
  python3 scripts/validate_isolated_spikes.py
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/isolated_spikes.csv")

# Measured 2026-08-18 on the first run. BIDIRECTIONAL: repairing spikes must lower this, with a note
# saying which were repaired, so a later regression cannot hide inside the old headroom.
BASELINE_SPIKES = 21

# The factor 18_isolated_spikes.py reports against; restated here so the gate does not depend on the
# generator's constant to know what the table means.
SPIKE = 20.0


def key(r):
    return (r["source"], r["country"], r["item"], r["unit"], r["year"])


# Every spike on the first run. GENERATED FROM THE TABLE, never hand-typed -- transcribing a baseline
# from a truncated printout once missed 18 of 30 entries.
BASELINE_SPIKE_KEYS = frozenset({
    ('iia', 'antigua and barbuda', 'cotton seed', 'tonnes', '1934'),
    ('iia', 'cameroon', 'groundnuts with shell', 'ha', '1932'),
    ('iia', 'cyprus', 'oil olive virgin', 'tonnes', '1920'),
    ('iia', 'cyprus', 'tobacco unmanufactured', 'ha', '1925'),
    ('iia', 'egypt', 'tangerines mandarins clementines satsumas', 'tonnes', '1940'),
    ('iia', 'france', 'eggs hen in shell', 'tonnes', '1937'),
    ('iia', 'greece', 'grapes', 'tonnes', '1936'),
    ('iia', 'guadeloupe', 'cotton seed', 'tonnes', '1934'),
    ('iia', 'japan', 'p', 'tonnes', '1931'),
    ('iia', 'japan', 'silk worm cocoons reelable', 'tonnes', '1942'),
    ('iia', 'malawi', 'cotton lint', 'tonnes', '1935'),
    ('iia', 'nicaragua', 'cotton seed', 'tonnes', '1934'),
    ('iia', 'spain', 'wine', 'tonnes', '1920'),
    ('iia', 'syrian arab republic', 'hempseed', 'ha', '1936'),
    ('iia', 'syrian arab republic', 'hempseed', 'ha', '1940'),
    ('iia', 'turkey', 'silk worm cocoons reelable', 'tonnes', '1941'),
    ('juan', 'bulgaria', 'linseed', 'tonnes', '1898'),
    ('juan', 'bulgaria', 'rapeseed', 'tonnes', '1905'),
    ('juan', 'panama', 'cattle', 'heads', '1934'),
    ('mitchell', 'czech republic', 'beer of barley', 'tonnes', '1937'),
    ('sa_colonial', 'western australia', 'maize', 'Bushels', '1886'),
})


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"SKIP: {os.path.relpath(TABLE, REPO)} missing — run 18_isolated_spikes.py --write")
        return 0
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    print(f"recorded spikes: {len(rows)} (ceiling {BASELINE_SPIKES}, pinned {len(BASELINE_SPIKE_KEYS)})")

    problems = []
    if len(rows) > BASELINE_SPIKES:
        problems.append(
            f"{len(rows)} single-year spikes read >={SPIKE:.0f}x both their neighbours, above the "
            f"ceiling of {BASELINE_SPIKES}. Output does not move by that factor for one year and back")
    elif len(rows) < BASELINE_SPIKES:
        problems.append(
            f"only {len(rows)} spikes remain, below the pinned ceiling of {BASELINE_SPIKES} — lower the "
            f"baseline and say which were repaired and how")

    seen = {key(r) for r in rows}
    for k in sorted(seen - BASELINE_SPIKE_KEYS):
        problems.append(
            f"NEW spike: {k[1]} / {k[2]} ({k[3]}) at {k[4]}, {k[0]}. A single year many times its own "
            f"neighbours is an extraction defect — a dropped decimal, prepended digits, a misaligned "
            f"column or a footnote read as a value")
    for k in sorted(BASELINE_SPIKE_KEYS - seen):
        problems.append(
            f"{k[1]} / {k[2]} at {k[4]} is pinned as a spike but is not one any more — remove its "
            f"entry, saying what was repaired")

    # A spike whose recorded factor contradicts its own three values would mean the table and the
    # generator have drifted apart, and every judgement here rests on that column.
    for r in rows:
        bound = max(float(r["value_prev"]), float(r["value_next"]))
        if bound <= 0:
            problems.append(f"{r['country']} / {r['item']} at {r['year']}: non-positive neighbour")
            continue
        derived = float(r["value"]) / bound
        if abs(derived - float(r["factor_vs_larger_neighbour"])) > 0.01 * max(1.0, derived):
            problems.append(
                f"{r['country']} / {r['item']} at {r['year']}: recorded factor "
                f"{r['factor_vs_larger_neighbour']} does not match its own values ({derived:.2f})")

    if problems:
        print(f"\nFAIL: {len(problems)} problem(s)\n")
        for p in problems:
            print(f"  {p}")
        return 1
    print("\nPASS: no new spike, every one accounted for, and each factor re-derived from its own values")
    return 0


if __name__ == "__main__":
    sys.exit(main())
