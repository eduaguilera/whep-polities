#!/usr/bin/env python3
"""Per-row verdicts on iia tobacco/hops production from 1934, the era issue 416 sized.

WHAT THIS SETTLES. Issue 416 established the scope -- 328 production rows from 1934 across 56 labels,
against a pre-1934 median yield of 0.92 t/ha and a 1934+ median of 76.00 -- and said the remedy needs a
PER-ROW test, because a blanket division is not supportable: the yield medians move ~65x, not 100x, and
some 1934+ rows are fine. The test was then done in a comment and never persisted, so the verdicts were
one re-derivation away from being lost. This writes them to tracked state.

THE ZERO-AREA CLASS, AND WHY IT IS FIRST. 50 of the 241 rows that HAVE a paired area row have an area of
exactly 0 against production of 200 to 85,000 tonnes. Their implied yield is INFINITE -- the strongest
evidence any row here carries -- and the obvious way to write this screen loses every one of them:

    if area > 0:  test the yield          # 50 rows fall through to the weaker no-area test

That guard is why the earlier count of "160 impossible_yield" was low. This repo has paid for the same
shape before (issue 420 filtered `area_ha > 0` before a division and dropped 177 infinite-yield cells --
the most impossible cases -- from the tool built to find impossible yields). So zero area is a verdict
here, not a skip.

Those zeros are almost certainly issue 414's defect appearing in the AREA series: `iia_1938_39` reads
blank cells as 0, and its window is exactly this era. That is an interaction between two open defects
rather than a coincidence -- a false-zero area disables the yield test for the production row beside it --
and it is recorded per row so the two remedies can be sequenced (issue 433 maps them).

THE CLASSES, strongest evidence first:

  impossible_yield_zero_area  production > 0 on an area of exactly 0. Infinite yield.
  impossible_yield            paired area > 0 and implied yield > 20 t/ha. Tobacco leaf runs 1-3 t/ha
                              and hops similar, so 20 is an order of magnitude above the crop's ceiling
                              rather than a fitted threshold.
  no_area_level_shift         no paired area, but the row is >= 30x the label's OWN pre-1934 median for
                              that item. Weaker than a yield test -- it assumes the label's own history
                              is the right baseline -- but it needs no area, which is what makes the 87
                              unpaired rows reachable at all.
  high_yield_3to20            elevated and not impossible. NOT convicted: a 5 t/ha tobacco yield is
                              wrong for a field but not arithmetically impossible, and calling it a
                              defect would be the magnitude argument this repo has been burned by.
  plausible_yield             <= 3 t/ha. The row is fine.
  no_area_level_consistent    no area, has a pre-1934 baseline, and sits within it.
  untestable                  no area and no pre-1934 baseline for the label+item. Counted, never
                              convicted -- an untestable row is not an innocent one, and saying so is
                              the difference between this table and a correction list.

WHAT THIS DOES NOT DO. It does not write corrections and it does not name a factor per row. The implied
factors run 21x to 293x with a median of 68x, so no single divisor fits, and `yield_series_corrections.csv`
remains the place a repair is proposed with its anchor. This is the evidence a repair would rest on.

Usage:
  python3 pipelines/polity-autoimprove/29_era_shift_verdicts.py            # report only
  python3 pipelines/polity-autoimprove/29_era_shift_verdicts.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/29_era_shift_verdicts.py --check    # fail if stale
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
OUT = os.path.join(STATE, "era_shift_verdicts.csv")
MATCHED = os.path.join(STATE, "matched_rows.parquet")

SOURCE = "iia"
ITEMS = ("hops", "tobacco, unmanufactured")
ERA_FROM = 1934                 # the boundary issue 414 explains: the last year two volumes cover is 1933
IMPOSSIBLE_YIELD = 20.0         # t/ha; an order of magnitude above the crop's ceiling, not a fitted value
HIGH_YIELD = 3.0
LEVEL_SHIFT = 30.0              # x the label's own pre-era median

FIELDS = ("source", "label", "whep_code", "item", "year", "unit", "production", "area_ha",
          "implied_yield", "own_pre_era_median", "ratio_to_own", "verdict", "convicted")

CONVICTING = {"impossible_yield_zero_area", "impossible_yield", "no_area_level_shift"}


def _n(x, nd=6):
    if x is None:
        return ""
    f = float(x)
    return str(int(f)) if f == int(f) and abs(f) < 1e15 else repr(round(f, nd))


def build(matched: str) -> list[dict]:
    import pandas as pd

    d = pd.read_parquet(matched)
    t = d[d.source.eq(SOURCE) & d.item.isin(ITEMS)]
    prod = t[t.unit.eq("tonnes")].dropna(subset=["year"])
    area = t[t.unit.eq("ha")].dropna(subset=["year"])
    key = ["country", "item", "year"]
    # median where a group holds several rows: this screen is about the ERA, not about within-group
    # duplication, which state/collapse_groups.csv covers separately.
    a = area.groupby(key).value.median()
    base = prod[prod.year <= ERA_FROM - 1].groupby(["country", "item"]).value.median()

    rows = []
    for r in prod[prod.year >= ERA_FROM].itertuples():
        k = (r.country, r.item, r.year)
        ar = a.get(k)
        bs = base.get((r.country, r.item))
        yld = None
        if ar is not None and float(ar) > 0:
            yld = float(r.value) / float(ar)
        ratio = (float(r.value) / float(bs)) if bs is not None and float(bs) > 0 else None

        if ar is not None and float(ar) == 0.0 and float(r.value) > 0:
            v = "impossible_yield_zero_area"
        elif yld is not None and yld > IMPOSSIBLE_YIELD:
            v = "impossible_yield"
        elif yld is not None and yld > HIGH_YIELD:
            v = "high_yield_3to20"
        elif yld is not None:
            v = "plausible_yield"
        elif ratio is not None and ratio >= LEVEL_SHIFT:
            v = "no_area_level_shift"
        elif ratio is not None:
            v = "no_area_level_consistent"
        else:
            v = "untestable"

        rows.append({
            "source": SOURCE, "label": r.country, "whep_code": r.whep_code, "item": r.item,
            "year": int(r.year), "unit": r.unit, "production": _n(r.value),
            "area_ha": ("" if ar is None else _n(ar)),
            "implied_yield": ("" if yld is None else _n(yld)),
            "own_pre_era_median": ("" if bs is None else _n(bs)),
            "ratio_to_own": ("" if ratio is None else _n(ratio)),
            "verdict": v, "convicted": str(v in CONVICTING),
        })
    rows.sort(key=lambda r: (r["verdict"], r["label"], r["item"], r["year"]))
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
    args = ap.parse_args()

    if not os.path.exists(args.matched):
        print(f"panel absent ({args.matched}); nothing to do", file=sys.stderr)
        return 0

    rows = build(args.matched)
    order = ("impossible_yield_zero_area", "impossible_yield", "no_area_level_shift",
             "high_yield_3to20", "plausible_yield", "no_area_level_consistent", "untestable")
    vc = {k: sum(1 for r in rows if r["verdict"] == k) for k in order}
    conv = sum(1 for r in rows if r["convicted"] == "True")
    print(f"{len(rows)} {SOURCE} tobacco/hops production row(s) from {ERA_FROM}, "
          f"{len({r['label'] for r in rows})} label(s)")
    for k in order:
        mark = "  <- convicted" if k in CONVICTING else ""
        print(f"  {k:28} {vc[k]:4}{mark}")
    print(f"convicted on the row's own evidence: {conv} of {len(rows)} "
          f"({100.0 * conv / len(rows):.0f}%)")

    if args.check:
        if not os.path.exists(OUT):
            print(f"MISSING {os.path.relpath(OUT, REPO)}", file=sys.stderr)
            return 1
        with open(OUT, newline="") as fh:
            have = list(csv.DictReader(fh))
        if have != [{k: str(v) for k, v in r.items()} for r in rows]:
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
