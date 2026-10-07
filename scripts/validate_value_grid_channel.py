#!/usr/bin/env python3
"""Gate the per-row PRECISION CHANNEL (issue 446) -- the columns that say how coarsely a value was printed.

`state/source_value_precision.csv` records each source's reporting grid per (source, unit, era), but a
consumer holding one row still saw a bare number. The matcher now derives four columns per row
(`matchlib.value_precision`), `matched_rows.parquet` carries them, and the harmonized build publishes
`value_grid` and `source_grid_verdict`. The panel and the parquet are not in the repository, so CI
cannot rebuild any of that; this gate checks what the repository alone supports:

  A  THE DERIVATION, on a synthetic frame with a known answer: a series on a 1000-grid reads 1000; a
     fine series reads fine; a series shorter than MIN_SERIES_NONZERO reads UNKNOWN (NaN), never a
     grid; zeros inherit their series' grid; an era-split source (iia) gets one grid per era, so a
     fine early volume cannot hide a coarse late one; a coarse source verdict raises `value_grid`
     above a finer series grid; a period row takes its end year's era.
  B  THE WIRING: stage 01 writes the columns, build.R refuses a matches file without them, rescales
     the grid with the value's own unit multiplier and divisor, and aggregates to the COARSEST
     contributor, and the harmonized README documents both published columns.
  C  THE CONTRACT: the manifest's `value_precision` block lists exactly the columns the code derives,
     and fingerprints the table the verdicts come from.
  D  LOCAL ONLY (skipped in CI, where matched_rows.parquet is absent): every non-zero value is a
     multiple of its own series_grid, and value_grid is never finer than series_grid.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
MATCHLIB = os.path.join(REPO, "pipelines/polity-autoimprove/matchlib.py")
STAGE01 = os.path.join(REPO, "pipelines/polity-autoimprove/01_match_and_findings.py")
BUILD_R = os.path.join(REPO, "pipelines/historical-production-harmonized/build.R")
RESOLVER = os.path.join(REPO, "pipelines/historical-production-harmonized/R/resolve_collapse_groups.R")
README = os.path.join(REPO, "pipelines/historical-production-harmonized/README.md")
MANIFEST = os.path.join(REPO, "data/final/polities_manifest.json")
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/source_value_precision.csv")
MATCHED = os.path.join(REPO, "pipelines/polity-autoimprove/state/matched_rows.parquet")

HARMONIZED_COLUMNS = ("value_grid", "source_grid_verdict")


def load_matchlib():
    spec = importlib.util.spec_from_file_location("matchlib_value_grid", MATCHLIB)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def derivation(ml, fails):
    import pandas as pd

    table = {("mitchell", "tonnes"): {"all": "coarse_1000"},
             ("fine", "tonnes"): {"all": "fine"},
             ("iia", "ha"): {"all": "mixed", "pre-1934": "fine", "1934+": "coarse_1000"}}
    rows = []

    def add(source, label, unit, years, values, period=None):
        for y, v in zip(years, values):
            rows.append({"source": source, "source_label_raw": label, "item": "x", "unit": unit,
                         "indicator": None, "year": y, "period": period, "value": v})

    add("mitchell", "a", "tonnes", range(1900, 1907), [1000, 2000, 0, 5000, 12000, 7000, 3000])
    add("fine", "b", "tonnes", range(1900, 1906), [1000, 2000, 2500.5, 3000, 4000, 5000])
    add("fine", "c", "tonnes", range(1900, 1903), [1000, 2000, 3000])          # too short
    add("iia", "d", "ha", range(1925, 1933), [10, 25, 31, 40, 52, 66, 77, 81])  # fine early
    add("iia", "d", "ha", range(1934, 1942), [1000, 3000, 2000, 5000, 4000, 6000, 8000, 7000])
    add("iia", "e", "ha", [None], [4000], period="1936-1940")                    # period row
    df = pd.DataFrame(rows)
    df["year"] = pd.array(df["year"], dtype="Int64")
    out = ml.value_precision(df, table)
    if tuple(out.columns) != tuple(ml.PRECISION_COLUMNS):
        fails.append(f"A: value_precision returns {tuple(out.columns)}, PRECISION_COLUMNS says "
                     f"{tuple(ml.PRECISION_COLUMNS)}")
        return

    def grab(label, year=None):
        m = df["source_label_raw"] == label
        if year is not None:
            m &= df["year"] == year
        return out[m]

    g = grab("a")
    if not (g["series_grid"] == 1000).all():
        fails.append(f"A: a series of multiples of 1000 reads {sorted(set(g['series_grid']))}, not 1000")
    if grab("a", 1902)["series_grid"].iloc[0] != 1000:
        fails.append("A: a zero row must inherit its series' grid (a zero below half a step is the "
                     "case this channel exists to make identifiable)")
    if (grab("b")["series_grid"] != 0.1).any():
        fails.append(f"A: a series with one value on a 0.1 grid reads {sorted(set(grab('b')['series_grid']))}, "
                     f"not 0.1")
    c = grab("c")
    if c["series_grid"].notna().any() or c["value_grid"].notna().any():
        fails.append("A: a series under MIN_SERIES_NONZERO must read UNKNOWN (NaN), not a grid -- three "
                     "round numbers prove nothing, and NaN means unknown rather than exact")
    if not (grab("a")["value_grid"] == 1000).all():
        fails.append("A: value_grid must be the coarser of series grid and verdict grid")
    if (grab("b")["source_grid_verdict"] != "fine").any() or (grab("b")["value_grid"] != 0.1).any():
        fails.append("A: a `fine` source verdict must add no grid, leaving value_grid at the series' own")
    early = grab("d")[df.loc[grab("d").index, "year"] < 1934]
    late = grab("d")[df.loc[grab("d").index, "year"] >= 1934]
    if not (early["series_grid"] == 1).all():
        fails.append(f"A: iia early-era series grid is {sorted(set(early['series_grid']))}, expected 1 "
                     f"(one grid per era, or a fine volume hides a coarse one)")
    if not (late["series_grid"] == 1000).all() or not (late["source_grid_verdict"] == "coarse_1000").all():
        fails.append("A: iia 1934+ must read grid 1000 and verdict coarse_1000")
    if not (early["source_grid_verdict"] == "fine").all():
        fails.append("A: iia pre-1934 must take the era's `fine` verdict, not the `all` row's `mixed`")
    if (grab("e")["source_grid_verdict"] != "coarse_1000").any():
        fails.append("A: an undated iia period row `1936-1940` must take the 1934+ era by its end year")
    # the era-less mixed fallback
    t2 = {("iia", "ha"): {"all": "mixed"}}
    if (ml.value_precision(df[df.source == "iia"], t2)["source_grid_verdict"] != "mixed").any():
        fails.append("A: a source with only an `all` row must take it for every row")


def wiring(ml, fails):
    s01 = open(STAGE01, encoding="utf-8").read()
    if "value_precision(" not in s01 or ".join(work_precision)" not in s01:
        fails.append("B: 01_match_and_findings.py no longer joins value_precision() onto matched_rows.parquet")
    r = open(BUILD_R, encoding="utf-8").read()
    need = {
        "refuses a matches file without the columns":
            'c("value_grid", "source_grid_verdict") %in% names(matches)',
        "rescales the grid like the value":
            "as.numeric(.data$value_grid) * .data$unit_multiplier / .data$value_divisor",
        "rescales the grid by the exact inverse of a sub-1 divisor (issue 424)":
            "as.numeric(.data$value_grid) * .data$unit_multiplier * round(1 / .data$value_divisor)",
        "publishes the grid columns": '"value_grid",\n    "source_grid_verdict"\n  ) |>',
    }
    for what, tok in need.items():
        if tok not in r:
            fails.append(f"B: build.R no longer {what} (missing `{tok}`)")
    rv = open(RESOLVER, encoding="utf-8").read()
    need_r = {
        "keeps the coarsest grid when it merges identical rows":
            "grid = coarsest_grid(g$value_grid)",
        "keeps the coarsest verdict when it merges identical rows":
            "verdict = coarsest_verdict(g$source_grid_verdict)",
    }
    for what, tok in need_r.items():
        if tok not in rv:
            fails.append(f"B: resolve_collapse_groups.R no longer {what} (missing `{tok}`)")
    doc = open(README, encoding="utf-8").read()
    for c in HARMONIZED_COLUMNS:
        if f"`{c}`" not in doc:
            fails.append(f"B: the harmonized README does not document `{c}`")


def contract(ml, fails):
    m = json.load(open(MANIFEST, encoding="utf-8"))
    vp = m.get("value_precision")
    if not vp:
        fails.append("C: the manifest has no `value_precision` block -- the channel is undocumented "
                     "for the consumer contract")
        return
    if tuple(vp.get("matched_rows_columns", ())) != tuple(ml.PRECISION_COLUMNS):
        fails.append(f"C: manifest matched_rows_columns {vp.get('matched_rows_columns')} != the "
                     f"derived {list(ml.PRECISION_COLUMNS)}")
    if tuple(vp.get("harmonized_columns", ())) != HARMONIZED_COLUMNS:
        fails.append(f"C: manifest harmonized_columns {vp.get('harmonized_columns')} != "
                     f"{list(HARMONIZED_COLUMNS)}")
    got = hashlib.sha256(open(TABLE, "rb").read()).hexdigest()
    if vp.get("sha256") != got:
        fails.append("C: manifest value_precision.sha256 is stale against source_value_precision.csv; "
                     "run scripts/write_manifest.py")
    if "unknown" not in vp.get("why", "").lower():
        fails.append("C: the manifest must say a NULL grid is UNKNOWN, not exact")


def local_rederive(ml, fails):
    if not os.path.exists(MATCHED):
        print("D skipped: matched_rows.parquet absent (CI)")
        return
    import pandas as pd
    m = pd.read_parquet(MATCHED)
    if not set(ml.PRECISION_COLUMNS) <= set(m.columns):
        fails.append("D: matched_rows.parquet lacks the precision columns; re-run 01_match_and_findings.py")
        return
    # The floor grid (10^GRID_EXP_MIN) means "0.001 or finer", so it is not a lattice to test against.
    nz = m[m["value"].notna() & (m["value"] != 0) & m["series_grid"].notna()
           & (m["series_grid"] > 10.0 ** ml.GRID_EXP_MIN * 1.5)]
    r = nz["value"] / nz["series_grid"]
    bad = int(((r - r.round()).abs() > 1e-6 * r.abs().clip(lower=1)).sum())
    if bad:
        fails.append(f"D: {bad} non-zero value(s) are not a multiple of their own series_grid")
    if int((m["value_grid"] < m["series_grid"]).sum()):
        fails.append("D: value_grid finer than series_grid on some rows")
    print(f"D ok: {len(nz):,} non-zero values checked against their series grid")


def main() -> int:
    for p in (MATCHLIB, STAGE01, BUILD_R, RESOLVER, README, MANIFEST, TABLE):
        if not os.path.exists(p):
            print(f"MISSING {p}", file=sys.stderr)
            return 1
    ml = load_matchlib()
    fails: list[str] = []
    derivation(ml, fails)
    wiring(ml, fails)
    contract(ml, fails)
    local_rederive(ml, fails)
    if fails:
        print(f"FAIL {len(fails)} problem(s) in the value-grid channel:", file=sys.stderr)
        for f in fails:
            print(f"  {f}", file=sys.stderr)
        return 1
    print("OK value-grid channel: derivation, wiring and manifest contract agree")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
