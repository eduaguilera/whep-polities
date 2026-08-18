#!/usr/bin/env python3
"""Where one series-year carries several rows that nothing in the panel can tell apart.

1,130 `(country, item, unit, source, indicator, year)` groups hold more than one row -- 3,081 rows,
all `fao1952` -- and NO column distinguishes the members: `item_code`, `source_detail`, `period`,
`polity_code` and `iso3c` are identical across every one. The cause is visible in the item labels,
which are collapsed multi-commodity ranges: `horses mules asses` is three species and its `item_code`
is the RANGE `110_117`, so which row is which animal is not recoverable. Afghanistan 1949 reads
1,000 / 500 / 200 under that label.

THE SERIOUS PART IS THE SUBSET WHERE A TOTAL SITS BESIDE ITS OWN PARTS. In 239 of the 1,130 groups the
largest value equals the sum of the rest to within 2%:

    united states  meat        1000 t  1950   10,015 == 4,884 + 4,860 + 271
    italy          grapes      1000 t  1951    7,318 == 4,435 + 2,883
    france         meat        1000 t  1949    1,805 ==   965 +   770 +  70

Summing such a group returns exactly double. And none of the usual defences applies: `is_aggregate`
is `False` on every row and correctly so, because the COUNTRY is not an aggregate -- the aggregation is
on the ITEM axis, which that flag does not describe. `validate_composition_sums.py` reasons about
part/whole POLITIES. `05_magnitude_screen.py` screens series medians.

The other 891 groups are genuine sibling commodities, safe to add up but unlabelled, so no consumer can
say which figure is horses and which is asses. That is a smaller problem and is kept separate.

WHY A TRACKED TABLE. The panel is gitignored and absent in CI, so this writes what it finds and
`scripts/validate_item_axis_aggregates.py` reads it -- the same arrangement as the splice, constant-run,
spike, overlap and provenance tables. The VALUES are written out so the gate can re-derive every
classification instead of trusting it.

WHAT THIS DOES NOT DECIDE. Which row is the total. `largest == sum of rest` is a fingerprint, not a
label: at these magnitudes and with exact equality across 239 groups, coincidence is not a plausible
account of the bulk of them, but it is not proof for any single one. Recovering WHICH commodity each
part is needs the FAO 1952 yearbook pages, one item range at a time.

Usage:
  python3 pipelines/polity-autoimprove/24_item_axis_aggregates.py            # report only
  python3 pipelines/polity-autoimprove/24_item_axis_aggregates.py --write    # refresh the table
"""
from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import tempfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
OUT = os.path.join(HERE, "state/item_axis_aggregates.csv")
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B", "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"))

# The largest value must match the sum of the others this closely to read as a total beside its parts.
TOTAL_TOL = 0.02
# Between TOTAL_TOL and this it is too close to call and is recorded as such rather than forced.
NEAR_TOL = 0.10
COLS = ["source", "country", "item", "unit", "indicator", "year", "n_rows", "values",
        "largest", "sum_of_rest", "ratio", "verdict"]


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def classify(vals):
    v = sorted(vals, reverse=True)
    rest = sum(v[1:])
    if rest <= 0:
        return "inconclusive", rest, None
    ratio = v[0] / rest
    if abs(v[0] - rest) / rest <= TOTAL_TOL:
        return "total_beside_parts", rest, ratio
    if abs(v[0] - rest) / rest <= NEAR_TOL:
        return "near_total", rest, ratio
    return "siblings_only", rest, ratio


def measure(panel_path):
    import pandas as pd
    d = pd.read_parquet(panel_path)
    if "is_aggregate" in d.columns:
        d = d[~d["is_aggregate"].astype(bool)]
    d = d.dropna(subset=["value", "year"])
    d = d[d["value"] > 0]
    d = d.assign(_c=d["country"].map(norm), _i=d["item"].map(norm))

    rows = []
    keys = ["_c", "_i", "unit", "source", "indicator", "year"]
    for k, g in d.groupby(keys, dropna=False):
        if len(g) < 2:
            continue
        vals = [float(x) for x in g["value"]]
        verdict, rest, ratio = classify(vals)
        rows.append({
            "source": k[3], "country": k[0], "item": k[1], "unit": str(k[2]),
            "indicator": "" if k[4] is None or str(k[4]) == "nan" else str(k[4]),
            "year": int(k[5]), "n_rows": len(vals),
            "values": ";".join(f"{v:.4f}".rstrip("0").rstrip(".") for v in sorted(vals, reverse=True)),
            "largest": f"{max(vals):.4f}".rstrip("0").rstrip("."),
            "sum_of_rest": f"{rest:.4f}".rstrip("0").rstrip("."),
            "ratio": "" if ratio is None else f"{ratio:.4f}",
            "verdict": verdict,
        })
    rows.sort(key=lambda r: (r["verdict"], r["source"], r["item"], r["country"], r["year"]))
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layer-b", default=DEFAULT_PANEL)
    ap.add_argument("--write", action="store_true", help=f"refresh {os.path.relpath(OUT, REPO)}")
    args = ap.parse_args()

    if not os.path.exists(args.layer_b):
        print(f"SKIP: layer-B panel not present at {args.layer_b}")
        return 0

    rows = measure(args.layer_b)
    by = Counter(r["verdict"] for r in rows)
    print(f"indistinguishable (series, year) groups: {len(rows)}   "
          f"rows inside them: {sum(r['n_rows'] for r in rows)}")
    for v in ("total_beside_parts", "near_total", "siblings_only", "inconclusive"):
        if by.get(v):
            print(f"   {v:20} {by[v]:>5}")
    print(f"   sources: {dict(Counter(r['source'] for r in rows))}")
    print(f"\nlargest `total_beside_parts` groups:")
    tot = [r for r in rows if r["verdict"] == "total_beside_parts"]
    for r in sorted(tot, key=lambda r: -float(r["largest"]))[:10]:
        print(f"   {r['country'][:16]:18} {r['item'][:26]:28} {r['unit'][:9]:10} {r['year']}  "
              f"{float(r['largest']):>10,.0f} == {r['values'].split(';', 1)[1][:34]}")
    print(f"\n   by item: {dict(Counter(r['item'] for r in tot).most_common(8))}")

    if args.write:
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(OUT), suffix=".tmp")
        os.close(fd)
        with open(tmp, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=COLS)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, OUT)
        print(f"\nwrote {len(rows)} groups to {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
