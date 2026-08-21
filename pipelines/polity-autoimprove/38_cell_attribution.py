#!/usr/bin/env python3
"""Which raw label does each cell of an `unattributable` series come from? (issues 372, 443)

THE BLIND SPOT THIS FILLS. `20_item_provenance.py` picks ONE best-matching raw label per series and needs
a 60% share to name it; 134 series covering 2,442 values fall short and are recorded
`unattributable`. That status reads as "we could not tell", but for many of them the answer is "from two
or more, and here is which cell came from which". Issue 372 says so in its own words about Ghana: its
Gold Coast leg attributes at only 50%, "the mixture is real; the floor hid it. That is a false negative
in the method, and there are probably others."

There are. Four were derived by hand on 2026-08-21 alone -- `congo` cacao from `french equatorial africa:
middle congo`, `united states of america` coffee from `us puerto rico`, `china, mainland` eggs from
`japan: kwantung leased territory`, `russian federation` hempseed from `ussr in europe` -- each time by
running the same query in a scratch script. This file runs it once, for every cell in the blind spot.

WHAT MAKES A CELL ATTRIBUTABLE HERE, and why it works below the share floor. A cell is attributed only
when EXACTLY ONE raw label matches on (raw_product, variable, year, value). That constrains three axes at
once, so it does not depend on the value being rare -- and the values usually are not: 1,150 occurs 38
times in the extract, 1,480 37 times. The year-and-product constraint does the work. A series-level
fingerprint cannot do this because it needs enough matching cells to clear a share; a cell needs only
itself.

THE CANDIDATE PRODUCTS COME FROM THE CROSSWALK, NOT FROM STRING SIMILARITY. `item_equivalences.csv` maps
a layer-B item to its raw product(s); only those are searched. Pooling several products for one item is
what produced five spurious `flax fibre and tow` rows in an earlier pass of a different measurement, so
`n_products` is recorded per row and a reader can see when more than one was in play.

ZERO-VALUED CELLS ARE EXCLUDED. A published 0 matches every raw row printing 0, which in an earlier sweep
manufactured 20 "findings" where `american samoa` and `sweden` matched a Mozambique sub-unit.

WHAT A ROW IS NOT. It is not a verdict that the cell is misrouted. `gabon` matching `french equatorial
africa: gabon` is correct; `congo` matching `...: middle congo` is not, and no arithmetic separates those
-- that judgement needs the composition and succession registries. This table records WHERE a cell came
from and leaves what follows to the issues.

Usage:
  python3 pipelines/polity-autoimprove/38_cell_attribution.py            # report only
  python3 pipelines/polity-autoimprove/38_cell_attribution.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/38_cell_attribution.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import collections
import csv
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "cell_attribution.csv")
PROVENANCE = os.path.join(STATE, "item_provenance.csv")
EQUIV = os.path.join(STATE, "item_equivalences.csv")
PANEL_DEFAULT = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B", "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"))
RAW_DEFAULT = os.path.expanduser(os.environ.get(
    "WHEP_IIA_RAW",
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx"))

UNIT_VARIABLE = {"ha": "area", "tonnes": "production"}

FIELDS = ("layer_b_label", "item", "unit", "when", "value", "raw_label", "raw_product",
          "variable", "n_products_searched", "n_raw_rows_in_cell", "cells_for_this_label",
          "cells_in_series", "series_time_structure")


# COLUMN NAMES CARRY A TRAILING UNDERSCORE, NOT A LEADING ONE. `DataFrame.itertuples()` silently renames
# any attribute starting with "_" to a positional alias, so `t._p` raises AttributeError while the column
# is present and correct. That cost three separate debugging rounds on 2026-08-21 in three different
# scripts, always with an error pointing at a column that plainly exists.
def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def time_structure(spans: dict) -> str:
    """Do a series' raw labels PARTITION time, or INTERLEAVE? This is the column that decides whether a
    date-keyed reroute is even possible, so it travels with the rows rather than being re-derived.

    `partition` -- the labels' year ranges are disjoint, so there is a boundary year and the split is a
    SUCCESSION: `austria-hungary` 1909-1914 then `austria` 1925-1932 at the dissolution;
    `italian libya: tripolitania` 1924-1925 then `italian libya` 1928-1939 at the 1934 unification. This
    is the shape issue 443's `split_candidate` models, and requiring separation is what keeps it honest.

    `interleaved` -- the ranges overlap, and then the label's own dates carry NO boundary. Two sub-shapes,
    both fatal to a date-keyed repair, and the column does not try to separate them because the arithmetic
    cannot: (a) a whole reported concurrently with its part, `australia` beside `australia: queensland`,
    `dutch east indies` beside `dutch java and madura`; (b) a PERSISTENT COLUMN HEADER whose dates
    contradict the entity's -- `italian east africa` supplies 1928-1935 though Italian East Africa existed
    1936-1941, and `ethiopian empire` supplies 1939-1940, during the occupation. Issue 372 names this for
    `german togoland`. A reroute keyed on the label's name would be wrong in both directions.

    30 of 52 multi-label series are `interleaved`, which is also the measure of how much work the
    separation criterion is doing: without it they would all read as successions.
    """
    labels = sorted(spans)
    if len(labels) < 2:
        return "single_label"
    for i in range(len(labels) - 1):
        for j in range(i + 1, len(labels)):
            a, b = spans[labels[i]], spans[labels[j]]
            if a[0] <= b[1] and b[0] <= a[1]:
                return "interleaved"
    return "partition"


def build(panel_path: str, raw_path: str) -> list[dict]:
    import pandas as pd

    with open(PROVENANCE, newline="") as fh:
        prov = [r for r in csv.DictReader(fh) if r["status"] == "unattributable"]
    # KEY ON THE NORMALISED ITEM. `item_provenance.csv` stores item names through the same norm() as
    # `20_item_provenance.py` -- `cacao beans`, `coffee green` -- while the panel stores `cacao, beans`
    # and `coffee, green`. Matching the raw strings excluded every comma-bearing item silently: 48 of the
    # 134 unattributable series, 934 values, including `united states of america / coffee green`, the
    # series adjudicated on issue 424. The table looked complete because nothing in it was wrong; what
    # was missing left no trace. Check the generator of any state table for a normalise call before
    # joining against it.
    targets = {(r["layer_b_label"], r["item"], r["unit"]) for r in prov}
    if not targets:
        return []

    equiv = collections.defaultdict(set)
    with open(EQUIV, newline="") as fh:
        for r in csv.DictReader(fh):
            equiv[r["item"]].add(str(r["raw_product"]).strip().lower())

    raw = pd.read_excel(raw_path)
    raw.columns = [c.strip().lower() for c in raw.columns]
    raw = raw[raw["value"].notna()]
    raw = raw.assign(c_=raw["country"].astype(str).str.strip().str.lower(),
                     p_=raw["product"].astype(str).str.strip().str.lower(),
                     y_=raw["year"].astype(str).str.strip())
    # (product, variable, year) -> [(label, value)]
    idx = collections.defaultdict(list)
    for t in raw.itertuples():
        idx[(t.p_, t.variable, t.y_)].append((t.c_, float(t.value)))

    d = pd.read_parquet(panel_path, columns=["source", "country", "item", "unit", "value",
                                             "year", "period"])
    # ZERO EXCLUDED: a 0 matches every raw row printing 0.
    d = d[(d.source == "iia") & d.value.notna() & (d.value != 0)]
    when = d.period.where(d.period.notna(), d.year.astype("string"))
    d = d.assign(when_=when)

    rows = []
    for t in d.itertuples():
        key = (str(t.country), norm(t.item), str(t.unit))
        if key not in targets:
            continue
        var = UNIT_VARIABLE.get(str(t.unit))
        prods = equiv.get(norm(t.item), set())
        if var is None or not prods:
            continue
        v = float(t.value)
        cands, in_cell = [], 0
        for p in sorted(prods):
            cell = idx.get((p, var, str(t.when_).strip()), ())
            in_cell += len(cell)
            for lab, val in cell:
                if abs(val - v) <= 1e-6 * max(abs(v), 1.0):
                    cands.append((lab, p))
        uniq = sorted(set(cands))
        if len(uniq) != 1:
            continue
        rows.append({
            # the NORMALISED item, so this table joins to item_provenance and item_equivalences
            "layer_b_label": t.country, "item": norm(t.item), "unit": t.unit,
            "when": str(t.when_).strip(), "value": repr(v) if v != int(v) else str(int(v)),
            "raw_label": uniq[0][0], "raw_product": uniq[0][1], "variable": var,
            "n_products_searched": len(prods), "n_raw_rows_in_cell": in_cell,
        })
    # A UNIQUE MATCH CAN STILL BE A COINCIDENCE, and these two columns are what let a reader see it.
    # `jamaica / cotton lint / tonnes` attributes 8 cells to `british jamaica` and 2 to `bulgaria` --
    # issue 443 calls the Bulgaria leg "plainly coincidence" on exactly this ground, a tiny minority on
    # few distinct values. Ghana's `british gold coast` 10 against `german togoland` 10 is the opposite
    # shape and is issue 372's confirmed mixture. Neither is decidable from a single row, so the counts
    # travel with every row rather than living in prose.
    per = collections.Counter((r["layer_b_label"], r["item"], r["unit"], r["raw_label"]) for r in rows)
    tot = collections.Counter((r["layer_b_label"], r["item"], r["unit"]) for r in rows)
    for r in rows:
        k = (r["layer_b_label"], r["item"], r["unit"])
        r["cells_for_this_label"] = per[(*k, r["raw_label"])]
        r["cells_in_series"] = tot[k]

    # Per-series time structure. An undatable `when` (a period this regex does not parse) leaves the
    # series `undatable` rather than being guessed at.
    spans = collections.defaultdict(dict)
    ok = collections.defaultdict(lambda: True)
    for r in rows:
        k = (r["layer_b_label"], r["item"], r["unit"])
        m = re.match(r"^(\d{4})(?:-(\d{4}))?$", r["when"].strip())
        if not m:
            ok[k] = False
            continue
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        cur = spans[k].get(r["raw_label"])
        spans[k][r["raw_label"]] = (min(lo, cur[0]), max(hi, cur[1])) if cur else (lo, hi)
    for r in rows:
        k = (r["layer_b_label"], r["item"], r["unit"])
        r["series_time_structure"] = time_structure(spans[k]) if ok[k] else "undatable"
    rows.sort(key=lambda r: (r["layer_b_label"], r["item"], r["unit"], r["when"]))
    return rows


def write(rows: list[dict], path: str) -> None:
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            for r in rows:
                w.writerow(r)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--layer-b", default=PANEL_DEFAULT)
    ap.add_argument("--raw", default=RAW_DEFAULT)
    a = ap.parse_args()

    for p in (a.layer_b, a.raw, PROVENANCE, EQUIV):
        if not os.path.exists(p):
            print(f"input absent ({p}); nothing to do", file=sys.stderr)
            return 0
    rows = build(a.layer_b, a.raw)
    series = collections.Counter((r["layer_b_label"], r["item"], r["unit"]) for r in rows)
    labels = collections.Counter(r["raw_label"] for r in rows)
    print(f"{len(rows)} cell(s) uniquely attributed across {len(series)} `unattributable` series")
    print("  most common raw labels:")
    for lab, n in labels.most_common(12):
        print(f"    {n:4}  {lab}")
    print("  series with cells from more than one raw label:")
    per = collections.defaultdict(collections.Counter)
    for r in rows:
        per[(r["layer_b_label"], r["item"], r["unit"])][r["raw_label"]] += 1
    multi = {k: v for k, v in per.items() if len(v) > 1}
    for k, v in sorted(multi.items()):
        print(f"    {k[0]} / {k[1]} / {k[2]}: {dict(v)}")
    print(f"  ({len(multi)} of {len(series)} series draw on more than one label)")

    if a.check:
        if not os.path.exists(OUT):
            print(f"MISSING {OUT}; run with --write", file=sys.stderr)
            return 1
        with open(OUT, newline="") as fh:
            have = list(csv.DictReader(fh))
        want = [{k: str(v) for k, v in r.items()} for r in rows]
        if have != want:
            print(f"STALE {OUT}: {len(have)} row(s) on disk, {len(want)} rebuilt", file=sys.stderr)
            for h, w in zip(have, want):
                if h != w:
                    print(f"  first difference:\n    disk {h}\n    built {w}", file=sys.stderr)
                    break
            return 1
        print(f"OK {os.path.basename(OUT)} matches a fresh rebuild ({len(have)} rows)")
    if a.write:
        write(rows, OUT)
        print(f"wrote {OUT} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
