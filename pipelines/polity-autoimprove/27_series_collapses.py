#!/usr/bin/env python3
"""Where does a series COLLAPSE — one year many times below its neighbours, or below its own start/end?

`18_isolated_spikes.py` is one-directional by construction: it flags a year reading >=20x ABOVE both
its neighbours, and it explicitly skips endpoints because they have only one neighbour. Both choices
were right for what it was built to catch and both leave a hole, and the hole has a confirmed defect
sitting in it.

WHAT FELL THROUGH IT. `iia nauru / p` runs 275,720 / 245,040 / 424,896 for 1930-1932 and then ends on
**97** in 1933 -- a 4,380x collapse in the series' final year. It is a transposition: the iia_1933_34
volume swapped Nauru's and Australia's 1933 phosphate, and iia_1938_39 has them the right way round
(369,500 and 100). Confirmed in state/data_errors.csv, found only because 26_edition_conflicts.py
compares yearbook volumes. The spike detector could not see it twice over: wrong sign, and an endpoint.

THREE POSITIONS, because the evidence available differs at each:

    interior_collapse   a year >=20x below BOTH neighbours. The exact mirror of an isolated spike,
                        and the strongest shape -- a real collapse and recovery in adjacent years is
                        rare. 55 found.
    terminal_collapse   the last value >=20x below its only neighbour. 10 found.
    leading_collapse    the first value >=20x below its only neighbour. 52 found.

THIS TABLE DOES NOT CLAIM ITS ROWS ARE DEFECTS, and the measurement is why. Among the ten terminal
collapses, `iia hungary / silk-worm cocoons` 236 -> 4 in **1945**, `juan hungary / castor beans`
6,000 -> 200 in **1945**, `iia hungary / sugar raw centrifugal` 176,400 -> 6,500 in **1945** and
`iia iran / castor beans` 2,600 -> 100 in **1944** are all plausible: a war ends a series on a
genuinely collapsed harvest. Meanwhile `mitchell china, mainland / millet` 6,524,000 -> 4,000 ha in
1952 and `iia norway / no3` 148,000 -> 130 t in 1921 are not plausible at all.

NO THRESHOLD SEPARATES THOSE TWO GROUPS, and inventing one that happened to would be fitting it to
the examples in front of me -- the error issue 406 already caught me making. The ratio does not
discriminate (Hungary's sugar collapse at 27x and Iran's castor at 26x sit below Tanzania's cassava
at 70x, which is not obviously war-related), so the table records the SHAPE and leaves the verdict to
whoever can check the year. What it guarantees is that the shape can no longer appear silently.

UNORDERABLE SERIES ARE SKIPPED, not guessed at: 342 series carry two rows for one year with nothing
in the panel to order them (issue 367), and a series with no defined neighbour has no collapse.
Zero and negative values are excluded -- a ratio against zero is undefined, and a drop TO zero is the
separate concern issue 414 measures.

WHY A TRACKED TABLE. The panel is gitignored and absent in CI, so this writes
`state/series_collapses.csv`, that file is committed, and the gate reads it -- the same arrangement as
16_source_splices.py, 17_constant_runs.py, 18_isolated_spikes.py and 26_edition_conflicts.py.

Usage:
  python3 pipelines/polity-autoimprove/27_series_collapses.py            # report only
  python3 pipelines/polity-autoimprove/27_series_collapses.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/27_series_collapses.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "series_collapses.csv")
DEFAULT_PANEL = os.path.expanduser(os.environ.get(
    "WHEP_LAYER_B", "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"))

# The same factor 18_isolated_spikes.py uses, deliberately: this is its mirror, and two detectors for
# one phenomenon that disagreed about what counts as extreme would be worse than either alone.
COLLAPSE = 20.0

# `indicator` MUST be in the series key. Without it fao1952 packs several indicators under one item
# code and the detector compares indicators rather than years -- the trap that gave 18_isolated_spikes
# 110 hits instead of 21.
KEY = ["source", "country", "item", "unit", "indicator"]

FIELDS = ["source", "country", "item", "unit", "indicator", "position", "year",
          "value", "neighbour_value", "neighbour_year", "factor", "series_n"]


def build(panel_path: str) -> list[dict]:
    import pandas as pd

    d = pd.read_parquet(panel_path)
    d = d.dropna(subset=["year", "value"])
    d = d[d["value"] > 0]
    out = []
    for k, g in d.groupby(KEY, dropna=False):
        g = g.sort_values("year")
        # A series with two rows for one year has no defined neighbour (issue 367). Skipped, not
        # guessed at.
        if g["year"].nunique() < len(g):
            continue
        v = [float(x) for x in g["value"]]
        y = [int(x) for x in g["year"]]
        if len(v) < 4:
            continue
        base = dict(zip(KEY, [("" if x != x else x) if not isinstance(x, str) else x for x in k]))

        def emit(position, i, nb_i):
            out.append({**base, "position": position, "year": y[i], "value": f"{v[i]:g}",
                        "neighbour_value": f"{v[nb_i]:g}", "neighbour_year": y[nb_i],
                        "factor": f"{v[nb_i] / v[i]:.1f}", "series_n": len(v)})

        if v[-2] / v[-1] >= COLLAPSE:
            emit("terminal_collapse", len(v) - 1, len(v) - 2)
        if v[1] / v[0] >= COLLAPSE:
            emit("leading_collapse", 0, 1)
        for i in range(1, len(v) - 1):
            if v[i - 1] / v[i] >= COLLAPSE and v[i + 1] / v[i] >= COLLAPSE:
                # Report against the SMALLER neighbour, so `factor` is the weakest claim the row
                # supports rather than the most impressive one.
                nb = i - 1 if v[i - 1] <= v[i + 1] else i + 1
                emit("interior_collapse", i, nb)
    out.sort(key=lambda r: (r["position"], r["source"], str(r["country"]), str(r["item"]),
                            str(r["unit"]), r["year"]))
    return out


def write(rows: list[dict], path: str) -> None:
    """Build fully in memory then replace atomically — a truncating open() has cost this repo two
    tracked state files mid-error."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layer-b", default=DEFAULT_PANEL)
    ap.add_argument("--write", action="store_true", help=f"refresh {os.path.relpath(OUT, REPO)}")
    ap.add_argument("--check", action="store_true", help="exit 1 if the tracked table is stale")
    args = ap.parse_args()

    if not os.path.exists(args.layer_b):
        print(f"panel absent ({args.layer_b}); nothing to do", file=sys.stderr)
        return 0

    rows = build(args.layer_b)
    by = {}
    for r in rows:
        by[r["position"]] = by.get(r["position"], 0) + 1
    print(f"series collapses >={COLLAPSE:.0f}x: {len(rows)}")
    for p in sorted(by):
        print(f"  {p:20} {by[p]}")

    if args.check:
        if not os.path.exists(OUT):
            print(f"MISSING {os.path.relpath(OUT, REPO)}", file=sys.stderr)
            return 1
        with open(OUT, newline="") as fh:
            have = list(csv.DictReader(fh))
        want = [{k: str(v) for k, v in r.items()} for r in rows]
        if have != want:
            print(f"STALE {os.path.relpath(OUT, REPO)}: rerun with --write", file=sys.stderr)
            return 1
        print("table is current")
        return 0

    if args.write:
        write(rows, OUT)
        print(f"wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
