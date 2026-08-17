#!/usr/bin/env python3
"""Validate the area x yield correction tables against their own arithmetic.

`pipelines/polity-autoimprove/07_yield_consistency.py` (issues #29, #111) writes two
repair tables from layer B, which lives OUTSIDE this repository:

  state/yield_corrections.csv         one row per cell whose implied yield is physically
                                      impossible, with what each of the two possible
                                      repairs would imply
  state/yield_series_corrections.csv  one row per defective RUN, with which COLUMN moved
                                      and the factor that restores the reference yield

Both are consumed by a human or a script that then edits the upstream parquet. Nothing else
in this repository reads them, so nothing else would notice if a row's stated diagnosis
stopped matching its own numbers — and every column a consumer acts on is derived, not
observed: `direction` from the two ratio columns, `implied_factor` from the run's medians,
`looks_like_power_of_ten` from the ratio. This gate re-derives all of them from the numbers
in the same row, so a generator change cannot quietly ship a table whose labels and figures
disagree. Because layer B is absent in CI, re-running the generator is not an option there;
re-deriving from the committed table is.

The defect that motivated it is real. Until 2026-08-17 the series table carried
`implied_factor_pow10` and nothing else, always populated with the NEAREST power of ten:

    iia congo "coffee, green" 1922-1934   direction=production  implied_factor 26.1
                                          implied_factor_pow10  1

A consumer repairing that run by x10 lands 2.6x away from the factor the table itself
computed, and iia congo green coffee at 114 t against a 2,986 t implied level is exactly the
kind of run someone would batch-fix by powers of ten. Re-measuring issue #111's "off by a
constant power of ten" headline showed it is true of 14 of the 28 runs with a factor and 5
of the 9 multi-year ones, so the generator now also writes `implied_factor_is_pow10` and
this gate holds it to the same 50% window the per-cell table uses.

WHAT IS CHECKED

  per-cell table   yield_t_ha == prod_t / area_ha; ratio_to_ref == yield / ref_yield;
                   orders_out is the nearest power of ten of that ratio;
                   looks_like_power_of_ten is that ratio within 50% of 10^orders_out and
                   orders_out != 0; prod_t_if_area_ok == area x ref; area_ha_if_prod_ok ==
                   prod / ref; and every row really is outside the [LO, HI] physical band,
                   because a row inside it is not a detection at all.

  series table     years <-> n_paired_in_run / year_first / year_last;
                   1 <= n_flagged_cells <= n_paired_in_run;
                   direction and secondary_suspect re-derived from the ratio columns at the
                   generator's documented 10x / 3x thresholds;
                   direction_basis `within-series` iff clean_years_in_series >= 3;
                   implied_factor present iff exactly one column moved -- never for
                   `undetermined` and never for `area+production`, where a factor would
                   invite an unattended rewrite of a cell nobody has attributed;
                   the factor points the RIGHT WAY (a production factor above 1 only where
                   the yield is too LOW, an area factor above 1 only where it is too HIGH),
                   since a factor inverted against a 2-order defect is a 10,000x edit;
                   implied_factor_is_pow10 re-derived, as above.

  across tables    every flagged cell falls inside a run of its own series, and the runs'
                   n_flagged_cells sums to the per-cell table's row count. A series row
                   lost in a refactor would otherwise silently strip 44 cells of the
                   series-level diagnosis that is the whole point of issue #111.

Usage:
  python3 scripts/validate_yield_corrections.py
Exit 1 if any derived column disagrees with the numbers in its own row.
"""
import csv
import math
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(REPO, "pipelines/polity-autoimprove/state")
CELLS = os.path.join(STATE, "yield_corrections.csv")
SERIES = os.path.join(STATE, "yield_series_corrections.csv")

# The generator's own constants. Duplicated deliberately: this gate must be able to judge
# the committed table in CI, where layer B is absent and the generator cannot run, and a
# gate that imported its thresholds from the code it audits would follow that code's drift.
HI, LO = 200.0, 0.01
MOVED_RATIO, SECONDARY_RATIO = 10.0, 3.0
MIN_CLEAN_YEARS = 3
POW10_WINDOW = 0.5

CELL_COLUMNS = ["source", "country", "item", "year", "area_ha", "prod_t", "yield_t_ha",
                "ref_yield", "ratio_to_ref", "orders_out", "looks_like_power_of_ten",
                "prod_t_if_area_ok", "area_ha_if_prod_ok"]
SERIES_COLUMNS = ["source", "country", "item", "year_first", "year_last",
                  "n_paired_in_run", "n_flagged_cells", "median_orders_out", "direction",
                  "direction_basis", "secondary_suspect", "area_ratio_vs_basis",
                  "prod_ratio_vs_basis", "clean_years_in_series", "implied_factor",
                  "implied_factor_pow10", "implied_factor_is_pow10", "ref_yield", "years"]
BASES = {"within-series", "peer-range", "none"}
DIRECTIONS = {"production", "area", "area+production", "undetermined"}


def num(s):
    """A float, or None for a blank / unparseable cell (both tables leave blanks)."""
    try:
        v = float(str(s).strip())
    except (TypeError, ValueError):
        return None
    return None if v != v else v


def near(got, want, tol=1e-3):
    return got is not None and abs(got - want) <= tol * max(1.0, abs(want))


def pow10(ratio):
    return int(round(math.log10(ratio))) if ratio and ratio > 0 else 0


def is_pow10(ratio):
    if ratio is None or ratio <= 0:
        return False
    p = pow10(ratio)
    return p != 0 and abs(ratio / (10.0 ** p) - 1.0) < POW10_WINDOW


def verdict(ratio):
    """`moved` / `suspect` / `` for one column's ratio to its basis."""
    if ratio is None or ratio <= 0:
        return ""
    if ratio >= MOVED_RATIO or ratio <= 1.0 / MOVED_RATIO:
        return "moved"
    if ratio >= SECONDARY_RATIO or ratio <= 1.0 / SECONDARY_RATIO:
        return "suspect"
    return ""


def read(path):
    if not os.path.exists(path):
        print(f"FAIL: {os.path.relpath(path, REPO)} is missing")
        sys.exit(1)
    with open(path, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return rows, (list(rows[0].keys()) if rows else [])


cells, cell_header = read(CELLS)
series, series_header = read(SERIES)

problems = []
for want, header, name in ((CELL_COLUMNS, cell_header, "yield_corrections.csv"),
                           (SERIES_COLUMNS, series_header, "yield_series_corrections.csv")):
    absent = [c for c in want if c not in header]
    if absent:
        problems.append(f"{name}: columns a consumer reads by name are absent: {absent}")
if problems:
    print("\n".join(f"   FAIL {p}" for p in problems))
    print(f"\nFAIL: {len(problems)} problem(s)")
    sys.exit(1)

# --- per-cell table ---------------------------------------------------------------------
for r in cells:
    where = f"{r['source']} {r['country']} {r['item']} {r['year']}"
    a, p = num(r["area_ha"]), num(r["prod_t"])
    y, ref = num(r["yield_t_ha"]), num(r["ref_yield"])
    ratio, orders = num(r["ratio_to_ref"]), num(r["orders_out"])
    if None in (a, p, y, ref, ratio, orders) or a <= 0 or p <= 0 or ref <= 0:
        problems.append(f"{where}: a detection with a missing or non-positive number "
                        f"(area={r['area_ha']!r} prod={r['prod_t']!r} "
                        f"ref={r['ref_yield']!r}) — nothing can be re-derived from it")
        continue
    if not near(y, p / a):
        problems.append(f"{where}: yield_t_ha {y:g} is not prod_t / area_ha "
                        f"({p:g} / {a:g} = {p / a:g})")
    if not near(ratio, y / ref):
        problems.append(f"{where}: ratio_to_ref {ratio:g} is not yield / ref_yield "
                        f"({y:g} / {ref:g} = {y / ref:g})")
    if int(orders) != pow10(ratio):
        problems.append(f"{where}: orders_out {int(orders)} is not the nearest power of "
                        f"ten of ratio_to_ref {ratio:g} ({pow10(ratio)})")
    said = str(r["looks_like_power_of_ten"]).strip().lower() == "true"
    real = int(orders) != 0 and abs(ratio / (10.0 ** int(orders)) - 1.0) < POW10_WINDOW
    if said != real:
        problems.append(
            f"{where}: looks_like_power_of_ten={said} but ratio_to_ref {ratio:g} is "
            f"{'not ' if not real else ''}within {POW10_WINDOW:.0%} of 10^{int(orders)} — "
            f"a consumer shifting the decimal would land "
            f"{'nowhere near' if not real else 'on'} the recorded value"
        )
    if not near(num(r["prod_t_if_area_ok"]), a * ref):
        problems.append(f"{where}: prod_t_if_area_ok {r['prod_t_if_area_ok']} is not "
                        f"area x ref_yield ({a * ref:g})")
    if not near(num(r["area_ha_if_prod_ok"]), p / ref):
        problems.append(f"{where}: area_ha_if_prod_ok {r['area_ha_if_prod_ok']} is not "
                        f"prod / ref_yield ({p / ref:g})")
    if LO <= y <= HI:
        problems.append(f"{where}: implied yield {y:g} t/ha is inside the physical band "
                        f"[{LO}, {HI}], so this row is not a detection")

# --- series table -----------------------------------------------------------------------
runs = {}
for r in series:
    where = (f"{r['source']} {r['country']} {r['item']} "
             f"{r['year_first']}-{r['year_last']}")
    years = [int(y) for y in str(r["years"]).split(";") if y.strip()]
    n_paired, n_flag = num(r["n_paired_in_run"]), num(r["n_flagged_cells"])
    if len(years) != n_paired:
        problems.append(f"{where}: years lists {len(years)} year(s) but "
                        f"n_paired_in_run is {n_paired:g}")
    if years and (min(years) != int(r["year_first"]) or max(years) != int(r["year_last"])):
        problems.append(f"{where}: years spans {min(years)}-{max(years)}, not the stated "
                        f"{r['year_first']}-{r['year_last']}")
    if not (n_flag and 1 <= n_flag <= (n_paired or 0)):
        problems.append(f"{where}: n_flagged_cells {n_flag} is not between 1 and "
                        f"n_paired_in_run {n_paired} — a run exists because a cell in it "
                        f"was flagged")
    runs.setdefault((r["source"], r["country"], r["item"]), set()).update(years)

    if r["direction"] not in DIRECTIONS:
        problems.append(f"{where}: direction {r['direction']!r} is not one of "
                        f"{sorted(DIRECTIONS)}")
    if r["direction_basis"] not in BASES:
        problems.append(f"{where}: direction_basis {r['direction_basis']!r} is not one of "
                        f"{sorted(BASES)}")
    clean = num(r["clean_years_in_series"]) or 0
    if (r["direction_basis"] == "within-series") != (clean >= MIN_CLEAN_YEARS):
        problems.append(
            f"{where}: direction_basis={r['direction_basis']} with "
            f"{clean:g} clean year(s); the series' own clean years are the basis only at "
            f"{MIN_CLEAN_YEARS}+, below which the fallback is the cross-country range"
        )

    ar, pr = num(r["area_ratio_vs_basis"]), num(r["prod_ratio_vs_basis"])
    va, vp = verdict(ar), verdict(pr)
    moved = [n for n, v in (("area", va), ("production", vp)) if v == "moved"]
    suspect = [n for n, v in (("area", va), ("production", vp)) if v == "suspect"]
    want_dir = "+".join(moved) if moved else "undetermined"
    want_sus = "+".join(suspect)
    if r["direction"] != want_dir:
        problems.append(
            f"{where}: direction={r['direction']!r} but area_ratio={r['area_ratio_vs_basis']} "
            f"and prod_ratio={r['prod_ratio_vs_basis']} imply {want_dir!r} at the "
            f"{MOVED_RATIO:g}x threshold — the column named here is the one a fixer edits"
        )
    if str(r["secondary_suspect"]).strip() != want_sus:
        problems.append(f"{where}: secondary_suspect={r['secondary_suspect']!r} but the "
                        f"ratios imply {want_sus!r} at the {SECONDARY_RATIO:g}x threshold")

    fac = num(r["implied_factor"])
    single = r["direction"] in ("production", "area")
    if single and fac is None:
        problems.append(f"{where}: direction={r['direction']} names one column but no "
                        f"implied_factor says by how much")
    if fac is not None and not single:
        problems.append(
            f"{where}: direction={r['direction']} attributes the defect to no single "
            f"column, yet implied_factor={fac:g} invites an unattended repair"
        )
    if fac is not None and single:
        orders = num(r["median_orders_out"])
        too_low = orders is not None and orders < 0
        want_up = too_low if r["direction"] == "production" else not too_low
        if (fac > 1.0) != want_up:
            problems.append(
                f"{where}: median_orders_out {orders:g} says the yield is too "
                f"{'LOW' if too_low else 'HIGH'}, so the {r['direction']} factor must be "
                f"{'above' if want_up else 'below'} 1, but it is {fac:g} — applying it "
                f"would move the cell further out by the same orders again"
            )
        said = str(r["implied_factor_is_pow10"]).strip().lower() == "true"
        if said != is_pow10(fac):
            problems.append(
                f"{where}: implied_factor_is_pow10={said} but the factor {fac:g} is "
                f"{'not ' if not is_pow10(fac) else ''}within {POW10_WINDOW:.0%} of "
                f"10^{pow10(fac)}; implied_factor_pow10 is only the NEAREST power of ten, "
                f"so repairing this run by 10^{pow10(fac)} would land "
                f"{fac / 10.0 ** pow10(fac):.3g}x away from the table's own factor"
            )

# --- across the two tables --------------------------------------------------------------
orphans = [f"{r['source']} {r['country']} {r['item']} {r['year']}" for r in cells
           if int(r["year"]) not in runs.get((r["source"], r["country"], r["item"]), set())]
if orphans:
    problems.append(
        f"{len(orphans)} flagged cell(s) fall inside no run of their own series, so they "
        f"carry no series-level diagnosis: {orphans[:5]}"
    )
total_flagged = sum(int(num(r["n_flagged_cells"]) or 0) for r in series)
if total_flagged != len(cells):
    problems.append(
        f"the runs account for {total_flagged} flagged cell(s) but the per-cell table has "
        f"{len(cells)} — the series pass must cover every detection exactly once"
    )

multi = [r for r in series if (num(r["n_paired_in_run"]) or 0) >= 3]
with_fac = [r for r in series if num(r["implied_factor"]) is not None]
clean_fac = [r for r in with_fac
             if str(r["implied_factor_is_pow10"]).strip().lower() == "true"]
print(f"{len(cells)} flagged cell(s), {len(series)} defective run(s) "
      f"({len(multi)} spanning 3+ paired years)")
print(f"  runs naming one column: {len(with_fac)}; of those a clean power of ten: "
      f"{len(clean_fac)}")

print(f"\nDERIVED COLUMNS DISAGREEING WITH THEIR OWN ROW: {len(problems)}")
for p in problems[:40]:
    print(f"   FAIL {p}")

print(f"\n{'FAIL' if problems else 'PASS'}: {len(problems)} problem(s) across "
      f"{len(cells)} cell row(s) and {len(series)} run row(s)")
sys.exit(1 if problems else 0)
