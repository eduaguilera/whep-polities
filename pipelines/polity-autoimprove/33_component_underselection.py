#!/usr/bin/env python3
"""A layer-B series that consistently publishes the SMALLEST of several raw components (issue 490).

THE SHAPE, and why the existing gate cannot see it. Issue 378 found that an item series can switch raw
product year to year, and 379 gated it on OSCILLATION (A...B...A) because a one-way switch is
indistinguishable from growth. That criterion is sound and it has a blind spot: a series that NEVER
switches, because it consistently picks the *smallest* of several products the source prints side by
side. No oscillation, no level shift, no seam, and every value is plausible for the product it came
from. Eight series are in this state and only ONE of them (`japan / p`) appears in 379's gated table.

THE EXHIBIT. `spain / p / tonnes` reads phosphate ROCK while the same page of the same volume prints
calcium superphosphate:

    1930   rock 5,400   superphosphate 999,607        1932   rock  9,980   superphosphate 994,185
    1931   rock 7,734   superphosphate 887,850        1933   rock 14,507   superphosphate 966,653

15 of 15 attributable cells, worst 185x. `japan / p` reaches 3138x.

ATTRIBUTION IS BY VALUE MATCH AND ONLY WHERE IT IS UNAMBIGUOUS. A layer-B cell is attributed to a raw
product only when EXACTLY ONE same-year product of that item's crosswalk matches its value, so a value
shared by two materials attributes to neither and is not counted in either column.

TWO FILTERS THAT ARE NOT OPTIONAL, both of which changed the answer:

  * ZERO-VALUED CELLS ARE EXCLUDED. A 0 matches every product printing 0. Including them produced a
    headline of 2,160,000x for `germany / p`, which is purely an artefact of dividing by a zero
    denominator, and its attributions are not reliable.
  * A FLOOR OF MIN_CELLS ATTRIBUTABLE CELLS, which excludes the case that found this. `canada / p`
    reads 36 t in 1930 against 16,069 t of calcium superphosphate -- a 446x gap -- but only 3 of its
    cells are non-zero, so it sits below the floor and is an exhibit rather than evidence.

WHY THIS TABLE PINS NO FLOOR AT ALL, unlike `grid_ambiguous_zeros.csv`. That table measures a property
of the SOURCE -- its reporting grid -- which nothing done here can remove, so a floor on its size is
safe and catches a broken regeneration. This defect is fixable in this repo, so a floor on the defect
count would make the fix fail CI: the exact "pin the broken state" error.

The first version of this file floored the DENOMINATOR instead, `n_attributable`, on the reasoning that
"how many cells can be attributed at all" is a property of the data's shape and survives any remedy.
THAT IS WRONG, and it is worth recording because it is a plausible-sounding trap. Attribution works by
matching a layer-B value to exactly one raw product. If the remedy converts `p` to a genuine P2O5
total, the published value equals no single material any more, so attribution fails everywhere and the
DENOMINATOR collapses to zero along with the numerator. Both floors break on a correct fix.

So the count is printed and not pinned, and the residual risk is stated rather than papered over: a
regeneration that silently produces zero rows passes this gate. What the gate does assert is that every
row still satisfies the criterion that made it a finding, which is the same bargain
`validate_cross_label_duplication.py` makes for the same reason.

WHAT IS NOT DECIDED HERE. The remedy. Summing the materials double-counts, because superphosphate is
manufactured FROM phosphate rock, and the item is a nutrient category while the raw figures are
material gross weights at different P2O5 contents (rock ~30%, superphosphate ~18%). So
`item_equivalences.csv`'s `approved_aggregation` verdict describes an intent the data does not
implement and could not implement additively. Issue 490 holds that decision.

Usage:
  python3 pipelines/polity-autoimprove/33_component_underselection.py            # report only
  python3 pipelines/polity-autoimprove/33_component_underselection.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/33_component_underselection.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "component_underselection.csv")
MATCHED = os.path.join(STATE, "matched_rows.parquet")
EQUIV = os.path.join(STATE, "item_equivalences.csv")
PROVENANCE = os.path.join(STATE, "iia_label_provenance.csv")
DEFAULT_RAW = os.path.expanduser(os.environ.get(
    "WHEP_IIA_RAW",
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx"))

# Items whose crosswalk maps several MATERIALS onto one nutrient category. Restricted deliberately:
# these are the pairs `22_item_equivalences.py` marks `approved_aggregation` for a nutrient item, and
# they are where "several products stand side by side in the same cell" is the source's own structure
# rather than an ambiguity.
ITEMS = ("p", "n", "k")
MIN_CELLS = 4           # attributable cells needed before a share means anything
UNDERSEL_SHARE = 0.60   # this fraction of attributable cells must be under-selections
SMALLER_THAN = 0.50     # "under-selected" = the picked product is under half the same-year maximum
TOL = 0.005             # relative tolerance for matching a layer-B value to a raw one

FIELDS = ("source", "label", "item", "unit", "n_attributable", "n_underselected",
          "share_underselected", "worst_ratio", "worst_year", "worst_picked_product",
          "worst_picked_value", "worst_max_value")


def _n(x, nd=4):
    f = float(x)
    return str(int(f)) if f == int(f) and abs(f) < 1e15 else repr(round(f, nd))


def build(matched: str, rawpath: str) -> list[dict]:
    import pandas as pd

    eq = {}
    with open(EQUIV, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r["item"] in ITEMS:
                eq.setdefault(r["item"], set()).add(r["raw_product"].strip().lower())
    lp = {}
    with open(PROVENANCE, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            d = (r.get("dominant_raw_label") or "").strip().lower()
            k = (r.get("layer_b_label") or "").strip().lower()
            if d and k:
                lp[k] = d

    raw = pd.read_excel(rawpath)
    raw = raw[raw.variable.astype(str).str.lower().eq("production")]
    raw = raw.assign(_c=raw.country.astype(str).str.strip().str.lower(),
                     _p=raw["product"].astype(str).str.strip().str.lower(),
                     _y=pd.to_numeric(raw.year, errors="coerce"))
    d = pd.read_parquet(matched)
    d = d[d.source.eq("iia") & d.item.isin(ITEMS) & d.unit.eq("tonnes")
          & d.year.notna() & d.value.gt(0) & d.country.notna()]

    rows = []
    for (label, item), g in d.groupby([d.country.astype(str).str.lower(), "item"], sort=True):
        cands = {lp.get(label, label), label}
        r = raw[raw._c.isin(cands) & raw._p.isin(eq.get(item, set()))]
        if r.empty:
            continue
        n_attr = n_under = 0
        worst = None
        for _, x in g.iterrows():
            yr = r[(r._y == x.year) & (r.value > 0)]
            if yr._p.nunique() < 2:
                continue                       # nothing stands beside it, so nothing to under-select
            hit = yr[(yr.value - x.value).abs() < max(0.5, TOL * abs(x.value))]
            if hit._p.nunique() != 1:
                continue                       # ambiguous value -> attributed to neither
            n_attr += 1
            mx = float(yr.value.max())
            picked = float(hit.value.max())
            if picked < mx * SMALLER_THAN:
                n_under += 1
                ratio = mx / picked
                if worst is None or ratio > worst[0]:
                    worst = (ratio, int(x.year), hit._p.iloc[0], picked, mx)
        if n_attr >= MIN_CELLS and n_under >= n_attr * UNDERSEL_SHARE and worst:
            rows.append({
                "source": "iia", "label": label, "item": item, "unit": "tonnes",
                "n_attributable": n_attr, "n_underselected": n_under,
                "share_underselected": _n(n_under / n_attr),
                "worst_ratio": _n(worst[0]), "worst_year": worst[1],
                "worst_picked_product": worst[2],
                "worst_picked_value": _n(worst[3]), "worst_max_value": _n(worst[4]),
            })
    rows.sort(key=lambda r: (-float(r["worst_ratio"]), r["label"], r["item"]))
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
    ap.add_argument("--raw", default=DEFAULT_RAW)
    ap.add_argument("--write", action="store_true")
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()

    for p in (a.matched, a.raw):
        if not os.path.exists(p):
            print(f"input absent ({p}); nothing to do", file=sys.stderr)
            return 0

    rows = build(a.matched, a.raw)
    tot = sum(int(r["n_underselected"]) for r in rows)
    att = sum(int(r["n_attributable"]) for r in rows)
    print(f"{len(rows)} series publish a minor component as the nutrient category "
          f"({tot} of {att} attributable non-zero cells; floor {MIN_CELLS} cells, "
          f"{UNDERSEL_SHARE:.0%} of them under half the same-year maximum)")
    for r in rows:
        print(f"  {r['label'][:18]:19}{r['item']:3}{r['n_underselected']:>4}/"
              f"{r['n_attributable']:<4} worst {float(r['worst_ratio']):>7.0f}x  "
              f"{r['worst_year']}: {r['worst_picked_product'][:34]:36}"
              f"{float(r['worst_picked_value']):>10,.0f} vs {float(r['worst_max_value']):>10,.0f}")

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
