#!/usr/bin/env python3
"""Which of the IIA extract's production/area zeros can the volume's own REPORTING GRID produce,
and which are refuted by the other half of their own cell (issue 414).

WHAT THIS SETTLES, AND WHY IT NEEDED A NEW TEST. Issue 414 established that `iia_1938_39` holds 940
of the extract's 1,102 production/area zeros -- a 6.45% zero rate against 0.10-0.82% in every other
volume -- and that 83 of them are contradicted by a second volume printing a real value for the same
cell. #531 then split those 83 by whether the late volume's grid could round the contradicting value
to zero, and 76 could. That analysis reaches 83 cells because a second volume covers only 1933; the
other ~690 zeros had no test at all.

THIS FILE TESTS EVERY DATED ZERO, and the discriminator is INSIDE the cell rather than across
volumes: a zero AREA sits beside a production figure, and a zero PRODUCTION beside an area. If the
zero is the grid's rounding of a sub-grid value, the true quantity is below half a grid step, and
that puts an arithmetic BOUND on the implied yield:

    zero area       ->  yield > production / (area_grid / 2)      a MINIMUM implied yield
    zero production ->  yield < (prod_grid / 2) / area            a MAXIMUM implied yield

When that bound falls outside the volume's own observed yield range for the same product by an order
of magnitude, a sub-grid value cannot produce the pair and the zero is not a rounding.

THE TEST IS SCALE-INVARIANT BY CONSTRUCTION, which is what makes it usable here at all. The
reference yield is measured on the SAME VOLUME and the SAME PRODUCT, so a uniform per-item scale
error cancels in the ratio. That matters because #416's x100 tobacco and hops inflation lives in
exactly these volumes: `iia_1938_39` reports a median tobacco yield of 90 t/ha and `iia_1939_45` of
82.6 t/ha, both about a hundred times a real one, and a test against an external yield would flag
every tobacco cell in the source. Against the volume's own distribution, tobacco cells are ordinary
-- and the three that do fire (`british uganda`, 1942-1944) are 3,000x outside a band that is itself
inflated, so they survive any scale reading.

THE HEADLINE IS A NEGATIVE RESULT. `iia_1938_39` -- the volume this issue is named after -- holds 278
of the 291 testable cells, and NOT ONE of them is refuted:

    grid_can_explain              253    an area below 500 ha fits the tonnage beside it
    no_product_reference           23    all 23 are citrus, see below
    paired_value_is_the_outlier     2    the PRODUCTION is wrong, not the zero
    refuted_by_paired_axis          0

The two that fire are both the production side: `french guadeloupe` cottonseed 1934 at 3.88 Mt
(already pinned as an isolated spike) and `british antigua` cottonseed 1934 at 14,400 t against a
series whose own median in the same volume is 200 t. Neither says anything about its area.

The 23 without a reference are every one of them citrus -- `citrus fruits: other`, `: limes`,
`: sweet limes`, `: lemons, other` -- products with fewer than 8 paired cells in the volume. They are
left unadjudicated rather than folded in, but they are not hiding a refutation: their implied minimum
yields run 0.2-14.2 t/ha and the volume's own `citrus fruits: lemons` band is 5.5-18.1, so borrowing
a sibling citrus reference would place all 23 inside it.

That is the strongest evidence yet that the volume's zeros are mostly a RESOLUTION FLOOR (#446) and
not blank cells. Two structural measurements point the same way:

    non-zero HECTARE values in iia_1938_39 on a 1000-grid    4,632 of 4,634 = 99.96%
    non-zero TONNE values on a 100-grid                      8,314 of 8,991 = 92.47%
    ...against 3.6%-19.0% (ha) in the four earlier volumes

(The two hectare exceptions are period-average rows, `british jamaica` cacao and `poland` hops.)

A volume that cannot express 1,700 ha except as 2,000 cannot express 400 ha except as 0. And 586 of
its 732 dated zeros (80%) sit in a series that is zero in EVERY year the volume covers, which is what
a permanently sub-grid quantity looks like -- 138 series, mostly minor crops in small territories.

WHAT IT DOES CONFIRM is 11 cells, all in the OTHER coarse volume:

    british nigeria     cotton: ginned  area        1939-1944   6 cells    17x-78x outside
    french equatorial   cotton: ginned  area        1939        1 cell     52x
    dominican republic  tobacco         area        1939        1 cell     12x
    british uganda      tobacco         production  1942-1944   3 cells   1985x-3308x

`british nigeria`'s row is the whole series: seven zeros of seven, area never once positive, against
2,900-13,300 t of lint every year -- registered as `nga-1941-1945-cotton-area-zero` on the cotton-seed
tonnage beside it, and widened to 1939-1940 here on the lint's own.

THE FOUR FINE-GRID VOLUMES CONTRIBUTE NOTHING TESTABLE, which is worth saying because it is not a
null finding about them: of their 83 dated production/area zeros, not one has a positive value on the
other axis. Their zeros are `fertilizers: phosphate, natural` and similar single-axis series, so the
paired-axis test has no purchase there and their zeros stay unadjudicated by any method here.

A TEST THAT LOOKED DECISIVE AND IS NOT, recorded so nobody rebuilds it. The obvious alternative is
to compare a zero against the volume's OWN period-average row for the same series -- same volume,
same grid, no scale confound. It fires on 30 series (105 zero-years), and its top hit is a trap:

    new zealand  fertilizers: phosphate, natural  production   iia_1929_30
      1921-1925 period average  11,176 t      1926: 0     1927: 0

That reads as a 112-step contradiction. But the same series runs 3,178 -> 2,421 -> 1,600 in
1922-1924 and the 11,176 is a STALE FIGURE -- it is the 1909-1913 average from `iia_1925_26`,
re-printed under a later period label. The zeros are the end of a monotone decline, i.e. a mine
running out, and they are probably right. A period average is not evidence about a particular year
when the series is trending, so the period test is reported by this tool and never used to confirm.

The same caution applies to the trailing-edge class it finds -- `estonia` cow milk 1944 = 0 beside a
1934-1938 average of 1.65 Mt, `latvia` factory cheese 1940, `total general including the ussr`
linseed area 1943-1945 = 0 against a 7.68 M ha average. Those zeros are wrong as PUBLISHED VALUES,
because layer B carries them as output of nil, but "not separately reported under occupation" and
"blank cell read as 0" are not distinguishable from the numbers, and both differ from a rounding.

Usage:
  python3 pipelines/polity-autoimprove/40_zero_grid_floor.py [--raw PATH]
  python3 pipelines/polity-autoimprove/40_zero_grid_floor.py --write
  python3 pipelines/polity-autoimprove/40_zero_grid_floor.py --check
"""
from __future__ import annotations

import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "zero_grid_floor.csv")
DEFAULT_RAW = os.path.expanduser(os.environ.get(
    "WHEP_IIA_RAW",
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx"))

# Candidate reporting steps, coarsest first. 0.1 is the finest because the extract carries one
# decimal at most on production.
GRIDS = (1000.0, 100.0, 10.0, 1.0, 0.1)
# A volume+unit is "on" a step when this share of its non-zero values are multiples of it. 0.85 is
# well clear of both regimes measured: the coarse volumes sit at 0.92-1.00 and the fine ones at
# 0.04-0.30, so nothing lands near the boundary and the choice carries no weight.
GRID_SHARE = 0.85
# An order of magnitude outside the product's own 10th-90th percentile yield band. Deliberately not
# tuned: at 3x the set grows by 4 cells that are all within a factor of 3 of an ordinary yield, and
# at 30x it loses `british nigeria`'s two smallest years. 10 is the round choice, and the confirmed
# cells clear it by 9x-3000x rather than sitting on it.
FACTOR = 10.0
# Fewer paired cells than this and the product's yield band is not a distribution.
MIN_REF = 8
# A paired value this far above its own series' median is the likelier defect, so the zero beside it
# is NOT adjudicated: the yield identity says one of the two is wrong, not which.
OUTLIER = 10.0
# Positives needed before a series has a median worth comparing against.
MIN_SERIES = 4

FIELDS = ("volume", "country", "product", "variable", "unit", "year", "grid", "verdict",
          "paired_variable", "paired_value", "implied_yield_bound", "ref_p10", "ref_p90", "ref_n",
          "factor_outside", "paired_vs_series_median", "series_zeros", "series_positives")


def _n(x, nd=4):
    f = float(x)
    return str(int(f)) if f == int(f) and abs(f) < 1e15 else repr(round(f, nd))


def _coarsest(v):
    import numpy as np
    for step in GRIDS:
        r = np.mod(v, step)
        if float((np.isclose(r, 0.0) | np.isclose(r, step)).mean()) >= GRID_SHARE:
            return step
    return GRIDS[-1]


def measure_grids(pa):
    """Coarsest step that GRID_SHARE of the non-zero values are multiples of, PER PRODUCT.

    Per product and not merely per (volume, unit), because the step is not uniform inside a volume
    and assuming it was would have overstated every bound. `iia_1939_45` reports hectares on a
    1000-grid for 6,083 of its 6,311 values -- but `hops` and `rubber` areas on a 100-grid, which is
    228 of the 228 exceptions. On the tonnage side `eggs`, `tea` and `wine` are finer still
    (`british malta` eggs are printed as 3,611.3 t in a volume where 92% of tonnages are round
    hundreds).

    A finer product step makes this test STRICTER, not looser -- half a step is the largest value
    that can round to zero, so the implied-yield bound tightens -- so the fallback to the volume-wide
    step for a product with too few values is the conservative direction.

    Returns (by_product, by_unit): keys (volume, unit, product) and (volume, unit).
    """
    nz = pa[pa.value != 0]
    by_unit = {k: _coarsest(g.value.to_numpy(dtype=float))
               for k, g in nz.groupby(["yearbook", "unit"])}
    by_product = {k: _coarsest(g.value.to_numpy(dtype=float))
                  for k, g in nz.groupby(["yearbook", "unit", "_p"]) if len(g) >= MIN_REF}
    return by_product, by_unit


def build(raw_path: str) -> list[dict]:
    import numpy as np
    import pandas as pd

    raw = pd.read_excel(raw_path)
    raw = raw.assign(_c=raw["country"].astype(str).str.strip().str.lower(),
                     _p=raw["product"].astype(str).str.strip().str.lower(),
                     _v=raw["variable"].astype(str).str.lower(),
                     _y=pd.to_numeric(raw["year"], errors="coerce"))
    pa = raw[raw["_v"].isin(("production", "area")) & raw["value"].notna()].copy()
    gprod, gunit = measure_grids(pa)
    dated = pa[pa["_y"].notna()].copy()
    dated["_y"] = dated["_y"].astype(int)

    # A series' median, for the outlier guard on the paired value. KEYED ON THE VOLUME, not on the
    # whole extract: `dominican republic` tobacco production runs 4,175-22,700 t up to 1932 and
    # 313,500-1,864,000 t from 1933, which is #416's x100 era boundary inside one series. Against the
    # extract-wide median of 15,808 its ordinary 1939 value of 871,400 reads as a 55x outlier and the
    # guard fires on a cell that is perfectly in line with its own volume. Against the volume's own
    # median it is 0.6x. Falls back to the extract when a volume carries too few positives to have a
    # median of its own.
    vmed = (pa[pa.value > 0].groupby(["yearbook", "_c", "_p", "_v"]).value
            .agg(["median", "size"]).rename(columns={"median": "m", "size": "n"}))
    smed = (pa[pa.value > 0].groupby(["_c", "_p", "_v"]).value
            .agg(["median", "size"]).rename(columns={"median": "m", "size": "n"}))

    rows = []
    def grid_for(vol, unit, product):
        return gprod.get((vol, unit, product), gunit.get((vol, unit), GRIDS[-1]))

    for vol, v in dated.groupby("yearbook", sort=True):
        area = v[v["_v"] == "area"].groupby(["_c", "_p", "_y"]).value.max()
        prod = v[v["_v"] == "production"].groupby(["_c", "_p", "_y"]).value.max()
        j = pd.concat({"area": area, "prod": prod}, axis=1).reset_index()
        both = j[(j["area"] > 0) & (j["prod"] > 0)].copy()
        both["_yield"] = both["prod"] / both["area"]
        ref = both.groupby("_p")["_yield"].agg(
            n="size", p10=lambda s: float(np.percentile(s, 10)),
            p90=lambda s: float(np.percentile(s, 90)))
        # per-series zero/positive census within the volume, for context on every emitted row
        cen = {}
        for (c, p, vv, u), g in v.groupby(["_c", "_p", "_v", "unit"]):
            byy = {}
            for y, val in zip(g["_y"], g["value"]):
                byy[y] = max(byy.get(y, -1.0), float(val))
            cen[(c, p, vv, u)] = (sum(1 for y in byy if byy[y] == 0),
                                  sum(1 for y in byy if byy[y] > 0))

        for r in j.itertuples():
            for zero_var, paired_var, zv, pv, grid, unit in (
                    ("area", "production", r.area, r.prod, grid_for(vol, "hectares", r._2), "hectares"),
                    ("production", "area", r.prod, r.area, grid_for(vol, "tonnes", r._2), "tonnes")):
                if not (zv == 0 and pv is not None and pv == pv and pv > 0):
                    continue
                if r._2 not in ref.index or int(ref.at[r._2, "n"]) < MIN_REF:
                    verdict, bound, p10, p90, refn, fac = "no_product_reference", None, None, None, 0, None
                else:
                    p10 = float(ref.at[r._2, "p10"])
                    p90 = float(ref.at[r._2, "p90"])
                    refn = int(ref.at[r._2, "n"])
                    if zero_var == "area":
                        bound = float(pv) / (grid / 2.0)       # implied MINIMUM yield
                        fac = bound / p90 if p90 > 0 else float("inf")
                    else:
                        bound = (grid / 2.0) / float(pv)       # implied MAXIMUM yield
                        fac = (p10 / bound) if bound > 0 else float("inf")
                    verdict = "refuted_by_paired_axis" if fac > FACTOR else "grid_can_explain"
                key = (r._1, r._2, paired_var)
                ratio, m = None, None
                if (vol,) + key in vmed.index and int(vmed.at[(vol,) + key, "n"]) >= MIN_SERIES:
                    m = float(vmed.at[(vol,) + key, "m"])
                elif key in smed.index and int(smed.at[key, "n"]) >= MIN_SERIES:
                    m = float(smed.at[key, "m"])
                if m is not None and m > 0:
                    ratio = float(pv) / m
                    if verdict == "refuted_by_paired_axis" and ratio > OUTLIER:
                        verdict = "paired_value_is_the_outlier"
                nz, np_ = cen.get((r._1, r._2, zero_var, unit), (0, 0))
                rows.append({
                    "volume": vol, "country": r._1, "product": r._2, "variable": zero_var,
                    "unit": unit, "year": int(r._3), "grid": _n(grid), "verdict": verdict,
                    "paired_variable": paired_var, "paired_value": _n(pv),
                    "implied_yield_bound": "" if bound is None else _n(bound),
                    "ref_p10": "" if p10 is None else _n(p10),
                    "ref_p90": "" if p90 is None else _n(p90), "ref_n": refn,
                    "factor_outside": "" if fac is None else _n(fac),
                    "paired_vs_series_median": "" if ratio is None else _n(ratio),
                    "series_zeros": nz, "series_positives": np_})
    order = {"refuted_by_paired_axis": 0, "paired_value_is_the_outlier": 1,
             "no_product_reference": 2, "grid_can_explain": 3}
    rows.sort(key=lambda r: (order[r["verdict"]],
                             -float(r["factor_outside"] or 0), r["volume"], r["country"],
                             r["product"], r["variable"], r["year"]))
    return rows


def report(rows):
    import collections
    by = collections.Counter(r["verdict"] for r in rows)
    print(f"{len(rows)} dated production/area ZERO cell(s) in the IIA extract that carry a positive "
          f"value on the other axis")
    for k in ("refuted_by_paired_axis", "paired_value_is_the_outlier", "grid_can_explain",
              "no_product_reference"):
        print(f"  {k:30}{by[k]:5}")
    per = collections.Counter((r["volume"], r["verdict"]) for r in rows)
    print("\n  by volume:")
    for vol in sorted({r["volume"] for r in rows}):
        print(f"    {vol:14}refuted {per[(vol,'refuted_by_paired_axis')]:3}   "
              f"paired-value outlier {per[(vol,'paired_value_is_the_outlier')]:3}   "
              f"grid can explain {per[(vol,'grid_can_explain')]:4}   "
              f"no reference {per[(vol,'no_product_reference')]:3}")
    print("\n  the refuted cells, and the paired-value outliers beside them:")
    for r in rows:
        if r["verdict"] not in ("refuted_by_paired_axis", "paired_value_is_the_outlier"):
            continue
        print(f"    {r['volume']:12}{r['country'][:26]:28}{r['product'][:16]:18}"
              f"{r['variable'][:10]:11}{r['year']}  {r['variable']}=0 vs "
              f"{r['paired_variable']}={float(r['paired_value']):,.1f}  implied yield "
              f"{float(r['implied_yield_bound']):>10,.3f}  band "
              f"{float(r['ref_p10']):.3f}-{float(r['ref_p90']):.3f}  "
              f"{float(r['factor_outside']):>8,.1f}x outside"
              + ("" if r["verdict"] == "refuted_by_paired_axis"
                 else f"  -- BUT the paired value is {float(r['paired_vs_series_median']):,.0f}x its "
                      f"own series median, so the zero is not adjudicated"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=DEFAULT_RAW)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.raw):
        print(f"SKIP: {a.raw} not present on this machine", file=sys.stderr)
        return 0
    rows = build(a.raw)
    report(rows)

    if a.check:
        if not os.path.exists(OUT):
            print(f"MISSING {OUT}; run with --write", file=sys.stderr)
            return 1
        with open(OUT, newline="", encoding="utf-8") as fh:
            have = list(csv.DictReader(fh))
        want = [{k: str(v) for k, v in r.items()} for r in rows]
        if have != want:
            print(f"STALE {OUT}: {len(have)} row(s) on disk, {len(want)} rebuilt", file=sys.stderr)
            for h, w in zip(have, want):
                if h != w:
                    print(f"  first difference:\n    disk  {h}\n    built {w}", file=sys.stderr)
                    break
            return 1
        print(f"\nOK {os.path.basename(OUT)} matches a fresh rebuild ({len(have)} rows)")
    if a.write:
        from atomic import write_csv_atomic
        write_csv_atomic(OUT, FIELDS, rows)
        print(f"\nwrote {OUT} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    raise SystemExit(main())
