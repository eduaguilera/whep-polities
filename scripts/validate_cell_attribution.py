#!/usr/bin/env python3
"""Gate `state/cell_attribution.csv` (issues 372, 443) -- CI cannot rebuild it.

The table is derived from the raw IIA extract and the layer-B panel, neither in the repository, so the
generator's `--check` cannot run in CI. Four arms check what the file supports alone, and two of them
reach into other tracked tables:

  A  schema: exactly the generator's columns, every field populated.
  B  internal consistency: `cells_for_this_label` <= `cells_in_series`, both positive; the value is not
     zero (a published 0 matches every raw row printing 0, which is why the generator excludes them);
     at least one product was searched; and the per-series counts agree with the rows actually present.
  C  THE CROSSWALK IS RE-DERIVED. Every `raw_product` must be one `item_equivalences.csv` maps for that
     item. A row naming a product outside the crosswalk is an attribution by string similarity, which
     is exactly what this table is built to avoid.
  D  SCOPE. Every series here must be `unattributable` in `item_provenance.csv`. The table exists to
     fill that status's blind spot, and a row for an `attributable` series would be asserting a second,
     competing provenance for a series that already has one.
  E  BASELINE pins the multi-label splits cited on issues. BIDIRECTIONAL.
  F  `series_time_structure` is RE-DERIVED from the rows' own years by importing the generator's
     time_structure(). It is the column that decides whether a date-keyed reroute is even possible --
     `partition` means there is a boundary year, `interleaved` means the label's own dates carry none --
     so a wrong value here is the most consequential kind of wrong this table can be. 30 of 52
     multi-label series are `interleaved`, so the distinction is not a formality.
"""
from __future__ import annotations

import collections
import csv
import importlib.util
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
TOOL = os.path.join(REPO, "pipelines/polity-autoimprove/38_cell_attribution.py")
TABLE = os.path.join(REPO, "pipelines/polity-autoimprove/state/cell_attribution.csv")
PROVENANCE = os.path.join(REPO, "pipelines/polity-autoimprove/state/item_provenance.csv")
EQUIV = os.path.join(REPO, "pipelines/polity-autoimprove/state/item_equivalences.csv")

# (label, item, unit, raw_label) -> cell count. The splits other issues quote.
BASELINE = {
    # issue 372's Ghana mixture, the case its own 60% share floor hid
    ("ghana", "cotton lint", "tonnes", "british gold coast"): 10,
    ("ghana", "cotton lint", "tonnes", "german togoland"): 10,
    # issue 315/524's Soviet continental halves, and issue 422's Karafuto
    ("russian federation", "cotton lint", "ha", "ussr in asia"): 4,
    ("russian federation", "hempseed", "tonnes", "ussr in europe"): 5,
    ("russian federation", "rapeseed", "ha", "japan: karafuto prefecture"): 4,
}


def load_tool():
    spec = importlib.util.spec_from_file_location("cell_attribution", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    for p in (TABLE, PROVENANCE, EQUIV):
        if not os.path.exists(p):
            print(f"MISSING {p}", file=sys.stderr)
            return 1
    tool = load_tool()
    with open(TABLE, newline="") as fh:
        rdr = csv.DictReader(fh)
        cols = tuple(rdr.fieldnames or ())
        rows = list(rdr)
    if cols != tool.FIELDS:
        print(f"FAIL columns {cols} != generator FIELDS {tool.FIELDS}", file=sys.stderr)
        return 1

    equiv = collections.defaultdict(set)
    with open(EQUIV, newline="") as fh:
        for r in csv.DictReader(fh):
            equiv[r["item"]].add(str(r["raw_product"]).strip().lower())
    with open(PROVENANCE, newline="") as fh:
        prov = {(r["layer_b_label"], r["item"], r["unit"]): r["status"] for r in csv.DictReader(fh)}

    fails = []
    per = collections.Counter()
    tot = collections.Counter()
    for r in rows:
        k = (r["layer_b_label"], r["item"], r["unit"])
        per[(*k, r["raw_label"])] += 1
        tot[k] += 1

    for i, r in enumerate(rows, 2):
        who = f"row {i} ({r['layer_b_label']}/{r['item']}/{r['unit']}/{r['when']})"
        for c in tool.FIELDS:
            if not str(r[c]).strip():
                fails.append(f"{who}: empty {c}")
                break
        else:
            k = (r["layer_b_label"], r["item"], r["unit"])
            try:
                mine, series = int(r["cells_for_this_label"]), int(r["cells_in_series"])
                np_, nc = int(r["n_products_searched"]), int(r["n_raw_rows_in_cell"])
                val = float(r["value"])
            except ValueError as e:
                fails.append(f"{who}: unparseable numeric ({e})")
                continue
            # --- B ---
            if val == 0:
                fails.append(f"{who}: value is 0 -- a published 0 matches every raw row printing 0, so "
                             f"the generator excludes them and an attribution here is meaningless")
            if not 1 <= mine <= series:
                fails.append(f"{who}: cells_for_this_label {mine} outside 1..{series}")
            if np_ < 1 or nc < 1:
                fails.append(f"{who}: n_products_searched {np_} / n_raw_rows_in_cell {nc} must be >= 1")
            if mine != per[(*k, r["raw_label"])]:
                fails.append(f"{who}: cells_for_this_label says {mine} but {per[(*k, r['raw_label'])]} "
                             f"rows carry that label in this series")
            if series != tot[k]:
                fails.append(f"{who}: cells_in_series says {series} but {tot[k]} rows are present")
            # --- C ---
            if r["raw_product"] not in equiv.get(tool.norm(r["item"]), set()):
                fails.append(f"{who}: raw_product {r['raw_product']!r} is not one item_equivalences maps "
                             f"for {r['item']!r} -- an attribution outside the crosswalk")
            # --- D ---
            st = prov.get(k)
            if st is None:
                fails.append(f"{who}: this series has no row in item_provenance.csv at all")
            elif st != "unattributable":
                fails.append(f"{who}: item_provenance says this series is {st!r}, not `unattributable`. "
                             f"This table fills that status's blind spot; a row here asserts a second "
                             f"provenance for a series that already has one")

    # --- F: re-derive the per-series time structure ---
    import re as _re
    spans = collections.defaultdict(dict)
    datable = collections.defaultdict(lambda: True)
    declared = {}
    for r in rows:
        k = (r["layer_b_label"], r["item"], r["unit"])
        declared.setdefault(k, set()).add(r["series_time_structure"])
        m = _re.match(r"^(\d{4})(?:-(\d{4}))?$", r["when"].strip())
        if not m:
            datable[k] = False
            continue
        lo, hi = int(m.group(1)), int(m.group(2) or m.group(1))
        cur = spans[k].get(r["raw_label"])
        spans[k][r["raw_label"]] = (min(lo, cur[0]), max(hi, cur[1])) if cur else (lo, hi)
    for k, decl in sorted(declared.items()):
        if len(decl) > 1:
            fails.append(f"{k}: rows disagree about series_time_structure {sorted(decl)} -- it is a "
                         f"per-series property and must be identical on every row of the series")
            continue
        want = tool.time_structure(spans[k]) if datable[k] else "undatable"
        got = next(iter(decl))
        if got != want:
            fails.append(f"{k}: series_time_structure is {got!r}, but the rows' own years give {want!r} "
                         f"({ {l: v for l, v in sorted(spans[k].items())} })")

    # --- E ---
    for k, want in sorted(BASELINE.items()):
        got = per.get(k, 0)
        if got != want:
            fails.append(f"BASELINE {k}: table has {got} cell(s), baseline says {want}. If the rebuild "
                         f"is right, update BASELINE in the same commit (it is bidirectional)")

    if fails:
        print(f"FAIL {len(fails)} problem(s) in cell_attribution.csv:", file=sys.stderr)
        for f in fails[:40]:
            print(f"  {f}", file=sys.stderr)
        if len(fails) > 40:
            print(f"  ... and {len(fails) - 40} more", file=sys.stderr)
        return 1
    multi = sum(1 for k in tot if len({x for x in per if x[:3] == k}) > 1)
    print(f"OK cell_attribution.csv: {len(rows)} cell(s), {len(tot)} series, {multi} drawing on more "
          f"than one raw label, {len(BASELINE)} baselined split(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
