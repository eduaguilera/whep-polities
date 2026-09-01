#!/usr/bin/env python3
"""Does one layer-B item series draw on several different RAW PRODUCTS, switching year to year?

`20_item_provenance.py` asks which raw LABEL an item series came from -- a territory question. This
asks which raw PRODUCT each individual cell came from, which is a different failure: the territory can
be right, the item name constant, the source unchanged, and the series still be a patchwork of
different commodities.

THE EXHIBIT, `australia / sugar raw centrifugal / tonnes`, 33 cells:

    1912  131,961  sugar: cane
    1913      922  sugar: BEET             x0.01
    1920  165,616  sugar: cane             x105
    1922    2,829  sugar: BEET             x0.01
    1925  537,212  sugar: cane, unrefined  x175
    1938  783,200  sugar: cane
    1939    6,400  sugar: BEET             x0.01
    1944  611,300  sugar: cane             x873

Australia's beet sugar industry was negligible, so 12 of the 33 cells are about 1/300 of the series
they sit in. Same shape in `sweden / p`: calcium superphosphate 1909-1920, BASIC SLAG 1930-1932
(x0.08), superphosphate again 1933 (x28) -- which is why a `p` series is a patchwork of fertilizer
MATERIALS and not a P2O5 total, refuting half of the convention registered for it in issue 369.

WHY NOTHING ELSE SEES IT. The source never changes, so `16_source_splices.py` finds no seam. Each
value is entirely plausible FOR THE PRODUCT IT CAME FROM, so no magnitude screen fires. The item name
is constant, so nothing keyed on the item notices. It is also part of the mechanism behind issue 360's
level-shift confound: a detector hunting territorial steps in these series finds the yearbook's choice
of table.

THE TEST IS OSCILLATION, AND THE REASON IS A CONFOUND I HIT FIRST. Comparing each product's MEDIAN
reports a level gap for any GROWING series that happens to draw on an early product and a late one --
growth, not a defect. So a series is only recorded when a product RECURS after another has intervened
(A...B...A), traced year by year. That pattern cannot be produced by a trend.

A cell counts only when EXACTLY ONE (raw label, product) pair carries its (year, value). A value
matched by several is a collision, not evidence -- `australia / sugar` 1942 reads 700, which also
appears under castorseed, coffee and butter -- and those cells are counted as ambiguous, never guessed.

WHAT THIS DOES NOT DECIDE. Which product the series SHOULD carry, or what the other cells should become.
`australia / sugar` is clear because Australia grew no beet, but that is agronomy, not arithmetic.

Usage:
  python3 pipelines/polity-autoimprove/21_item_product_switches.py            # report only
  python3 pipelines/polity-autoimprove/21_item_product_switches.py --write    # refresh the table
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
OUT = os.path.join(HERE, "state/item_product_switches.csv")
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B") or os.environ.get("WHEP_LAYERB")
    # ONE PANEL, EITHER SPELLING (issue 629). Two names were in use -- WHEP_LAYERB in
    # 01_match_and_findings.py and extdata.py, WHEP_LAYER_B in the other 17 tools -- so
    # neither redirected the whole pipeline and setting one left stage 01 matching against
    # a different panel than the analysis stages measured.
    or "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet")
DEFAULT_RAW = os.path.expanduser(os.environ.get(
    "WHEP_IIA_RAW",
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx"))

PRODUCTION = {"production", "area", "bearing area", "production of cocoons"}
MIN_CELLS = 8          # a series shorter than this cannot show a convincing return
MIN_PER_PRODUCT = 2    # one cell of a product is as likely to be a collision as a switch
LEVEL = 3.0            # the jump at a switch must clear this to be worth recording


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def raw_index(raw_path):
    """(year, value) -> {(raw_label, product)}, production side only."""
    import pandas as pd
    r = pd.read_excel(raw_path)
    r["c"] = r["country"].astype(str).str.strip().str.lower()
    r["v"] = pd.to_numeric(r["value"], errors="coerce")
    r["y"] = pd.to_numeric(r["year"], errors="coerce")
    r = r[r["variable"].isin(PRODUCTION)].dropna(subset=["v", "y"])
    idx = defaultdict(set)
    for x in r.itertuples():
        idx[(int(x.y), round(float(x.v), 1))].add((x.c, str(x.product)))
    return idx


def oscillates(seq):
    """True when a product RECURS after another has intervened: A ... B ... A.

    This is the whole discriminator. A monotonic series that draws on one product early and another
    late shows the same LEVEL gap as a defect but never returns, so it is not recorded.
    """
    seen_then_left = set()
    current = None
    for p in seq:
        if p != current:
            if p in seen_then_left:
                return True
            if current is not None:
                seen_then_left.add(current)
            current = p
    return False


def measure(panel_path, raw_path):
    import pandas as pd
    idx = raw_index(raw_path)
    d = pd.read_parquet(panel_path)
    if "is_aggregate" in d.columns:
        d = d[~d["is_aggregate"].astype(bool)]
    d = d[d["source"] == "iia"].dropna(subset=["value", "year"])
    d["i"] = d["item"].map(norm)

    rows = []
    for (label, item, unit), g in d.groupby([d["country"].astype(str), "i", "unit"]):
        g = g.sort_values("year")
        traced, n_ambig = [], 0
        for x in g.itertuples():
            m = idx.get((int(x.year), round(float(x.value), 1)), set())
            if len(m) == 1:
                traced.append((int(x.year), float(x.value), next(iter(m))[1]))
            else:
                n_ambig += 1
        if len(traced) < MIN_CELLS:
            continue
        per = defaultdict(int)
        for _y, _v, p in traced:
            per[p] += 1
        products = {p for p, c in per.items() if c >= MIN_PER_PRODUCT}
        if len(products) < 2:
            continue
        seq = [(y, v, p) for y, v, p in traced if p in products]
        if not oscillates([p for _y, _v, p in seq]):
            continue
        # the largest jump that lands exactly on a product change
        worst, worst_at = 0.0, None
        for a, b in zip(seq, seq[1:]):
            if a[2] == b[2] or a[1] <= 0 or b[1] <= 0:
                continue
            ratio = max(a[1] / b[1], b[1] / a[1])
            if ratio > worst:
                worst, worst_at = ratio, (a, b)
        if worst < LEVEL:
            continue
        (ya, va, pa), (yb, vb, pb) = worst_at
        rows.append({
            "layer_b_label": label, "item": item, "unit": unit,
            "n_cells": len(g), "n_traced": len(traced), "n_ambiguous": n_ambig,
            "n_products": len(products),
            "products": ";".join(f"{p}={per[p]}" for p in sorted(products, key=lambda q: -per[q])),
            "worst_switch_ratio": f"{worst:.2f}",
            "worst_switch": f"{ya}:{va:.0f} [{pa}] -> {yb}:{vb:.0f} [{pb}]",
        })
    rows.sort(key=lambda r: -float(r["worst_switch_ratio"]))
    return rows


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
    ap.add_argument("--write", action="store_true", help=f"refresh {os.path.relpath(OUT, REPO)}")
    args = ap.parse_args()

    for path, what in ((args.layer_b, "layer-B panel"), (args.raw, "raw IIA extract")):
        if not os.path.exists(path):
            print(f"SKIP: {what} not present at {path}")
            return 0

    rows = measure(args.layer_b, args.raw)
    print(f"iia series that OSCILLATE between raw products with a >={LEVEL:.0f}x jump at a "
          f"switch: {len(rows)}\n")
    print(f"{'jump':>10}  {'label':20} {'item':22} {'unit':6} {'cells':>5} {'prod':>4}  switch")
    for r in rows:
        print(f"  {float(r['worst_switch_ratio']):>9,.0f}x {r['layer_b_label'][:18]:20} "
              f"{r['item'][:20]:22} {r['unit'][:5]:6} {r['n_cells']:>5} {r['n_products']:>4}  "
              f"{r['worst_switch'][:64]}")

    if args.write or args.check:
        cols = ["layer_b_label", "item", "unit", "n_cells", "n_traced", "n_ambiguous",
                "n_products", "products", "worst_switch_ratio", "worst_switch"]
        if args.check:
            if not os.path.exists(OUT):
                print(f"MISSING {os.path.relpath(OUT, REPO)}", file=sys.stderr)
                return 1
            with open(OUT, newline="", encoding="utf-8") as fh:
                have = list(csv.DictReader(fh))
            want = [{k: ("" if v is None else str(v)) for k, v in dict(r).items()} for r in rows]
            if [{k: r.get(k, "") for k in cols} for r in have] != \
                    [{k: r.get(k, "") for k in cols} for r in want]:
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
                w = csv.DictWriter(fh, fieldnames=cols)
                w.writeheader()
                w.writerows(rows)
            os.replace(tmp, OUT)
        except BaseException:
            if os.path.exists(tmp):
                os.unlink(tmp)
            raise
        print(f"\nwrote {len(rows)} series to {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
