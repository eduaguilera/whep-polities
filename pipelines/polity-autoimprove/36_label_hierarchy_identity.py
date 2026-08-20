#!/usr/bin/env python3
"""Does a source's own arithmetic say its nested labels PARTITION a territory, or DUPLICATE it?

THE QUESTION THIS ANSWERS, and why it keeps coming up. Several open issues turn on whether two labels
of one source are a whole and its parts (must not both be aggregated), the same territory twice (a
pure double count), or an overlapping pair (neither) -- 411 (Germany), 449 (China), 450 (French North
Africa), 355, 312, 400. Each was argued from history or from magnitude. But where a source prints the
whole AND the parts in the same cell, its own arithmetic decides it, and that is the strongest evidence
class available here: an exact identity, not a plausibility judgement.

THE CONTROL, and it is what made this file worth writing. `fao1952` prints `Germany` beside `Germany
Western`, `Germany Eastern` and `Germany Berlin` at period 1934-1938:

    rye  area        1,666 + 1,209 +   3 =  2,878  vs  2,878 printed
    milk production 14,906 + 4,940 +  67 = 19,913  vs 19,913 printed

28 cells carry the whole and all three parts and 28 of 28 sum to within 2%. That is not a relationship
anyone has to argue for.

THE FOUR VERDICTS ARE GENUINELY DIFFERENT DEFECTS, which is the point of separating them:

    partition   all kids present and they sum to the whole -> aggregating whole AND parts double counts
    duplicate   ONE kid, and it equals the whole           -> the kid is a synonym, not a subdivision
    subset      the kids sum to LESS than the whole        -> only a finding as `subset_all_parts`,
                                                             where every named child is present and
                                                             they still fall short; with only some
                                                             children present a shortfall is expected
    overlap     the kids sum to MORE than the whole        -> the children are not disjoint

`iia` `ethiopia` / `ethiopia pdr` lands in `duplicate` at 3 of 3 cells exact, and that pair is already
recorded in `data_errors.csv` as a nested-reporting-level collision -- so the screen re-finds a known
case it was not built for, which is the check that it works.

WHY THE PARTS PRESENT ARE PART OF THE KEY, and the mistake this corrects. Grouping only on the whole
label conflates two different measurements. For Germany the cells where TWO kids are present also read
median 1.000 -- because the two are usually Western + Eastern and Berlin is a rounding error at 1-67
units. But the two currently routed to `DEU-1920-1938` are Western + BERLIN, which sum to a median
**65.6%** of the Reich. Same whole, same count of parts, opposite conclusions. So a row here is keyed on
the exact SET of parts present, and a reader must not read "2 of 3" as a quantity.

THE LABEL TREE USES THE LONGEST PROPER PREFIX, not any prefix. `Germany Western trizone` is a child of
`Germany Western`, not of `Germany`; attributing it to `Germany` makes `Germany` look like it has four
children, and then requiring all four to be present in a cell excludes every cell there is. My first
version did exactly that and the Germany control -- the case the file was built on -- did not appear in
the output at all. A screen whose own worked example is absent is not returning a clean result, it is
broken, so the tree is built from immediate parents only.

WHAT IT CANNOT DO. The prefix tree only finds hierarchies the source spells out in its label text
(`China 22 provinces`, `French North Africa Algeria`), and only where a SPACE or COLON separates the
two -- see the separator note in the tree. A whole and a part named differently -- `Korea`
and `Japanese Korea`, `USSR` and `Russian Federation` -- are invisible here and need the alias or
composition registries. And the identity is only testable where the source prints both in the same
cell, so a `subset` verdict may mean the panel is missing a part rather than the source being
inconsistent.

Usage:
  python3 pipelines/polity-autoimprove/36_label_hierarchy_identity.py            # report only
  python3 pipelines/polity-autoimprove/36_label_hierarchy_identity.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/36_label_hierarchy_identity.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import collections
import csv
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "label_hierarchy_identity.csv")
MATCHED = os.path.join(STATE, "matched_rows.parquet")

MIN_CELLS = 3        # two cells cannot separate an identity from a coincidence, EXCEPT under
                     # exact_identity_below_floor(): see its docstring for the one narrow exemption
TOL = 0.02           # "sums to the whole" band; the Germany control sits at 0.000
EXACT_SHARE = 0.80   # a verdict needs most of its cells inside TOL, not just the median

FIELDS = ("source", "whole_label", "n_kids", "n_parts_present", "parts_present", "cells",
          "exact_cells", "median_ratio", "min_ratio", "max_ratio", "verdict", "items")


def _n(x, nd=4):
    f = float(x)
    return str(int(f)) if f == int(f) and abs(f) < 1e15 else repr(round(f, nd))


def classify(n_kids: int, n_present: int, median: float, exact_share: float) -> str:
    """The four classes in the docstring. `mixed` is deliberate: a group whose cells disagree is a
    finding about the group, not something to force into one of the other three."""
    near_one = abs(median - 1.0) <= TOL and exact_share >= EXACT_SHARE
    if near_one:
        if n_present == 1:
            return "duplicate" if n_kids == 1 else "duplicate_of_whole_by_one_child"
        return "partition" if n_present == n_kids else "partition_of_present_parts"
    if median > 1.0 + TOL:
        return "overlap"
    if median < 1.0 - TOL:
        # A SHORTFALL IS ONLY A FINDING WHEN EVERY NAMED CHILD IS PRESENT. One small child obviously
        # sums to less than its parent -- `Canada Newfoundland` is 0.4% of Canada, which is arithmetic
        # working correctly, not a defect. Left undistinguished, that expected case was 17 of the 20
        # shortfalls here and would have been the table's dominant class, inviting a reader to treat
        # the count as a defect count.
        return "subset_all_parts" if n_present == n_kids else "subset_partial_parts"
    return "mixed"


def is_round(v: float) -> bool:
    """A value a coincidence could reach. Small round numbers match anything -- the floor discipline
    used by 16_source_splices.py and 25_same_polity_overlaps.py for the same reason."""
    a = abs(float(v))
    return a == 0 or (a >= 10 and a % 10 == 0)


def exact_identity_below_floor(present, klist, vals) -> bool:
    """Keep a group with fewer than MIN_CELLS cells when a SINGLE cell is already proof.

    THE CASE THIS EXISTS FOR, and it is a case the floor hid from the tool built to find it. fao1952
    prints `Korea`, `Korea South` and `Korea North`, and in the one cell carrying all three:

        commercial nitrogenous fertilizers, consumption, 1949    108.9  =  98.9 + 10.0

    That settles a question two issues had left open -- whether the bare `Korea` label means the
    peninsula or the ROK -- and it settles it inside the disputed years. But it is ONE cell, so
    MIN_CELLS = 3 dropped it, and the group survived only as a 21-cell `n_parts_present = 1` row at a
    median 0.53, which proves nothing on its own and should not have (issue 355).

    THE FLOOR IS STILL DOING ITS JOB FOR EVERYTHING ELSE. The exemption is deliberately narrow: EVERY
    named child present (so nothing is missing from the sum), EVERY cell exact (not a median), at least
    two children (a single child equal to its parent is a duplicate, and one cell cannot tell that from
    a coincidence), and the whole's value NOT round in any cell. 108.9 = 98.9 + 10.0 carries four
    significant digits; 100 = 90 + 10 would be admitted by arithmetic alone and is worth nothing.
    """
    if len(present) != len(klist) or len(klist) < 2:
        return False
    if not all(abs(r - 1.0) <= TOL for r, _, w in vals):
        return False
    # AT LEAST ONE cell must have a non-round whole, not every cell. Requiring it of all of them was
    # too strict and excluded a plainly real identity: fao1952 `British Borneo` = Brunei + North
    # Borneo + Sarawak twice over, 770 = 35 + 295 + 440 at 1937 and 953 = 47 + 335 + 571 at 1951. The
    # first total is round, so an all() dropped the pair -- while a three-term sum landing exactly in
    # two independent years is much stronger evidence than the single cell this exemption was written
    # for. The guard is still load-bearing: it is what keeps a lone 100 = 90 + 10 out.
    return any(not is_round(w) for _, _, w in vals)


def build(matched: str) -> list[dict]:
    import pandas as pd

    d = pd.read_parquet(matched)
    d = d[d.value.notna() & d.country.notna()]
    # Variant labels differing only in whitespace/case are one label here: issue 449 measured that they
    # never collide on a cell, so collapsing them cannot merge two observations into one.
    lab = d.country.str.replace(r"\s+", " ", regex=True).str.strip().str.lower()
    # `year` and `period` are complementary in this panel (issue 310), so one column identifies the
    # observation's time for both annual rows and the yearbooks' multi-year averages.
    when = d.period.where(d.period.notna(), d.year.astype("string"))
    d = d.assign(_lab=lab, _when=when)

    rows = []
    for src, g in d.groupby("source", sort=True):
        labs = sorted(g._lab.unique())
        parent = {}
        for b in labs:
            # THE SEPARATOR MUST BE A SPACE OR A COLON, not any non-alphanumeric character. A
            # hyphen joins the two halves of ONE name: `guinea-bissau` is not a part of `guinea`, and
            # accepting it put a fabricated hierarchy in this table at a plausible-looking 0.89 ratio
            # across 8 cells (`mitchell` 0.96 across 12). Nothing in the numbers would have exposed it
            # -- only reading which label had been made a child of which.
            cands = [a for a in labs if a != b and b.startswith(a) and b[len(a)] in " :"]
            if cands:
                parent[b] = max(cands, key=len)      # IMMEDIATE parent only: see the docstring
        kids = collections.defaultdict(list)
        for b, a in parent.items():
            kids[a].append(b)

        for whole, klist in sorted(kids.items()):
            groups = collections.defaultdict(list)
            for _, gg in g[g._lab.isin([whole] + klist)].groupby(
                    ["item", "indicator", "unit", "_when"], dropna=False):
                wr = gg[gg._lab == whole]
                pr = gg[gg._lab != whole]
                if wr.empty or pr.empty:
                    continue
                w = float(wr.value.sum())
                if w == 0:                            # a zero whole makes the ratio meaningless
                    continue
                key = tuple(sorted(pr._lab.unique()))
                groups[key].append((float(pr.value.sum()) / w, str(gg["item"].iloc[0]), w))

            for present, vals in sorted(groups.items()):
                if len(vals) < MIN_CELLS and not exact_identity_below_floor(present, klist, vals):
                    continue
                ratios = sorted(v for v, _, _ in vals)
                mid = ratios[len(ratios) // 2] if len(ratios) % 2 else (
                    ratios[len(ratios) // 2 - 1] + ratios[len(ratios) // 2]) / 2
                exact = sum(1 for r in ratios if abs(r - 1.0) <= TOL)
                items = sorted({i for _, i, _ in vals})
                rows.append({
                    "source": src,
                    "whole_label": whole,
                    "n_kids": len(klist),
                    "n_parts_present": len(present),
                    "parts_present": " | ".join(present),
                    "cells": len(ratios),
                    "exact_cells": exact,
                    "median_ratio": _n(mid),
                    "min_ratio": _n(ratios[0]),
                    "max_ratio": _n(ratios[-1]),
                    "verdict": classify(len(klist), len(present), mid, exact / len(ratios)),
                    "items": " | ".join(items[:6]) + (" ..." if len(items) > 6 else ""),
                })
    rows.sort(key=lambda r: (r["source"], r["whole_label"], r["n_parts_present"], r["parts_present"]))
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
    a = ap.parse_args()

    if not os.path.exists(MATCHED):
        print(f"input absent ({MATCHED}); nothing to do", file=sys.stderr)
        return 0
    rows = build(MATCHED)
    by = collections.Counter(r["verdict"] for r in rows)
    sub = sum(1 for r in rows if int(r["cells"]) < MIN_CELLS)
    print(f"{len(rows)} prefix-hierarchy group(s) carrying the whole and at least one part, with at "
          f"least {MIN_CELLS} cells or ({sub}) a single exact full-partition identity")
    for v, n in sorted(by.items()):
        print(f"  {v:34} {n}")
    for r in rows:
        print(f"  {r['source']:9} {r['whole_label'][:26]:28} {r['n_parts_present']}/{r['n_kids']} kids  "
              f"cells={r['cells']:>3} exact={r['exact_cells']:>3}  ratio={float(r['median_ratio']):>8.4f}"
              f"  {r['verdict']}")

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
