#!/usr/bin/env python3
"""Internal-consistency check and repair table for the FAO 1952 land-use series.

The land-use block is self-checking: for a given (polity, year) the component
categories must sum to `use total`, and `use total` must equal the territory's
own land area. That makes bad cells both DETECTABLE and RECOVERABLE — the
correct value of a single bad component is total minus the sum of the others.

Hypotheses are tried in order of how much evidence they carry, and only one is
recorded per bad cell:

  1. SPURIOUS ROW — drop the cell. The *other* components already sum to `use
     total` to within a hair, so this cell is an extra/duplicated row rather than
     a corrupted number. AOF 1950: arable+pastures+builton+forests = 471,149 =
     use total exactly, and `unused productive land` 14,701 is the extra row.
  2. DECIMAL POINT DROPPED (x10 / x100 / x1000) — bad == good x 10^k to within
     one unit, i.e. the shift is *exact*, not merely the right order of
     magnitude. Ruanda-Urundi 1951: builton 12,581 for 1,258.1.
  3. DIGITS PREPENDED — the decimal string of the recorded value ends with the
     decimal string of the implied one. Brazil 1947: arable 1,918,835 for 18,835
     ("19" prepended). Note this is NOT a x100 decimal shift: 18,835 x 100 is
     1,883,500. The earlier version of this script tested the ratio 101.9
     against x100 with a 2% window and mislabelled it.
  4. UNIFORM DECIMAL SHIFT ACROSS SEVERAL CELLS — every component that is
     individually larger than `use total` (so individually impossible) divided
     by the same 10^k makes the block consistent. Guam 1951: builton 8,361 and
     unused 12,118 for 8.361 and 12.118; the block then sums to 54.5 against a
     use total of 54 (Guam's own polygon measures 55, in the same 1000 ha).
  5. otherwise: reported as an inconsistency with no single-cell story. Most of
     these are short of `use total` by a suspiciously round amount (1,000 /
     2,000 / 6,000 / 10,000), which looks like a *missing* category row; they are
     flagged, deliberately not auto-corrected.

`use land` is NOT in COMPONENTS: it is a sub-aggregate of `use total` (Brazil
1947: land 846,420 vs total 851,604) and what it excludes is not documented, so
blocks whose only fault is a bad `use land` are out of scope here.

This script does NOT modify the source parquet (it lives outside the repo, in
the maintainer's own store). It writes a correction table so the fix can be
applied upstream in the consolidation step, where it belongs. `action` says what
the upstream applier should do: `replace_value` or `drop_row`; `(multiple)` rows
carry `action=review`.

Usage:
  python3 pipelines/polity-autoimprove/06_landuse_consistency.py
Writes state/landuse_corrections.csv
"""
import pandas as pd, geopandas as gpd, os, warnings
warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H = os.path.join(REPO, "pipelines/polity-autoimprove/state")

# component categories that should sum to `use total`
COMPONENTS = ["use agricultural area arable land orchards",
              "use agricultural area permanent peadows pastures",
              "use builton wasteland",
              "use forests woodlands",
              "use unused productive land"]
TOTAL = "use total"

m = pd.read_parquet(os.path.join(H, "matched_rows.parquet"))
lu = m[m["item"].astype(str).str.startswith("use ")].copy()
lu["v"] = pd.to_numeric(lu["value"], errors="coerce")

g = gpd.read_file(os.path.join(REPO, "data/final/polities_database.gpkg"))
g = g[g.geometry.notna() & ~g.geometry.is_empty]
g["terr_1000ha"] = (g.to_crs("ESRI:54034").geometry.area / 1e6) * 100 / 1000  # km2 -> 1000 ha
terr = dict(zip(g.polity_code, g.terr_1000ha))

def tol(total):
    """Consistency window on a block sum. 2% of total, at least 1 unit."""
    return max(1.0, 0.02 * total)


def exact_pow10(n):
    """The exponent if n is EXACTLY a power of ten, else None. Exact, not within a window: the whole
    point is that a residual of 1,000 is a different animal from one of 1,036."""
    if n <= 0:
        return None
    k = 0
    v = float(n)
    while v >= 10 and abs(v / 10 - round(v / 10)) < 1e-9:
        v /= 10
        k += 1
    return k if abs(v - 1.0) < 1e-9 and k >= 1 else None


def exact_shift(bad, good):
    """k such that bad == good * 10^k to within one unit, else None.

    Requires the shift to be *exact* (up to the rounding the printed value would
    have suffered), so a ratio that merely lands near 100 cannot pass.
    """
    for k in (3, 2, 1):
        if abs(bad - good * 10 ** k) <= 1.0:
            return k
    return None


rows = []
n_blocks_bad = 0
for (code, year), grp in lu.groupby(["whep_code", "year"]):
    vals = dict(zip(grp["item"].astype(str), grp.v))
    total = vals.get(TOTAL)
    present = [c for c in COMPONENTS if c in vals]
    if total is None or len(present) < 2: continue
    comp_sum = sum(vals[c] for c in present)
    if abs(comp_sum - total) <= tol(total):       # consistent within 2%
        continue
    n_blocks_bad += 1
    base = {"polity_code": code, "year": int(year), "use_total": total,
            "territory_1000ha": round(terr.get(code, float("nan")), 1),
            "components_present": len(present)}

    # (1) one component is a spurious extra row: the others already sum to total
    spurious = [c for c in present
                if abs((comp_sum - vals[c]) - total) <= max(0.5, 0.001 * total)]
    if len(spurious) == 1:
        c = spurious[0]
        rows.append({**base, "item": c, "recorded": vals[c], "implied_correct": "",
                     "action": "drop_row",
                     "diagnosis": f"spurious row: the other {len(present)-1} components "
                                  f"already sum to use total"})
        continue

    # (2)/(3) a single corrupted component: replacing it with (total - others)
    # makes the block consistent, and the replacement is a digit/decimal variant
    single = None
    for c in present:
        implied = total - (comp_sum - vals[c])
        bad, good = vals[c], implied
        if implied < 0 or good == 0 or bad == 0 or bad <= good: continue
        k = exact_shift(bad, good)
        if k is not None:
            single = (c, bad, good, f"decimal point dropped (x{10 ** k})")
            break
        if str(int(round(bad))).endswith(str(int(round(good)))):
            single = (c, bad, good, "digits prepended")
            break
        if bad / good > 2 and single is None:
            # weakest story; keep looking, a cleaner one on another cell wins
            single = (c, bad, good, "value too large (basis unclear)")
    if single:
        c, bad, good, kind = single
        # the arithmetic forces the value either way, but with no digit/decimal
        # story behind it the cell is not safe to rewrite unattended
        act = "review_cell" if kind.startswith("value too large") else "replace_value"
        rows.append({**base, "item": c, "recorded": bad,
                     "implied_correct": round(good, 3), "action": act,
                     "diagnosis": kind})
        continue

    # (4) several cells share one decimal shift. Candidates are the components
    # that individually exceed use total, so are individually impossible.
    impossible = [c for c in present if vals[c] > total]
    fixed = None
    if len(impossible) >= 2:
        rest = sum(vals[c] for c in present if c not in impossible)
        for k in (1000, 100, 10):
            if abs(rest + sum(vals[c] / k for c in impossible) - total) <= tol(total):
                fixed = k
                break
    if fixed:
        for c in impossible:
            rows.append({**base, "item": c, "recorded": vals[c],
                         "implied_correct": round(vals[c] / fixed, 3),
                         "action": "replace_value",
                         "diagnosis": f"decimal point dropped (x{fixed}), "
                                      f"{len(impossible)} cells in this block"})
        continue

    # (4b) THE DROPPED LEADING DIGIT, which cases (2)/(3) structurally cannot reach.
    #
    # The single-component search above skips any candidate with `bad <= good`, so it only ever
    # considers cells that came out too LARGE. Every diagnosis it can emit -- "digits prepended",
    # "decimal point dropped", "value too large" -- describes that direction. The characteristic
    # FAO-1952 fault is the opposite: a dropped leading `1`, leaving the cell exactly 10^k low
    # (Netherlands 1951 arable land recorded as 43 against an implied 1,043). Those blocks all fell
    # through to case (5) and were reported as free text, so the most common error mode in this source
    # was the one the tool could not name. Nine blocks, measured before this branch existed.
    #
    # The signature is that the residual is EXACTLY a power of ten. That is a much narrower
    # coincidence than it looks: ordinary residuals here run 194, 477, 1,036, 2,036, 6,444, 8,000 --
    # the free-text bucket has 14 such rows against 9 exact powers of ten.
    resid = total - comp_sum
    k = exact_pow10(abs(resid))
    if k is not None and k >= 1:
        step = 10 ** k
        if resid > 0:
            # A COMPONENT is low by 10^k. Which one cannot be settled from arithmetic: any component
            # smaller than 10^k had an empty leading-digit position and so is a candidate. Reported as
            # a candidate list rather than a guess.
            #
            # AND NO WITHIN-SERIES TEST CAN NARROW IT. fao1952 publishes exactly ONE land-use year per
            # territory -- verified for all seven positive-residual blocks (NLD, GBR, JPN 1951; ECU,
            # SLB 1949; LBR, JAM 1948; HUN 1947) -- so a component cannot be compared against its own
            # neighbouring years. The Netherlands identification in the literature rests on knowing
            # Dutch land use, which is external evidence this tool does not have.
            cands = sorted((c for c in present if vals[c] < step), key=lambda c: vals[c])
            rows.append({**base, "item": "(multiple)", "recorded": comp_sum,
                         "implied_correct": total, "action": "review",
                         "diagnosis": (f"leading digit dropped: one component is low by exactly "
                                       f"{step:,} (10^{k}); {len(cands)} candidate(s) below that "
                                       f"place value: " + ", ".join(
                                           f"{c}={vals[c]:,.0f}" for c in cands))})
            continue
        # resid < 0: the components EXCEED the total by exactly 10^k, so it is the TOTAL that lost its
        # leading digit. Uniquely identified, unlike the positive case -- and often confirmed outright,
        # because another row in the same block already carries the components' sum. Jamaica 1948:
        # `use total` reads 142, the components sum to 1,142, and `use land` reads 1,142.
        # Searched over EVERY row in the block, not just the components. The corroborating figure is
        # typically `use land`, which is not one of the five components -- restricting the search to
        # `present` reported "no corroborating row" for Jamaica 1948 even though `use land` reads
        # 1,142 there, exactly the components' sum.
        confirm = [c for c in vals
                   if c != TOTAL and abs(vals[c] - comp_sum) <= tol(comp_sum)]
        rows.append({**base, "item": "use total", "recorded": total,
                     "implied_correct": round(comp_sum, 3),
                     "action": "replace_value" if confirm else "review",
                     "diagnosis": (f"leading digit dropped from the TOTAL: low by exactly "
                                   f"{step:,} (10^{k})"
                                   + (f"; confirmed by {confirm[0]}={vals[confirm[0]]:,.0f}"
                                      if confirm else "; no corroborating row in the block"))})
        continue

    # (5) no single-cell story: report the inconsistency itself
    rows.append({**base, "item": "(multiple)", "recorded": comp_sum,
                 "implied_correct": total, "action": "review",
                 "diagnosis": f"components sum to {comp_sum:,.0f} but total is {total:,.0f}"})

COLS = ["polity_code", "year", "item", "recorded", "implied_correct", "action",
        "diagnosis", "use_total", "territory_1000ha", "components_present"]
out = pd.DataFrame(rows, columns=COLS)
if len(out):
    out = out.sort_values("recorded", ascending=False)
    out.to_csv(os.path.join(H, "landuse_corrections.csv"), index=False)
APPLY = {"replace_value", "drop_row"}
n_rows_ok = int(out.action.isin(APPLY).sum()) if len(out) else 0
n_blocks_ok = out[out.action.isin(APPLY)].groupby(["polity_code", "year"]).ngroups if len(out) else 0
n_cell_only = int((out.action == "review_cell").sum()) if len(out) else 0
print(f"land-use (polity, year) blocks checked: {lu.groupby(['whep_code','year']).ngroups}")
print(f"inconsistent blocks: {n_blocks_bad}   correction rows: {len(out)}")
print(f"  recoverable: {n_blocks_ok} blocks / {n_rows_ok} cells (action replace_value|drop_row)")
print(f"  cell located, no digit story: {n_cell_only} (action review_cell)")
print(f"  no single-cell story at all: {int((out.action == 'review').sum())} (action review)\n")
if len(out):
    for r in out.itertuples():
        good = f"{r.implied_correct:>10,.3f}" if r.implied_correct != "" else "     (drop)"
        print(f"  {r.polity_code:16s} {r.year}  {r.item[:44]:44s} "
              f"{r.recorded:>12,.0f} -> {good}   [{r.diagnosis}]")
    print(f"\nwrote {os.path.join(H,'landuse_corrections.csv')}")
