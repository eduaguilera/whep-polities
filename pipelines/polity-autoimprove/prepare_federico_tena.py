#!/usr/bin/env python3
"""Federico-Tena (January 2019) -> an intake table 00_intake.py can read.

Issue 26: only `consolidated_layer_b.parquet` (5 sources) and, by a separate
code-keyed matcher, FAOSTAT had ever been through `00_intake.py`. A SECOND
independent source is the strongest available test of the polity set itself:
where two sources disagree about the same territory-year, one of them is
describing a reporting unit our polities do not represent.

`00_intake.py` needs no changes for a new source; the work is preparing the
input table. This script is that preparation, and nothing else.

WHAT THE SOURCE IS. What the repo stages is Federico-Tena's DOCUMENTATION, not
its trade values: `data/external/federico_tena_polities.xlsx`, sheet
"List of trading polities", one row per trading polity with the first and last
year of its import series, of its export series and of its population series,
plus the 1913 population in thousands and a compiler's note. So the assertion
this source can support is a COVERAGE claim -- "Federico-Tena reports trade for
a territory called X in year Y" -- plus exactly one magnitude, the 1913
population. No trade level or value can be sourced from it (see
wiki/sources/federico-tena-2019.md, Known limitations).

WHY THE XLSX AND NOT THE CSV. `data/external/federico_tena/polities.csv` is a
LOSSY extract of the same sheet: `population_end` and `population_estimate` are
empty in all 243 rows, and the sheet's 1913-population column and its
"Trade sample serie included" column are absent altogether. The xlsx is read
directly so the intake table carries the population window and the one
magnitude the source actually has. The CSV is left untouched.

SHAPE OF THE OUTPUT. One row per (polity, series, year) over each series'
inclusive window -- which is what makes the table a test of year containment:
every year the source reports has to land inside some polity's span, and the
years that do not are the finding. Plus one row per polity carrying the 1913
population, keyed as its own item so its median is not mixed with the coverage
rows (which have no value at all). The source's OWN first/last year for the
polity travels as `ft_polity_start` / `ft_polity_end` columns, which
`00_intake.py` does not read: they are not coverage claims, they are the
source's independent dating of the reporting unit, and the whole point of
keeping them out of the year expansion is that a polity Federico-Tena lists
WITHOUT a trade series reports no trade at all (see COLUMN POSITIONS).

COLUMN POSITIONS -- read the header, do not guess. This script's first version
took columns 1-2 as the imports window, 3-4 as exports and 5/7 as a
"population" series, and every one of those was off by one column GROUP. Header
row 5 of the sheet names the groups and row 6 their sub-columns:

    cols 1,2  "Trading polity"  Starting / End   <- the polity's own dating
    cols 3,4  "Imports"         Starting / End
    cols 5,7  "Exports"         Starting / End
    col  9    "Population"      1913 '(000)      <- ONE value, not a series
    col  11   "Trade sample serie included: Exports"
    col  13   "Notes"

Cols 6, 8, 10 and 12 are empty merge spacers, and cols 1-2 are populated for
all 243 polities while 3-4 and 5/7 are populated for only 146 -- which is the
substantive consequence: 97 of the 243 trading polities carry NO trade series,
so the old mapping FABRICATED a per-year import series for every one of them
out of its existence window. It also emitted the import series as "exports" and
the export series as "population", a measure the sheet does not contain.

The fix is confirmed against dates the misreading contradicts outright: Korea
1876 (Treaty of Ganghwa) not 1800; Japan 1860 (opened 1859) not 1800; China
1830, Philippines 1810, Iceland 1849, Bulgaria 1879, Ireland 1922, Austria /
Czechoslovakia / the Baltics 1920, Poland 1922, Syria-and-Lebanon 1921,
Palestine/Jordan 1920. Under the old mapping Korea imported from 1800, while
closed to foreign trade. Measured effect: 48,569 rows -> 27,359, of which
21,210 removed were the fabricated existence-window series and the rest are
the re-labelling.

Usage:
  python3 pipelines/polity-autoimprove/prepare_federico_tena.py
  python3 pipelines/polity-autoimprove/00_intake.py \
    --input pipelines/polity-autoimprove/state/federico_tena_intake.csv \
    --label-col polity_name --year-col year --item-col item \
    --value-col value --unit-col unit --source-tag federico_tena \
    --out pipelines/polity-autoimprove/state/assertions_federico_tena.json
"""
import os, sys, argparse
import pandas as pd

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
XLSX = os.path.join(REPO, "data/external/federico_tena_polities.xlsx")
SHEET = "List of trading polities"
OUT = os.path.join(REPO, "pipelines/polity-autoimprove/state/federico_tena_intake.csv")

# The sheet's header is spread over three merged rows, so columns are taken by
# position from the first data row (skiprows=6). Positions read off header rows
# 5-6 of the January 2019 file on 2026-08-17 (see COLUMN POSITIONS above):
# Algeria = trading polity 1831-1938, imports 1830-1938, exports 1830-1938,
# 1913 population 5,579 thousand.
COLS = {0: "polity_name", 1: "ft_polity_start", 2: "ft_polity_end",
        3: "imports_start", 4: "imports_end", 5: "exports_start",
        7: "exports_end", 9: "population_1913_thousands",
        11: "trade_sample_exports_start", 13: "notes"}
CONTINENTS = ("Africa", "Americas", "Asia", "Europe", "Oceania")

# Multi-territory umbrella reporting units: each pools a dozen scattered island
# groups whose own rows say "joint estimation" with it, so the row is an
# AGGREGATE of territories and not a candidate polity. Flagged rather than
# dropped here -- `00_intake.py --aggregate-col is_aggregate` drops them, and
# the default run keeps them so their coverage is measured and their status is
# decided by verification (verdict `not_a_polity`) instead of by this script.
UMBRELLAS = frozenset({
    "British settlement Oceania", "French Settlements in Oceania",
    "German colonies Oceania", "US settlement Oceania",
})
SERIES = ("imports", "exports")


def load_sheet(path=XLSX):
    d = pd.read_excel(path, sheet_name=SHEET, header=None, skiprows=6)
    d = d.iloc[:, list(COLS)].rename(columns=COLS)
    d["polity_name"] = d["polity_name"].astype(str).str.strip()
    # drop the continent banner rows (their numeric cells are column indices)
    # and any trailing blank row
    d = d[~d["polity_name"].isin(CONTINENTS)]
    d = d[d["polity_name"].ne("nan") & d["polity_name"].ne("")]
    for c in COLS.values():
        if c not in ("polity_name", "notes"):
            d[c] = pd.to_numeric(d[c], errors="coerce")
    # every listed polity carries a "Trading polity" window; only the header and
    # banner rows do not, so this is the row filter as well as a real column
    return d[d["ft_polity_start"].notna()].reset_index(drop=True)


def build(d):
    rows = []
    for r in d.itertuples(index=False):
        agg = r.polity_name in UMBRELLAS
        ps = int(r.ft_polity_start)
        pe = None if pd.isna(r.ft_polity_end) else int(r.ft_polity_end)
        for s in SERIES:
            y0 = getattr(r, f"{s}_start")
            if pd.isna(y0):
                continue
            y1 = getattr(r, f"{s}_end")
            y1 = int(y0) if pd.isna(y1) else int(y1)
            for y in range(int(y0), y1 + 1):
                rows.append((r.polity_name, y, s, None, None, agg, ps, pe, r.notes))
        p13 = r.population_1913_thousands
        if not pd.isna(p13):
            rows.append((r.polity_name, 1913, "population_1913", float(p13),
                         "thousand persons", agg, ps, pe, r.notes))
    out = pd.DataFrame(rows, columns=["polity_name", "year", "item", "value",
                                      "unit", "is_aggregate", "ft_polity_start",
                                      "ft_polity_end", "notes"])
    return out.sort_values(["polity_name", "item", "year"]).reset_index(drop=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--xlsx", default=XLSX)
    ap.add_argument("--out", default=OUT)
    A = ap.parse_args()
    if not os.path.exists(A.xlsx):
        sys.exit(f"missing {A.xlsx}")
    d = load_sheet(A.xlsx)
    t = build(d)
    t.to_csv(A.out, index=False)
    print(f"polities: {len(d)} ({len(UMBRELLAS & set(d.polity_name))} umbrella aggregates)")
    for s in SERIES:
        n = int(d[f"{s}_start"].notna().sum())
        print(f"  {s:11s} series: {n:3d} polities")
    no_series = d[d.imports_start.isna() & d.exports_start.isna()]
    print(f"NO trade series at all: {len(no_series)} polities "
          f"(listed with a period, but the sheet gives them no import or export "
          f"window; {int(no_series.population_1913_thousands.notna().sum())} of them "
          f"still carry a 1913 population)")
    print(f"1913 population given for {int(d.population_1913_thousands.notna().sum())} polities")
    print(f"rows: {len(t):,} over years {t.year.min()}-{t.year.max()}")
    print(f"wrote {A.out}")
