#!/usr/bin/env python3
"""Which raw IIA product does each layer-B ITEM actually stand for, and is that mapping approved?

Three defects already found are the same shape: a layer-B item carrying a raw product it is not named
for. `wheat` is spelt and meslin (issue 375) -- the source has no wheat production rows at all.
`flax fibre and tow` is majority LINSEED, the seed rather than the fibre, with 19 cells also present
under the `linseed` item (issue 380). And a `p` series is a patchwork of fertilizer MATERIALS rather
than a P2O5 total (issue 378).

Each was found by hand. This turns the question into a small, curated registry so the next one fails a
gate instead of waiting to be noticed: every (layer-B item, raw product) pair that carries at least
MIN_CELLS cells in some series must have an explicit VERDICT.

The list is short enough to curate. Of 96 observed pairs, 64 share a word between the item name and the
product name and are self-evident (`cotton lint` <- `cotton: ginned`); the other 32 need a decision.

  approved_rename       the same thing under another name -- `cotton seed` <- `cottonseed`,
                        `silk worm cocoons reelable` <- `sericulture`, `soybeans` <- `soybean`
  approved_aggregation  several specific products deliberately mapped to one category -- `n` <-
                        ammonium sulfate AND calcium cyanamide. Legitimate as a MAPPING, but the
                        resulting series is a patchwork, which is what 21_item_product_switches.py
                        gates separately
  defect                the item is not the product -- `wheat` <- `spelt`, `flax fibre and tow` <-
                        `linseed`
  unresolved            genuinely unclear and NOT to be waved through: `fertilizer mixed` <-
                        `sulphur` is the honest example, since sulphur is a fungicide and soil
                        amendment rather than a mixed fertiliser

REGENERATING MUST NOT DESTROY THE VERDICTS. This script MERGES: existing pairs keep their verdict and
note, only the measured counts are refreshed, and new pairs arrive with an EMPTY verdict for the gate
to reject. Overwriting a hand-adjudicated column from a fresh measurement has silently reversed
decisions in this pipeline before.

Usage:
  python3 pipelines/polity-autoimprove/22_item_equivalences.py            # report only
  python3 pipelines/polity-autoimprove/22_item_equivalences.py --write    # merge and refresh
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "state/item_equivalences.csv")
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B", "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"))
DEFAULT_RAW = os.path.expanduser(os.environ.get(
    "WHEP_IIA_RAW",
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx"))

PRODUCTION = {"production", "area", "bearing area", "production of cocoons"}
MIN_CELLS = 2       # one cell of a product in one series is as likely a value collision as a mapping
VERDICTS = ("approved_rename", "approved_aggregation", "defect", "unresolved")
COLS = ["item", "raw_product", "cells", "series", "names_share_word", "verdict", "note"]


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def observed(panel_path, raw_path):
    import pandas as pd
    r = pd.read_excel(raw_path)
    r["v"] = pd.to_numeric(r["value"], errors="coerce")
    r["y"] = pd.to_numeric(r["year"], errors="coerce")
    r = r[r["variable"].isin(PRODUCTION)].dropna(subset=["v", "y"])
    idx = defaultdict(set)
    for x in r.itertuples():
        idx[(int(x.y), round(float(x.v), 1))].add(str(x.product))

    d = pd.read_parquet(panel_path)
    if "is_aggregate" in d.columns:
        d = d[~d["is_aggregate"].astype(bool)]
    d = d[d["source"] == "iia"].dropna(subset=["value", "year"])
    d["i"] = d["item"].map(norm)

    cells, series = defaultdict(int), defaultdict(int)
    for (_lab, item, _un), g in d.groupby([d["country"].astype(str), "i", "unit"]):
        got = defaultdict(int)
        for x in g.itertuples():
            m = idx.get((int(x.year), round(float(x.value), 1)), set())
            if len(m) == 1:                     # a value carried by several products is not evidence
                got[next(iter(m))] += 1
        for p, c in got.items():
            if c >= MIN_CELLS:
                cells[(item, p)] += c
                series[(item, p)] += 1
    return cells, series


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layer-b", default=DEFAULT_PANEL)
    ap.add_argument("--raw", default=DEFAULT_RAW)
    # Every tool from 25 up carries --check; these eight did not, so their tracked tables could drift
    # undetected. That is not hypothetical: 04's --check caught territory_basis.csv drifting after a
    # routing fix, and 23's absence let verdict_carryover.csv go stale (issues 308, 472). Safe here
    # because all eight were verified to regenerate byte-identically with default arguments -- the
    # precondition 15_label_provenance did NOT meet, where a check would have invited data loss.
    ap.add_argument("--check", action="store_true",
                    help="exit 1 if the tracked table is not what this run produces")
    ap.add_argument("--write", action="store_true", help=f"merge into {os.path.relpath(OUT, REPO)}")
    args = ap.parse_args()

    for path, what in ((args.layer_b, "layer-B panel"), (args.raw, "raw IIA extract")):
        if not os.path.exists(path):
            print(f"SKIP: {what} not present at {path}")
            return 0

    cells, series = observed(args.layer_b, args.raw)

    prior = {}
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                prior[(row["item"], row["raw_product"])] = row

    rows, new_pairs, gone = [], [], []
    for key in sorted(cells):
        item, product = key
        old = prior.get(key, {})
        if not old:
            new_pairs.append(key)
        rows.append({
            "item": item, "raw_product": product,
            "cells": cells[key], "series": series[key],
            "names_share_word": "yes" if set(norm(item).split()) & set(norm(product).split()) else "no",
            # MERGED, never overwritten: a fresh measurement must not reverse an adjudication.
            "verdict": old.get("verdict", ""),
            "note": old.get("note", ""),
        })
    for key in sorted(prior):
        if key not in cells:
            gone.append(key)

    by = defaultdict(int)
    for r in rows:
        by[r["verdict"] or "(unclassified)"] += 1
    print(f"observed (item, raw product) pairs with >={MIN_CELLS} cells: {len(rows)}")
    for v in list(VERDICTS) + ["(unclassified)"]:
        if by.get(v):
            print(f"   {v:22} {by[v]:>4}")
    print(f"   of all pairs, names share a word: "
          f"{sum(1 for r in rows if r['names_share_word'] == 'yes')}")
    if new_pairs:
        print(f"\nNEW pairs, arriving unclassified ({len(new_pairs)}):")
        for item, p in new_pairs:
            print(f"   {item[:30]:32} <- {p[:36]:38} {cells[(item, p)]:>4} cells")
    if gone:
        print(f"\npairs no longer observed ({len(gone)}) — their verdicts are dropped on --write:")
        for item, p in gone:
            print(f"   {item[:30]:32} <- {p[:36]}")
    print("\ndefect / unresolved pairs:")
    for r in rows:
        if r["verdict"] in ("defect", "unresolved"):
            print(f"   {r['verdict']:12} {r['item'][:26]:28} <- {r['raw_product'][:30]:32} "
                  f"{r['cells']:>4} cells in {r['series']:>2} series")

    if args.write or args.check:
        if args.check:
            if not os.path.exists(OUT):
                print(f"MISSING {os.path.relpath(OUT, REPO)}", file=sys.stderr)
                return 1
            with open(OUT, newline="", encoding="utf-8") as fh:
                have = list(csv.DictReader(fh))
            want = [{k: ("" if v is None else str(v)) for k, v in dict(r).items()} for r in rows]
            if [{k: r.get(k, "") for k in COLS} for r in have] != \
                    [{k: r.get(k, "") for k in COLS} for r in want]:
                print(f"STALE {os.path.relpath(OUT, REPO)}: committed {len(have)} row(s), this run "
                      f"produces {len(want)}; rerun with --write", file=sys.stderr)
                return 1
            print(f"table is current ({len(have)} rows)")
            return 0
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(OUT), suffix=".tmp")
        os.close(fd)
        # The unlink matters: a DictWriter raises on an unexpected key, and without this the
        # half-written .tmp is left behind in a TRACKED state directory where `git add -A`
        # can commit it. That happened on 2026-08-20 when a column was added to the rows but
        # not to the fieldnames.
        try:
            with open(tmp, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=COLS)
                w.writeheader()
                w.writerows(rows)
            os.replace(tmp, OUT)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        print(f"\nwrote {len(rows)} pairs to {os.path.relpath(OUT, REPO)} "
              f"({len(new_pairs)} new, {len(gone)} dropped)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
