#!/usr/bin/env python3
"""Does a series COLLAPSE — one year many times below its neighbours, or below its own start/end?

`validate_isolated_spikes.py` guards the opposite shape and is one-directional by construction: it
flags a year reading >=20x ABOVE both neighbours and explicitly skips endpoints. Both choices were
right for what it was built to catch, and together they left a hole with a CONFIRMED defect in it.

`iia nauru / p` runs 275,720 / 245,040 / 424,896 for 1930-1932 and ends on **97** in 1933 — a 4,380x
collapse in the series\' final year. It is a transposition: the iia_1933_34 volume swapped Nauru\'s and
Australia\'s 1933 phosphate, and iia_1938_39 has them the right way round (369,500 and 100). The spike
detector could not see it twice over: wrong sign, and an endpoint. It was found only because
26_edition_conflicts.py compares yearbook volumes, and it is banked in state/data_errors.csv.

`pipelines/polity-autoimprove/27_series_collapses.py` measures the mirror shape from the layer-B
panel. The panel is gitignored and absent in CI, so this gate reads the committed table.

WHAT THE FIRST RUN MEASURED: 117 collapses at >=20x, in three positions and **zero overlap** with the
21 rows of `isolated_spikes.csv` — a disjoint class, not a re-detection.

    interior_collapse   55   a year >=20x below BOTH neighbours; the exact mirror of a spike
    leading_collapse    52   the first value >=20x below its only neighbour
    terminal_collapse   10   the last value >=20x below its only neighbour

    by source: iia 58, juan 37, mitchell 20, fao1952 2

THE TABLE DOES NOT CLAIM ITS ROWS ARE DEFECTS, AND THAT IS A MEASURED POSITION. Of the ten terminal
collapses, four are plausible war endings — `iia hungary / silk-worm cocoons` 236 -> 4 (1945),
`juan hungary / castor beans` 6,000 -> 200 (1945), `iia hungary / sugar raw centrifugal`
176,400 -> 6,500 (1945), `iia iran / castor beans` 2,600 -> 100 (1944) — while
`mitchell china, mainland / millet` 6,524,000 -> 4,000 ha (1952) and `iia norway / no3`
148,000 -> 130 t (1921) are not plausible at all. NO RATIO SEPARATES THEM: Hungary\'s sugar sits at
27x and Iran\'s castor at 26x, below Tanzania\'s cassava at 70x. A threshold that happened to split
them would be fitted to the examples in front of me, which is the error issue 406 caught. So the gate
guards the SHAPE and leaves each verdict to whoever can check the year.

Two signals:
  A. COUNT CEILINGS  per position. Bidirectional: repairing collapses must lower them with a note,
     so the table cannot quietly refill.
  B. EVERY COLLAPSE  all 117 pinned by identity, so one cannot be swapped for another under a
     constant total — the failure a count-only ceiling cannot see.

Usage:
  python3 scripts/validate_series_collapses.py
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/series_collapses.csv")

# Measured 2026-08-19 on the first run. BIDIRECTIONAL: repairing a collapse must lower the matching
# ceiling with a note saying which cell was fixed and how.
BASELINE = {"interior_collapse": 55, "leading_collapse": 52, "terminal_collapse": 10}

# The factor 27_series_collapses.py reports against, restated so the gate does not depend on the
# generator\'s constant to know what the table means. Deliberately the same 20x
# validate_isolated_spikes.py uses: two detectors for one phenomenon that disagreed about what
# counts as extreme would be worse than either alone.
COLLAPSE = 20.0

POSITIONS = frozenset(BASELINE)

# Every collapse on the first run. GENERATED FROM THE TABLE, never hand-typed — transcribing a
# baseline from a truncated printout once missed 18 of 30 entries.
BASELINE_KEYS = frozenset({
    ('iia', 'algeria', 'flax fibre and tow', 'tonnes', 'interior_collapse', '1919'),
    ('iia', 'algeria', 'grapes', 'ha', 'interior_collapse', '1933'),
    ('iia', 'algeria', 'linseed', 'tonnes', 'interior_collapse', '1920'),
    ('iia', 'algeria', 'wine', 'ha', 'interior_collapse', '1933'),
    ('iia', 'australia', 'flax fibre and tow', 'ha', 'interior_collapse', '1923'),
    ('iia', 'australia', 'linseed', 'ha', 'interior_collapse', '1923'),
    ('iia', 'canada', 'eggs, hen, in shell', 'tonnes', 'interior_collapse', '1930'),
    ('iia', 'czech republic', 'rye', 'ha', 'interior_collapse', '1943'),
    ('iia', 'egypt', 'tangerines, mandarins, clementines, satsumas', 'tonnes', 'interior_collapse', '1939'),
    ('iia', 'greece', 'grapes', 'tonnes', 'interior_collapse', '1937'),
    ('iia', 'italy', 'sugar raw centrifugal', 'tonnes', 'interior_collapse', '1941'),
    ('iia', 'japan', 'p', 'tonnes', 'interior_collapse', '1930'),
    ('iia', 'japan', 'p', 'tonnes', 'interior_collapse', '1932'),
    ('iia', 'libya', 'wine', 'ha', 'interior_collapse', '1933'),
    ('iia', 'lithuania', 'sugar raw centrifugal', 'tonnes', 'interior_collapse', '1933'),
    ('iia', 'morocco', 'wine', 'ha', 'interior_collapse', '1933'),
    ('iia', 'panama', 'cacao, beans', 'tonnes', 'interior_collapse', '1917'),
    ('iia', 'russian federation', 'flax fibre and tow', 'ha', 'interior_collapse', '1918'),
    ('iia', 'russian federation', 'flax fibre and tow', 'tonnes', 'interior_collapse', '1918'),
    ('iia', 'russian federation', 'hemp tow waste', 'ha', 'interior_collapse', '1918'),
    ('iia', 'russian federation', 'rapeseed', 'ha', 'interior_collapse', '1914'),
    ('iia', 'russian federation', 'rapeseed', 'tonnes', 'interior_collapse', '1914'),
    ('iia', 'russian federation', 'rye', 'ha', 'interior_collapse', '1918'),
    ('iia', 'russian federation', 'rye', 'tonnes', 'interior_collapse', '1918'),
    ('iia', 'russian federation', 'rye', 'tonnes', 'interior_collapse', '1931'),
    ('iia', 'serbia', 'rye', 'ha', 'interior_collapse', '1943'),
    ('iia', 'syrian arab republic', 'olives', 'tonnes', 'interior_collapse', '1941'),
    ('iia', 'tunisia', 'wine', 'ha', 'interior_collapse', '1933'),
    ('iia', 'united states of america', 'coffee, green', 'ha', 'interior_collapse', '1924'),
    ('iia', 'united states of america', 'coffee, green', 'tonnes', 'interior_collapse', '1933'),
    ('juan', 'argentina', 'grapes', 'tonnes', 'interior_collapse', '1932'),
    ('juan', 'brazil', 'figs', 'tonnes', 'interior_collapse', '1959'),
    ('juan', 'bulgaria', 'flax fibre and tow', 'ha', 'interior_collapse', '1899'),
    ('juan', 'bulgaria', 'linseed', 'ha', 'interior_collapse', '1899'),
    ('juan', 'bulgaria', 'linseed', 'tonnes', 'interior_collapse', '1899'),
    ('juan', 'bulgaria', 'rapeseed', 'ha', 'interior_collapse', '1915'),
    ('juan', 'denmark', 'rapeseed', 'tonnes', 'interior_collapse', '1921'),
    ('juan', 'mexico', 'sugar cane', 'ha', 'interior_collapse', '1899'),
    ('juan', 'mexico', 'sugar cane', 'tonnes', 'interior_collapse', '1899'),
    ('juan', 'panama', 'swine / pigs', 'heads', 'interior_collapse', '1921'),
    ('juan', 'spain', 'canary seed', 'tonnes', 'interior_collapse', '1901'),
    ('juan', 'spain', 'grain, mixed', 'tonnes', 'interior_collapse', '1907'),
    ('juan', 'spain', 'linseed', 'tonnes', 'interior_collapse', '1924'),
    ('juan', 'switzerland', 'plums and sloes', 'tonnes', 'interior_collapse', '1887'),
    ('juan', 'switzerland', 'walnuts, with shell', 'tonnes', 'interior_collapse', '1887'),
    ('mitchell', 'cameroon', 'coffee, green', 'tonnes', 'interior_collapse', '1941'),
    ('mitchell', 'china, mainland', 'groundnuts, with shell', 'tonnes', 'interior_collapse', '1930'),
    ('mitchell', 'china, mainland', 'oats', 'ha', 'interior_collapse', '1952'),
    ('mitchell', 'india', 'asses', 'heads', 'interior_collapse', '1908'),
    ('mitchell', 'india', 'swine / pigs', 'heads', 'interior_collapse', '1947'),
    ('mitchell', 'india', 'tobacco, unmanufactured', 'tonnes', 'interior_collapse', '1946'),
    ('mitchell', 'korea', 'barley', 'ha', 'interior_collapse', '1944'),
    ('mitchell', 'nigeria', 'cattle', 'heads', 'interior_collapse', '1950'),
    ('mitchell', 'nigeria', 'goats', 'heads', 'interior_collapse', '1950'),
    ('mitchell', 'nigeria', 'sheep', 'heads', 'interior_collapse', '1950'),
    ('fao1952', 'Canada', 'horses mules asses', '1000 heads', 'leading_collapse', '1931'),
    ('fao1952', 'United Kingdom', 'horses mules asses', '1000 heads', 'leading_collapse', '1938'),
    ('iia', 'chile', 'flax fibre and tow', 'tonnes', 'leading_collapse', '1910'),
    ('iia', 'czech republic', 'hemp tow waste', 'ha', 'leading_collapse', '1919'),
    ('iia', 'czech republic', 'rye', 'ha', 'leading_collapse', '1910'),
    ('iia', 'czech republic', 'yarn of true hemp', 'tonnes', 'leading_collapse', '1919'),
    ('iia', 'dr congo', 'cotton seed', 'ha', 'leading_collapse', '1922'),
    ('iia', 'ivory coast', 'cacao, beans', 'ha', 'leading_collapse', '1922'),
    ('iia', 'morocco', 'p', 'tonnes', 'leading_collapse', '1921'),
    ('iia', 'mozambique', 'cotton lint', 'ha', 'leading_collapse', '1922'),
    ('iia', 'mozambique', 'cotton seed', 'ha', 'leading_collapse', '1922'),
    ('iia', 'syrian arab republic', 'cotton lint', 'ha', 'leading_collapse', '1922'),
    ('iia', 'syrian arab republic', 'cotton seed', 'ha', 'leading_collapse', '1922'),
    ('iia', 'zambia', 'cotton lint', 'ha', 'leading_collapse', '1922'),
    ('iia', 'zambia', 'cotton lint', 'tonnes', 'leading_collapse', '1922'),
    ('iia', 'zambia', 'cotton seed', 'ha', 'leading_collapse', '1922'),
    ('iia', 'zambia', 'cotton seed', 'tonnes', 'leading_collapse', '1922'),
    ('iia', 'zambia', 'tobacco, unmanufactured', 'ha', 'leading_collapse', '1922'),
    ('iia', 'zambia', 'tobacco, unmanufactured', 'tonnes', 'leading_collapse', '1922'),
    ('iia', 'zimbabwe', 'cotton lint', 'ha', 'leading_collapse', '1922'),
    ('iia', 'zimbabwe', 'cotton lint', 'tonnes', 'leading_collapse', '1922'),
    ('iia', 'zimbabwe', 'cotton seed', 'ha', 'leading_collapse', '1922'),
    ('iia', 'zimbabwe', 'cotton seed', 'tonnes', 'leading_collapse', '1922'),
    ('juan', 'argentina', 'artichokes', 'tonnes', 'leading_collapse', '1937'),
    ('juan', 'argentina', 'barley', 'ha', 'leading_collapse', '1872'),
    ('juan', 'argentina', 'fibre crops nes', 'tonnes', 'leading_collapse', '1937'),
    ('juan', 'argentina', 'garlic', 'tonnes', 'leading_collapse', '1937'),
    ('juan', 'argentina', 'soybeans', 'ha', 'leading_collapse', '1937'),
    ('juan', 'argentina', 'sugar cane', 'ha', 'leading_collapse', '1872'),
    ('juan', 'argentina', 'tea', 'ha', 'leading_collapse', '1937'),
    ('juan', 'bulgaria', 'linseed', 'tonnes', 'leading_collapse', '1897'),
    ('juan', 'canada', 'goats', 'heads', 'leading_collapse', '1918'),
    ('juan', 'colombia', 'coffee, green', 'ha', 'leading_collapse', '1916'),
    ('juan', 'czechoslovakia', 'hemp tow waste', 'tonnes', 'leading_collapse', '1919'),
    ('juan', 'czechoslovakia', 'maize', 'tonnes', 'leading_collapse', '1919'),
    ('juan', 'czechoslovakia', 'sunflower seed', 'ha', 'leading_collapse', '1919'),
    ('juan', 'el salvador', 'asses', 'heads', 'leading_collapse', '1930'),
    ('juan', 'germany', 'mules and hinnies', 'heads', 'leading_collapse', '1912'),
    ('juan', 'haiti', 'maize', 'ha', 'leading_collapse', '1930'),
    ('juan', 'mexico', 'oil, cottonseed', 'tonnes', 'leading_collapse', '1907'),
    ('juan', 'peru', 'chick peas', 'tonnes', 'leading_collapse', '1948'),
    ('juan', 'switzerland', 'apples', 'tonnes', 'leading_collapse', '1850'),
    ('juan', 'switzerland', 'rapeseed', 'tonnes', 'leading_collapse', '1909'),
    ('juan', 'united states of america', 'soybeans', 'ha', 'leading_collapse', '1909'),
    ('mitchell', 'india', 'asses', 'heads', 'leading_collapse', '1947'),
    ('mitchell', 'india', 'buffalo', 'heads', 'leading_collapse', '1947'),
    ('mitchell', 'india', 'camels', 'heads', 'leading_collapse', '1947'),
    ('mitchell', 'india', 'cattle', 'heads', 'leading_collapse', '1947'),
    ('mitchell', 'india', 'goats', 'heads', 'leading_collapse', '1947'),
    ('mitchell', 'india', 'horses', 'heads', 'leading_collapse', '1947'),
    ('mitchell', 'india', 'sheep', 'heads', 'leading_collapse', '1947'),
    ('mitchell', 'natal', 'tobacco, unmanufactured', 'tonnes', 'leading_collapse', '1861'),
    ('iia', 'hungary', 'silk-worm cocoons, reelable', 'tonnes', 'terminal_collapse', '1945'),
    ('iia', 'hungary', 'sugar raw centrifugal', 'tonnes', 'terminal_collapse', '1945'),
    ('iia', 'iran', 'castor beans seed', 'tonnes', 'terminal_collapse', '1944'),
    ('iia', 'israel', 'oranges', 'tonnes', 'terminal_collapse', '1939'),
    ('iia', 'mauritius', 'coffee, green', 'tonnes', 'terminal_collapse', '1915'),
    ('iia', 'nauru', 'p', 'tonnes', 'terminal_collapse', '1933'),
    ('iia', 'norway', 'no3', 'tonnes', 'terminal_collapse', '1921'),
    ('juan', 'hungary', 'castor beans seed', 'tonnes', 'terminal_collapse', '1945'),
    ('mitchell', 'china, mainland', 'millet', 'ha', 'terminal_collapse', '1952'),
    ('mitchell', 'tanzania', 'cassava, fresh', 'ha', 'terminal_collapse', '1960'),
})


def key(r):
    return (r["source"], r["country"], r["item"], r["unit"], r["position"], r["year"])


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} missing — run 27_series_collapses.py --write",
              file=sys.stderr)
        return 1
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))

    counts = {}
    for r in rows:
        counts[r["position"]] = counts.get(r["position"], 0) + 1
    print(f"series collapses: {len(rows)} (pinned {len(BASELINE_KEYS)})  "
          + "  ".join(f"{p}={counts.get(p, 0)}/{BASELINE[p]}" for p in sorted(BASELINE)))

    problems = []
    for pos in sorted(BASELINE):
        n = counts.get(pos, 0)
        if n > BASELINE[pos]:
            problems.append(
                f"A {n} {pos} rows, above the ceiling of {BASELINE[pos]}. A year reading "
                f">={COLLAPSE:.0f}x below its neighbours is a dropped digit, a misaligned column or a "
                f"transposed pair until someone shows it is a real collapse")
        elif n < BASELINE[pos]:
            problems.append(
                f"A only {n} {pos} rows remain, below the pinned ceiling of {BASELINE[pos]} — lower "
                f"the baseline and say which cells were repaired and on what evidence")
    for pos in sorted(set(counts) - POSITIONS):
        problems.append(f"A unknown position {pos!r} — generator and gate disagree about the vocabulary")

    seen = {key(r) for r in rows}
    for k in sorted(seen - BASELINE_KEYS):
        problems.append(
            f"B NEW {k[4]}: {k[1]} / {k[2]} ({k[3]}) at {k[5]}, {k[0]} — reads >={COLLAPSE:.0f}x below "
            f"its neighbour(s) and is not pinned")
    for k in sorted(BASELINE_KEYS - seen):
        problems.append(
            f"B {k[1]} / {k[2]} at {k[5]} is pinned as a {k[4]} but is not one any more — remove its "
            f"entry, saying what was repaired")

    # A row whose recorded factor contradicts its own two values means the table and this gate
    # disagree about what the row says, and every judgement above rests on that column.
    for r in rows:
        try:
            v, nb, f = float(r["value"]), float(r["neighbour_value"]), float(r["factor"])
        except ValueError:
            problems.append(f"C {r['country']}/{r['item']} {r['year']}: unparseable numbers")
            continue
        if v <= 0:
            problems.append(f"C {r['country']}/{r['item']} {r['year']}: value {v:g} is not positive, "
                            f"so the ratio is undefined and the row should not exist")
            continue
        if abs(nb / v - f) > max(0.05, f * 1e-3):
            problems.append(
                f"C {r['country']}/{r['item']} {r['year']}: recorded factor {f:g} does not match its "
                f"own values ({nb:g} / {v:g} = {nb / v:.1f}) — the column every judgement rests on no "
                f"longer describes the row it sits in")
        if f < COLLAPSE:
            problems.append(
                f"C {r['country']}/{r['item']} {r['year']}: factor {f:g} is below the {COLLAPSE:.0f}x "
                f"threshold the table is defined by")

    for p in problems:
        print(f"FAIL: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
