#!/usr/bin/env python3
"""Published zeros that the REPORTING GRID cannot distinguish from a small positive value (issue 446).

THE MECHANISM. A source that reports on a 1000-grid cannot express 400. It rounds to 0, and a 0 in the
panel is indistinguishable from "reported none". Issue 446 measured the grid as a precision problem --
a value carrying +/-50 presented as a point -- but at the bottom of the range it stops being a
precision problem and becomes a CATEGORICAL one: the sign changes. A consumer averaging the series
takes those zeros as real, and #446's `.prepare_historical_production()` mean pulls straight down.

THE DISCRIMINATOR IS `min_nonzero == grid`, and it is what makes this narrow enough to be useful.
Being on a coarse grid is not itself suspicious: a series of 500,000-tonne wheat harvests on a
1000-grid has a rounding error of 0.1% and its zeros mean what they say. The zeros are ambiguous only
where the series' SMALLEST OBSERVED VALUE IS THE GRID STEP ITSELF -- that is, the quantity lives at the
grid's resolution floor, so the step below the smallest observation is zero and everything from 1 to
half a step lands there.

    layer B non-aggregate zeros                                    1,017
      in a series whose non-zero values are all on a 100/1000 grid    227
      ...and whose smallest non-zero value IS the grid step           201    <- this file

EVERY INSTANCE IS A MINOR COMMODITY IN A SMALL TERRITORY, which is the check that the criterion
selects a real class rather than an arbitrary slice. On the `juan` side: goats, asses, mules and
hinnies, geese, ducks, turkeys, swine -- in Iceland, Switzerland, Czechoslovakia, Austria, Luxembourg.
On the `iia` side: lemons and limes, grapefruit, dry beans, groundnuts, sesame -- in Algeria, Zambia,
Cyprus, Saint Vincent, Jordan, Eritrea, Somalia, Serbia, Kenya, Dominica. Nothing else appears. The
extreme case is `juan iceland goats`, whose 103 observations have a vocabulary of exactly
{0, 1000, 2000} with 69 zeros.

WHAT IS CLAIMED, AND WHAT IS NOT. The claim is that these zeros are UNINFORMATIVE -- in a series whose
observed range is {0, 1000}, a zero says nothing about whether the true value was 0 or 400. It is NOT
claimed that any particular one is non-zero; that would need a source outside the panel. This file
therefore records no verdict and proposes no repair, because the remedy is #446's open schema question
(a precision column, or a per-(source, unit) grid table) and not something to decide here.

THIS IS A DIFFERENT POPULATION FROM #414's FALSE ZEROS, and conflating them would apply the wrong fix
to both. #414's are an EXTRACTION artefact -- a blank yearbook cell read as 0, upstream, concentrated
in `iia_1938_39` -- and their remedy is to restore the blank. These are a ROUNDING artefact of the
reporting step, and their remedy is to publish the step. The 171 `juan` zeros here cannot belong to
#414 at all, since it is a defect of one IIA volume.

FOUND FROM THE OTHER END. Eight of the zero-collapses in `series_collapses.csv` are `juan` rows sitting
beside a neighbour of exactly 1000 -- this class surfacing in a detector built to find something else.

Usage:
  python3 pipelines/polity-autoimprove/32_grid_ambiguous_zeros.py            # report only
  python3 pipelines/polity-autoimprove/32_grid_ambiguous_zeros.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/32_grid_ambiguous_zeros.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "grid_ambiguous_zeros.csv")
MATCHED = os.path.join(STATE, "matched_rows.parquet")

# Coarsest first: a series on a 1000-grid is also on a 100-grid, and the 1000 is the operative step.
GRIDS = (1000.0, 100.0)
# Fewer non-zero values than this and "all of them are on a grid" is a coincidence, not a convention.
# Three is deliberately low because the criterion carries a second, independent condition
# (min_nonzero == grid) that a bare grid test does not.
MIN_NONZERO = 3

FIELDS = ("source", "country", "item", "unit", "indicator", "grid", "zeros", "zeros_dated",
          "zeros_undated", "n_nonzero", "min_nonzero", "max_nonzero", "distinct_nonzero",
          "zero_share", "zero_years")


def _n(x, nd=4):
    f = float(x)
    return str(int(f)) if f == int(f) and abs(f) < 1e15 else repr(round(f, nd))


def build(matched: str) -> list[dict]:
    import pandas as pd

    d = pd.read_parquet(matched)
    d = d[d.value.notna() & d.country.notna()]
    rows = []
    keys = ["source", "country", "item", "unit", "indicator"]
    for k, g in d.groupby(keys, dropna=False, sort=True):
        nz = g.value[g.value > 0]
        n_zero = int((g.value == 0).sum())
        if n_zero == 0 or len(nz) < MIN_NONZERO:
            continue
        for grid in GRIDS:
            if not (nz % grid == 0).all():
                continue
            # THE DISCRIMINATOR: the quantity must live at the grid's resolution floor. A series whose
            # smallest observation is many steps above zero has no rounding path to zero.
            if float(nz.min()) != grid:
                break
            zr = g[g.value == 0]
            yrs = sorted(int(y) for y in zr.year.dropna().unique())
            # SPLIT DATED FROM UNDATED, because they are not equally exposed. A zero on a `period`
            # row (`1928-1932`) never reaches the R package: `build.R` filters `!is.na(year)` and
            # carries no period column, so `zeros_undated` is latent and `zeros_dated` is what a
            # consumer can actually average. The first version of this file listed only dated years
            # and still counted all of them, so four rows had a `zero_years` list shorter than their
            # own `zeros` with nothing to explain the gap -- the undated ones had been dropped
            # silently by a `.dropna()`. Both halves are now named.
            n_undated = int(zr.year.isna().sum())
            rows.append({
                "source": k[0], "country": k[1], "item": k[2], "unit": k[3],
                "indicator": ("" if k[4] is None or str(k[4]) == "nan" else str(k[4])),
                "grid": _n(grid), "zeros": n_zero,
                "zeros_dated": n_zero - n_undated, "zeros_undated": n_undated,
                "n_nonzero": len(nz),
                "min_nonzero": _n(nz.min()), "max_nonzero": _n(nz.max()),
                "distinct_nonzero": int(nz.nunique()),
                "zero_share": _n(n_zero / (n_zero + len(nz))),
                "zero_years": ";".join(str(y) for y in yrs),
            })
            break
    rows.sort(key=lambda r: (-int(r["zeros"]), r["source"], str(r["country"]), str(r["item"])))
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
    ap.add_argument("--matched", default=MATCHED)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.matched):
        print(f"panel absent ({a.matched}); nothing to do", file=sys.stderr)
        return 0

    rows = build(a.matched)
    tz = sum(int(r["zeros"]) for r in rows)
    td = sum(int(r["zeros_dated"]) for r in rows)
    print(f"{tz} published zero(s) ({td} dated, {tz - td} on period rows the R package drops) "
          f"in {len(rows)} series cannot be distinguished from a value below "
          f"half the reporting step (floor: {MIN_NONZERO} non-zero values, all on the grid, "
          f"smallest equal to the step)")
    by = {}
    for r in rows:
        by.setdefault((r["source"], r["unit"]), [0, 0])
        by[(r["source"], r["unit"])][0] += int(r["zeros"])
        by[(r["source"], r["unit"])][1] += 1
    for (src, unit), (z, n) in sorted(by.items(), key=lambda kv: -kv[1][0]):
        print(f"  {src:9} {unit:7} {z:>4} zero(s) in {n:>2} series")
    for r in rows[:10]:
        print(f"  {r['source']:9} {str(r['country'])[:15]:16} {str(r['item'])[:26]:27} "
              f"{r['unit']:7} grid={r['grid']:>5} zeros={r['zeros']:>3} "
              f"nonzero={r['n_nonzero']:>3} range {r['min_nonzero']}-{r['max_nonzero']}")

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
