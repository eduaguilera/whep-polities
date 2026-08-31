#!/usr/bin/env python3
"""The `period` label on an IIA multi-year average names its YEARBOOK VOLUME exactly, which gives
layer B the provenance column it does not otherwise have (issue 416).

WHAT THIS ADDS. Layer B carries no raw-provenance column: `source, source_detail, continent, country,
item, item_code, indicator, year, period, value, unit, iso3c, polity_code, is_aggregate` is the whole
list, so tracing a published `iia` cell to the volume that printed it has needed a crosswalk on the
country axis (`iia_label_provenance.csv`), another on the item axis (`item_equivalences.csv`), and a
value match on top -- and that chain reaches only cells whose value survives intact, so it is blind to
any label layer B builds by summing (#483/#548).

For the 6,163 iia rows that carry a `period` instead of a `year`, none of that is necessary. In the raw
extract's 42,587 multi-year rows there are seven distinct period labels and EACH IS PRINTED BY EXACTLY
ONE VOLUME -- zero periods appear in two:

    1900-1913 -> iia_1925_26      1925-1929 -> iia_1933_34
    1909-1913 -> iia_1925_26      1928-1932 -> iia_1938_39
    1921-1925 -> iia_1929_30      1934-1938 -> iia_1939_45
    1924-1928 -> iia_1933_34

The map is a function, so the period label alone attributes the row. Coverage is 6,163 of 6,163.

WHY IT MATTERS HERE: THE PERIOD LABEL NAMES THE YEARS, NOT THE EDITION. `1928-1932` is printed by
`iia_1938_39` -- a retrospective average of pre-1934 years, published by one of the two late volumes
whose defects have no second opinion to correct them (#414, #416). So a screen keyed on the years in
the label attributes the row to the wrong volume, and this is not hypothetical: on tobacco (tonnes),
rows above 500,000 t against a world total of 2-3 Mt run

    1909-1913  <- iia_1925_26   clean         0 / 43    0.0%
    1925-1929  <- iia_1933_34   clean         2 / 76    2.6%
    1928-1932  <- iia_1938_39   LATE         34 / 83   41.0%
    1934-1938  <- iia_1939_45   LATE         37 / 84   44.0%

and the two in the clean volume are `india` 612,500 t and `united states of america` 630,805.5 t, both
CORRECT -- the USA was the world's largest producer at roughly 600 kt and India the other giant, so the
500,000 t screen over-flags precisely the two biggest legitimate producers. Read that way the clean
volumes hold 0 real defects in 119 rows and the late ones 71 in 167. The defect is a property of the
EDITION, and the period label is what identifies it.

TWO GAPS THIS TABLE EXPOSES. `iia-tobacco-implausible-magnitudes` records "40 of the 607 iia tobacco
rows" across 16 labels; 607 is exactly the DATED row count, and the period rows add 73 more above
500,000 t across 38 labels. And `era_shift_verdicts.csv` reaches period rows only at `1934-1938`, so
the implausible `1928-1932` rows carry no verdict of any kind -- 34 on tobacco, 38 counting hops.
The `era_screened` column below is what makes that second gap countable rather than argued.

Not a repair. This publishes provenance and scope; it changes no value.
"""
import argparse
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "period_volume_provenance.csv")
ERA = os.path.join(STATE, "era_shift_verdicts.csv")
DEFAULT_RAW = os.path.expanduser(
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx")
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B", "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"))

# The two volumes published from 1938 on. 1933 is the only year two volumes cover, so from 1934 these
# are the sole source and their defects pass straight through -- the basis of #414, #415, #416, #417.
LATE_VOLUMES = {"iia_1938_39", "iia_1939_45"}

# #416 names tobacco and hops, and only these. 500,000 t is implausible for tobacco against a world
# total of 2-3 Mt; it is entirely ordinary for wheat, so the screen must not be applied item-blind.
SCREEN_ITEMS = {"tobacco, unmanufactured", "hops"}
SCREEN_UNIT = "tonnes"
SCREEN_T = 500_000.0

FIELDS = ["source", "country", "polity_code", "item", "unit", "indicator", "period", "value",
          "volume", "volume_is_late", "era_screened", "implausible_tobacco_hops"]


def _s(v):
    """Null-safe string. A None or NaN written by DictWriter lands as an empty field, but `str()` of it
    is "None"/"nan", so --check would report a permanent STALE against a table it had just produced.
    `indicator` is null on every iia period row, which is exactly where this bit."""
    if v is None or (isinstance(v, float) and v != v):
        return ""
    return str(v)


def period_volume_map(raw_path):
    """Derive period -> volume from the raw extract, and prove it is a function while doing so."""
    import pandas as pd
    raw = pd.read_excel(raw_path)
    y = raw["year"].astype(str).str.strip()
    multi = raw[y.str.match(r"^\d{4}\s*-\s*\d{4}$", na=False)].copy()
    multi["_y"] = y[multi.index]
    out, ambiguous = {}, []
    for per, grp in multi.groupby("_y"):
        vols = sorted(grp["yearbook"].dropna().unique())
        if len(vols) != 1:
            ambiguous.append((per, vols))
        out[per] = vols[0] if vols else ""
    return out, ambiguous, len(multi)


def build(raw_path, panel_path):
    import pandas as pd
    vmap, ambiguous, n_multi = period_volume_map(raw_path)
    if ambiguous:
        # Not a tolerance: the whole point of the table is that one period names one volume. If a
        # re-extraction ever breaks that, attributing rows by period label is no longer sound and the
        # table must not be written from a broken map.
        print("FAIL: period -> volume is not a function in the raw extract:", file=sys.stderr)
        for per, vols in ambiguous:
            print(f"  {per} printed by {vols}", file=sys.stderr)
        raise SystemExit(1)
    print(f"period -> volume derived from {n_multi:,} multi-year raw rows; "
          f"{len(vmap)} periods, each printed by exactly one volume")

    era_seen = set()
    if os.path.exists(ERA):
        with open(ERA, newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                if (r.get("period") or "").strip():
                    era_seen.add((r["label"], r["item"], r["period"].strip()))

    lb = pd.read_parquet(panel_path)
    p = lb[(lb["source"] == "iia") & lb["year"].isna() & lb["period"].notna()].copy()
    p["_per"] = p["period"].astype(str).str.strip()
    p = p[p["_per"] != ""]
    unmapped = sorted(set(p["_per"]) - set(vmap))
    if unmapped:
        print(f"FAIL: layer B carries iia period labels the raw extract does not print: {unmapped}",
              file=sys.stderr)
        raise SystemExit(1)

    rows = []
    for _, r in p.iterrows():
        vol = vmap[r["_per"]]
        screened = (r["item"] in SCREEN_ITEMS and r["unit"] == SCREEN_UNIT
                    and r["value"] == r["value"] and r["value"] is not None)
        rows.append({
            "source": _s(r["source"]),
            "country": _s(r["country"]),
            "polity_code": _s(r["polity_code"]),
            "item": _s(r["item"]),
            "unit": _s(r["unit"]),
            "indicator": _s(r["indicator"]),
            "period": r["_per"],
            "value": r["value"],
            "volume": vol,
            "volume_is_late": "yes" if vol in LATE_VOLUMES else "no",
            "era_screened": "yes" if (r["country"], r["item"], r["_per"]) in era_seen else "no",
            "implausible_tobacco_hops": ("yes" if float(r["value"]) > SCREEN_T else "no")
                                        if screened else "",
        })
    rows.sort(key=lambda r: (r["period"], r["item"], r["country"], r["indicator"], r["unit"],
                             str(r["value"])))
    return rows


def report(rows):
    import collections
    print(f"\n{len(rows)} iia period rows attributed to a volume (coverage is total by construction)")
    by_vol = collections.Counter(r["volume"] for r in rows)
    for vol in sorted(by_vol):
        tag = "LATE" if vol in LATE_VOLUMES else "clean"
        print(f"  {vol:12s} {tag:5s} {by_vol[vol]:5d}")
    late = sum(1 for r in rows if r["volume_is_late"] == "yes")
    print(f"  from a late volume: {late} of {len(rows)}   "
          f"items {len({r['item'] for r in rows if r['volume_is_late'] == 'yes'})}, "
          f"labels {len({r['country'] for r in rows if r['volume_is_late'] == 'yes'})}")

    scr = [r for r in rows if r["implausible_tobacco_hops"]]
    print(f"\ntobacco/hops (tonnes) period rows: {len(scr)}")
    print(f"  {'period':11s} {'volume':12s} {'':5s}  above 500 kt")
    for per in sorted({r["period"] for r in scr}):
        d = [r for r in scr if r["period"] == per]
        b = [r for r in d if r["implausible_tobacco_hops"] == "yes"]
        vol = d[0]["volume"]
        tag = "LATE" if vol in LATE_VOLUMES else "clean"
        print(f"  {per:11s} {vol:12s} {tag:5s}  {len(b):3d} / {len(d):3d}  "
              f"{100.0 * len(b) / len(d):5.1f}%")

    gap = [r for r in scr if r["implausible_tobacco_hops"] == "yes" and r["era_screened"] == "no"]
    print(f"\nimplausible tobacco/hops period rows with NO era verdict: {len(gap)}")
    for per in sorted({r["period"] for r in gap}):
        print(f"  {per}: {sum(1 for r in gap if r['period'] == per)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=DEFAULT_RAW)
    ap.add_argument("--layer-b", default=DEFAULT_PANEL)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    for path, what in ((a.raw, "raw IIA extract"), (a.layer_b, "layer B panel")):
        if not os.path.exists(path):
            print(f"SKIP: {what} not present on this machine ({path})", file=sys.stderr)
            return 0
    rows = build(a.raw, a.layer_b)
    report(rows)

    if a.check:
        if not os.path.exists(OUT):
            print(f"MISSING {OUT}; run with --write", file=sys.stderr)
            return 1
        with open(OUT, newline="", encoding="utf-8") as fh:
            have = list(csv.DictReader(fh))
        want = [{k: str(v) for k, v in r.items()} for r in rows]
        if have != want:
            print(f"STALE {OUT}: {len(have)} row(s) on disk, {len(want)} rebuilt", file=sys.stderr)
            for h, w in zip(have, want):
                if h != w:
                    print(f"  first difference:\n    disk  {h}\n    built {w}", file=sys.stderr)
                    break
            return 1
        print(f"\nOK {os.path.basename(OUT)} matches a fresh rebuild ({len(have)} rows)")
    if a.write:
        from atomic import write_csv_atomic
        write_csv_atomic(OUT, FIELDS, rows)
        print(f"\nwrote {OUT} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.path.insert(0, HERE)
    raise SystemExit(main())
