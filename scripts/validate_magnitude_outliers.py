#!/usr/bin/env python3
"""Does the magnitude screen's outlier table still describe its own rows?

`state/magnitude_outliers.csv` is the largest tracked state table (402 KB, 2,718 rows) and until
2026-08-19 **no gate read it**. Issue 432 measured the consequence: the committed copy had drifted 115
rows behind its generator, and among the rows it still carried were SIX pointing at two polity codes
that no longer exist — `LAO-1893-1953` and `SEN-1886-1959`, both re-spanned since (to `LAO-1893-1954`
and `SEN-1886-1960`). That is issue 17's orphan class: a table is right on the day it runs, the
database then moves, and nothing raises because every consumer resolves a code by looking it up.

WHAT THIS GATE DELIBERATELY DOES NOT DO: check freshness. CI has no layer-B panel — the workflow
contains no `WHEP_LAYER_B` and no path into it — so whether a panel-derived table matches the current
panel is unverifiable here by construction. That is why the repo's pattern for these tables is "the
tool writes a committed table, and a gate reads the COMMITTED table".

AND WHY THERE IS NO ROW-COUNT BASELINE, unlike most gates here. A count pin would fail the moment
someone legitimately regenerates the table against a newer panel, which is the one action this issue
is asking for. Pinning a number that a correct action breaks would train the next person to edit the
baseline rather than read the failure. Every check below therefore holds at ANY row count.

Four signals, all re-derived from the row itself:

  A  `ratio` == (median_value / area) / item_median_intensity. This is the column every judgement in
     the table rests on, and it holds for all 2,718 rows. A row whose ratio stops describing its own
     numbers is the failure `validate_isolated_spikes.py` and `validate_series_collapses.py` guard in
     their own tables.
  B  every `whep_code` is a live polity. This is the check that would have caught the six orphans.
  C  `ratio` is at or above the generator's `--min-ratio` floor of 8.0, so a row that does not belong
     in an outlier table cannot sit in one.
  D  rows are ordered by `ratio` descending, which is the generator's own contract and the thing a
     partial or merged write would break.

Usage:
  python3 scripts/validate_magnitude_outliers.py
"""
from __future__ import annotations

import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/magnitude_outliers.csv")
POLITIES = os.path.join(REPO, "data/final/polities_database.csv")

# The generator's own default (`05_magnitude_screen.py --min-ratio`), restated so this gate does not
# depend on the tool's constant to know what the table means.
MIN_RATIO = 8.0

# Floating-point round-trip through CSV, not a tolerance on the claim.
REL_EPS = 1e-6

# The last two are the flow-flag annotation `05_magnitude_screen.py` joins on so a settled entrepot
# case (the Djibouti coffee decision, issue 14) is marked SETTLED rather than re-investigated. The
# committed table predated them entirely — the drift issue 432 found was structural, not just 115
# rows — and this gate's first run is what surfaced that.
COLUMNS = ["ratio", "item", "unit", "whep_code", "polity_name", "source", "median_value",
           "area", "n", "item_median_intensity", "assertion_keys",
           "known_flow", "flow_origin_iso3"]


def main() -> int:
    if not os.path.exists(TABLE):
        print(f"FAIL: {os.path.relpath(TABLE, REPO)} missing — run 05_magnitude_screen.py",
              file=sys.stderr)
        return 1
    with open(TABLE, encoding="utf-8") as fh:
        rdr = csv.DictReader(fh)
        rows = list(rdr)
        fields = list(rdr.fieldnames or [])

    problems = []
    if fields != COLUMNS:
        problems.append(f"columns are {fields}, expected {COLUMNS} — a rename would silently break "
                        f"every check below")

    if not os.path.exists(POLITIES):
        problems.append(f"{os.path.relpath(POLITIES, REPO)} is missing, so no code here can be "
                        f"checked against a real polity")
        live = None
    else:
        with open(POLITIES, encoding="utf-8") as fh:
            live = {r["polity_code"] for r in csv.DictReader(fh)}

    ratios = []
    orphans = set()
    for i, r in enumerate(rows, start=2):
        where = f"line {i} {r.get('whep_code')}/{str(r.get('item'))[:24]}"
        try:
            ratio = float(r["ratio"])
            mv = float(r["median_value"])
            area = float(r["area"])
            imi = float(r["item_median_intensity"])
        except (ValueError, KeyError, TypeError):
            problems.append(f"A {where}: unparseable numbers")
            continue
        ratios.append(ratio)

        # --- A: the ratio must describe its own row ---
        if area <= 0:
            problems.append(f"A {where}: area {area:g} is not positive, so the ratio is undefined")
        elif imi <= 0:
            problems.append(f"A {where}: item_median_intensity {imi:g} is not positive")
        else:
            want = (mv / area) / imi
            if abs(want - ratio) > max(REL_EPS * max(abs(ratio), 1e-12), 1e-9):
                problems.append(
                    f"A {where}: recorded ratio {ratio:,.4f} does not match its own numbers "
                    f"(({mv:g} / {area:g}) / {imi:g} = {want:,.4f}) — the column every judgement in "
                    f"this table rests on no longer describes the row it sits in")

        # --- C: it must clear the outlier floor ---
        if ratio < MIN_RATIO - 1e-9:
            problems.append(
                f"C {where}: ratio {ratio:,.4f} is below the generator's --min-ratio floor of "
                f"{MIN_RATIO}, so a row that is not an outlier is sitting in the outlier table")

        # --- B: the code must still exist ---
        if live is not None and r.get("whep_code") not in live:
            orphans.add(r["whep_code"])

        try:
            if int(r["n"]) <= 0:
                problems.append(f"{where}: n={r['n']} is not a positive observation count")
        except (ValueError, TypeError):
            problems.append(f"{where}: n={r.get('n')!r} is not an integer")

    for code in sorted(orphans):
        problems.append(
            f"B {code} is not a polity in data/final/polities_database.csv — the database moved "
            f"under this table (a re-span, rename or retirement) and every row on that code now "
            f"points at nothing. This is exactly how the six LAO-1893-1953 / SEN-1886-1959 rows "
            f"survived unnoticed (issue 432)")

    # --- D: the generator's ordering contract ---
    if ratios != sorted(ratios, reverse=True):
        problems.append(
            "D rows are not ordered by ratio descending, which is the generator's contract — a "
            "partial write or a hand merge is the usual cause")

    print(f"magnitude outliers: {len(rows)} rows, {len({r.get('whep_code') for r in rows})} "
          f"polities, min ratio {min(ratios) if ratios else float('nan'):,.4f} "
          f"(floor {MIN_RATIO}), orphaned codes {len(orphans)}")

    for p in problems:
        print(f"FAIL: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
