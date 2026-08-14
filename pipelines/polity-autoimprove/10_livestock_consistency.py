#!/usr/bin/env python3
"""Internal-consistency check and repair table for the FAO 1952 livestock block.

Issue 29 asked which OTHER series carry arithmetic we are not exploiting, and named
livestock as one: "heads x carcass weight = meat output". THAT IDENTITY IS NOT AVAILABLE,
and the reason is worth writing down because it is not the reason the issue assumed.

  1. Standing HERD is not SLAUGHTER. `livestock:livestock` counts animals alive at the
     census date; meat comes from the animals killed during the year, which is a fraction
     of the herd for cattle and MORE than the herd for pigs and poultry (a pig herd turns
     over faster than once a year). The product heads x carcass weight is therefore not
     meat output, it is an upper bound so loose that Belgium 1949 breaches it legitimately
     at 267 kg of meat per standing head against a 250 kg cattle carcass.
  2. The consolidated parquet cannot tell the species apart anyway. `item` = "meat" holds
     FOUR parallel yearbook columns under one label with no column distinguishing them:
     Argentina 1949 is four rows -- 1027, 139, 110, 276 -- and "horses mules asses" reaches
     16 rows for one country-year. A reader who sums layer B's item="meat" for Argentina
     1949 gets 1,552 where the yearbook's own total is 1,276: +21.6%, because the total row
     is summed together with its own components.

So the livestock arithmetic that IS available is the one 06_landuse_consistency.py already
exploits, and it is available for the same reason: THE MEAT TABLE'S COMPONENTS SUM TO ITS
STATED TOTAL. Recovering the lost column dimension makes that identity testable, and it
holds to the tonne for 204 of 218 country-years.

WHAT IT FOUND. All eleven mismatches in the four-column shape are EXACTLY 1,000 (1000 t),
which is a dropped leading "1" in the extraction -- and the identity says which cell and by
how much, so all eleven are recovered rather than merely flagged:

    Australia 1949   603 + 95 + 374 = 1,072   total recorded 72     -> 1,072
    Argentina 1949 1,027 + 139 + 110 = 1,276  total recorded 276    -> 1,276
    France    1950  11 + 790 + 100 vs total 1,901   -> the component 11    = 1,011
    Germany Western 1951 579 + 25 + 29 vs total 1,633 -> the component 25  = 1,025

Nine sit in the stated total, two in a component, and the two are the interesting ones
because the identity alone does not say which cell moved: any of four single-cell edits
would satisfy it. What decides is the column's own other years -- France's second column
runs 745-790 and rejects 1,790, while its first runs at 990 and rejects 11. The Germany
Western answer, 25 -> 1,025 for the second column, is confirmed independently: West German
pig meat in 1951 was of the order of a million tonnes, and 25,000 t would be 1.5% of that
country's meat supply.

The three remaining mismatches are a different fault. Cyprus's block has three of the four
columns and its total exceeds them by a constant 2 (1000 t) in all three years, which is not
a bad cell but a column the extraction never picked up. No correction is proposed for those.

THE SAME ERROR MODE IS ALREADY VISIBLE IN 06'S OUTPUT, undiagnosed: JPN-1945-1952 1951,
ECU-1942-2025 1949 and GBR-1921-2025 1951 all sit in landuse_corrections.csv as
"(multiple)" with a residual of exactly 1,000, and Netherlands 1951 arable land is 43
against an implied 1,043. 06's diagnoses only cover values that came out too LARGE (digits
prepended, decimal dropped); a dropped LEADING digit makes the value too SMALL and falls
through all of them. That is issue 4's table, not this script's, so it is reported and not
touched here.

SECOND PASS: CARCASS WEIGHTS AGAINST PHYSICAL BOUNDS. The per-animal carcass weights are
excluded from 05_magnitude_screen.py as "rate-like", so nothing checks them at all. They
are a per-animal mass, and an animal's dressed carcass has hard biological bounds -- a
sheep does not dress out at 627 kg and a calf does not dress out at 1 kg. Same logic as
07's yield ceiling: a physical constant, not a distribution. Five of the 562 carcass-weight
cells breach one: Northern Rhodesia sheep at 627 kg in 1950 and 1951 against its own 14 kg
in 1949, Spain at 69 against 11, Zanzibar and Pemba at 1 against 19, and Surinam calves at
1 kg with no in-bounds year of its own. None is a clean power of ten or a prepended digit,
so this pass flags and cites the country's in-bounds years and proposes no value.

HOW THE LOST COLUMN DIMENSION IS RECOVERED, and why this is checkable rather than assumed.
Within one (source_detail, country) the parquet's rows are the table's columns laid end to
end, each column carrying the same year/period sequence. A country is used only when its
rows are an exact k-fold repetition of one sequence of DISTINCT year/period keys; anything
else is skipped rather than guessed at. The ordering itself is then VALIDATED by the
identity: if row order did not carry the columns, the components would not sum to the total
anywhere, and the script refuses to assert a total column that does not reach
MIN_IDENTITY_RATE of its shape's country-years.

Like 06 and 07, this does NOT modify the source parquet (it lives outside the repo, in the
maintainer's own store). It writes a correction table so the fix lands upstream in the
consolidation step.

Usage:
  python3 pipelines/polity-autoimprove/10_livestock_consistency.py
Writes state/livestock_corrections.csv
"""
from __future__ import annotations

import os
import warnings

import pandas as pd

import extdata

warnings.filterwarnings("ignore")

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
H = os.path.join(REPO, "pipelines/polity-autoimprove/state")
OUT = os.path.join(H, "livestock_corrections.csv")

# The block this script reads. `indicator` distinguishes it from crops and land use.
LIVESTOCK_INDICATORS = ("livestock:production", "livestock:livestock")

# A total column is only accepted if the identity holds for this share of the shape's
# country-years. Measured on the current parquet: 0.936 (k=4) and 0.964 (k=3) in the meat
# table, and no other livestock table reaches it at all. If the parquet's row order ever
# stopped carrying the table's columns, every shape would fall below this and the script
# would assert nothing -- which is the point of the threshold.
MIN_IDENTITY_RATE = 0.90
MIN_IDENTITY_OBS = 20

# Tolerance for "the components sum to the total". The meat table is in 1000 t integers, so
# a genuine rounding residual is at most a tonne or two; 0.5% covers the wider tables.
def _tolerance(total: float) -> float:
    return max(1.0, 0.005 * abs(total))


# The extraction's characteristic error in this source: a leading "1" lost from a
# four-digit figure, i.e. the cell is exactly 1000 units low. See the docstring.
LEADING_DIGIT_STEP = 1000.0

# When more than one cell could carry the missing digit, the tie is broken by asking which
# correction AGREES BETTER with the cell's own column elsewhere -- and by this factor, so a
# marginal improvement decides nothing. A ratio-to-level that improves by less than 2x is
# treated as no evidence either way.
IMPROVE_FACTOR = 2.0

# Hard biological bounds on a DRESSED CARCASS, in kg, per species. These are physical
# constants with room to spare, not percentiles: the floor is below the lightest real
# national average (Greek and Italian suckling lamb dress out at 7-8 kg) and the ceiling is
# above the heaviest (Dutch cattle at 290 kg, Italian veal at 100 kg).
CARCASS_BOUNDS = {
    "carcass weights cattle": (40.0, 450.0),
    "carcass weights calves": (8.0, 150.0),
    "carcass weights sheep lambs": (4.0, 60.0),
}


def column_blocks(group: pd.DataFrame):
    """Split one (source_detail, country) group into the table columns row order carries.

    Returns (keys, columns) where `keys` is the year/period sequence each column repeats
    and `columns[i][j]` is column i's value for keys[j] -- or (None, None) when the group
    is not an exact k-fold repetition of a sequence of distinct keys, in which case the
    country is skipped rather than guessed at.
    """
    group = group.sort_values("_ord")
    keys = [(str(y), str(p)) for y, p in zip(group["year"], group["period"])]
    n = len(keys)
    for width in range(1, n + 1):
        if n % width:
            continue
        head = keys[:width]
        if len(set(head)) == width and keys == head * (n // width):
            values = list(group["value"])
            return head, [values[i * width:(i + 1) * width] for i in range(n // width)]
    return None, None


def shape_blocks(frame: pd.DataFrame):
    """Every (country, keys, columns) triple of one source_detail, grouped by column count."""
    out = {}
    for country, group in frame.groupby("country"):
        keys, columns = column_blocks(group)
        if keys is None or len(columns) < 2:
            continue
        out.setdefault(len(columns), []).append((country, keys, columns))
    return out


def find_total_column(blocks: list) -> tuple:
    """Which column index, if any, is the stated total, and how well the identity holds.

    Tries every position rather than assuming the total is last, and returns the position
    only if it reaches MIN_IDENTITY_RATE over enough observations.
    """
    width = len(blocks[0][2])
    best = (None, 0.0, 0)
    for candidate in range(width):
        ok = seen = 0
        for _country, keys, columns in blocks:
            others = [c for i, c in enumerate(columns) if i != candidate]
            for j in range(len(keys)):
                total = columns[candidate][j]
                comp = sum(c[j] for c in others)
                if pd.isna(total) or any(pd.isna(c[j]) for c in others):
                    continue
                seen += 1
                ok += abs(total - comp) <= _tolerance(total)
        rate = ok / seen if seen else 0.0
        if seen >= MIN_IDENTITY_OBS and rate > best[1]:
            best = (candidate, rate, seen)
    if best[0] is not None and best[1] >= MIN_IDENTITY_RATE:
        return best
    return (None, best[1], best[2])


def near_level(column: list, keys: list, skip: int):
    """The median of one column's other observations, for the series test.

    The meat table carries at most four periods per country, so "nearest in time" and "all
    other years" are the same set; taking the median of the rest keeps one more bad cell in
    the same column from deciding the answer.
    """
    rest = [v for j, v in enumerate(column) if j != skip and not pd.isna(v)]
    if not rest:
        return None
    rest = sorted(rest)
    mid = len(rest) // 2
    return rest[mid] if len(rest) % 2 else (rest[mid - 1] + rest[mid]) / 2.0


def _digit_candidate(recorded: float, corrected: float) -> bool:
    """Is `recorded` -> `corrected` a leading thousands digit lost, or one prepended?

    Two forms, both observed in this extraction (06's table has the second as "digits
    prepended"):
      LOST      the cell is under 1000 and gains a leading 1  (276 -> 1276)
      PREPENDED the cell begins with 1 and drops it           (1027 -> 27)
    Anything else -- gaining a digit onto a value that already has four, or losing a leading
    digit that is not 1 -- is not this error mode, and is not offered as a candidate.
    """
    if corrected <= 0:
        return False
    if abs(abs(corrected - recorded) - LEADING_DIGIT_STEP) > 1e-6:
        return False
    if corrected > recorded:
        return recorded < LEADING_DIGIT_STEP
    text = f"{recorded:g}"
    return text.startswith("1") and float(text[1:] or 0) == corrected


def resolve_cell(columns: list, keys: list, j: int, total_col: int, diff: float):
    """Which single cell, corrected by +-1000, satisfies the identity -- if exactly one does.

    `diff` is total - components. A positive diff means the total exceeds its components, so
    either a COMPONENT lost a digit or the TOTAL gained one; a negative diff is the mirror.
    Both directions are offered, but only in the two digit forms `_digit_candidate` accepts,
    and that is what rules out most of the arithmetically possible cells.

    When more than one form survives, the tie is broken by which correction agrees BETTER
    with that column's own other observations, by at least IMPROVE_FACTOR. If that does not
    leave exactly one, the caller records `undetermined` and lists the candidates rather than
    picking one.
    """
    candidates = []
    for i in range(len(columns)):
        recorded = columns[i][j]
        if pd.isna(recorded):
            continue
        # Correcting the total moves it by -diff; correcting a component, by +diff.
        corrected = recorded - diff if i == total_col else recorded + diff
        if _digit_candidate(recorded, corrected):
            candidates.append((i, recorded, corrected))
    if len(candidates) == 1:
        return candidates[0], candidates, "sole cell the error mode can explain"
    survivors = []
    for i, recorded, corrected in candidates:
        level = near_level(columns[i], keys, j)
        if level is None or level <= 0:
            continue
        was = max(level, recorded) / max(min(level, recorded), 1e-9)
        now = max(level, corrected) / min(level, corrected)
        if now * IMPROVE_FACTOR <= was:
            survivors.append((i, recorded, corrected))
    if len(survivors) == 1:
        return survivors[0], candidates, "only correction its own column agrees with"
    return None, candidates, "undetermined"


def identity_pass(livestock: pd.DataFrame) -> list:
    """The component/total identity over every livestock table shape that carries one."""
    rows = []
    for source_detail, frame in livestock.groupby("source_detail"):
        by_width = shape_blocks(frame)
        widest = max(by_width) if by_width else 0
        for width, blocks in sorted(by_width.items()):
            total_col, rate, seen = find_total_column(blocks)
            if total_col is None:
                continue
            print(f"  {os.path.basename(str(source_detail))}  width={width}: "
                  f"column {total_col} is the stated total "
                  f"({rate:.1%} of {seen} country-years exact)")
            for country, keys, columns in blocks:
                for j, key in enumerate(keys):
                    total = columns[total_col][j]
                    parts = [c[j] for i, c in enumerate(columns) if i != total_col]
                    if pd.isna(total) or any(pd.isna(p) for p in parts):
                        continue
                    comp = sum(parts)
                    diff = total - comp
                    if abs(diff) <= _tolerance(total):
                        continue
                    year, period = key
                    base = {
                        "check": "meat-total-identity",
                        "source": "fao1952",
                        "source_detail": source_detail,
                        "country": country,
                        "year": "" if year == "<NA>" else year,
                        "period": "" if period == "None" else period,
                        "n_columns": width,
                        "total_column": total_col,
                        "total_recorded": total,
                        "components_sum": comp,
                        "residual": diff,
                        "columns": "|".join(
                            "" if pd.isna(c[j]) else f"{c[j]:g}" for c in columns),
                    }
                    if abs(abs(diff) - LEADING_DIGIT_STEP) <= 1e-6:
                        pick, candidates, how = resolve_cell(
                            columns, keys, j, total_col, diff)
                        cand = ";".join(f"col{i}:{r:g}->{c:g}" for i, r, c in candidates)
                        if pick is None:
                            rows.append(base | {
                                "column_index": "",
                                "recorded": "",
                                "implied_correct": "",
                                "diagnosis": "leading digit dropped (1000); which cell is "
                                             "undetermined",
                                "evidence": f"candidates {cand}",
                            })
                        else:
                            i, recorded, corrected = pick
                            rows.append(base | {
                                "column_index": i,
                                "recorded": recorded,
                                "implied_correct": corrected,
                                "diagnosis": "leading digit dropped (1000)"
                                             + (" in the stated total" if i == total_col
                                                else " in a component"),
                                "evidence": f"{how}; candidates {cand}",
                            })
                        continue
                    if width < widest and diff > 0:
                        rows.append(base | {
                            "column_index": "",
                            "recorded": "",
                            "implied_correct": "",
                            "diagnosis": f"a component column was not extracted: this block "
                                         f"has {width} of the table's {widest} columns and "
                                         f"the total exceeds them by {diff:g}",
                            "evidence": "no cell correction proposed",
                        })
                        continue
                    rows.append(base | {
                        "column_index": "",
                        "recorded": "",
                        "implied_correct": "",
                        "diagnosis": f"components sum to {comp:,.0f} but the stated total "
                                     f"is {total:,.0f}",
                        "evidence": "residual is not a single dropped digit",
                    })
    return rows


def carcass_pass(livestock: pd.DataFrame) -> list:
    """Per-animal carcass weights against hard biological bounds."""
    rows = []
    carcass = livestock[livestock["item"].isin(CARCASS_BOUNDS)]
    if len(carcass):
        units = set(carcass["unit"].dropna().unique())
        if units != {"kilograms"}:
            raise extdata.ExternalDataError(
                f"carcass weights are no longer in kilograms alone: {sorted(units)}. "
                f"CARCASS_BOUNDS is a kg constant; converting silently would compare a "
                f"physical bound against the wrong unit."
            )
    for (item, country), group in carcass.groupby(["item", "country"]):
        lo, hi = CARCASS_BOUNDS[item]
        for row in group.itertuples():
            if pd.isna(row.value) or lo <= row.value <= hi:
                continue
            clean = group[(group["value"] >= lo) & (group["value"] <= hi)]
            evidence = ("same country, in-bounds years: "
                        + ", ".join(f"{int(y)}={v:g}" for y, v in
                                    zip(clean["year"], clean["value"]))
                        if len(clean) else "no in-bounds year for this country and species")
            rows.append({
                "check": "carcass-weight-bounds",
                "source": "fao1952",
                "source_detail": row.source_detail,
                "country": country,
                "year": "" if pd.isna(row.year) else int(row.year),
                "period": "" if row.period is None else row.period,
                "n_columns": 1,
                "total_column": "",
                "total_recorded": "",
                "components_sum": "",
                "residual": "",
                "columns": f"{row.value:g}",
                "column_index": "",
                "recorded": row.value,
                "implied_correct": "",
                "diagnosis": f"{row.value:g} kg is outside the physical bounds for "
                             f"{item.replace('carcass weights ', '')} "
                             f"({lo:g}-{hi:g} kg dressed)",
                "evidence": evidence,
            })
    return rows


def main() -> int:
    layer_b = extdata.load_layer_b()
    livestock = layer_b[layer_b["indicator"].isin(LIVESTOCK_INDICATORS)].copy()
    extdata.require_any_value(livestock, "indicator", LIVESTOCK_INDICATORS,
                              "layer B livestock block")
    livestock["_ord"] = range(len(livestock))
    print(f"livestock rows: {len(livestock):,} in "
          f"{livestock['source_detail'].nunique()} tables\n")

    print("component/total identity:")
    rows = identity_pass(livestock)
    identity = sum(r["check"] == "meat-total-identity" for r in rows)
    print(f"  inconsistent country-years: {identity}\n")

    print("carcass weights against physical bounds:")
    rows += carcass_pass(livestock)
    print(f"  out-of-bounds cells: {sum(1 for r in rows if r['check'] == 'carcass-weight-bounds')}\n")

    out = pd.DataFrame(rows)
    if not len(out):
        print("nothing to correct")
        return 0
    out = out.sort_values(["check", "country", "year"])
    out.to_csv(OUT, index=False)
    for r in out.itertuples():
        where = f"{r.country} {r.year or r.period}"
        print(f"  {r.check:22s} {where:28s} {r.diagnosis}")
        if r.evidence:
            print(f"  {'':22s} {'':28s}   {r.evidence}")
    print(f"\nwrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
