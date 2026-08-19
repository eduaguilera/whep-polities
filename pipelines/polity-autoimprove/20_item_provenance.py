#!/usr/bin/env python3
"""Which raw IIA label does each layer-B ITEM SERIES come from, not just each label?

`15_label_provenance.py` fingerprints a whole layer-B label against the raw extract and asks which raw
label it came from. That question has the wrong shape for half the cases: a label can be right for one
commodity and wrong for another, and no label-level reroute can fix that, because the alias key is
(label, source, years) with no item dimension.

Measured per (label, item, unit) instead, 11 labels mix territories at the item level (issue 372):

    australia            australia               + australian christmas island   `p` = phosphate
    french polynesia     french oceania          + french oceania: makatea island `p` = phosphate
    austria              austria                 + austria-hungary                fertilizer, n, p
    united states        usa                     + usa and canada                 `n`
    syrian arab republic french syria            + french syria and lebanon       cotton only
    indonesia            dutch east indies       + dutch java and madura
    niger                french niger            + french west africa             cotton only
    papua new guinea     australian papua & ng   + dutch new guinea               cacao
    malaysia             british borneo          + british federated malay states
    china, mainland      china                   + japan: kwantung leased terr.   eggs
    timor-leste          portuguese timor        + portuguese timor and kambing

The two phosphate cases are the most diagnostic: `australia`'s `p` is CHRISTMAS ISLAND's phosphate and
`french polynesia`'s is MAKATEA's -- the great Pacific deposits, worked as dependencies. Read as
national production, either one attributes an island's mining output to a country thousands of km away.

THE DISTINCTNESS FILTER IS WHAT MAKES THIS TRUSTWORTHY, AND IT IS NOT OPTIONAL. A series whose values
are a handful of round numbers matches ANY label containing those numbers -- the same round-placeholder
pathology `17_constant_runs.py` measures. Without MIN_DISTINCT the method "finds" `cameroon <- new
zealand` (cotton seed, 100%), `egypt <- yugoslavia` (olives), `zambia <- uruguay` and `cyprus <-
uruguay`. Unfiltered 43 labels, filtered 11, and every geographic absurdity disappears -- which is the
evidence that the filter discriminates rather than merely shrinking the answer.

A KNOWN FALSE NEGATIVE, recorded because the threshold caused it. `ghana` is a real item-level mixture
-- cotton, cottonseed and groundnuts attribute 100% to `german togoland` while cacao and rubber are
`british gold coast` -- but its Gold Coast leg attributes at only 50%, under SHARE_FLOOR, so only one
source is attributable and the label is not classed as mixed. Raising the floor's reach would admit
noise; lowering it would admit more. The table reports `attributable`/`ambiguous`/`unattributable` per
series so a reader can see what was dropped instead of inferring coverage from silence.

WHY THE SHARE IS NOT A WEIGHT. It counts matched values, all equal. Issue 315 read `ghana` as "mostly
Togo" on a 63% share; per item the dominant series is cacao at a median 244,085 t against Togoland's
whole cacao output of 6,986 t. Many small cotton and groundnut observations outvoted a few very large
cacao ones, so the share measures publication verbosity, not economic weight. Never write "mostly X"
from a share alone.

Usage:
  python3 pipelines/polity-autoimprove/20_item_provenance.py            # report only
  python3 pipelines/polity-autoimprove/20_item_provenance.py --write    # refresh the tracked table
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
OUT = os.path.join(HERE, "state/item_provenance.csv")
DEFAULT_PANEL = os.path.expanduser(
    os.environ.get("WHEP_LAYER_B", "~/Nextcloud/whep/layer_b/consolidated_layer_b.parquet"))
DEFAULT_RAW = os.path.expanduser(os.environ.get(
    "WHEP_IIA_RAW",
    "~/3itkt6h41pb7jdan/2025-10-06_iia-dataframe/outputs/processed data/harmonized_data.xlsx"))

# The raw `variable` column separates trade from output. Matching without it lets a trade tonnage
# match a production tonnage, which is how 315's first pass produced numbers that meant nothing.
PRODUCTION = {"production", "area", "bearing area", "production of cocoons"}

MIN_VALUES = 8        # fewer than this and a share is not a measurement
MIN_DISTINCT = 6      # THE filter: few distinct round values match anything (see the docstring)
SHARE_FLOOR = 0.60    # below this the series is `unattributable`, not "probably X"
MIN_RAW_VALUES = 8    # a raw label too small to fingerprint against is not a candidate


def norm(s) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(s).lower()).strip()


def raw_sets(raw_path):
    """Fingerprint each raw (label, PRODUCT), not each raw label.

    Indexing by label alone unions every product that label carries, and `french syria and lebanon`
    carries 18. A layer-B `grapes` series could then be scored against values that belong to `wine`
    or `olive: oil` -- the same class of error as matching a trade tonnage to a production tonnage,
    which this method already had to correct for once. Per product removes it.

    It also buys a free corroboration the label-level version could not have: the winning raw product
    can be COMPARED to the layer-B item, and a match that respects commodity identity
    (`cottonseed` -> cotton seed, `cacao: raw` -> cacao beans) is much harder to produce by chance
    than one that only respects the numbers. The `product_agrees` column records it.

    Raw product names do NOT resemble layer-B item names -- the raw vocabulary is `grapes: table`,
    `citrus fruits: oranges, other`, `fertilizers: calcium cyanamide` -- so the comparison is on
    shared word stems, and disagreement is reported rather than used to reject a match.
    """
    import pandas as pd
    r = pd.read_excel(raw_path)
    r["c"] = r["country"].astype(str).str.strip().str.lower()
    r["p"] = r["product"].astype(str).str.strip()
    r["v"] = pd.to_numeric(r["value"], errors="coerce")
    r["y"] = pd.to_numeric(r["year"], errors="coerce")
    r = r[r["variable"].isin(PRODUCTION)].dropna(subset=["v", "y"])
    out = {}
    for (c, prod), g in r.groupby(["c", "p"]):
        s = {(int(x.y), round(float(x.v), 1)) for x in g.itertuples()}
        if len(s) >= MIN_RAW_VALUES:
            out[(c, prod)] = s
    return out


# Words that carry no commodity information, so their overlap must not count as agreement.
_STOP = {"of", "and", "the", "other", "raw", "total", "true", "n", "e", "c", "in", "shell",
         "unmanufactured", "green", "dry", "dried", "fibre", "fiber", "beans", "seed", "hen"}


def product_agrees(item: str, product: str) -> str:
    """Do the layer-B item and the winning raw product name a recognisably common commodity?

    Reported, never used to filter: the vocabularies genuinely differ, so a disagreement is a
    prompt to look rather than grounds to reject. `yes` where a non-stop word stem is shared.
    """
    a = {w for w in norm(item).split() if w not in _STOP and len(w) > 2}
    b = {w for w in norm(product).split() if w not in _STOP and len(w) > 2}
    if not a or not b:
        return "unknown"
    if a & b:
        return "yes"
    # stem-prefix match catches cottonseed/cotton, cacao/cacao
    for x in a:
        for y in b:
            if x.startswith(y[:4]) or y.startswith(x[:4]):
                return "yes"
    return "no"


def measure(panel_path, raw_path):
    import pandas as pd
    raw = raw_sets(raw_path)
    d = pd.read_parquet(panel_path)
    if "is_aggregate" in d.columns:
        d = d[~d["is_aggregate"].astype(bool)]
    d = d[d["source"] == "iia"].dropna(subset=["value", "year"])

    rows = []
    for label, g in d.groupby(d["country"].astype(str)):
        for (item, unit), gg in g.groupby([g["item"].map(norm), "unit"]):
            pairs = {(int(x.year), round(float(x.value), 1)) for x in gg.itertuples()}
            distinct = {v for _y, v in pairs}
            rec = {"layer_b_label": label, "item": item, "unit": unit,
                   "n_values": len(pairs), "n_distinct": len(distinct),
                   "raw_label": "", "raw_product": "", "product_agrees": "",
                   "share": "", "status": "", "runner_up": ""}
            if len(pairs) < MIN_VALUES:
                rec["status"] = "too_few_values"
            elif len(distinct) < MIN_DISTINCT:
                # Not "no match found" -- the series CANNOT be fingerprinted, because a handful of
                # round values collides with everything. Saying so is the point.
                rec["status"] = "too_few_distinct"
            else:
                ranked = sorted(((len(pairs & s) / len(pairs), c, prod)
                                 for (c, prod), s in raw.items()), reverse=True)
                # Ambiguity is judged on the LABEL, not the (label, product) pair: two products of
                # one raw label both clearing the floor is not a territorial ambiguity, which is the
                # only kind this table is about.
                over_labels = sorted({c for sh, c, _p in ranked if sh >= SHARE_FLOOR})
                if not over_labels:
                    rec["status"] = "unattributable"
                    if ranked:
                        rec["runner_up"] = f"{ranked[0][1]}/{ranked[0][2]}={ranked[0][0]:.2f}"
                elif len(over_labels) > 1:
                    rec["status"] = "ambiguous"
                    seen, parts = set(), []
                    for sh, c, prod in ranked:
                        if sh >= SHARE_FLOOR and c not in seen:
                            seen.add(c)
                            parts.append(f"{c}/{prod}={sh:.2f}")
                    rec["runner_up"] = ";".join(parts[:3])
                else:
                    rec["status"] = "attributable"
                    rec["raw_label"] = ranked[0][1]
                    rec["raw_product"] = ranked[0][2]
                    rec["product_agrees"] = product_agrees(item, ranked[0][2])
                    rec["share"] = f"{ranked[0][0]:.4f}"
                    nxt = next((r for r in ranked[1:] if r[1] != ranked[0][1]), None)
                    if nxt:
                        rec["runner_up"] = f"{nxt[1]}/{nxt[2]}={nxt[0]:.2f}"
            rows.append(rec)

    by_label = defaultdict(set)
    for r in rows:
        if r["status"] == "attributable":
            by_label[r["layer_b_label"]].add(r["raw_label"])
    mixed = {k for k, v in by_label.items() if len(v) > 1}
    for r in rows:
        r["label_is_mixed"] = "yes" if r["layer_b_label"] in mixed else "no"
    rows.sort(key=lambda r: (r["label_is_mixed"] == "no", r["layer_b_label"],
                             r["item"], r["unit"]))
    return rows, mixed


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--layer-b", default=DEFAULT_PANEL)
    ap.add_argument("--raw", default=DEFAULT_RAW)
    ap.add_argument("--write", action="store_true", help=f"refresh {os.path.relpath(OUT, REPO)}")
    args = ap.parse_args()

    for path, what in ((args.layer_b, "layer-B panel"), (args.raw, "raw IIA extract")):
        if not os.path.exists(path):
            print(f"SKIP: {what} not present at {path}")
            return 0

    rows, mixed = measure(args.layer_b, args.raw)
    counts = defaultdict(int)
    for r in rows:
        counts[r["status"]] += 1
    print(f"iia (label, item, unit) series: {len(rows)}")
    for k in ("attributable", "ambiguous", "unattributable", "too_few_distinct", "too_few_values"):
        print(f"   {k:18} {counts[k]:>5}")
    print(f"\nlabels mixing more than one raw label at the ITEM level: {len(mixed)}")
    for label in sorted(mixed):
        per = defaultdict(list)
        for r in rows:
            if r["layer_b_label"] == label and r["status"] == "attributable":
                per[r["raw_label"]].append(f"{r['item'][:20]} ({r['unit']},{r['n_values']}v)")
        print(f"  {label!r}")
        for c, items in sorted(per.items(), key=lambda t: -len(t[1])):
            print(f"      {c[:42]:44} <- {'; '.join(sorted(items))[:90]}")

    if args.write:
        cols = ["layer_b_label", "item", "unit", "n_values", "n_distinct", "raw_label",
                "raw_product", "product_agrees", "share", "status", "runner_up", "label_is_mixed"]
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(OUT), suffix=".tmp")
        os.close(fd)
        with open(tmp, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=cols)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, OUT)
        print(f"\nwrote {len(rows)} series to {os.path.relpath(OUT, REPO)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
