#!/usr/bin/env python3
"""Audit whep_crops v1.0 coverage: does every observed (iso3, year) reach exactly one polity?

whep_crops is keyed on ISO3 + item_code + year rather than on a free-text label, so it needs no
alias map and asks a different question from layer B. The question is coverage: for each
(iso3, year) the panel carries, is there exactly one live polity?

FILTER FIRST, OR THE ANSWER IS MEANINGLESS. 55.4% of production values have a `src_production`
beginning "backcast", and the panel carries a `state` column with `pre_emergence` for 70,743 rows.
Those describe a MODERN territory's past, not a past polity -- South Sudan has rows from 1850, and
matching them to a historical polity would be a category error. Only `state == "active"` rows with
a non-backcast source make a claim about an entity that existed.

    all (iso3, year) pairs                      36,366    7,043 uncovered (19%)
    observed, active pairs                      20,616      483 uncovered (2.3%)

The first number is a property of the dataset's method; the second is a property of this database.
Reporting the first as a coverage failure would be wrong, which is why this script filters.

WHAT THE 483 ARE, and they fall into three classes that need different fixes:

  1. AN ISO3 CODE ONLY COVERS ITS POST-INDEPENDENCE PERIODS -- about 1,900 of the 2,598 affected
     rows, and the structural one. The ISO code is present in this database; it just stops at
     independence, because the colonial-era rows carry a code of their own:

         iso3 SRB   covers 2006-      Serbian history 1816-1945 is under iso3 SER
         iso3 TZA   covers 1961-      1891-1961 is under iso3 TAN
         iso3 ISR   covers 1948-      Mandatory Palestine 1922-1948 is under iso3 PAL
         iso3 SOM   covers 1960-      1884-1960 is under BSS (British) and ITS (Italian)
         iso3 BWA   covers 1966-      1885-1966 is under iso3 BEC
         iso3 RUS   covers pre-1917 and post-1991; 1917-1991 is F228 (the USSR)

     That is a deliberate modelling choice -- a colony is not its successor state -- but it means
     ANY ISO3-KEYED SOURCE silently reaches nothing for the colonial era, and gets no error. This
     panel is 1.84M rows keyed exactly that way. Related to issue 55 on inconsistent dissolved-state
     ISO3 treatment, but the consequence here is interoperability rather than inconsistency.

  2. PERIOD GAPS THAT ARE NO LONGER LATENT. validate_period_gaps baselines four gaps as "genuinely
     uncovered and all are latent today, since no source reaches them: TCD 1919, SEN 1959, LAO 1953,
     and CIV 1900-1901". THIS PANEL REACHES SEN 1959 AND LAO 1953. It also finds gaps not on that
     list: CHL 1883 (7 rows -- CHL-1810-1884 ends exclusive at 1883 and CHL-1884-1899 begins at
     1884, so 1883 belongs to neither), HUN 1919, SYR 1945, SDN 1951, LBY 1909.

  3. GENUINELY MISSING POLITIES. TKL (Tokelau) has no row at any period, 252 rows. ERI 1952-1992
     has none either: the Eritrea family jumps from ERI-1889-1952 to ERI-1993-2025, leaving the
     federation-with-Ethiopia and annexation years uncovered, 360 rows.

Usage:
  python3 pipelines/polity-autoimprove/09_crops_coverage.py
"""
from __future__ import annotations

import collections
import csv
import os
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DEAD_STATUS = ("retired", "superseded")
CSV_PATH = os.path.join(REPO, "data/final/polities_database.csv")


def families() -> dict:
    with open(CSV_PATH, encoding="utf-8") as fh:
        rows = [
            r for r in csv.DictReader(fh)
            if (r.get("wiki_status") or "").strip() not in DEAD_STATUS
        ]
    fam = collections.defaultdict(list)
    for r in rows:
        if not r.get("iso3_code"):
            continue
        try:
            fam[r["iso3_code"]].append(
                (int(r["start_year"]), int(r["end_year"]), r["polity_code"],
                 r.get("polity_type", ""))
            )
        except (TypeError, ValueError):
            continue
    return fam


def main() -> int:
    import extdata
    try:
        panel = extdata.load_whep_crops(
            columns=["iso3", "year", "item_code", "src_production", "state"]
        )
    except FileNotFoundError as exc:
        print(f"SKIP: {exc}")
        return 0

    fam = families()
    observed = panel[
        (~panel.src_production.astype(str).str.startswith("backcast"))
        & panel.src_production.notna()
        & (panel.state == "active")
    ]
    print(f"whep_crops rows: {len(panel):,}   iso3: {panel.iso3.nunique()}   "
          f"years {panel.year.min()}-{panel.year.max()}")
    print(f"observed + active: {len(observed):,} ({len(observed) / len(panel):.1%})")

    rowcount = observed.groupby(["iso3", "year"]).size()
    pairs = observed[["iso3", "year"]].drop_duplicates()
    uncovered, ambiguous, ok = [], [], 0
    for iso, year in pairs.itertuples(index=False):
        live = [t for t in fam.get(iso, ()) if t[0] <= year < t[1]]
        if not live:
            uncovered.append((iso, int(year)))
        elif len(live) > 1 and len([t for t in live if t[3] == "national"]) != 1:
            ambiguous.append((iso, int(year)))
        else:
            ok += 1

    total = len(pairs)
    print(f"\ndistinct observed (iso3, year) pairs: {total:,}")
    print(f"  reach exactly one polity: {ok:,} ({ok / total:.1%})")
    print(f"  UNCOVERED: {len(uncovered):,} pairs, "
          f"{sum(int(rowcount.get(k, 0)) for k in uncovered):,} rows")
    print(f"  AMBIGUOUS (order decides): {len(ambiguous):,} pairs, "
          f"{sum(int(rowcount.get(k, 0)) for k in ambiguous):,} rows")

    by_iso = collections.defaultdict(list)
    for iso, year in uncovered:
        by_iso[iso].append(year)
    print("\nuncovered by iso3 (rows in parentheses):")
    for iso, years in sorted(
        by_iso.items(), key=lambda kv: -sum(int(rowcount.get((kv[0], y), 0)) for y in kv[1])
    ):
        rows_hit = sum(int(rowcount.get((iso, y), 0)) for y in years)
        present = sorted({t[2].rsplit("-", 2)[0] for t in fam.get(iso, ())})
        note = "NO FAMILY" if not present else f"family present as {present}"
        print(f"  {iso}  {len(years):>3d} years {min(years)}-{max(years)}  "
              f"({rows_hit:>5,} rows)  {note}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
