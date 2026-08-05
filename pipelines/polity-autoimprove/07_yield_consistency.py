#!/usr/bin/env python3
"""Internal-consistency check and repair table for area-and-production pairs.

Issue 29 asked which OTHER series carry arithmetic we are not exploiting, after
06_landuse_consistency.py showed what a self-checking series buys: 39 detectable bad
blocks, 14 of them recoverable, with no distributional assumption.

The answer is area x yield. Wherever a source reports BOTH a harvested area (ha) and a
production (tonnes) for the same (source, country, item, year), the implied yield
production / area is fully determined -- and yield has hard PHYSICAL bounds. No crop
yields 100,000 tonnes per hectare and none yields 0.0002. So an implausible ratio proves
that one of the two cells is wrong, without needing to know which is unusual for its
distribution.

That is strictly stronger than 05_magnitude_screen.py's outlier test, for the same reason
06 is: it compares a value against a physical constant rather than against its neighbours.

RECOVERABILITY. Most detections are powers of ten, which is what a dropped decimal point
or a "1000 tonnes" column labelled "tonnes" looks like:

  Russian Federation rye 1931   27,600,000 ha and 21,990 t  ->  0.0008 t/ha
                                rye yields ~1 t/ha, so production is ~1000x low --
                                it is thousands of tonnes labelled tonnes
  Somalia bananas 1949               3,000 ha and 301,263,000 t  ->  100,421 t/ha
  Ghana cotton lint 1915-1918   14,000-20,000 ha and 18 t  ->  ~0.001 t/ha
  China sesame seed 1930-33         64-126 ha and 31,888-116,299 t

For each, the OTHER cell plus a plausible yield says which one moved and by how much,
so this table proposes a correction rather than only a flag.

WHAT IT DOES NOT DO. It does not decide that a merely high yield is wrong. The bounds are
set where physics ends, not where a distribution thins: sugarcane genuinely exceeds
100 t/ha and some fodder crops more, so the ceiling is deliberately far above any real
crop. A tighter bound would need per-item knowledge and would start guessing.

Like 06, this does NOT modify the source parquet (it lives outside the repo, in the
maintainer's own store). It writes a correction table so the fix lands upstream in the
consolidation step, where it belongs.

Usage:
  python3 pipelines/polity-autoimprove/07_yield_consistency.py [--hi 200] [--lo 0.01]
Writes state/yield_corrections.csv
"""
import argparse
import os
import warnings

import pandas as pd

import extdata

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H = os.path.join(REPO, "pipelines/polity-autoimprove/state")
# Paths, schema assertions and the unit maps live in extdata.py, so a rename upstream
# raises here instead of quietly yielding an empty result. Six analyses in one session
# were wrong that way; see that module's docstring.
LAYER_B = extdata.LAYER_B
AREA_UNITS = extdata.AREA_UNITS
PROD_UNITS = extdata.PROD_UNITS

# Physical ceiling and floor on t/ha. Sugarcane reaches ~150 and a few fodder crops more,
# so 200 is above every real crop rather than at the edge of a distribution.
HI_DEFAULT = 200.0
LO_DEFAULT = 0.01


def nearest_power_of_ten(ratio: float) -> int:
    """How many orders of magnitude a cell is out by, to the nearest power of ten."""
    import math
    if ratio <= 0:
        return 0
    return int(round(math.log10(ratio)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hi", type=float, default=HI_DEFAULT)
    ap.add_argument("--lo", type=float, default=LO_DEFAULT)
    A = ap.parse_args()

    if not os.path.exists(LAYER_B):
        print(f"SKIP: {LAYER_B} not present (it lives outside the repo)")
        return 0

    # Asserts layer B's documented columns; raises rather than returning an empty frame.
    d = extdata.load_layer_b()
    # And assert the unit spellings this whole check depends on actually occur. Without
    # this, an upstream change from "ha" to "hectare" would report zero paired
    # observations and a clean pass.
    extdata.require_any_value(d, "unit", ["ha", "tonnes"], "layer B units")
    d = d[d["value"].notna() & d["year"].notna()].copy()
    d["u"] = d["unit"].astype(str).str.lower()

    d["af"] = d["u"].map(AREA_UNITS)
    d["pf"] = d["u"].map(PROD_UNITS)
    key = ["source", "country", "item", "year"]

    area = d[d["af"].notna()].copy()
    area["area_ha"] = area["value"] * area["af"]
    area = area.groupby(key, dropna=False)["area_ha"].sum().reset_index()

    prod = d[d["pf"].notna()].copy()
    prod["prod_t"] = prod["value"] * prod["pf"]
    prod = prod.groupby(key, dropna=False)["prod_t"].sum().reset_index()

    m = area.merge(prod, on=key, how="inner")
    m = m[(m["area_ha"] > 0) & (m["prod_t"] > 0)].copy()
    m["yield_t_ha"] = m["prod_t"] / m["area_ha"]

    # A per-item reference yield, taken as the MEDIAN of that item's own plausible
    # observations. Using the item's own data rather than an external table keeps this
    # source-agnostic, and the median is unaffected by the outliers being detected.
    ok = m[(m["yield_t_ha"] <= A.hi) & (m["yield_t_ha"] >= A.lo)]
    ref = ok.groupby("item")["yield_t_ha"].median().rename("ref_yield")
    m = m.join(ref, on="item")

    bad = m[(m["yield_t_ha"] > A.hi) | (m["yield_t_ha"] < A.lo)].copy()
    bad["ratio_to_ref"] = bad["yield_t_ha"] / bad["ref_yield"]
    bad["orders_out"] = bad["ratio_to_ref"].map(nearest_power_of_ten)
    # If production is the cell that moved, the repaired value is area x reference yield.
    # If area moved, it is production / reference yield. Both are offered: which one is
    # right is a source-document question, and this table says what each would imply.
    bad["prod_t_if_area_ok"] = bad["area_ha"] * bad["ref_yield"]
    bad["area_ha_if_prod_ok"] = bad["prod_t"] / bad["ref_yield"]
    bad["looks_like_power_of_ten"] = (
        bad["ratio_to_ref"].notna()
        & (abs(bad["ratio_to_ref"] / (10.0 ** bad["orders_out"]) - 1.0) < 0.5)
        & (bad["orders_out"] != 0)
    )

    cols = ["source", "country", "item", "year", "area_ha", "prod_t", "yield_t_ha",
            "ref_yield", "ratio_to_ref", "orders_out", "looks_like_power_of_ten",
            "prod_t_if_area_ok", "area_ha_if_prod_ok"]
    out = bad[cols].sort_values("yield_t_ha", ascending=False)
    os.makedirs(H, exist_ok=True)
    path = os.path.join(H, "yield_corrections.csv")
    out.to_csv(path, index=False)

    n_pow = int(out["looks_like_power_of_ten"].sum())
    print(f"paired (source, country, item, year) with BOTH area and production: {len(m):,}")
    print(f"  items covered: {m['item'].nunique()}   sources: "
          f"{sorted(m['source'].astype(str).unique())}")
    print(f"implausible yield (>{A.hi} or <{A.lo} t/ha): {len(out)} "
          f"({100 * len(out) / max(len(m), 1):.2f}%)")
    print(f"  of those, off by a clean power of ten: {n_pow} "
          f"-- a dropped decimal or a thousands column labelled units")
    print(f"  by source: {dict(out['source'].astype(str).value_counts())}")
    print(f"\nwrote state/yield_corrections.csv ({len(out)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
