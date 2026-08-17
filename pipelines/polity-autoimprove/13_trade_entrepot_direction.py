#!/usr/bin/env python3
"""The third quantity a trade mirror lacks: production, and what it decides.

12_trade_mirror_gap.py screened the doubly-reported FAOSTAT flows and stopped exactly where
a pair has to stop -- it flags 12,775 flows whose two sides disagree by more than 1000x and
refuses to name the guilty side, because two numbers about one shipment cannot arbitrate
themselves. Its docstring says the direction "needs a tie-breaker this screen does not
have (reporter reliability, or a third-party total)". This script supplies one, and it is
neither of those two: it is the exporter's OWN PRODUCTION plus the exporter's own imports,
in the same item and year. A shipment cannot exceed what the shipper had.

The same quantity answers issue 14's untested half. #14 recorded entrepot trade booked as
production -- Ethiopian coffee under French Somaliland -- and asked for a way to mark it.
The tell it proposed is exactly this comparison: B imports from A, then exports more than it
produces.

THE TWO HALVES ARE ONE COMPUTATION, AND THAT IS WHY THEY ARE IN ONE SCRIPT
-------------------------------------------------------------------------
Crediting imports is not a refinement of the entrepot screen, it is what stops the
tie-breaker being nonsense. Exporting more than you produce is NORMAL for an entrepot and
says nothing about any single flow being wrong. Measured on this pin, exports above ten
times production, at or above 1,000 t:

    Netherlands 332   Belgium 213   Hong Kong 196   Singapore 130   France 123   USA 121

-- which is issue 14's own candidate list (it named Singapore, Hong Kong, Rotterdam) arrived
at from the data rather than from a reading of history. So `exports > production` is a
LABEL, not a defect: the class #14 asks to mark. What is not normal is exports above
production PLUS imports: nothing was available to ship. Those two classes are the entrepot
table's two values of `flow_class`, and only the second is a candidate error.

WHY NOT LAYER B, WHICH IS WHAT THE ISSUE SAID TO CHECK AGAINST
--------------------------------------------------------------
Issue 112's follow-up says the entrepot pattern is "checkable against layer-B production".
On these flows it is not, and the script prints the reason every run:

    layer B                       1850-1960
    faostat-trade-bilateral       1986-2021       overlapping years: 0

Not one year in common, so a layer-B join would have produced an empty table and a clean,
plausible, completely wrong "no entrepots found" -- the failure mode issue 112 itself
records for the capital-Q filter. The FAOSTAT production pin covers 1961-2024 and is keyed
on the SAME area and item codes as the bilateral pin, so it needs no ISO3 crosswalk and no
item concordance: all 189 reporters resolve, and 234 of the 555 traded items.

WHAT THE TIE-BREAKER RESOLVES, WHICH IS A SMALL MINORITY, AND SAID SO
--------------------------------------------------------------------
Of the 12,775 flagged flows, 3,913 (30.6%) have a production row for the exporter's item and
year at all; the rest are processed or composite trade items FAOSTAT does not publish
production for, and are simply undecidable this way. Within those 3,913, at the documented
threshold -- a claim must exceed TWICE the exporter's whole same-year availability before
being called impossible -- 49 resolve:

    exporter's figure impossible   18   whep's rule keeps the side production rejects
    importer's figure impossible   31   whep's rule is right here
    both impossible                 0
    undetermined                3,864

So this is a tie-breaker that decides 1.3% of the flows it can see, and 0.4% of the flagged
set. That is the honest yield and the reason the pair table keeps no direction column: the
mirror alone still cannot say. What the 18 buy is specific: Mexico reports 195,282 t of
green onions exported to the United States in 1995 against 84,855 t of production plus
imports for the entire year, while the United States reports receiving 2 t. whep keeps the
195,282.

The threshold matters and the summary carries the whole ladder rather than one number:
resolved 75 at 1.1x, 63 at 1.5x, 49 at 2.0x, 31 at 3.0x, 19 at 5.0x. 2.0x is the default
because same-year availability ignores opening stocks, and a country can legitimately ship
last year's harvest -- doubling the whole year's supply is past what carryover explains,
while an 18% excess is not. Nothing here treats the resolved flows as repaired: no corrected
tonnage is written, because the surviving side is still only the side that was not refuted.

Usage:
  python3 pipelines/polity-autoimprove/13_trade_entrepot_direction.py
Writes state/trade_entrepot_flags.csv, state/trade_mirror_direction.csv and
state/trade_availability_summary.csv. Needs the bilateral pin (WHEP_TRADE_BILATERAL) and
the production pin (WHEP_FAOSTAT_PRODUCTION); scripts/validate_trade_direction_tiebreak.py
re-derives every claim these tables make from the committed CSVs and needs no pin.
"""
import argparse
import os
import warnings

import numpy as np
import pandas as pd

import extdata

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H = os.path.join(REPO, "pipelines/polity-autoimprove/state")
GAPS = os.path.join(H, "trade_mirror_gaps.csv")          # written by 12_trade_mirror_gap.py
ENTREPOT = os.path.join(H, "trade_entrepot_flags.csv")
DIRECTION = os.path.join(H, "trade_mirror_direction.csv")
SUMMARY = os.path.join(H, "trade_availability_summary.csv")

# The entrepot table's absolute floor. Below a thousand tonnes an "export exceeding
# production" is as likely to be a rounding of a small consignment as a routing fact, the
# same reason 12_ carries MIN_SIDE_T.
MIN_EXPORT_T = 1000.0
# How far above availability an export total must sit before the year is called unsourceable.
# 10% covers the rounding of three separately published quantities.
AVAIL_TOL = 1.1
# How far above PRODUCTION ALONE exports must sit to be called re-export. 10x, not 1.1x:
# a country that produces a little and ships a lot is an entrepot beyond argument, whereas
# 1.2x is ordinary stock drawdown and would label half the world.
REEXPORT_FACTOR = 10.0
# The tie-breaker's threshold. A single flow must exceed this multiple of the exporter's
# WHOLE same-year availability before the claim is called impossible. See the docstring for
# why it is 2.0 and not 1.1, and the summary for the sensitivity ladder.
DIRECTION_TOL = 2.0
SENSITIVITY = (1.1, 1.5, 2.0, 3.0, 5.0)

WHEP_KEEPS = "exporter"          # R/bilateral_trade.R, as recorded in 12_trade_mirror_gap.py

ENTREPOT_COLUMNS = ["reporter_code", "reporter", "item_code", "item", "year", "prod_t",
                    "imports_t", "exports_t", "avail_t", "exp_over_prod", "exp_over_avail",
                    "flow_class"]
DIRECTION_COLUMNS = ["reporter_code", "reporter", "partner_code", "partner", "item_code",
                     "item", "year", "exp_t", "imp_t", "ratio", "prod_t",
                     "reporter_imports_t", "avail_t", "exp_over_avail", "imp_over_avail",
                     "impossible_side", "plausible_side", "whep_keeps_plausible"]


def ratio_or_blank(num, den):
    """num/den rounded, or "" where den is zero -- which is a real state here, not an error.

    Austria reports 35,712 t of dry whey exported to Germany in 1991 with production 0 and
    imports 691 t. An infinity in a CSV column is worse than a blank: it invites a consumer
    to sort on it, and `float("inf")` is what a stray `1e999` also parses to. Blank means
    "the denominator was zero", the gate re-derives exactly that, and the class columns do
    not depend on the ratio.
    """
    out = []
    for n, d in zip(np.asarray(num, dtype=float), np.asarray(den, dtype=float)):
        out.append("" if d <= 0 else round(n / d, 3))
    return out


def reporter_totals(frame: pd.DataFrame) -> pd.DataFrame:
    """Total exports and total imports per (reporter, item, year), in tonnes.

    Element CODES and the tonne unit, for the reasons extdata documents: five codes spell
    themselves "Export Quantity" and only 5910 is in tonnes. Summed over ALL partners --
    that is the point, since the tie-breaker asks what the reporter had available in total,
    not what it sent to one destination.
    """
    t = frame[
        frame["Element Code"].isin(
            [extdata.TRADE_EXPORT_QUANTITY_CODE, extdata.TRADE_IMPORT_QUANTITY_CODE]
        )
        & (frame["Value"] > 0)
        & (frame["Unit"] == extdata.TRADE_TONNE_UNIT)
    ]
    key = ["Reporter Country Code", "Item Code", "Year"]
    exp = (t[t["Element Code"] == extdata.TRADE_EXPORT_QUANTITY_CODE]
           .groupby(key, as_index=False)["Value"].sum()
           .rename(columns={"Value": "exports_t"}))
    imp = (t[t["Element Code"] == extdata.TRADE_IMPORT_QUANTITY_CODE]
           .groupby(key, as_index=False)["Value"].sum()
           .rename(columns={"Value": "imports_t"}))
    tot = exp.merge(imp, how="outer", on=key).fillna({"exports_t": 0.0, "imports_t": 0.0})
    print(f"  reporter-item-year cells: {len(tot):,}")
    return tot


def production_by_cell() -> tuple[pd.DataFrame, dict, dict]:
    """Production in tonnes per (area, item, year), plus the pin's own year range."""
    pr = extdata.load_faostat_production(columns=[
        "Area Code", "Item Code", "Element Code", "Element", "Year", "Unit", "Value"])
    extdata.require_production_tonnes_code(pr)
    pr = pr[(pr["Element Code"] == extdata.PRODUCTION_ELEMENT_CODE)
            & (pr["Unit"] == extdata.PRODUCTION_TONNE_UNIT)
            & pr["Value"].notna()]
    span = {"min": int(pr["Year"].min()), "max": int(pr["Year"].max()), "rows": len(pr)}
    print(f"  production rows (element {extdata.PRODUCTION_ELEMENT_CODE}, tonnes): "
          f"{len(pr):,}   years {span['min']}-{span['max']}")
    prod = (pr.groupby(["Area Code", "Item Code", "Year"], as_index=False)["Value"].sum()
            .rename(columns={"Value": "prod_t", "Area Code": "Reporter Country Code"}))
    return prod, span, {}


def layer_b_overlap(bilateral_min: int, bilateral_max: int) -> dict:
    """Years shared by layer B and the bilateral pin. Measured, because the issue asserts it.

    Returns zeros with a note if layer B is absent, rather than raising: the point of the
    number is to correct issue 112's "checkable against layer-B production", and a machine
    without the gitignored parquet should still be able to run the rest.
    """
    try:
        b = extdata.load_layer_b()
    except (FileNotFoundError, extdata.ExternalDataError) as exc:
        print(f"  note: layer B unavailable ({exc.__class__.__name__}), overlap unmeasured")
        return {}
    years = set(int(y) for y in b["year"].dropna().unique())
    overlap = sorted(y for y in years if bilateral_min <= y <= bilateral_max)
    print(f"  layer B years {min(years)}-{max(years)} vs bilateral {bilateral_min}-"
          f"{bilateral_max}: {len(overlap)} overlapping years"
          + ("" if overlap else " -- so the entrepot check CANNOT use layer B"))
    return {"layer_b_year_min": min(years), "layer_b_year_max": max(years),
            "layer_b_bilateral_overlap_years": len(overlap)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--min-export", type=float, default=MIN_EXPORT_T)
    ap.add_argument("--direction-tol", type=float, default=DIRECTION_TOL)
    args = ap.parse_args()

    print(f"reading {extdata.find_trade_bilateral()}")
    names = {
        "reporter": extdata.trade_bilateral_code_names(
            "Reporter Country Code", "Reporter Countries"),
        "partner": extdata.trade_bilateral_code_names(
            "Partner Country Code", "Partner Countries"),
        "item": extdata.trade_bilateral_code_names("Item Code", "Item"),
    }
    extdata.require_trade_quantity_codes(
        extdata.trade_bilateral_code_names("Element Code", "Element"))
    frame = extdata.load_trade_bilateral(columns=[
        "Reporter Country Code", "Partner Country Code",
        "Item Code", "Element Code", "Year", "Unit", "Value"])
    b_min, b_max = int(frame["Year"].min()), int(frame["Year"].max())
    print(f"  pin rows: {len(frame):,}   years {b_min}-{b_max}")
    tot = reporter_totals(frame)
    del frame

    print(f"reading {extdata.find_faostat_production()}")
    prod, span, _ = production_by_cell()
    overlap = layer_b_overlap(b_min, b_max)

    cells = tot.merge(prod, how="left", on=["Reporter Country Code", "Item Code", "Year"])
    have = cells["prod_t"].notna()
    print(f"  cells with a production figure: {int(have.sum()):,} of {len(cells):,} "
          f"({100 * have.mean():.1f}%)")
    c = cells[have].copy()
    c["avail_t"] = c["prod_t"] + c["imports_t"]

    # ---- the entrepot table (issue 14) --------------------------------------------------
    big = c[c["exports_t"] >= args.min_export].copy()
    over_avail = big["exports_t"] > AVAIL_TOL * big["avail_t"]
    over_prod = big["exports_t"] > REEXPORT_FACTOR * big["prod_t"].clip(lower=0)
    ent = big[over_avail | (over_prod & ~over_avail)].copy()
    ent["flow_class"] = np.where(
        ent["exports_t"] > AVAIL_TOL * ent["avail_t"], "exceeds_availability", "reexport")
    ent_out = pd.DataFrame({
        "reporter_code": ent["Reporter Country Code"].astype(int),
        "reporter": ent["Reporter Country Code"].map(names["reporter"]),
        "item_code": ent["Item Code"].astype(int),
        "item": ent["Item Code"].map(names["item"]),
        "year": ent["Year"].astype(int),
        "prod_t": ent["prod_t"].values,
        "imports_t": ent["imports_t"].values,
        "exports_t": ent["exports_t"].values,
        "avail_t": ent["avail_t"].values,
    })
    ent_out["exp_over_prod"] = ratio_or_blank(ent["exports_t"], ent["prod_t"])
    ent_out["exp_over_avail"] = ratio_or_blank(ent["exports_t"], ent["avail_t"])
    ent_out["flow_class"] = ent["flow_class"].values
    ent_out = ent_out[ENTREPOT_COLUMNS].sort_values(
        ["flow_class", "exports_t", "reporter_code", "item_code", "year"],
        ascending=[True, False, True, True, True])
    ent_out.to_csv(ENTREPOT, index=False)
    counts = ent_out["flow_class"].value_counts().to_dict()
    print(f"\nwrote {os.path.relpath(ENTREPOT, REPO)} ({len(ent_out):,} rows: "
          + ", ".join(f"{k} {v:,}" for k, v in sorted(counts.items())) + ")")
    top = (ent_out[ent_out["flow_class"] == "reexport"].groupby("reporter").size()
           .sort_values(ascending=False).head(6))
    print("  re-export leaders (issue 14's class, NOT errors): "
          + ", ".join(f"{k} {v}" for k, v in top.items()))

    # ---- the direction tie-breaker (issue 112's remainder) ------------------------------
    if not os.path.exists(GAPS):
        raise SystemExit(f"{GAPS} is missing; run 12_trade_mirror_gap.py first.")
    gaps = pd.read_csv(GAPS)
    print(f"\nflagged mirror flows: {len(gaps):,}")
    avail = c.rename(columns={"Reporter Country Code": "reporter_code",
                              "Item Code": "item_code", "Year": "year",
                              "imports_t": "reporter_imports_t"})[
        ["reporter_code", "item_code", "year", "prod_t", "reporter_imports_t", "avail_t"]]
    j = gaps.merge(avail, how="inner", on=["reporter_code", "item_code", "year"])
    print(f"  with a production figure for the exporter's item and year: {len(j):,} "
          f"({100 * len(j) / max(len(gaps), 1):.1f}%) -- the rest are processed or "
          f"composite items FAOSTAT publishes no production for")

    tol = args.direction_tol
    exp_bad = j["exp_t"] > tol * j["avail_t"]
    imp_bad = j["imp_t"] > tol * j["avail_t"]
    j["impossible_side"] = np.where(exp_bad & imp_bad, "both",
                            np.where(exp_bad, "exporter",
                             np.where(imp_bad, "importer", "none")))
    # THE DIRECTION IS THE OTHER SIDE, and only where exactly one side is refuted. "both"
    # and "none" both mean undetermined, for opposite reasons -- one refutes nothing, the
    # other refutes everything and so cannot prefer -- and collapsing them into a guess is
    # the mistake 07_yield_consistency refuses when it writes `undetermined`.
    j["plausible_side"] = np.where(j["impossible_side"] == "exporter", "importer",
                            np.where(j["impossible_side"] == "importer", "exporter",
                                     "undetermined"))
    j["whep_keeps_plausible"] = np.where(
        j["plausible_side"] == "undetermined", "unknown",
        np.where(j["plausible_side"] == WHEP_KEEPS, "true", "false"))
    dir_out = pd.DataFrame({
        "reporter_code": j["reporter_code"].astype(int), "reporter": j["reporter"],
        "partner_code": j["partner_code"].astype(int), "partner": j["partner"],
        "item_code": j["item_code"].astype(int), "item": j["item"],
        "year": j["year"].astype(int), "exp_t": j["exp_t"], "imp_t": j["imp_t"],
        "ratio": j["ratio"], "prod_t": j["prod_t"],
        "reporter_imports_t": j["reporter_imports_t"], "avail_t": j["avail_t"],
    })
    dir_out["exp_over_avail"] = ratio_or_blank(j["exp_t"], j["avail_t"])
    dir_out["imp_over_avail"] = ratio_or_blank(j["imp_t"], j["avail_t"])
    for col in ("impossible_side", "plausible_side", "whep_keeps_plausible"):
        dir_out[col] = j[col].values
    dir_out = dir_out[DIRECTION_COLUMNS].sort_values(
        ["plausible_side", "ratio", "reporter_code", "item_code", "year"],
        ascending=[True, False, True, True, True])
    dir_out.to_csv(DIRECTION, index=False)
    vc = dir_out["impossible_side"].value_counts().to_dict()
    resolved = int((dir_out["plausible_side"] != "undetermined").sum())
    wrong = int((dir_out["whep_keeps_plausible"] == "false").sum())
    print(f"wrote {os.path.relpath(DIRECTION, REPO)} ({len(dir_out):,} rows)")
    print(f"  resolved at {tol:g}x availability: {resolved:,} "
          + ", ".join(f"{k} {v}" for k, v in sorted(vc.items())))
    print(f"  whep's '{WHEP_KEEPS}' preference keeps the refuted side in {wrong} of them")
    ladder = {}
    for t in SENSITIVITY:
        eb, ib = j["exp_t"] > t * j["avail_t"], j["imp_t"] > t * j["avail_t"]
        ladder[t] = int((eb ^ ib).sum())
        print(f"    sensitivity: at {t:g}x, {ladder[t]} resolve")

    rows = [
        ("bilateral_year_min", b_min),
        ("bilateral_year_max", b_max),
        ("production_pin_rows_tonnes", span["rows"]),
        ("production_year_min", span["min"]),
        ("production_year_max", span["max"]),
        *sorted(overlap.items()),
        ("reporter_item_year_cells", len(cells)),
        ("cells_with_production", int(have.sum())),
        ("entrepot_rows", len(ent_out)),
        ("entrepot_exceeds_availability", int(counts.get("exceeds_availability", 0))),
        ("entrepot_reexport", int(counts.get("reexport", 0))),
        ("entrepot_reporters", int(ent_out["reporter_code"].nunique())),
        ("entrepot_items", int(ent_out["item_code"].nunique())),
        ("entrepot_year_min", int(ent_out["year"].min())),
        ("entrepot_year_max", int(ent_out["year"].max())),
        ("mirror_flagged_flows", len(gaps)),
        ("direction_rows", len(dir_out)),
        ("direction_resolved", resolved),
        ("direction_exporter_impossible", int(vc.get("exporter", 0))),
        ("direction_importer_impossible", int(vc.get("importer", 0))),
        ("direction_both_impossible", int(vc.get("both", 0))),
        ("direction_undetermined", int(vc.get("none", 0))),
        ("direction_whep_keeps_refuted_side", wrong),
        *[(f"direction_resolved_at_{str(t).replace('.', '_')}x", n)
          for t, n in ladder.items()],
        ("min_export_t", args.min_export),
        ("avail_tol", AVAIL_TOL),
        ("reexport_factor", REEXPORT_FACTOR),
        ("direction_tol", tol),
        ("whep_keeps", WHEP_KEEPS),
    ]
    pd.DataFrame(rows, columns=["metric", "value"]).to_csv(SUMMARY, index=False)
    print(f"wrote {os.path.relpath(SUMMARY, REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
