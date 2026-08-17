#!/usr/bin/env python3
"""Mirror screen over FAOSTAT bilateral trade: which doubly-reported flows disagree absurdly.

Issue 112 established that trade mirrors ARE available -- 6.13M flows reported from both
sides -- and that whep's rule (`R/bilateral_trade.R`: "we trust the export data X") throws
the disagreement away without recording it. Where the EXPORTER is the party with the scale
error, that preference propagates it and the surviving number is internally plausible, so
nothing downstream can tell. Measured here: among the investigable flows below the exporter
is the larger side 50.8% of the time (49.8% across all the extremes), so an unconditional
preference picks the implausible side about half the time in that tail -- near enough to a
coin flip that a systematic error would be invisible in the surviving column. The mirror
gap is the only signal that a flow was risky, and it is computed nowhere.

This script computes it and writes the flows worth a look. It does NOT change any
preference rule and does NOT modify the pin, exactly as 06_landuse_consistency.py and
07_yield_consistency.py do not: the fix lands upstream, in whep. What lands here is the
evidence, in a form a reader without the 46.8M-row pin can review.

WHY THE SCREEN IS NOT "RATIO >= 1000x"
--------------------------------------
That is the screen issue 112 proposed, and taken literally it selects 39,804 flows -- but
re-measuring it shows two thirds of those are not disagreements at all:

    smaller side of the >1000x flows, tonnes     p25 0.02   p50 0.10   p75 1.00   p90 5.00
    smaller side below 1 tonne                   67.8%  (26,915 of 39,690)
    smaller side at or below 0.1 tonne           50.9%
    median LARGER side                           532 t

0.1 t against 532 t is a 5,000x "discrepancy" in which neither number need be wrong: one
side is reporting a trace consignment or a rounding of it against the other's real flow.
Ratio is the wrong statistic there because it is unbounded as the denominator goes to
zero -- the same reason 05_magnitude_screen.py cannot use a ratio against a near-zero
neighbour. So the screen is a PAIR of conditions, absolute and relative:

    both sides >= MIN_SIDE_T (1 tonne)   AND   ratio > RATIO_THRESHOLD (1000x)
      -> 12,775 flows, 0.208% of the 6.13M mirrored, across 153 reporters and 402 items

THIS IS NOT ISSUE 111'S POWER-OF-TEN CLASS, and the table says so per row rather than
leaving a reader to assume it. Of the 39,690 flows above 1000x, only 926 (2.3%) have a
ratio within 2% of an exact power of ten; on the investigable 12,775 it is 372 (2.9%).
Issue 111 is a whole SERIES off by a constant factor, recoverable with one multiplier.
This is a per-flow disagreement between two reporters, and the ratios cluster in
magnitude without landing on the decades -- so mirrors will not recover 111's nine series
and 111's corrections will not resolve these.

A BARE SHARE CANNOT SUPPORT THAT READING, WHICH IS WHY THERE IS A CONTROL
------------------------------------------------------------------------
"2.9% land on a power of ten" is not evidence of anything on its own, and neither is issue
112's own "21,257 of 178,131 (11.9%) within 5% of a clean power of ten": a multiplicative
window has a WIDTH in log space, and ratios spread over four decades will fall inside it at
some rate whatever their cause. The 2% ratio window spans log10(1.02/0.98) = 1.74% of a
decade, so ~1.7% of ANY smooth distribution lands in it. Comparing 2.9% to nothing at all
is how a null result gets reported as a signature.

So the same window is also applied HALF A DECADE AWAY -- centred on 10^(k+0.5), where a
scale error cannot put anything -- and both counts are stored, per row and in the summary.
The control is matched by construction: |r/c - 1| < w covers the same log width whatever c
is. Measured:

                        on 10^k        on 10^(k+0.5)     enrichment
    >=100x  (178,131)   4,376 (2.5%)    2,929 (1.6%)        1.49x
    >1000x   (39,690)     926 (2.3%)      654 (1.6%)        1.42x
    investigable         372 (2.9%)      211 (1.7%)        1.76x

So there IS a decade-aligned excess, and issue 112 was not imagining it -- but it is
1.5-1.8x, not the many-fold pile-up "the ratios cluster on powers of ten" describes, and it
accounts for 372 - 211 = 161 of the 12,775 flows (1.3%). The half-decade control is what
turns the claim from a share into a measurement, and the gate re-derives it: an unchecked
control column could be dropped low and fabricate any enrichment one liked.

WHAT THE TABLE DOES AND DOES NOT CLAIM
--------------------------------------
It flags a PAIR. Unlike the land-use identity (06) and area x yield (07), there is no third
quantity to solve for, so a mirror disagreement localises the error to (exporter, importer)
without saying which of the two moved. Hence no `implied_correct` column and no `action`:
inventing a direction here would be exactly the mistake 07 refuses when it writes
`undetermined`. `larger_side` and `keeps_larger_side` record which side whep's rule would
keep, which is the reviewable fact; the direction needs a tie-breaker this screen does not
have (reporter reliability, or a third-party total).

That tie-breaker now exists next door, and it is a third quantity rather than either of
those: 13_trade_entrepot_direction.py tests both claims against the exporter's own
production plus imports, since a shipment cannot exceed what the shipper had. It decides 49
of these flows and leaves 3,864 undetermined, which is why THIS table still carries no
direction column -- the mirror alone cannot say, and only 30.6% of the flows have a
production figure to be judged against at all.

It is also DIFFUSE: the top 20 (reporter, item) pairs hold 9.8% of the 12,775. So no
per-series correction table of 06's shape can cover it -- whatever consumes this has to
work per flow.

Usage:
  python3 pipelines/polity-autoimprove/12_trade_mirror_gap.py [--min-side 1.0] [--ratio 1000]
Writes state/trade_mirror_gaps.csv and state/trade_mirror_summary.csv
Needs the bilateral pin (WHEP_TRADE_BILATERAL); scripts/validate_trade_mirror_gaps.py
re-derives the table's own invariants from the committed CSVs and needs no pin.
"""
import argparse
import math
import os
import warnings

import numpy as np
import pandas as pd

import extdata

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H = os.path.join(REPO, "pipelines/polity-autoimprove/state")
GAPS = os.path.join(H, "trade_mirror_gaps.csv")
SUMMARY = os.path.join(H, "trade_mirror_summary.csv")

# The absolute floor. Below a tonne, a ratio says nothing about agreement: 67.8% of the
# >=1000x flows have their smaller side under 1 t, median 0.1 t.
MIN_SIDE_T = 1.0
# The relative condition, STRICT: ">1000x" and ">=1000x" differ by 114 flows on this pin
# (39,690 vs 39,804), which is the whole discrepancy between issue 112's body and this
# script's count. Strict, and said so in the summary.
RATIO_THRESHOLD = 1000.0
# How close a ratio must be to 10^k before the row calls it a power of ten. 2% of the
# RATIO, which is the reading of "within 2% of an exact power of ten" that a consumer
# would implement. Measured both ways because they disagree by a factor of two:
#   |ratio / 10^k - 1| < 0.02       926 of 39,690  (2.3%)
#   |log10(ratio) - k| < 0.02     1,970 of 39,690  (5.0%)   <- 112's "5.0%", a 4.7% window
POW10_WINDOW = 0.02
# The matched control for that window: the same test applied half a decade off the decade,
# at 10^(k+0.5), where no scale error can land. Without it, "2.9% are within 2% of a power
# of ten" is a share with nothing to be a share ABOVE -- the window itself covers 1.74% of
# a decade. Measured 1.7% on the control, so the enrichment is 1.76x.
HALF_DECADE_OFFSET = 0.5

KEY = ["Reporter Country Code", "Partner Country Code", "Item Code", "Year"]
COLUMNS = ["reporter_code", "reporter", "partner_code", "partner", "item_code", "item",
           "year", "exp_t", "imp_t", "ratio", "larger_side", "keeps_larger_side",
           "nearest_pow10", "ratio_is_pow10", "ratio_is_halfdecade"]

# whep's documented preference, from R/bilateral_trade.R. Named here because
# `keeps_larger_side` is meaningless without it.
WHEP_KEEPS = "exporter"


def nearest_power_of_ten(ratio: float) -> int:
    """How many orders of magnitude apart the two sides are, to the nearest power of ten."""
    if not ratio or ratio <= 0 or not math.isfinite(ratio):
        return 0
    return int(round(math.log10(ratio)))


def is_clean_power_of_ten(ratio: float, window: float = POW10_WINDOW) -> bool:
    """Is `ratio` within `window` OF THE RATIO of its nearest power of ten?

    Not within `window` of it in log space. The two windows differ by more than a factor
    of two on this data (2.3% vs 5.0%), and the log form is the looser one -- so reporting
    the log figure under the words "within 2%" overstates the power-of-ten share, which is
    the one number in issue 112's follow-up that does not reproduce.
    """
    if ratio is None or not math.isfinite(ratio) or ratio <= 0:
        return False
    p = nearest_power_of_ten(ratio)
    return p != 0 and abs(ratio / (10.0 ** p) - 1.0) < window


def is_clean_half_decade(ratio: float, window: float = POW10_WINDOW) -> bool:
    """The CONTROL for `is_clean_power_of_ten`: same window, centred half a decade away.

    A scale error is a factor of ten, so it can put a ratio on 10^k and cannot put one on
    10^(k+0.5). Whatever share lands here is therefore the rate at which a window of this
    width catches ratios for reasons that have nothing to do with scale, and the ratio of
    the two shares is the only defensible reading of "the ratios cluster on powers of ten".
    Matched by construction: |r/c - 1| < w spans log10((1+w)/(1-w)) of a decade for every c.
    """
    if ratio is None or not math.isfinite(ratio) or ratio <= 0:
        return False
    centre = 10.0 ** (math.floor(math.log10(ratio)) + HALF_DECADE_OFFSET)
    return abs(ratio / centre - 1.0) < window


def mirrored_flows(frame: pd.DataFrame) -> pd.DataFrame:
    """Join every reported export A->B to B's reported import from A, in tonnes.

    Element CODES, not the strings: five codes spell themselves "Export Quantity" and only
    5910 is in tonnes (see extdata.TRADE_EXPORT_QUANTITY_CODE). Summed per key first,
    because one (reporter, partner, item, year) can carry several rows.
    """
    t = frame[
        frame["Element Code"].isin(
            [extdata.TRADE_EXPORT_QUANTITY_CODE, extdata.TRADE_IMPORT_QUANTITY_CODE]
        )
        & (frame["Value"] > 0)
        & (frame["Unit"] == extdata.TRADE_TONNE_UNIT)
    ]
    print(f"  tonnage rows with a positive value: {len(t):,}")
    exp = (t[t["Element Code"] == extdata.TRADE_EXPORT_QUANTITY_CODE]
           .groupby(KEY, as_index=False)["Value"].sum().rename(columns={"Value": "exp_t"}))
    imp = (t[t["Element Code"] == extdata.TRADE_IMPORT_QUANTITY_CODE]
           .groupby(KEY, as_index=False)["Value"].sum().rename(columns={"Value": "imp_t"}))
    print(f"  export-quantity flows: {len(exp):,}   import-quantity flows: {len(imp):,}")
    # THE JOIN IS CROSSED. An import reported BY b FROM a is the same flow as an export
    # reported BY a TO b, so the importer's reporter/partner swap places. Merging without
    # the swap joins a's export to b against a's import from b -- a different flow in the
    # other direction, which merges cleanly and yields a plausible, wrong table.
    imp = imp.rename(columns={"Reporter Country Code": "Partner Country Code",
                              "Partner Country Code": "Reporter Country Code"})
    m = exp.merge(imp, on=KEY)
    print(f"  flows reported from BOTH sides: {len(m):,}")
    return m


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-side", type=float, default=MIN_SIDE_T,
                    help="both sides must reach this many tonnes (default 1.0)")
    ap.add_argument("--ratio", type=float, default=RATIO_THRESHOLD,
                    help="strict ratio threshold (default 1000)")
    args = ap.parse_args()

    print(f"reading {extdata.find_trade_bilateral()}")
    # The LABELS come from arrow's distinct pairs, not from the loaded frame: three label
    # columns over 46.8M rows cost gigabytes to hold 189, 220 and 559 distinct values.
    names = {
        "reporter": extdata.trade_bilateral_code_names(
            "Reporter Country Code", "Reporter Countries"),
        "partner": extdata.trade_bilateral_code_names(
            "Partner Country Code", "Partner Countries"),
        "item": extdata.trade_bilateral_code_names("Item Code", "Item"),
    }
    # The filter is on element CODES, so the capital-Q trap cannot bite -- but a renumbering
    # would be silent, hence this.
    extdata.require_trade_quantity_codes(
        extdata.trade_bilateral_code_names("Element Code", "Element"))
    frame = extdata.load_trade_bilateral(columns=[
        "Reporter Country Code", "Partner Country Code",
        "Item Code", "Element Code", "Year", "Unit", "Value",
    ])
    print(f"  pin rows: {len(frame):,}   labels: "
          + ", ".join(f"{k} {len(v)}" for k, v in names.items()))
    m = mirrored_flows(frame)
    del frame

    hi = np.maximum(m["exp_t"], m["imp_t"])
    lo = np.minimum(m["exp_t"], m["imp_t"])
    ratio = hi / lo
    gap = (hi - lo) / hi
    print(f"  median relative gap (hi-lo)/hi: {gap.median():.4f}   "
          f"exactly equal: {100 * (m['exp_t'] == m['imp_t']).mean():.2f}%")
    census = {}
    for k in (2, 10, 100, 1000):
        census[k] = int((ratio >= k).sum())
        print(f"  differ >={k}x: {census[k]:,}   (strictly >: {int((ratio > k).sum()):,})")

    extreme = m[ratio > args.ratio].copy()
    extreme["hi"], extreme["lo"] = hi[ratio > args.ratio], lo[ratio > args.ratio]
    trace = int((extreme["lo"] < args.min_side).sum())
    print(f"\n  above {args.ratio:g}x: {len(extreme):,}; of those, smaller side under "
          f"{args.min_side:g} t: {trace:,} ({100 * trace / max(len(extreme), 1):.1f}%), "
          f"median smaller side {extreme['lo'].median():g} t, median larger "
          f"{extreme['hi'].median():.1f} t -- EXCLUDED as trace reporting, not disagreement")

    inv = extreme[extreme["lo"] >= args.min_side].copy()
    print(f"  investigable flows: {len(inv):,} "
          f"({100 * len(inv) / max(len(m), 1):.3f}% of the mirrored)")

    out = pd.DataFrame({
        "reporter_code": inv["Reporter Country Code"].astype(int),
        "reporter": inv["Reporter Country Code"].map(names["reporter"]),
        "partner_code": inv["Partner Country Code"].astype(int),
        "partner": inv["Partner Country Code"].map(names["partner"]),
        "item_code": inv["Item Code"].astype(int),
        "item": inv["Item Code"].map(names["item"]),
        "year": inv["Year"].astype(int),
        "exp_t": inv["exp_t"],
        "imp_t": inv["imp_t"],
    })
    out["ratio"] = (inv["hi"] / inv["lo"]).round(3).values
    out["larger_side"] = np.where(inv["exp_t"] > inv["imp_t"], "exporter", "importer")
    out["keeps_larger_side"] = out["larger_side"] == WHEP_KEEPS
    out["nearest_pow10"] = [nearest_power_of_ten(r) for r in out["ratio"]]
    out["ratio_is_pow10"] = [is_clean_power_of_ten(r) for r in out["ratio"]]
    out["ratio_is_halfdecade"] = [is_clean_half_decade(r) for r in out["ratio"]]
    out = out[COLUMNS].sort_values(["ratio", "reporter_code", "item_code", "year"],
                                   ascending=[False, True, True, True])
    out.to_csv(GAPS, index=False)
    print(f"\nwrote {os.path.relpath(GAPS, REPO)} ({len(out):,} rows)")

    extreme_ratio = extreme["hi"] / extreme["lo"]
    pow10_all = sum(is_clean_power_of_ten(r) for r in extreme_ratio)
    half_all = sum(is_clean_half_decade(r) for r in extreme_ratio)
    half_inv = int(out["ratio_is_halfdecade"].sum())
    pow10_inv = int(out["ratio_is_pow10"].sum())
    rows = [
        ("mirrored_flows", len(m)),
        ("median_relative_gap", round(float(gap.median()), 4)),
        ("exactly_equal_share", round(float((m["exp_t"] == m["imp_t"]).mean()), 4)),
        ("differ_ge_2x", census[2]),
        ("differ_ge_10x", census[10]),
        ("differ_ge_100x", census[100]),
        ("differ_gt_threshold", len(extreme)),
        ("trace_excluded_smaller_side_below_min", trace),
        ("investigable_flows", len(out)),
        ("investigable_reporters", out["reporter_code"].nunique()),
        ("investigable_items", out["item_code"].nunique()),
        ("investigable_year_min", int(out["year"].min())),
        ("investigable_year_max", int(out["year"].max())),
        ("investigable_ratio_is_pow10", pow10_inv),
        # The matched control and the only number that makes the line above mean something.
        ("investigable_ratio_is_halfdecade", half_inv),
        ("investigable_pow10_enrichment",
         round(pow10_inv / half_inv, 3) if half_inv else None),
        ("investigable_keeps_larger_side", int(out["keeps_larger_side"].sum())),
        ("extremes_ratio_is_pow10", int(pow10_all)),
        ("extremes_ratio_is_halfdecade", int(half_all)),
        ("extremes_pow10_enrichment",
         round(pow10_all / half_all, 3) if half_all else None),
        ("min_side_t", args.min_side),
        ("ratio_threshold_strict", args.ratio),
        ("pow10_window", POW10_WINDOW),
        ("halfdecade_control_offset", HALF_DECADE_OFFSET),
        ("whep_keeps", WHEP_KEEPS),
    ]
    pd.DataFrame(rows, columns=["metric", "value"]).to_csv(SUMMARY, index=False)
    print(f"wrote {os.path.relpath(SUMMARY, REPO)}")
    top = out.groupby(["reporter", "item"]).size().sort_values(ascending=False)
    print(f"  top 20 (reporter, item) pairs hold {100 * top.head(20).sum() / len(out):.1f}% "
          f"-- diffuse, so no per-series correction table can cover it")
    print(f"  ratio within {POW10_WINDOW:.0%} of a power of ten: "
          f"{pow10_inv:,} of {len(out):,} "
          f"({100 * out['ratio_is_pow10'].mean():.1f}%) -- NOT issue 111's class")
    print(f"    matched control at 10^k+{HALF_DECADE_OFFSET:g}: {half_inv:,} "
          f"({100 * out['ratio_is_halfdecade'].mean():.1f}%) -- so the decade-aligned "
          f"excess is {pow10_inv / half_inv:.2f}x, or {pow10_inv - half_inv:,} flows, "
          f"not the pile-up issue 112 read off a bare share")
    print(f"  whep's rule keeps the LARGER side in "
          f"{100 * out['keeps_larger_side'].mean():.1f}% of them")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
