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

WHAT IT MEASURES: 239 rows in five positions, with **zero overlap** with the 21 rows of
`isolated_spikes.csv` — a disjoint class, not a re-detection.

    interior_collapse   55   a year >=20x below BOTH neighbours; the exact mirror of a spike
    leading_collapse    51   the first value >=20x below its only neighbour
    terminal_collapse   10   the last value >=20x below its only neighbour
    zero_tail           81   a series ending in >=2 zeros after real output
    zero_interior       42   a single zero with real output on both sides

THE TWO ZERO CLASSES WERE ADDED BECAUSE NOTHING COULD SEE THEM. This tool first excluded zeros,
deferring them to issue 414 — and that deferral was wrong: `edition_conflicts.csv` needs two volumes
and only 1933 has them, and `impossible_pairs.csv` needs a paired area. `17_constant_runs.py`
excludes zeros too, for the same divide-by-zero reason. So a series that dropped to zero and stayed
there was invisible to EVERY detector in this repo.

`juan united kingdom / mules and hinnies` reads 0.0 for every year 1921-1938 while the SAME source
and label report asses (10,000 falling to 7,000) and horses (2,055,000 to 1,100,000) throughout. The
source is reporting draught animals and not reporting mules; the zero means "not stated".

68 of the 81 tails begin in 1933-1936 — the `iia_1938_39` window — so most of this class is issue
414's blank-read-as-0 appearing as a RUN rather than a cell. The rest are not: the UK mules run
starts in 1921, and `latvia` and `lithuania` sugar beet go to zero in 1940, when both were annexed
and their output would be reported inside Soviet statistics instead.

LEGITIMATE ZEROS ARE EXCLUDED BY CONSTRUCTION, not by judgement. A series that OPENS at zero is in
neither class: `iia morocco / p` reads zero for 1909-1918 because Moroccan phosphate mining had not
begun, and a leading run of zeros is exactly what that should look like.

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

# Measured 2026-08-19. BIDIRECTIONAL: repairing a collapse must lower the matching ceiling with a
# note saying which cell was fixed and how.
#
# `leading_collapse` fell from 52 to 51 when the generator stopped deleting zero rows before
# comparing. `iia morocco / p` opens with TEN zeros (1909-1918, before Moroccan phosphate mining
# began, so they are legitimate); the old `value > 0` filter removed them, promoted the first
# POSITIVE value to the head of the series, and reported a leading collapse between two years that
# were not the series start at all. That row was FABRICATED by the filter, not merely hidden by it.
BASELINE = {"interior_collapse": 55, "leading_collapse": 51, "terminal_collapse": 10,
            "zero_tail": 81, "zero_interior": 42}

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
    ('iia', 'algeria', 'beans, dry', 'ha', 'zero_interior', '1938'),
    ('iia', 'algeria', 'cotton lint', 'tonnes', 'zero_interior', '1935'),
    ('iia', 'algeria', 'cotton lint', 'tonnes', 'zero_interior', '1938'),
    ('iia', 'algeria', 'cotton seed', 'tonnes', 'zero_interior', '1935'),
    ('iia', 'algeria', 'cotton seed', 'tonnes', 'zero_interior', '1938'),
    ('iia', 'antigua and barbuda', 'cotton lint', 'tonnes', 'zero_interior', '1934'),
    ('iia', 'antigua and barbuda', 'cotton lint', 'tonnes', 'zero_interior', '1936'),
    ('iia', 'bulgaria', 'sugar raw centrifugal', 'tonnes', 'zero_interior', '1925'),
    ('iia', 'canada', 'p', 'tonnes', 'zero_interior', '1920'),
    ('iia', 'canada', 'p', 'tonnes', 'zero_interior', '1931'),
    ('iia', 'cyprus', 'flax fibre and tow', 'ha', 'zero_interior', '1938'),
    ('iia', 'cyprus', 'flax fibre and tow', 'tonnes', 'zero_interior', '1938'),
    ('iia', 'cyprus', 'yarn of true hemp', 'tonnes', 'zero_interior', '1934'),
    ('iia', 'egypt', 'flax fibre and tow', 'ha', 'zero_interior', '1913'),
    ('iia', 'falkland islands (malvinas)', 'fertilizer, mixed', 'tonnes', 'zero_interior', '1918'),
    ('iia', 'germany', 'yarn of true hemp', 'ha', 'zero_interior', '1934'),
    ('iia', 'indonesia', 'p', 'tonnes', 'zero_interior', '1918'),
    ('iia', 'kenya', 'beans, dry', 'ha', 'zero_interior', '1938'),
    ('iia', 'kenya', 'flax fibre and tow', 'ha', 'zero_interior', '1935'),
    ('iia', 'kenya', 'groundnuts, with shell', 'tonnes', 'zero_interior', '1934'),
    ('iia', 'libya', 'oil, olive, virgin', 'tonnes', 'zero_interior', '1935'),
    ('iia', 'malawi', 'cotton lint', 'ha', 'zero_interior', '1937'),
    ('iia', 'malawi', 'cotton seed', 'ha', 'zero_interior', '1937'),
    ('iia', 'montserrat', 'lemons and limes', 'ha', 'zero_interior', '1934'),
    ('iia', 'montserrat', 'sugar raw centrifugal', 'tonnes', 'zero_interior', '1937'),
    ('iia', 'morocco', 'cotton lint', 'tonnes', 'zero_interior', '1934'),
    ('iia', 'morocco', 'cotton lint', 'tonnes', 'zero_interior', '1940'),
    ('iia', 'morocco', 'cotton seed', 'tonnes', 'zero_interior', '1934'),
    ('iia', 'myanmar', 'sesame seed', 'ha', 'zero_interior', '1944'),
    ('iia', 'new caledonia', 'p', 'tonnes', 'zero_interior', '1932'),
    ('iia', 'palau', 'p', 'tonnes', 'zero_interior', '1913'),
    ('iia', 'portugal', 'n', 'tonnes', 'zero_interior', '1920'),
    ('iia', 'saint lucia', 'lemons and limes', 'ha', 'zero_interior', '1933'),
    ('iia', 'serbia', 'lemons and limes', 'tonnes', 'zero_interior', '1936'),
    ('iia', 'somalia', 'sesame seed', 'ha', 'zero_interior', '1935'),
    ('iia', 'sri lanka', 'cotton seed', 'tonnes', 'zero_interior', '1933'),
    ('iia', 'switzerland', 'sugar raw centrifugal', 'tonnes', 'zero_interior', '1912'),
    ('iia', 'vanuatu', 'cotton seed', 'tonnes', 'zero_interior', '1933'),
    ('iia', 'vanuatu', 'cotton seed', 'tonnes', 'zero_interior', '1936'),
    ('juan', 'czechoslovakia', 'asses', 'heads', 'zero_interior', '1935'),
    ('juan', 'iceland', 'goats', 'heads', 'zero_interior', '1945'),
    ('juan', 'iceland', 'goats', 'heads', 'zero_interior', '1948'),
    ('fao1952', 'Germany Berlin', 'milk', '1000 tonnes', 'zero_tail', '1950'),
    ('fao1952', 'Germany Eastern', 'milk', '1000 tonnes', 'zero_tail', '1950'),
    ('iia', 'algeria', 'silk-worm cocoons, reelable', 'tonnes', 'zero_tail', '1933'),
    ('iia', 'australia', 'coffee, green', 'ha', 'zero_tail', '1933'),
    ('iia', 'australia', 'coffee, green', 'tonnes', 'zero_tail', '1933'),
    ('iia', 'australia', 'olives', 'ha', 'zero_tail', '1933'),
    ('iia', 'austria', 'soybeans', 'ha', 'zero_tail', '1934'),
    ('iia', 'austria', 'yarn of true hemp', 'ha', 'zero_tail', '1934'),
    ('iia', 'barbados', 'cotton lint', 'ha', 'zero_tail', '1934'),
    ('iia', 'barbados', 'cotton lint', 'tonnes', 'zero_tail', '1934'),
    ('iia', 'barbados', 'cotton seed', 'ha', 'zero_tail', '1934'),
    ('iia', 'belgium', 'hempseed', 'ha', 'zero_tail', '1934'),
    ('iia', 'belgium', 'rapeseed', 'ha', 'zero_tail', '1934'),
    ('iia', 'belgium', 'yarn of true hemp', 'ha', 'zero_tail', '1934'),
    ('iia', 'benin', 'cacao, beans', 'ha', 'zero_tail', '1934'),
    ('iia', 'burundi', 'tobacco, unmanufactured', 'ha', 'zero_tail', '1934'),
    ('iia', 'china, taiwan province of', 'other berries and fruits of the genus vaccinium n.e.c.', 'ha', 'zero_tail', '1936'),
    ('iia', 'china, taiwan province of', 'rapeseed', 'ha', 'zero_tail', '1934'),
    ('iia', 'costa rica', 'lemons and limes', 'tonnes', 'zero_tail', '1931'),
    ('iia', 'cyprus', 'hempseed', 'ha', 'zero_tail', '1934'),
    ('iia', 'cyprus', 'hempseed', 'tonnes', 'zero_tail', '1934'),
    ('iia', 'cyprus', 'yarn of true hemp', 'ha', 'zero_tail', '1934'),
    ('iia', 'dominican republic', 'cotton seed', 'tonnes', 'zero_tail', '1933'),
    ('iia', 'ecuador', 'lemons and limes', 'tonnes', 'zero_tail', '1934'),
    ('iia', 'eritrea', 'groundnuts, with shell', 'ha', 'zero_tail', '1936'),
    ('iia', 'eritrea', 'groundnuts, with shell', 'tonnes', 'zero_tail', '1936'),
    ('iia', 'eritrea', 'tobacco, unmanufactured', 'ha', 'zero_tail', '1934'),
    ('iia', 'eswatini', 'tobacco, unmanufactured', 'ha', 'zero_tail', '1933'),
    ('iia', 'fiji', 'cotton lint', 'ha', 'zero_tail', '1933'),
    ('iia', 'fiji', 'cotton lint', 'tonnes', 'zero_tail', '1933'),
    ('iia', 'fiji', 'cotton seed', 'ha', 'zero_tail', '1933'),
    ('iia', 'fiji', 'cotton seed', 'tonnes', 'zero_tail', '1933'),
    ('iia', 'french guiana', 'cacao, beans', 'ha', 'zero_tail', '1933'),
    ('iia', 'french guiana', 'cacao, beans', 'tonnes', 'zero_tail', '1933'),
    ('iia', 'french polynesia', 'tobacco, unmanufactured', 'ha', 'zero_tail', '1934'),
    ('iia', 'greece', 'grapes', 'tonnes', 'zero_tail', '1941'),
    ('iia', 'guadeloupe', 'cotton lint', 'ha', 'zero_tail', '1934'),
    ('iia', 'guadeloupe', 'cotton lint', 'tonnes', 'zero_tail', '1934'),
    ('iia', 'guadeloupe', 'cotton seed', 'ha', 'zero_tail', '1934'),
    ('iia', 'guatemala', 'cotton lint', 'tonnes', 'zero_tail', '1933'),
    ('iia', 'guatemala', 'groundnuts, with shell', 'ha', 'zero_tail', '1934'),
    ('iia', 'guyana', 'lemons and limes', 'ha', 'zero_tail', '1934'),
    ('iia', 'india', 'cotton lint', 'ha', 'zero_tail', '1934'),
    ('iia', 'india', 'cotton seed', 'ha', 'zero_tail', '1936'),
    ('iia', 'latvia', 'sugar raw centrifugal', 'tonnes', 'zero_tail', '1940'),
    ('iia', 'libya', 'tobacco, unmanufactured', 'ha', 'zero_tail', '1934'),
    ('iia', 'lithuania', 'sugar raw centrifugal', 'tonnes', 'zero_tail', '1940'),
    ('iia', 'madagascar', 'cotton lint', 'ha', 'zero_tail', '1934'),
    ('iia', 'madagascar', 'cotton lint', 'tonnes', 'zero_tail', '1933'),
    ('iia', 'madagascar', 'cotton seed', 'ha', 'zero_tail', '1934'),
    ('iia', 'malawi', 'coffee, green', 'tonnes', 'zero_tail', '1936'),
    ('iia', 'malta', 'cotton lint', 'ha', 'zero_tail', '1934'),
    ('iia', 'malta', 'cotton lint', 'tonnes', 'zero_tail', '1934'),
    ('iia', 'malta', 'cotton seed', 'ha', 'zero_tail', '1934'),
    ('iia', 'malta', 'cotton seed', 'tonnes', 'zero_tail', '1934'),
    ('iia', 'mauritius', 'groundnuts, with shell', 'ha', 'zero_tail', '1934'),
    ('iia', 'mauritius', 'tobacco, unmanufactured', 'ha', 'zero_tail', '1933'),
    ('iia', 'netherlands', 'tobacco, unmanufactured', 'ha', 'zero_tail', '1934'),
    ('iia', 'new caledonia', 'cotton lint', 'ha', 'zero_tail', '1935'),
    ('iia', 'new caledonia', 'cotton lint', 'tonnes', 'zero_tail', '1935'),
    ('iia', 'new caledonia', 'cotton seed', 'ha', 'zero_tail', '1935'),
    ('iia', 'new caledonia', 'cotton seed', 'tonnes', 'zero_tail', '1934'),
    ('iia', 'new zealand', 'grapes', 'ha', 'zero_tail', '1933'),
    ('iia', 'new zealand', 'rye', 'ha', 'zero_tail', '1934'),
    ('iia', 'new zealand', 'wine', 'ha', 'zero_tail', '1933'),
    ('iia', 'nigeria', 'cotton lint', 'ha', 'zero_tail', '1939'),
    ('iia', 'paraguay', 'lemons and limes', 'tonnes', 'zero_tail', '1933'),
    ('iia', 'portugal', 'lemons and limes', 'tonnes', 'zero_tail', '1933'),
    ('iia', 'saint vincent and the grenadines', 'groundnuts, with shell', 'ha', 'zero_tail', '1934'),
    ('iia', 'south korea', 'sugar raw centrifugal', 'tonnes', 'zero_tail', '1932'),
    ('iia', 'tunisia', 'tobacco, unmanufactured', 'ha', 'zero_tail', '1935'),
    ('iia', 'uruguay', 'rye', 'ha', 'zero_tail', '1935'),
    ('iia', 'vanuatu', 'cotton lint', 'ha', 'zero_tail', '1934'),
    ('iia', 'vanuatu', 'cotton seed', 'ha', 'zero_tail', '1934'),
    ('iia', 'zambia', 'groundnuts, with shell', 'ha', 'zero_tail', '1933'),
    ('iia', 'zambia', 'oranges', 'ha', 'zero_tail', '1933'),
    ('juan', 'iceland', 'ducks', 'heads', 'zero_tail', '1948'),
    ('juan', 'iceland', 'geese and guinea fowls', 'heads', 'zero_tail', '1948'),
    ('juan', 'iceland', 'goats', 'heads', 'zero_tail', '1950'),
    ('juan', 'switzerland', 'asses', 'heads', 'zero_tail', '1943'),
    ('juan', 'united kingdom', 'mules and hinnies', 'heads', 'zero_tail', '1921'),
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
        # The zero positions carry no ratio, deliberately: `factor` is left EMPTY rather than filled
        # with a sentinel that later arithmetic might believe. Their shape check is that they really
        # do sit at zero.
        if r["position"].startswith("zero_"):
            if r["factor"] != "":
                problems.append(
                    f"C {r['country']}/{r['item']} {r['year']}: a {r['position']} carries a factor "
                    f"{r['factor']!r}, but there is no ratio against zero — an empty column has been "
                    f"filled with something a consumer could take for a measurement")
            if float(r["value"]) != 0:
                problems.append(
                    f"C {r['country']}/{r['item']} {r['year']} is classed {r['position']} but its "
                    f"value is {r['value']}, not zero")
            continue
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
