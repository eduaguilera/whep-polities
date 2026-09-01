#!/usr/bin/env python3
"""How coarse is each source's reporting grid? The machine-readable half of issue 446.

WHAT ISSUE 446 ASKS FOR. It measures that 47.6% of the panel's non-zero values sit on a 1000-grid and
are published as exact points, and it sets out three options. Option 2 is *"a per-(source, year-range)
precision table in this repo, joined by consumers"*, on the ground that a per-ROW precision column would
be mostly redundant -- for `mitchell` the answer is one constant for the whole source, and for `iia` one
constant per volume. The grids are already registered in `source_conventions.csv` with mechanical
re-tests (`check_mitchell_thousand_grid`, `check_iia_volume_grid`, `check_juan_heads_thousand_grid`), so
what is missing is only the joinable form. This file is that form, DERIVED from the panel rather than
transcribed from the prose, so the two cannot drift apart silently.

THE KEY IS (source, unit), NOT (source, year). Issue 446's own follow-up found that `juan` does not
reduce to one constant and does not partition by country -- of 53 countries with 200+ rows, none is
above 80% on a 1000-grid -- but it DOES partition by unit: `heads` 89.1% against `ha` 49.3% and
`tonnes` 34.1%. `mitchell` shows the same shape more sharply: `ha` and `heads` are 100.0% on a
1000-grid while `tonnes` is 78.2%. A table keyed on the source alone would average those together and
describe neither.

THE ERA ROWS DO NOT SUM TO THE `all` ROW, and that is not a bug to hide. An undated row -- a yearbook
period average like `1934-1938` -- has no year to compare against the cut, so it belongs to neither era
bucket while still counting in `all`. For `iia / ha` that is 2,411 of 9,996 values (24%), which is large
enough that a reader subtracting the two era rows and finding a shortfall should know why. Assigning a
period average to an era by its end year would have imported issue 310's whole problem into a precision
table for no gain.

ONLY `iia` IS SPLIT BY ERA, and only because its boundary is independently established: its volumes
cover disjoint year windows and the 1934 handover is registered as a convention (#445). Splitting a
source whose eras are not documented would invite reading a rise in coarseness as a boundary when it is
a mixture of sub-sources -- which is exactly what 446 says `juan`'s 44% -> 89% drift is.

THE VERDICT LADDER IS ORDERED AND MONOTONE, so a row cannot satisfy two rules:

    g1000 >= 0.80   coarse_1000   values carry about +/-500 in their own unit
    g100  >= 0.80   coarse_100    about +/-50
    g100  >= 0.40   mixed         a real mixture, not a single grid -- do not assume either
    otherwise       fine          reported at unit resolution or finer

WHAT THIS DOES NOT SAY. Not that any INDIVIDUAL value is rounded: being a multiple of 1,000 is not proof
about a cell, it is proof about a source. That is the level a precision table records and the level
446's argument is pitched at. Sub-unit share is carried alongside because it is the strongest single
discriminator -- 2 sub-unit values out of 40,664 is a fact about `mitchell` that no round-number share
could establish on its own.

Usage:
  python3 pipelines/polity-autoimprove/37_value_precision.py            # report only
  python3 pipelines/polity-autoimprove/37_value_precision.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/37_value_precision.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "source_value_precision.csv")
PANEL_DEFAULT = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B") or os.environ.get("WHEP_LAYERB")
    # ONE PANEL, EITHER SPELLING (issue 629). Two names were in use -- WHEP_LAYERB in
    # 01_match_and_findings.py and extdata.py, WHEP_LAYER_B in the other 17 tools -- so
    # neither redirected the whole pipeline and setting one left stage 01 matching against
    # a different panel than the analysis stages measured.
    or "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet")

MIN_ROWS = 500          # below this a share is not a measurement of a convention
ERA_SPLIT = {"iia": 1934}   # the only source whose era boundary is independently registered (#445)

FIELDS = ("source", "unit", "era", "n_nonzero", "share_grid_1000", "share_grid_100",
          "share_subunit", "verdict")


def _n(x, nd=4):
    f = float(x)
    return str(int(f)) if f == int(f) and abs(f) < 1e15 else repr(round(f, nd))


def classify(g1000: float, g100: float) -> str:
    """Ordered ladder; see the docstring. Deliberately does not use the sub-unit share: a source can
    report whole units without rounding to hundreds, and `fine` should not require fractions."""
    if g1000 >= 0.80:
        return "coarse_1000"
    if g100 >= 0.80:
        return "coarse_100"
    if g100 >= 0.40:
        return "mixed"
    return "fine"


def build(panel: str) -> list[dict]:
    import pandas as pd

    d = pd.read_parquet(panel, columns=["source", "unit", "value", "year", "is_aggregate"])
    d = d[~d.is_aggregate.fillna(False)]
    # ZERO IS EXCLUDED: 0 is a multiple of every grid, so including it inflates every share by the
    # source's zero rate -- which varies 0.4%-6.5% between iia volumes alone (#414).
    d = d[d.value.notna() & (d.value != 0)]

    rows = []
    for (src, unit), g in d.groupby(["source", "unit"], sort=True):
        buckets = [("all", g)]
        cut = ERA_SPLIT.get(src)
        if cut is not None:
            buckets += [(f"pre-{cut}", g[g.year < cut]), (f"{cut}+", g[g.year >= cut])]
        for era, sub in buckets:
            v = sub.value.astype(float)
            if len(v) < MIN_ROWS:
                continue
            whole = v == v.astype(int)
            iv = v[whole].astype("int64")
            g1000 = float((iv % 1000 == 0).sum()) / len(v)
            g100 = float((iv % 100 == 0).sum()) / len(v)
            rows.append({
                "source": src, "unit": unit, "era": era, "n_nonzero": len(v),
                "share_grid_1000": _n(g1000), "share_grid_100": _n(g100),
                "share_subunit": _n(float((~whole).mean())),
                "verdict": classify(g1000, g100),
            })
    rows.sort(key=lambda r: (r["source"], r["unit"], r["era"]))
    return rows


def write(rows: list[dict], path: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--layer-b", default=PANEL_DEFAULT)
    a = ap.parse_args()

    if not os.path.exists(a.layer_b):
        print(f"panel absent ({a.layer_b}); nothing to do", file=sys.stderr)
        return 0
    rows = build(a.layer_b)
    import collections
    by = collections.Counter(r["verdict"] for r in rows)
    print(f"{len(rows)} (source, unit, era) group(s) with at least {MIN_ROWS} non-zero values")
    for v, n in sorted(by.items()):
        print(f"  {v:12} {n}")
    for r in rows:
        print(f"  {r['source']:12}{r['unit']:15}{r['era']:10}n={int(r['n_nonzero']):>6}  "
              f"1000-grid={float(r['share_grid_1000']):>6.1%}  100-grid={float(r['share_grid_100']):>6.1%}"
              f"  sub-unit={float(r['share_subunit']):>5.1%}  {r['verdict']}")

    if a.check:
        if not os.path.exists(OUT):
            print(f"MISSING {OUT}; run with --write", file=sys.stderr)
            return 1
        with open(OUT, newline="") as fh:
            have = list(csv.DictReader(fh))
        want = [{k: str(v) for k, v in r.items()} for r in rows]
        if have != want:
            print(f"STALE {OUT}: {len(have)} row(s) on disk, {len(want)} rebuilt", file=sys.stderr)
            for h, w in zip(have, want):
                if h != w:
                    print(f"  first difference:\n    disk {h}\n    built {w}", file=sys.stderr)
                    break
            return 1
        print(f"OK {os.path.basename(OUT)} matches a fresh rebuild ({len(have)} rows)")
    if a.write:
        write(rows, OUT)
        print(f"wrote {OUT} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
