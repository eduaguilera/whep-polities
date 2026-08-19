#!/usr/bin/env python3
"""Where do FOUR OR MORE items share one value in a single label-year? A broadcast cell, not data.

Every repetition detector here looks along the YEAR axis. `17_constant_runs.py` finds one value
repeated across years within one series; `27_series_collapses.py` finds a year out of line with its
own neighbours. Neither can see a value repeated across ITEMS within one year, and that shape has a
different cause: not a carried-forward estimate but a single cell broadcast over a row, or a
placeholder standing in for a table nobody filled.

WHAT MAKES IT DIAGNOSTIC. `27_series_collapses.py` already flags `mitchell india / swine` at 1947 as
an interior collapse -- 3,000 between 3,653,000 and 4,420,000. What it cannot say is that asses,
buffalo, camels, cattle, goats, horses, sheep and swine ALL read exactly 3,000 that year. Eight
independent errors landing on the same number is not a hypothesis anyone needs to weigh; one broadcast
cell is. The cross-item pattern is the diagnosis, and it is invisible to a per-series test.

THE VALUE ITSELF PROVES NOTHING. `3,000` occurs 148 times across 48 mitchell labels and 23 items,
legitimately -- plenty of small producers really do report 3,000 head. It is the coincidence WITHIN a
label-year that carries the signal, which is why the key is (source, label, unit, year) and why the
threshold is a count of distinct items rather than any property of the number.

WHY UNIT IS IN THE KEY. Without it the test pools livestock heads with crop hectares and tonnes, and
the india block disappears: its crop rows that year carry ordinary varied values, so the group is no
longer uniform and the block goes unreported. A placeholder is broadcast across one TABLE, and a table
is one unit.

WHAT THE FIRST RUN FOUND -- five blocks in the whole panel, and all five are defects:

    mitchell india    heads 1947   8 items all      3,000   other years' median 20,895,500  (6,965x)
    mitchell somalia  heads 1959   4 items all     15,000   other years' median  1,286,000  (   86x)
    iia      belgium  ha    1934   4 items all          0
    iia      belgium  ha    1935   4 items all          0
    iia      belgium  ha    1936   4 items all          0

The belgium blocks are issue 414's blank-read-as-0 arriving as a block rather than a cell, and they
fall inside the iia_1938_39 window. India's cattle reads 3,000 in a year it reads 160,220,000 (1936)
and 155,295,000 (1951), so no external source is needed to convict it.

Usage:
  python3 pipelines/polity-autoimprove/28_item_blocks.py            # report only
  python3 pipelines/polity-autoimprove/28_item_blocks.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/28_item_blocks.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "item_blocks.csv")
DEFAULT_PANEL = os.path.expanduser(os.environ.get(
    "WHEP_LAYER_B", "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"))

# Four distinct items sharing one value. Three would admit real coincidences among small producers --
# a country reporting 1,000 head of three different animals is unremarkable -- and the observed blocks
# are at 4 and 8, so nothing is lost. NOT tuned to the findings: raising it to 5 would drop somalia
# and belgium, which are defects, and lowering it to 3 admits noise.
MIN_ITEMS = 4

FIELDS = ["source", "country", "unit", "year", "n_items", "value", "items",
          "other_years_median", "ratio_to_other_years"]


def build(panel_path: str) -> list[dict]:
    import pandas as pd

    d = pd.read_parquet(panel_path)
    d = d.dropna(subset=["year", "value"])
    out = []
    for (src, lab, unit, yr), g in d.groupby(["source", "country", "unit", d["year"].astype(int)]):
        if g["item"].nunique() < MIN_ITEMS:
            continue
        vals = g["value"].unique()
        if len(vals) != 1:
            continue
        value = float(vals[0])
        items = sorted({str(i) for i in g["item"]})
        # The same items' level in OTHER years is what makes the block indefensible rather than merely
        # odd. Measured over every other year those items report, not just adjacent ones.
        oth = d[(d["source"] == src) & (d["country"] == lab) & (d["unit"] == unit)
                & (d["item"].isin(items)) & (d["year"].astype(int) != yr)]
        med = float(oth["value"].median()) if len(oth) else float("nan")
        out.append({
            "source": src, "country": lab, "unit": unit, "year": yr,
            "n_items": len(items), "value": f"{value:g}", "items": ";".join(items),
            "other_years_median": "" if med != med else f"{med:g}",
            "ratio_to_other_years": ("" if med != med or value == 0 else f"{med / value:.1f}"),
        })
    out.sort(key=lambda r: (r["source"], r["country"], r["unit"], r["year"]))
    return out


def write(rows: list[dict], path: str) -> None:
    """Build fully in memory then replace atomically — a truncating open() has cost this repo two
    tracked state files mid-error."""
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, path)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layer-b", default=DEFAULT_PANEL)
    ap.add_argument("--write", action="store_true", help=f"refresh {os.path.relpath(OUT, REPO)}")
    ap.add_argument("--check", action="store_true", help="exit 1 if the tracked table is stale")
    args = ap.parse_args()

    if not os.path.exists(args.layer_b):
        print(f"panel absent ({args.layer_b}); nothing to do", file=sys.stderr)
        return 0

    rows = build(args.layer_b)
    print(f"label-years where >={MIN_ITEMS} items share one value: {len(rows)}")
    for r in rows:
        extra = (f"   other years' median {r['other_years_median']}"
                 f" ({r['ratio_to_other_years']}x)" if r["ratio_to_other_years"] else "")
        print(f"  {r['source']:9}{r['country'][:20]:22}{r['unit']:7}{r['year']}  "
              f"{r['n_items']} items all = {r['value']:>12}{extra}")

    if args.check:
        if not os.path.exists(OUT):
            print(f"MISSING {os.path.relpath(OUT, REPO)}", file=sys.stderr)
            return 1
        with open(OUT, newline="") as fh:
            have = list(csv.DictReader(fh))
        want = [{k: str(v) for k, v in r.items()} for r in rows]
        if have != want:
            print(f"STALE {os.path.relpath(OUT, REPO)}: rerun with --write", file=sys.stderr)
            return 1
        print("table is current")
        return 0

    if args.write:
        write(rows, OUT)
        print(f"wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
