#!/usr/bin/env python3
"""Two labels of one source sharing a CONTIGUOUS BLOCK of identical values (issue 468).

THE SIGNATURE, and why a block is the interesting case. Two labels whose values are identical in
EVERY shared year are synonyms -- `25_same_polity_overlaps.py` already reports those, and they are a
spelling problem rather than a data one. Two labels that never agree are ordinary. A contiguous BLOCK
of identical years inside an otherwise differing pair is neither: it says one series was copied into
the other for a stretch and then stopped.

FOUND BY GENERALISING AN ACCIDENT. `iia` `czech republic` and `serbia` carry byte-identical rye AREA
for 1941-1944 and differ in all 18 other shared years; that turned up while yield-testing years a
confirmed `data_errors.csv` entry did not enumerate (issue 433). This screen looks for the same shape
everywhere, and it re-finds that case, which is the check that it works.

THE DISTINCTNESS FLOOR DOES ALMOST ALL THE WORK, and without it this file would be a
false-positive generator:

    pairs with a contiguous identical block                89
      ...surviving MIN_DISTINCT = 4 on the block            6

83 of the 89 are coincidence -- `estonia`/`iceland` goats, `belgium`/`malta` mules -- small round
numbers that match anything. The repo has been here before: a fingerprint over few distinct values
"proves" a relationship that does not exist, which is why 16_source_splices.py and
25_same_polity_overlaps.py carry the same floor. Four is deliberately lower than their six, because
a block is additionally constrained by CONTIGUITY and by the pair differing outside it; those two
conditions carry evidence a bare value-set match does not.

EVERY BLOCK FOUND IS A WAR WINDOW -- 1914-1921, 1939-1945, 1940-1946, 1941-1944, 1942-1945. That is
when national reporting broke down and compilers filled gaps, so the concentration is a mechanism
hint rather than a coincidence, and it is worth watching whether new instances keep that shape.

DIRECTION IS RECORDED WHERE THE LEVELS SAY IT. Outside the block the two series differ by a median
ratio; inside it they agree. Whichever side the block's values MATCH in level is the donor, and the
other label is the one carrying figures that are not its own. Sweden has no linseed rows at all
before its block, then seven years of Czechoslovakia's, then its own series; Finland's barley runs
118-199 kt either side of its block and 631-765 kt inside it, which is France's scale. So
`smaller_label` is the affected side. Where the levels do not separate cleanly the column is left
empty rather than guessed.

WHAT THIS DOES NOT DO. It does not repair anything and does not claim a mechanism -- a compilation
copy, a gap-fill from a neighbour and a spreadsheet fill-down all fit. `juan` supplies five of the
six instances and has no raw extract in this repo, so for those the provenance cannot be checked here.

Usage:
  python3 pipelines/polity-autoimprove/31_cross_label_duplication.py            # report only
  python3 pipelines/polity-autoimprove/31_cross_label_duplication.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/31_cross_label_duplication.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import csv
import itertools
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "cross_label_duplication.csv")
MATCHED = os.path.join(STATE, "matched_rows.parquet")

MIN_SHARED = 6          # fewer shared years than this and a block cannot be distinguished from noise
MIN_BLOCK = 3           # a block of two is a coincidence waiting to happen
MIN_DISTINCT = 4        # THE floor: see the docstring
# outside the block the pair must actually differ; inside this band they are effectively one series
SAME_LO, SAME_HI = 0.67, 1.5
MAX_LABELS = 60         # a (source, item, unit) with more labels than this is a global panel, not a pair
# A block whose own values swing more than this has no level to compare, so direction is left empty.
# Not a tuned number: the one independently verified case (iia czech/serbia) swings 35x and must be
# excluded, while the blocks that DO carry a level swing 1.2x-2.4x, so anything between separates them.
MAX_BLOCK_SPREAD = 5.0

FIELDS = ("source", "item", "unit", "label_a", "label_b", "shared_years", "block_years",
          "block_first", "block_last", "block_distinct", "outside_ratio_median", "block_spread",
          "smaller_label", "block_matches_level_of")


def _n(x, nd=4):
    f = float(x)
    return str(int(f)) if f == int(f) and abs(f) < 1e15 else repr(round(f, nd))


def build(matched: str) -> list[dict]:
    import pandas as pd

    d = pd.read_parquet(matched)
    d = d[d.value.notna() & d.year.notna() & d.country.notna()]
    d = d.assign(_l=d.country.str.strip().str.lower())
    rows = []
    for (src, item, unit), g in d.groupby(["source", "item", "unit"], sort=True):
        labs = sorted(g._l.unique())
        if not (2 <= len(labs) <= MAX_LABELS):
            continue
        piv = g.groupby(["_l", "year"]).value.median().unstack()
        for a, b in itertools.combinations(labs, 2):
            if a not in piv.index or b not in piv.index:
                continue
            x, y = piv.loc[a], piv.loc[b]
            both = x.notna() & y.notna()
            n_shared = int(both.sum())
            if n_shared < MIN_SHARED:
                continue
            eq = x[both] == y[both]
            n_eq = int(eq.sum())
            if n_eq < MIN_BLOCK or n_eq == n_shared:      # never equal, or synonyms
                continue
            block = x[both][eq]
            if block.nunique() < MIN_DISTINCT:
                continue                                   # the floor
            yrs = sorted(int(v) for v in eq[eq].index)
            if any(yrs[i + 1] - yrs[i] != 1 for i in range(len(yrs) - 1)):
                continue                                   # not contiguous
            out = (x[both][~eq] / y[both][~eq]).abs()
            if out.empty:
                continue
            om = float(out.median())
            if SAME_LO < om < SAME_HI:
                continue                                   # effectively one series outside too
            # DIRECTION: outside the block one label is consistently larger. The block's own level
            # tells which one it came from, and that side is the donor.
            smaller = a if om > 1 else b                   # om = median(a/b) over differing years
            larger = b if om > 1 else a
            lvl_s = float(x[both][~eq].median() if smaller == a else y[both][~eq].median())
            lvl_l = float(y[both][~eq].median() if smaller == a else x[both][~eq].median())
            bl = float(block.median())
            # A LEVEL COMPARISON NEEDS THE BLOCK TO HAVE A LEVEL. The first version of this column
            # answered "serbia" for the iia czech/serbia case -- the one instance whose direction is
            # independently established, and it is czech -> serbia (issue 433, proven by yield checks).
            # It got it backwards because THAT block is internally incoherent: 26,000 ha beside
            # 915,000 ha in adjacent years, a 35x swing, so its median describes nothing and lands
            # nearer the smaller series by arithmetic accident.
            #
            # Direction is therefore attributed only when the block is coherent enough to HAVE a
            # level, and left empty otherwise. An empty cell means "read the series", which is the
            # honest answer for a block whose own values disagree by more than the two labels do.
            blk_spread = float(block.max() / block.min()) if float(block.min()) > 0 else float("inf")
            matches = ""
            if (blk_spread <= MAX_BLOCK_SPREAD
                    and lvl_s > 0 and lvl_l > 0 and abs(lvl_l / lvl_s - 1) > 0.5):
                matches = larger if abs(bl - lvl_l) < abs(bl - lvl_s) else smaller
            rows.append({
                "source": src, "item": item, "unit": unit, "label_a": a, "label_b": b,
                "shared_years": n_shared, "block_years": n_eq,
                "block_first": yrs[0], "block_last": yrs[-1],
                "block_distinct": int(block.nunique()), "outside_ratio_median": _n(om),
                "block_spread": (_n(blk_spread) if blk_spread != float("inf") else ""),
                "smaller_label": smaller, "block_matches_level_of": matches,
            })
    rows.sort(key=lambda r: (-int(r["block_years"]), r["source"], r["item"], r["label_a"]))
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
    ap.add_argument("--matched", default=MATCHED)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    if not os.path.exists(a.matched):
        print(f"panel absent ({a.matched}); nothing to do", file=sys.stderr)
        return 0

    rows = build(a.matched)
    print(f"{len(rows)} label pair(s) share a contiguous block of identical values "
          f"(floor: {MIN_DISTINCT} distinct values, {MIN_BLOCK} years, contiguous, "
          f"differing outside)")
    for r in rows:
        d = (f" -> block matches {r['block_matches_level_of']}'s level"
             if r["block_matches_level_of"] else " -> level does not separate")
        print(f"  {r['source']:9} {r['item'][:24]:24} {r['unit']:7} "
              f"{r['label_a'][:20]:20}/{r['label_b'][:20]:20} "
              f"{r['block_years']}/{r['shared_years']} eq {r['block_first']}-{r['block_last']}"
              f"  {r['block_distinct']} distinct{d}")
    by_src = {}
    for r in rows:
        by_src[r["source"]] = by_src.get(r["source"], 0) + 1
    print(f"by source: {by_src}")

    if a.check:
        if not os.path.exists(OUT):
            print(f"MISSING {os.path.relpath(OUT, REPO)}", file=sys.stderr)
            return 1
        with open(OUT, newline="") as fh:
            have = list(csv.DictReader(fh))
        if have != [{k: str(v) for k, v in r.items()} for r in rows]:
            print(f"STALE {os.path.relpath(OUT, REPO)}: rerun with --write", file=sys.stderr)
            return 1
        print("table is current")
        return 0
    if a.write:
        write(rows, OUT)
        print(f"wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
