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

SERIES, NOT CELLS (issue 111). Most detections are not isolated: 44 of the 77 flagged cells
fall into nine (source, country, item) series spanning three or more years. A single
implausible cell is a data-entry slip; a run of them is a UNIT error for the whole series,
and the two need different treatment. So a second pass groups the flagged cells into runs
and writes state/yield_series_corrections.csv: 39 runs, 12 of them 3+ years long.

Two things that pass discovered, and that the per-cell table cannot express:

  1. THE CELL COUNT UNDERSTATES THE DEFECT, because a cell is only flagged when it crosses
     a hard physical bound AND both columns are present. The nine series' 44 cells sit inside
     runs holding 113 paired observations. mitchell natal maize has 12 cells below 0.01 t/ha
     and 43 paired years at the same ~0.01 t/ha level: the other 31 sit just inside the floor.
     iia czech republic tobacco is the extreme case -- ONE flagged cell (1943, 271 t/ha) and
     a ten-observation run 1934-1944 sitting at 130-155 t/ha, under the 200 ceiling the whole
     way. Counting runs rather than cells is what makes the number honest.

  2. WHICH COLUMN MOVED is decided by the series' OWN nearby clean years where it has them,
     not by the reference yield. If the run's area matches the series' clean-year area and
     only its production is off by an order of magnitude, production moved. That test is
     stronger than any ratio to a cross-source reference median, and it is what settles
     natal maize (production; the area 9,000-160,000 ha is in family with every other
     mitchell maize country) against czech grapes (area; 8-23 ha against 18,696 ha in 1920
     and 17,298 in 1933, same source). Where a series has no clean years, the fallback is
     whether each column falls inside the same source+item cross-country range, and where
     neither test decides, the row says `undetermined` rather than guessing.

     `area_ratio_vs_basis` / `prod_ratio_vs_basis` are read against `direction_basis`:
     under `within-series` they are the run's median over the nearby clean years' median;
     under `peer-range` they are 1.0 for a column inside the source's cross-country
     [p10, p90] for the item and the ratio to the breached edge for one outside it.

  3. THE OFFSET IS OFTEN NOT A POWER OF TEN. Issue 111's headline is "off by a constant
     power of ten", and re-measuring it in 2026-08 shows that is true of only 14 of the 28
     runs carrying a repair factor, and 5 of the 9 multi-year ones. `implied_factor_pow10`
     is the NEAREST power of ten and always populated, so a reader who took it as the
     repair would divide iia congo green coffee by 10 when the factor that restores the
     reference yield is 26.1, and juan austria grapes by 100 when it is 212. So the row
     also carries `implied_factor_is_pow10`, on the per-cell table's own 50% window
     (POW10_WINDOW): true means a decimal shift explains the run, false means the run is
     real but its magnitude is not a clean shift and needs the source document.
     scripts/validate_yield_corrections.py re-derives that boolean, so it cannot drift
     back into an unconditional assertion.

     AND `true` IS NOT A TIGHT FIT. On the 50% window the 14 true runs' residuals after a
     10^n repair span 0.52x-1.44x -- fao1952 tanganyika bananas 0.524 and iia taiwan tobacco
     0.525 are nearly a factor of TWO from the nearest power of ten, and iia russian
     federation rye is 1.44x. The two runs issue 111's title leans on (mitchell natal maize
     1.08, iia ghana cotton lint 1.09) are the tightest of the fourteen, not typical, so a
     batch x10^n pass would leave the worst of them 48% out rather than 8-9%. The gate prints
     that range on every run. Use `implied_factor`, not `implied_factor_pow10`.

  4. WHICH RUNS CAN BE REPAIRED WITHOUT THE YEARBOOK PAGE (issue 111's remaining half).
     The 0.52x-1.44x residual above was read as evidence that even the `true` runs are
     unrepairable. That reading uses the wrong yardstick. A residual is only evidence
     against the decimal-shift hypothesis if it exceeds the noise the CLEAN observations
     themselves show, and here they show a great deal of it: juan sweden linseed's ten clean
     years span 0.37x-2.13x of their own median, juan chile flax 0.53x-4.70x. A run landing
     1.32x from a power of ten inside a series whose good years span 0.86x-1.76x is not
     evidence of anything.

     TWO CHANGES follow. First the ANCHOR: the level a run is compared against is the
     series' OWN clean paired years where it has three or more (`own_level_yield`), and the
     cross-source reference only where it does not (`repair_anchor_basis`). That matters
     substantively -- iia ghana cotton lint's clean years yield 0.071 t/ha against the item
     reference of 0.140, so its factor is 55, not the 109 the reference implies, and 55 is
     not a power of ten. Second the TEST: the residual is judged against that anchor's own
     p10-p90 dispersion (`noise_band_lo/hi`, BAND_Q), not against a fixed window.

     `repairable_without_source` is the resulting four-way verdict, measured 2026-08-17:

       decimal-shift       11 runs, 27 cells, 73 paired obs -- REPAIRABLE. One column moved,
                           the factor against its own anchor is a power of ten, and the
                           residual is inside that anchor's own noise. `repair_factor`
                           carries the repair, an EXACT 10^n. Led by mitchell natal maize
                           1860-1906 (43 obs, x100 on production) and iia australia hops
                           1933-1944 (11 obs, /100).
       shift-outside-noise  4 runs, 12 cells -- NOT repairable. Passes the loose 50% window
                           and fails its own series' dispersion: iia ghana cotton lint (0.55
                           against a 0.84-1.09 band) and iia taiwan tobacco (0.757 against
                           0.79-1.17) are the multi-year cases. Those are the runs issue
                           111's headline leans on hardest, and they are exactly the ones
                           the anchor change disqualifies.
       not-a-shift         13 runs, 23 cells -- NOT repairable. x26.1, x38.7, x1680 are not
                           transcription artefacts, and the only repair on offer is the
                           factor that reproduces the anchor, which is circular: it makes
                           the cell agree with the assumption used to detect it and cannot
                           be checked against anything.
       no-direction        11 runs, 15 cells -- NOT repairable, for a different reason:
                           nothing here says WHICH of the two cells to edit, and editing the
                           wrong one corrupts a good number while leaving the bad one.

     A fifth verdict, `shift-unyardsticked`, covers a run with neither three clean paired
     years nor ten clean peer observations. No run is in it today; it exists so that such a
     run cannot fall into the licensed set by default if the inputs change.

     So 27 of the 77 flagged cells are repairable from internal evidence alone and 50 are
     not, and the reason differs: 12 fail an arithmetic test, 23 have no error mode to
     apply, 15 have no attributable cell. The repair is published for the first group only,
     because a blank is an instruction. POW10_WINDOW stays at 0.5: it answers "is this
     series' offset shaped like a decimal shift", a different question from "may this cell
     be edited unseen", and narrowing it would silently re-answer the first.

A column whose ratio is large but under 10x is recorded as `secondary_suspect`, not asserted:
a real territorial change produces exactly that signature. juan austria grapes is the case --
its area drops 213,400 -> 48,500 ha at 1918 because pre-1918 "austria" is Cisleithania, not
the republic. Asserting "both columns moved" there would corrupt a correct cell.

Like 06, this does NOT modify the source parquet (it lives outside the repo, in the
maintainer's own store). It writes correction tables so the fix lands upstream in the
consolidation step, where it belongs.

Usage:
  python3 pipelines/polity-autoimprove/07_yield_consistency.py [--hi 200] [--lo 0.01]
Writes state/yield_corrections.csv and state/yield_series_corrections.csv
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

# --- thresholds for the series pass (issue 111) -----------------------------------------
# A year belongs to a defective run if its yield is a full order of magnitude from the
# item's reference. Real year-to-year yield variation is well under 3x even in a famine
# year, so 10x is not a distributional judgement.
ANOM_ORDERS = 1.0
# A year counts as CLEAN, and so as evidence of the series' true level, only well inside
# that: half an order of magnitude (3.2x) from the reference.
CLEAN_ORDERS = 0.5
# A column is asserted to have MOVED only at a full order of magnitude. Between 3x and 10x
# it is recorded as a secondary suspect and nothing is asserted: a genuine change of
# reporting territory (austria 1918: 213,400 -> 48,500 ha) lands in exactly that band.
MOVED_RATIO = 10.0
SECONDARY_RATIO = 3.0
# The cross-country fallback needs a distribution to speak of.
MIN_PEERS = 10
MIN_CLEAN_YEARS = 3
# The clean level a run is compared against is the median of the NEAREST-IN-TIME clean
# years, not of the whole series. A series can change level for real -- juan sweden linseed
# runs at 300-3,500 ha before 1934 and 19,000-51,000 ha after 1939 because of the wartime
# oilseed expansion -- and a whole-series median run against a wartime run says "the area
# moved" when the area is the one column that is right. Ten years each way is enough to be
# robust to one polluted neighbour and short enough not to cross a structural break.
NEAR_YEARS = 10
# How close to a power of ten a factor must be before the table says it IS one. 0.5 is the
# per-cell table's own window, kept identical so the two columns mean the same thing.
POW10_WINDOW = 0.5
# The quantiles of the CLEAN observations' own dispersion that bound a residual (issue 111's
# repairability question; see the module docstring). p10/p90 rather than min/max so one
# polluted clean year cannot widen the band enough to admit anything.
BAND_Q = (0.10, 0.90)


def nearest_power_of_ten(ratio: float) -> int:
    """How many orders of magnitude a cell is out by, to the nearest power of ten."""
    import math
    if ratio <= 0:
        return 0
    return int(round(math.log10(ratio)))


def is_clean_power_of_ten(ratio: float) -> bool:
    """Is `ratio` within POW10_WINDOW of its nearest power of ten (and not 10^0)?

    Same test, same window, as the per-cell table's `looks_like_power_of_ten`. The series
    table needs it because `implied_factor_pow10` is only the NEAREST power of ten, and a
    reader who takes it as the repair gets iia congo coffee 2.6x wrong (x26.1 -> x10).
    """
    if ratio is None or not (ratio == ratio) or ratio <= 0:
        return False
    p = nearest_power_of_ten(ratio)
    return p != 0 and abs(ratio / (10.0 ** p) - 1.0) < POW10_WINDOW


def _ratio_verdict(ratio: float) -> str:
    """`moved` / `suspect` / `` for an inside-run to outside-run ratio of one column."""
    if ratio is None or not (ratio == ratio) or ratio <= 0:
        return ""
    if ratio >= MOVED_RATIO or ratio <= 1.0 / MOVED_RATIO:
        return "moved"
    if ratio >= SECONDARY_RATIO or ratio <= 1.0 / SECONDARY_RATIO:
        return "suspect"
    return ""


def _runs_of(series: pd.DataFrame, flagged_years: set) -> list:
    """Maximal runs of consecutive same-sign anomalous years containing a flagged cell.

    Consecutive in the series' OWN ordered paired years, not in calendar years: a source
    that reports 1930-33 and then 1939 has one gap, not a new defect, and splitting on the
    gap would report two runs where the unit error is one.
    """
    s = series.sort_values("year").reset_index(drop=True)
    runs, cur = [], []
    for i, r in s.iterrows():
        sign = 0 if not r["anom"] else (1 if r["log_dev"] > 0 else -1)
        if sign and (not cur or cur[-1][1] == sign):
            cur.append((i, sign))
            continue
        if cur:
            runs.append([i for i, _ in cur])
        cur = [(i, sign)] if sign else []
    if cur:
        runs.append([i for i, _ in cur])
    return [s.loc[idx] for idx in runs
            if any(y in flagged_years for y in s.loc[idx, "year"])]


def _near_level(col_series: pd.DataFrame, col: str, anom_years: set, mid: float):
    """The NEAR_YEARS values of one column closest in time to a run, excluding the run."""
    s = col_series[~col_series["year"].isin(anom_years)]
    if not len(s):
        return s[col]
    s = s.assign(_d=(s["year"] - mid).abs()).nsmallest(NEAR_YEARS, "_d")
    return s[col]


def series_pass(m: pd.DataFrame, bad: pd.DataFrame,
                area: pd.DataFrame, prod: pd.DataFrame) -> pd.DataFrame:
    """Group flagged cells into per-series runs and say which COLUMN moved.

    See the module docstring: the per-cell table cannot express either how far a defective
    run really extends or which of the two cells is the wrong one, and both change the fix.

    `area` and `prod` are the pre-merge per-column series, so a column's own level outside
    the run is measured over EVERY year it reports -- not only the years where the other
    column happens to be present too. That matters: iia china sesame seed reports production
    for 1922-24 and 1939-45 with no area at all, and those years are what show the 1930-33
    production level to be normal for the source and the 65-126 ha area to be the defect.
    """
    import math
    m = m.copy()
    m["log_dev"] = [math.log10(y / r) if (r and r == r and y > 0) else float("nan")
                    for y, r in zip(m["yield_t_ha"], m["ref_yield"])]
    m["anom"] = m["log_dev"].abs() >= ANOM_ORDERS
    flagged = {(s, c, i): set() for s, c, i in
               zip(bad["source"], bad["country"], bad["item"])}
    for s, c, i, y in zip(bad["source"], bad["country"], bad["item"], bad["year"]):
        flagged[(s, c, i)].add(y)

    key = ["source", "country", "item"]
    a_idx = {k: g for k, g in area.groupby(key, dropna=False)}
    p_idx = {k: g for k, g in prod.groupby(key, dropna=False)}

    rows = []
    for k, ser in m.groupby(key, dropna=False):
        if k not in flagged:
            continue
        anom_years = set(ser.loc[ser["anom"], "year"])
        for run in _runs_of(ser, flagged[k]):
            ar = pr = float("nan")
            basis = "none"
            # A column's OWN level outside every anomalous year of the series, taken over
            # the years nearest the run (see NEAR_YEARS).
            mid = run["year"].median()
            out_a = _near_level(a_idx.get(k, area.iloc[:0]), "area_ha", anom_years, mid)
            out_p = _near_level(p_idx.get(k, prod.iloc[:0]), "prod_t", anom_years, mid)
            n_clean = min(len(out_a), len(out_p))
            peers = m[(m["source"] == k[0]) & (m["item"] == k[2])
                      & (m["country"] != k[1]) & (m["log_dev"].abs() <= CLEAN_ORDERS)]
            if n_clean >= MIN_CLEAN_YEARS:
                basis = "within-series"
                ar = run["area_ha"].median() / out_a.median()
                pr = run["prod_t"].median() / out_p.median()
            else:
                if len(peers) >= MIN_PEERS:
                    basis = "peer-range"
                    # A ratio to the peer MEDIAN is meaningless across countries of
                    # different size, so the test here is CONTAINMENT in the source's own
                    # cross-country range for the item. A column inside the range is
                    # reported as ratio 1 (nothing to explain); one outside is reported as
                    # its ratio to the nearer edge, which is what has to be explained.
                    edge = {}
                    for col in ("area_ha", "prod_t"):
                        lo, hi = peers[col].quantile(0.10), peers[col].quantile(0.90)
                        v = run[col].median()
                        edge[col] = (v / lo) if v < lo else ((v / hi) if v > hi else 1.0)
                    ar, pr = edge["area_ha"], edge["prod_t"]
            va, vp = _ratio_verdict(ar), _ratio_verdict(pr)
            moved = [n for n, v in (("area", va), ("production", vp)) if v == "moved"]
            suspect = [n for n, v in (("area", va), ("production", vp)) if v == "suspect"]
            direction = "+".join(moved) if moved else "undetermined"
            ref = run["ref_yield"].median()
            # The factor that restores the reference yield, computed on the column that moved.
            if direction == "production":
                fac = (run["area_ha"] * run["ref_yield"] / run["prod_t"]).median()
            elif direction == "area":
                fac = (run["prod_t"] / run["ref_yield"] / run["area_ha"]).median()
            else:
                fac = float("nan")
            # Rounded to the 3 significant figures actually written, so the boolean below
            # and any downstream re-derivation are computed on the SAME number a reader
            # sees rather than on an unwritten full-precision one.
            facr = float(f"{fac:.3g}") if fac == fac else ""

            # --- can this be repaired WITHOUT the source page? (issue 111) ---------------
            # The yardstick is NOT a fixed window around 10^n. It is the dispersion the
            # CLEAN observations themselves show around whichever level anchors the run,
            # because a residual is only evidence against the decimal-shift hypothesis if
            # it is larger than the noise the same series (or the same source's other
            # countries) already exhibits. See the module docstring.
            clean_pair = ser[(~ser["year"].isin(anom_years))
                             & (ser["log_dev"].abs() <= CLEAN_ORDERS)]
            clean_pair = clean_pair.assign(_d=(clean_pair["year"] - mid).abs()) \
                                   .nsmallest(NEAR_YEARS, "_d")
            n_own = len(clean_pair)
            own = clean_pair["yield_t_ha"].median() if n_own else float("nan")
            if n_own >= MIN_CLEAN_YEARS:
                anchor_basis, anchor, spread = "own-clean-years", own, \
                    clean_pair["yield_t_ha"] / own
            elif len(peers) >= MIN_PEERS:
                anchor_basis, anchor, spread = "peer-countries", ref, \
                    peers["yield_t_ha"] / ref
            else:
                anchor_basis, anchor, spread = "none", ref, None
            band_lo = band_hi = float("nan")
            if spread is not None and len(spread):
                band_lo = float(spread.quantile(BAND_Q[0]))
                band_hi = float(spread.quantile(BAND_Q[1]))
            if direction == "production" and anchor == anchor and anchor > 0:
                afac = (run["area_ha"] * anchor / run["prod_t"]).median()
            elif direction == "area" and anchor == anchor and anchor > 0:
                afac = (run["prod_t"] / anchor / run["area_ha"]).median()
            else:
                afac = float("nan")
            afacr = float(f"{afac:.3g}") if afac == afac else ""
            resid = (afacr / 10.0 ** nearest_power_of_ten(afacr)) if afacr != "" else \
                float("nan")
            if direction not in ("area", "production"):
                verdict = "no-direction"
            elif afacr == "" or not is_clean_power_of_ten(afacr):
                verdict = "not-a-shift"
            elif band_lo != band_lo:
                verdict = "shift-unyardsticked"
            elif band_lo <= resid <= band_hi:
                verdict = "decimal-shift"
            else:
                verdict = "shift-outside-noise"

            rows.append({
                "source": k[0], "country": k[1], "item": k[2],
                "year_first": int(run["year"].min()), "year_last": int(run["year"].max()),
                "n_paired_in_run": len(run),
                "n_flagged_cells": int(sum(y in flagged[k] for y in run["year"])),
                "median_orders_out": round(run["log_dev"].median(), 2),
                "direction": direction,
                "direction_basis": basis,
                "secondary_suspect": "+".join(suspect),
                "area_ratio_vs_basis": float(f"{ar:.3g}") if ar == ar else "",
                "prod_ratio_vs_basis": float(f"{pr:.3g}") if pr == pr else "",
                "clean_years_in_series": n_clean,
                "run_area_ha_median": float(f"{run['area_ha'].median():.4g}"),
                "run_prod_t_median": float(f"{run['prod_t'].median():.4g}"),
                "near_area_ha_median": (float(f"{out_a.median():.4g}") if len(out_a) else ""),
                "near_prod_t_median": (float(f"{out_p.median():.4g}") if len(out_p) else ""),
                "implied_factor": facr,
                "implied_factor_pow10": nearest_power_of_ten(fac) if fac == fac else "",
                # Whether the run really IS off by a clean power of ten, on the same 50%
                # window the per-cell table's `looks_like_power_of_ten` uses. Without
                # this the pow10 column reads as an assertion, and it is only the
                # NEAREST power of ten: iia congo coffee needs x26.1, not x10.
                "implied_factor_is_pow10": (is_clean_power_of_ten(facr)
                                            if fac == fac else ""),
                "ref_yield": round(ref, 3) if ref == ref else "",
                # --- repairability without the source page (issue 111) --------------------
                "own_level_yield": round(own, 4) if own == own else "",
                "own_clean_pairs": n_own,
                "repair_anchor_basis": anchor_basis,
                "repair_anchor_yield": (round(anchor, 4) if anchor == anchor else ""),
                "anchor_factor": afacr,
                "noise_band_lo": round(band_lo, 3) if band_lo == band_lo else "",
                "noise_band_hi": round(band_hi, 3) if band_hi == band_hi else "",
                "repair_residual": (round(resid, 3) if resid == resid else ""),
                "repairable_without_source": verdict,
                # The repair itself, and ONLY where it is licensed: an exact power of ten,
                # never the fitted factor. Blank is the instruction "do not repair this".
                "repair_factor": (10.0 ** nearest_power_of_ten(afacr)
                                  if verdict == "decimal-shift" else ""),
                "years": ";".join(str(int(y)) for y in sorted(run["year"])),
            })
    out = pd.DataFrame(rows)
    if len(out):
        out = out.sort_values("n_paired_in_run", ascending=False)
    return out


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

    ser = series_pass(m, bad, area, prod)
    ser_path = os.path.join(H, "yield_series_corrections.csv")
    ser.to_csv(ser_path, index=False)

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

    multi = ser[ser["n_paired_in_run"] >= 3]
    print(f"\nseries pass: {len(ser)} defective runs, "
          f"{int(ser['n_paired_in_run'].sum())} paired observations inside them "
          f"vs {int(ser['n_flagged_cells'].sum())} cells the per-cell test flagged")
    print(f"  runs of 3+ years (a unit error, not a slip): {len(multi)} covering "
          f"{int(multi['n_paired_in_run'].sum())} observations "
          f"({int(multi['n_flagged_cells'].sum())} flagged cells)")
    print(f"  direction decided: {dict(ser['direction'].value_counts())}")
    fac_rows = ser[ser["implied_factor"] != ""]
    print(f"  runs with a repair factor: {len(fac_rows)}, of which a clean power of ten: "
          f"{int((fac_rows['implied_factor_is_pow10'] == True).sum())}"  # noqa: E712
          f" -- the rest are NOT x10^n and must not be repaired as if they were")
    print(f"  basis: {dict(ser['direction_basis'].value_counts())}")
    # Issue 111's remaining question: what can be repaired WITHOUT the yearbook page.
    print("  repairable without the source page:")
    for v, n in ser["repairable_without_source"].value_counts().items():
        sub = ser[ser["repairable_without_source"] == v]
        print(f"    {v:20s} {n:2d} run(s), {int(sub['n_flagged_cells'].sum()):2d} "
              f"flagged cell(s), {int(sub['n_paired_in_run'].sum()):3d} paired observation(s)")
    lic = ser[ser["repairable_without_source"] == "decimal-shift"]
    if len(lic):
        rr = lic["repair_residual"].astype(float)
        print(f"  the licensed set's residuals after its 10^n repair: "
              f"{rr.min():.2f}x-{rr.max():.2f}x, each inside ITS OWN clean-year noise band")
    for r in multi.itertuples():
        print(f"  {str(r.source):8s} {str(r.country)[:26]:26s} {str(r.item)[:24]:24s} "
              f"{r.year_first}-{r.year_last}  n={r.n_paired_in_run:2d} "
              f"(flagged {r.n_flagged_cells:2d})  {r.direction:13s} x{r.implied_factor} "
              f"[{r.direction_basis}] {r.repairable_without_source}"
              + (f"  secondary: {r.secondary_suspect}" if r.secondary_suspect else ""))
    print(f"\nwrote state/yield_series_corrections.csv ({len(ser)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
