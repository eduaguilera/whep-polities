#!/usr/bin/env python3
"""Which layer-B iia cells did one yearbook volume print a power of ten off, where another volume
prints the same cell right? (issue 424)

WHY THIS EXISTS. A x10 shift in one cell sits under every magnitude detector here: `27_series_collapses`
and `18_isolated_spikes` both use a 20x floor, and a 10x dip at a plausible number opens no gap and
clears every bound. What CAN convict it is the source disagreeing with itself: IIA volumes overlap
(iia_1933_34 and iia_1938_39 both print 1933; iia_1933_34 also reprints 1929-1932), so the same cell
is sometimes printed twice. `26_edition_conflicts.py` pairs those printings on the RAW (label,
product) key; this tool pairs them on the LAYER-B key (layer-B label, item, unit, year) -- through
`iia_label_provenance.csv` and `item_equivalences.csv` -- and then asks which side layer B carries
and which side the series itself supports.

That re-keying matters: a product renamed between volumes (`cotton` in iia_1933_34, `cotton: ginned`
in iia_1938_39) is invisible to the raw-keyed table and lands on one layer-B item here. Pairs of
DIFFERENT raw products are admitted only when (a) both map to the item with an approved equivalence
verdict and (b) neither volume prints both products for the cell -- i.e. a rename, not two materials
(tunisia's natural phosphate and superphosphate both feed `p`, in both volumes) and not a recorded
item defect (`linseed` on `flax fibre and tow`).

THE VERDICT IS THE SERIES', NOT THE FACTOR'S. A power-of-ten disagreement says the two printings
differ; it cannot say which is wrong, and both directions occur. iia_1938_39 prints hops AREA in a
unit ten times smaller (issue 416), so czech republic's 1933 hops area of 10,267 ha in iia_1933_34 is
RIGHT and the 103,000 beside it is the unit change -- although it is exactly the "smaller value in
iia_1933_34" shape of the other cells. So each pair is judged against the nearest dated neighbour on
either side (within 3 years) of the same layer-B series, with the value-scale rules applied to the
neighbours (data/final/source_value_scale_corrections.csv; a rule on the cell itself is ignored, so
the verdict never depends on its own correction):

    carried_convicted   layer B's value is within 2x of NEITHER neighbour, the other volume's is
                        within 2x of BOTH -- the cell is repairable by the factor
    carried_consistent  the reverse: layer B carries the side the series supports
    undecided           anything else, including a missing neighbour on either side
    not_in_layer_b      layer B carries neither printed value for the cell

`carried_convicted` rows must each be covered by a cell rule in the value-scale table, and every cell
rule must be a `carried_convicted` row; scripts/validate_value_scale_corrections.py checks both ways
from this table, in CI.

Needs the raw IIA extract and layer B, which are absent in CI, so the table is tracked and the gate
reads it -- the same arrangement as 26_edition_conflicts.py.

Usage:
  python3 pipelines/polity-autoimprove/46_volume_scale_conflicts.py            # report only
  python3 pipelines/polity-autoimprove/46_volume_scale_conflicts.py --write    # refresh the table
  python3 pipelines/polity-autoimprove/46_volume_scale_conflicts.py --check    # fail if stale
"""
from __future__ import annotations

import argparse
import collections
import csv
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
STATE = os.path.join(HERE, "state")
OUT = os.path.join(STATE, "volume_scale_conflicts.csv")
DEFAULT_RAW = os.path.expanduser(os.environ.get(
    "WHEP_IIA_RAW",
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx"))
sys.path.insert(0, HERE)

# Same 5% window as 26_edition_conflicts.py and 07_yield_consistency.py, so the three cannot disagree
# about what "a power of ten" means.
POW10_WINDOW = 0.05
# A neighbour must agree within this band; the same 2x the value-scale gate uses for siblings.
BAND = 2.0
# How far a neighbour may sit from the cell. Three years is the widest gap inside the 1929-1938
# overlap the volumes share.
REACH = 3
RAW_UNITS = {"hectares": "ha", "tonnes": "tonnes"}
APPROVED = frozenset({"approved_rename", "approved_aggregation"})

FIELDS = ["layer_b_label", "item", "unit", "year", "carried_volume", "carried_value", "carried_raw",
          "other_volume", "other_value", "other_raw", "ratio", "factor", "prev_year", "prev_value",
          "next_year", "next_value", "verdict", "rule_divisor"]


def _nz(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def _fmt(v) -> str:
    if v is None:
        return ""
    if isinstance(v, float):
        return repr(round(v, 6))
    return str(v)


def within(a, b) -> bool:
    return a is not None and b is not None and a > 0 and b > 0 and 1 / BAND <= a / b <= BAND


def build(raw_path, lb_path=None):
    import pandas as pd
    import extdata
    import matchlib

    lab2lb = collections.defaultdict(set)
    with open(os.path.join(STATE, "iia_label_provenance.csv"), newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            for col in ("dominant_raw_label", "raw_label"):
                v = (r.get(col) or "").strip().lower()
                if v:
                    lab2lb[v].add(r["layer_b_label"])
    prod2item = collections.defaultdict(dict)       # raw product -> {normalised item: verdict}
    with open(os.path.join(STATE, "item_equivalences.csv"), newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            prod2item[r["raw_product"].strip().lower()][_nz(r["item"])] = r["verdict"]

    lb = pd.read_parquet(lb_path or extdata.LAYER_B)
    lb = lb[(lb["source"] == "iia") & ~lb["is_aggregate"].fillna(False).astype(bool)
            & lb["year"].notna() & lb["value"].notna()].copy()
    rules = matchlib.load_value_scale_corrections(extdata.VALUE_SCALE_CORRECTIONS)
    lb["div"], _ = matchlib.value_scale_divisors(lb, rules)
    lb["ni"] = lb["item"].map(_nz)
    lb["y"] = pd.to_numeric(lb["year"], errors="coerce").astype(int)
    item_name = dict(zip(lb["ni"], lb["item"]))
    # key -> year -> [(printed value, divisor the value-scale rules give it)]. Neighbours are read
    # divided; the cell itself is read as printed, so its own rule never decides its verdict.
    series = collections.defaultdict(lambda: collections.defaultdict(list))
    for c, ni, u, y, v, d in zip(lb["country"], lb["ni"], lb["unit"], lb["y"], lb["value"], lb["div"]):
        series[(c, ni, u)][int(y)].append((float(v), float(d)))

    raw = pd.read_excel(raw_path)
    raw = raw[raw["variable"].astype(str).str.lower().isin(["production", "area"])]
    raw = raw.assign(y=pd.to_numeric(raw["year"], errors="coerce"))
    raw = raw[raw["y"].notna() & raw["value"].notna()]
    # (layer-B label, item, unit, year) -> volume -> {(value, raw label, raw product, verdict)}
    cells = collections.defaultdict(lambda: collections.defaultdict(set))
    for lab, prod, unit, y, v, vol in zip(raw["country"], raw["product"], raw["unit"], raw["y"],
                                          raw["value"], raw["yearbook"]):
        u = RAW_UNITS.get(str(unit).strip().lower())
        if u is None:
            continue
        p = str(prod).strip().lower()
        items = prod2item.get(p) or {}
        for target in lab2lb.get(str(lab).strip().lower(), ()):
            for ni, verdict in items.items():
                cells[(target, ni, u, int(y))][str(vol)].add((float(v), str(lab).strip().lower(), p, verdict))

    out = []
    for key in sorted(cells):
        vols = cells[key]
        if len(vols) < 2:
            continue
        label, ni, unit, year = key
        if ni not in item_name:
            continue
        names = sorted(vols)
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                va_, vb_ = names[i], names[j]
                prods_a = {p for _, _, p, _ in vols[va_]}
                prods_b = {p for _, _, p, _ in vols[vb_]}
                for a, la, pa, ra in sorted(vols[va_]):
                    for b, lb_, pb, rb in sorted(vols[vb_]):
                        if a <= 0 or b <= 0:
                            continue
                        if pa != pb and not (ra in APPROVED and rb in APPROVED
                                             and pb not in prods_a and pa not in prods_b):
                            continue
                        r = max(a, b) / min(a, b)
                        e = round(math.log10(r))
                        if e < 1 or abs(r / 10 ** e - 1) > POW10_WINDOW:
                            continue
                        out.append(_judge(series, item_name, key, (va_, a, f"{la}|{pa}"),
                                          (vb_, b, f"{lb_}|{pb}")))
    # One row per (cell, carried printing, other printing); a raw cell feeding two products of one
    # item would otherwise repeat.
    seen, rows = set(), []
    for r in out:
        k = tuple(r[f] for f in FIELDS)
        if k not in seen:
            seen.add(k)
            rows.append(r)
    rows.sort(key=lambda r: (r["layer_b_label"], r["item"], r["unit"], r["year"], r["carried_volume"],
                             r["other_volume"], r["carried_raw"], r["other_raw"]))
    return [{k: _fmt(r[k]) for k in FIELDS} for r in rows]


def _judge(series, item_name, key, side_a, side_b):
    label, ni, unit, year = key
    s = series.get((label, ni, unit), {})
    here = s.get(year, [])
    vals = {round(v, 6) for v, _ in here}
    has_a, has_b = round(side_a[1], 6) in vals, round(side_b[1], 6) in vals
    if has_a == has_b:
        carried, other = side_a, side_b
        verdict = "not_in_layer_b" if not has_a else "undecided"
    else:
        carried, other = (side_a, side_b) if has_a else (side_b, side_a)
        verdict = None

    def neighbour(step):
        for d in range(1, REACH + 1):
            got = s.get(year + step * d)
            if got:
                vs = sorted(v / dv for v, dv in got)
                return year + step * d, vs[len(vs) // 2]
        return None, None

    py, pv = neighbour(-1)
    ny, nv = neighbour(+1)
    if verdict is None:
        c_ok = within(carried[1], pv) and within(carried[1], nv)
        o_ok = within(other[1], pv) and within(other[1], nv)
        c_any = within(carried[1], pv) or within(carried[1], nv)
        if o_ok and not c_any:
            verdict = "carried_convicted"
        elif c_ok and not (within(other[1], pv) or within(other[1], nv)):
            verdict = "carried_consistent"
        else:
            verdict = "undecided"
    ratio = other[1] / carried[1]
    factor = 10 ** round(math.log10(ratio))
    rule = ""
    if verdict != "not_in_layer_b":
        divs = {dv for v, dv in here if round(v, 6) == round(carried[1], 6) and dv != 1}
        rule = ";".join(_fmt(float(d)) for d in sorted(divs))
    return {"layer_b_label": label, "item": item_name[ni], "unit": unit, "year": year,
            "carried_volume": carried[0], "carried_value": carried[1], "carried_raw": carried[2],
            "other_volume": other[0], "other_value": other[1], "other_raw": other[2],
            "ratio": round(ratio, 4), "factor": factor if factor >= 1 else float(factor),
            "prev_year": py, "prev_value": pv, "next_year": ny, "next_value": nv,
            "verdict": verdict, "rule_divisor": rule}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=DEFAULT_RAW)
    ap.add_argument("--layer-b", default=None)
    ap.add_argument("--write", action="store_true", help=f"refresh {os.path.relpath(OUT, REPO)}")
    ap.add_argument("--check", action="store_true", help="exit 1 if the tracked table is stale")
    args = ap.parse_args()

    import extdata
    lbp = args.layer_b or extdata.LAYER_B
    for p in (args.raw, lbp):
        if not os.path.exists(p):
            print(f"SKIP: {p} absent on this machine; nothing to do", file=sys.stderr)
            return 0

    rows = build(args.raw, lbp)
    counts = collections.Counter(r["verdict"] for r in rows)
    print(f"power-of-ten disagreements between volumes, on the layer-B key: {len(rows)}")
    for k in sorted(counts):
        print(f"  {k:20} {counts[k]}")
    for r in rows:
        if r["verdict"] == "carried_convicted":
            print(f"  convicted: {r['layer_b_label']} / {r['item']} / {r['unit']} / {r['year']}: "
                  f"{r['carried_value']} ({r['carried_volume']}) vs {r['other_value']} "
                  f"({r['other_volume']}); neighbours {r['prev_value']} / {r['next_value']}; "
                  f"rule {r['rule_divisor'] or 'NONE'}")

    if args.check:
        if not os.path.exists(OUT):
            print(f"MISSING {os.path.relpath(OUT, REPO)}", file=sys.stderr)
            return 1
        with open(OUT, newline="", encoding="utf-8") as fh:
            have = list(csv.DictReader(fh))
        if have != rows:
            print(f"STALE {os.path.relpath(OUT, REPO)}: rerun with --write", file=sys.stderr)
            return 1
        print("table is current")
        return 0

    if args.write:
        from atomic import write_csv_atomic
        write_csv_atomic(OUT, FIELDS, rows)
        print(f"wrote {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
